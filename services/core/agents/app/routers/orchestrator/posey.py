from fastapi import APIRouter, HTTPException, Request, Depends, Form, UploadFile, File, Body
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, UUID4, Field, model_validator, ValidationError, ConfigDict
from datetime import datetime
from uuid import uuid4
from ...middleware.response import standardize_response
from ...orchestrators.posey import PoseyAgent
from app.config import logger, db, LLM_CONFIG
from app.db import get_db
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import time
import traceback
from app.utils.minion_registry import MinionRegistry
from app.utils.result_types import AgentExecutionResult
from app.utils.message_handler import extract_messages_from_context
from app.minions.base import BaseMinion
from app.config.prompts.base import get_location_from_ip
from app.models.system import LocationInfo
import markdown
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.tables import TableExtension
from markdown.extensions.nl2br import Nl2BrExtension
from markdown.extensions.smarty import SmartyExtension

router = APIRouter(
    prefix="/orchestrator/posey",
    tags=["posey", "orchestrator"]
)

class AgentExecutionResponse(BaseModel):
    """Standardized response format for agent execution results"""
    message: str
    confidence: float = 0.0
    abilities_used: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    usage: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class AgentMetadata(BaseModel):
    name: str
    description: str
    agent_type: str = Field(..., description="Type of agent (e.g., 'memory', 'code_review')")
    capabilities: List[str]
    status: str = Field(default="active", pattern="^(active|inactive|maintenance)$")
    specialization: List[str] = Field(default_factory=list)
    experience_level: str = Field(default="mid", pattern="^(junior|mid|senior|expert)$")
    metadata: dict[str, Any] = Field(default_factory=dict)

class AgentResponse(BaseModel):
    id: UUID4
    created_at: datetime
    updated_at: datetime
    total_tasks: int = 0
    success_rate: float = 0.0
    average_rating: float = 0.0

class StatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(active|inactive|maintenance)$")

# Define a Pydantic model for incoming messages
class MessageModel(BaseModel):
    id: str | UUID4 # Allow string or UUID from client
    content: str
    role: str
    sender_type: str
    created_at: datetime | str # Allow ISO string or datetime
    metadata: Optional[str] = None # Expect stringified JSON from client
    # Allow any other fields client might send (like legacy 'meta')
    model_config = ConfigDict(extra="allow") 

class RunRequest(BaseModel):
    """Data model for the JSON payload part of the multipart request"""
    # Use the specific MessageModel for validation
    messages: Optional[List[MessageModel]] = None
    conversation_id: Optional[str] = Field(default=None, alias='conversation_id')
    metadata: Dict[str, Any] = Field(default_factory=dict)
    prompt: Optional[str] = None # Keep for potential fallback/logging, though messages are primary

    @model_validator(mode='after')
    def validate_input(self) -> 'RunRequest':
        # Validation might change if 'prompt' is no longer mandatory when 'messages' exists
        if self.messages is None or len(self.messages) == 0:
            if self.prompt is None:
                 raise ValueError("Either 'prompt' or 'messages' must be provided in the payload")
            # If only prompt is given, create a minimal messages list
            # Note: The creation of a dict here is fine, as it will be re-validated if needed,
            # but the main issue is accessing attributes of existing MessageModel objects below.
            self.messages = [MessageModel(role="user", content=self.prompt, id=str(uuid4()), sender_type='unknown', created_at=datetime.utcnow())]
        elif self.prompt is None:
            # If messages exist, derive prompt from last user message for internal use
            # Use attribute access (m.role) here as well
            user_messages = [m for m in self.messages if m.role == "user"]
            if user_messages:
                # Use attribute access (user_messages[-1].content) here as well
                self.prompt = user_messages[-1].content
            else:
                 # This case should ideally not happen if validation is done correctly client-side
                 logger.warning("Received messages list without any user message.")
                 self.prompt = "" # Assign empty string if no user message found

        return self

@router.get("/list", response_model=List[AgentResponse])
@standardize_response
async def list_agents(
    status: Optional[str] = None,
    capability: Optional[str] = None,
    experience_level: Optional[str] = None
):
    """List all agents with optional filtering"""
    try:
        query = "SELECT * FROM {} WHERE type = 'agent'".format(db.couchbase.name)
        params = []

        if status:
            query += " AND status = $1"
            params.append(status)

        if capability:
            query += " AND $2 WITHIN capabilities"
            params.append(capability)

        if experience_level:
            query += " AND experience_level = $3"
            params.append(experience_level)

        # Execute query and return results
        # Implementation depends on your database setup
        return {"success": True, "data": []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/run")
@standardize_response
async def run_posey(
    request: Request,
    db_session: AsyncSession = Depends(get_db),
    # Receive payload as a JSON string in a Form field
    payload: str = Form(...),
    # Receive files
    files: List[UploadFile] = File([]) # Use File([]) for optional list
):
    """Run Posey accepting multipart/form-data with JSON payload and optional files"""
    request_id = str(uuid4())
    logger.info(f"[RUN_POSEY / {request_id}] Request received (multipart/form-data).")
    logger.info(f"[RUN_POSEY / {request_id}] Received {len(files)} file(s).")

    try:
        # Parse the JSON payload string into the RunRequest model
        try:
            run_request_data = json.loads(payload)
            run_request = RunRequest(**run_request_data)
        except json.JSONDecodeError:
            logger.error(f"[RUN_POSEY / {request_id}] Failed to decode JSON payload: {payload[:200]}...")
            raise HTTPException(status_code=400, detail="Invalid JSON payload provided.")
        except ValidationError as e:
            logger.error(f"[RUN_POSEY / {request_id}] Validation error for payload: {e}")
            raise HTTPException(status_code=400, detail=f"Payload validation failed: {e}")

        # --- Always fetch preferences from DB based on authenticated user --- 
        db_user_prefs = {} # Initialize default
        config_source_log = "none (defaulting)"
        try:
            # Ensure user state and ID exist (should be guaranteed by auth middleware)
            if not hasattr(request.state, 'user') or not request.state.user.get('id'):
                logger.error(f"[RUN_POSEY / {request_id}] User ID not found in request.state. Authentication middleware might have failed.")
                raise HTTPException(status_code=401, detail="User authentication context missing.")
            
            user_id = request.state.user['id']
            logger.info(f"[RUN_POSEY / {request_id}] Always fetching preferences from DB for user_id: {user_id}")
            query_prefs = text("SELECT preferences FROM users WHERE id = :user_id")
            result_prefs = await db_session.execute(query_prefs, {"user_id": user_id})
            row_prefs = result_prefs.fetchone()
            db_prefs_data = row_prefs[0] if row_prefs and row_prefs[0] else None
            
            if isinstance(db_prefs_data, dict):
                logger.info(f"[RUN_POSEY / {request_id}] Successfully fetched preferences from database.")
                logger.debug(f"[RUN_POSEY / {request_id}] Preferences from DB: {db_prefs_data}")
                db_user_prefs = db_prefs_data # Store fetched prefs
                config_source_log = "database"
            elif db_prefs_data is not None:
                logger.warning(f"[RUN_POSEY / {request_id}] Preferences found in DB for user {user_id} but are not a dictionary (type: {type(db_prefs_data)}). Using empty dict.")
                # config_source_log remains 'none (defaulting)'
            else:
                logger.warning(f"[RUN_POSEY / {request_id}] No preferences found in DB for user {user_id}. Using empty dict.")
                # config_source_log remains 'none (defaulting)'
            
        except HTTPException as http_exc: # Re-raise HTTPException
            raise http_exc
        except Exception as db_err:
            logger.error(f"[RUN_POSEY / {request_id}] Error fetching preferences from DB: {db_err}", exc_info=True)
            config_source_log = "none (db_error)"

        # --- Merge with Payload Preferences (Payload takes priority) --- 
        final_user_prefs = db_user_prefs.copy() # Start with DB prefs
        payload_prefs = run_request_data.get("metadata", {}).get("preferences")
        
        if payload_prefs and isinstance(payload_prefs, dict):
            logger.info(f"[RUN_POSEY / {request_id}] Found preferences in request payload. Merging with DB preferences (payload takes priority).")
            logger.debug(f"[RUN_POSEY / {request_id}] Preferences from Payload: {payload_prefs}")
            final_user_prefs.update(payload_prefs) # Merge, payload overwrites duplicates
            if config_source_log == "database":
                config_source_log = "database_and_payload"
            else:
                config_source_log = "payload_only"
        else:
            logger.info(f"[RUN_POSEY / {request_id}] No valid preferences found in request payload metadata. Using only DB preferences (if any).")
            # config_source_log remains as determined by DB fetch
            
        # Log the final source and content of user_prefs being used
        logger.debug(f"[RUN_POSEY / {request_id}] Final user_prefs used (source: {config_source_log}): {final_user_prefs}")

        # Log file details
        uploaded_file_info = []
        for file in files:
            logger.info(f"[RUN_POSEY / {request_id}] File: {file.filename}, Type: {file.content_type}, Size: {file.size}")
            uploaded_file_info.append({
                "filename": file.filename,
                "content_type": file.content_type,
                "size": file.size
            })
            # Potential: Save files temporarily or process them here if needed before passing to agent
            # Example: content = await file.read()

        # Get registry from app state
        try:
            registry: MinionRegistry = request.app.state.minion_registry
        except AttributeError:
            logger.critical(f"[RUN_POSEY / {request_id}] MinionRegistry not found in app state. Ensure it's initialized correctly.")
            raise HTTPException(status_code=500, detail="Internal server error: Orchestrator configuration failed.")

        # Get pre-initialized minions from app state
        try:
            initialized_minions: Dict[str, BaseMinion] = request.app.state.initialized_minions
            if not initialized_minions:
                logger.warning(f"[RUN_POSEY / {request_id}] No minions were pre-initialized during startup. Posey may lack capabilities.")
        except AttributeError:
             logger.critical(f"[RUN_POSEY / {request_id}] initialized_minions not found in app state. Startup initialization likely failed.")
             raise HTTPException(status_code=500, detail="Internal server error: Orchestrator configuration failed (minions).")

        # Instantiate agent using the async factory method, passing initialized minions AND preferences
        posey_agent = await PoseyAgent.create(
            db=db_session, 
            registry=registry, 
            initialized_minions=initialized_minions,
            user_preferences=final_user_prefs # Pass the potentially merged preferences
        )

        # --- Determine Location (Prefs or IP Fallback) --- 
        final_location: Optional[Dict[str, Any]] = None
        # 1. Check user preferences (assuming location might be stored directly)
        prefs_location = final_user_prefs.get("location")
        if prefs_location and isinstance(prefs_location, dict):
             # Assuming it's already a dict matching LocationInfo structure
             try:
                  # Validate structure slightly
                  LocationInfo(**prefs_location) 
                  final_location = prefs_location
                  logger.info(f"[RUN_POSEY / {request_id}] Using location from user preferences.")
             except ValidationError:
                  logger.warning(f"[RUN_POSEY / {request_id}] Location in preferences is not a valid LocationInfo structure: {prefs_location}. Proceeding without location from prefs.")
        elif prefs_location: # If it exists but isn't a dict
             logger.warning(f"[RUN_POSEY / {request_id}] Location in preferences is not a dictionary: {prefs_location}. Proceeding without location from prefs.")

        # 2. Fallback to IP lookup if not found/valid in prefs
        if final_location is None:
             logger.info(f"[RUN_POSEY / {request_id}] Location not found in preferences, attempting IP lookup.")
             try:
                  location_from_ip: Optional[LocationInfo] = get_location_from_ip()
                  if location_from_ip:
                       final_location = location_from_ip.model_dump(exclude_none=True) # Convert model to dict
                       logger.info(f"[RUN_POSEY / {request_id}] Using location determined from IP: {final_location.get('city')}, {final_location.get('region')}")
                  else:
                       logger.warning(f"[RUN_POSEY / {request_id}] IP lookup did not return location information.")
             except Exception as ip_err:
                  logger.error(f"[RUN_POSEY / {request_id}] Error during IP location lookup: {ip_err}", exc_info=True)
        # --- End Determine Location --- 

        # Build context - include uploaded file info AND determined location
        context = {
            "user_id": request.state.user["id"],
            "request_id": request_id,
            "conversation_id": run_request.conversation_id,
            "preferences": {
                "llm": {
                    "provider": final_user_prefs.get("preferred_provider", LLM_CONFIG["default"]["provider"]),
                    "model": final_user_prefs.get("preferred_model", LLM_CONFIG["default"]["model"])
                },
                "image": {
                    "provider": final_user_prefs.get("preferred_image_provider", "openai"), # Assuming keys like these
                    "model": final_user_prefs.get("preferred_image_model", "dall-e-3")
                },
                 # Include other relevant preferences from user_prefs
                 **{k: v for k, v in final_user_prefs.items() if k not in ['preferred_provider', 'preferred_model', 'preferred_image_provider', 'preferred_image_model', 'location']} # Exclude location here
            },
            "location": final_location, # Add the determined location object/dict
            "metadata": run_request.metadata,
            # Convert MessageModel objects to dicts for downstream compatibility
            "messages": [m.model_dump() if hasattr(m, "model_dump") else dict(m) for m in run_request.messages] if run_request.messages else [],
            "uploaded_files": uploaded_file_info # Add info about uploaded files
        }

        # Derive prompt from messages (RunRequest validator handles this)
        prompt = run_request.prompt
        if not prompt and run_request.messages:
             # Use attribute access (m.role) for MessageModel objects
             user_messages = [m for m in run_request.messages if m.role == "user"]
             if user_messages:
                 # Use attribute access (user_messages[-1].content)
                 prompt = user_messages[-1].content

        if not prompt:
             logger.error(f"[RUN_POSEY / {request_id}] Could not determine prompt from messages.")
             raise HTTPException(status_code=400, detail="Could not determine prompt from messages.")

        logger.info(f"[RUN_POSEY / {request_id}] Running Posey agent with messages and {len(files)} files.")
        start_time = time.time()
        # Pass the prompt derived from messages (or originally provided)
        # --- Use the enhanced context --- 
        execution_result: AgentExecutionResult = await posey_agent.run(prompt, context)
        end_time = time.time()

        # Log the result
        logger.info(f"Posey agent execution completed in {end_time - start_time:.2f}s")
        logger.info(f"Result type: {type(execution_result)}")

        # Initialize response data with default values
        response_data = {
            "answer": "Error processing response.",
            "confidence": 0.0,
            "sources": [],
            "metadata": {
                "processing_time": end_time - start_time,
                "agent_count": 0,
                "abilities_used": [],
                "model": context["preferences"]["llm"]["model"],
                "provider": context["preferences"]["llm"]["provider"],
                "request_id": request_id,
                "status": "error" # Default to error, update on success
            },
            "memory_updates": []
        }

        # Safely extract data from execution_result
        if isinstance(execution_result, AgentExecutionResult):
            original_answer = execution_result.answer
            response_data["confidence"] = execution_result.confidence
            response_data["sources"] = [
                {
                    "type": "agent_result",
                    "name": "posey",
                    "data": execution_result.metadata.get('sources', [])
                }
            ]
            
            # --- Generate contentHtml --- 
            generated_html = None
            if isinstance(original_answer, str):
                try:
                    generated_html = markdown.markdown(
                        original_answer,
                        extensions=[
                            FencedCodeExtension(),
                            TableExtension(),
                            Nl2BrExtension(),
                            SmartyExtension(),
                        ],
                        output_format='html5'
                    )
                    logger.debug(f"[{request_id}] Successfully converted answer to HTML.")
                except Exception as md_err:
                    logger.error(f"[{request_id}] Error converting answer to HTML: {md_err}", exc_info=True)
            
            # --- Determine final answer field --- 
            # Prioritize raw text if possible, otherwise use original or placeholder
            # Basic check if original answer contains HTML tags
            if isinstance(original_answer, str) and ('<' in original_answer and '>' in original_answer): 
                # If original looks like HTML, maybe use a placeholder or stripped version
                # For now, let's just use the original, as frontend uses contentHtml
                final_answer = original_answer 
                # Alternatively, try stripping (requires library like beautifulsoup4)
                # from bs4 import BeautifulSoup
                # soup = BeautifulSoup(original_answer, 'html.parser')
                # final_answer = soup.get_text()
            else:
                final_answer = original_answer # Assume it was raw text
                
            response_data["answer"] = final_answer
            
            # --- Merge metadata --- 
            merged_metadata = {
                "processing_time": end_time - start_time,
                "request_id": request_id,
                "model": context["preferences"]["llm"]["model"],
                "provider": context["preferences"]["llm"]["provider"],
                **execution_result.metadata,
                "abilities_used": execution_result.abilities_used,
                "status": "success",
                "contentHtml": generated_html # Add the generated HTML here
            }
            response_data["metadata"] = merged_metadata
            response_data["memory_updates"] = execution_result.metadata.get("memory_updates", [])
            
            # Add LLM usage data if available
            if execution_result.metadata.get("usage"):
                 response_data["metadata"]["usage"] = execution_result.metadata["usage"]
            elif hasattr(execution_result, '_usage'): # Fallback
                 response_data["metadata"]["usage"] = {
                    'requests': execution_result._usage.requests if hasattr(execution_result._usage, 'requests') else 0,
                    'request_tokens': execution_result._usage.request_tokens if hasattr(execution_result._usage, 'request_tokens') else 0,
                    'response_tokens': execution_result._usage.response_tokens if hasattr(execution_result._usage, 'response_tokens') else 0,
                    'total_tokens': execution_result._usage.total_tokens if hasattr(execution_result._usage, 'total_tokens') else 0
                 }
        else:
             # Handle unexpected result type
             logger.warning(f"[RUN_POSEY / {request_id}] Unexpected result type: {type(execution_result)}. Attempting to parse.")
             response_data["answer"] = str(execution_result) 
             response_data["metadata"]["status"] = "partial_success"
             response_data["metadata"]["contentHtml"] = None # Ensure it's None here too

        return {
            "success": True, # Indicate API call succeeded, check metadata.status for agent status
            "data": response_data
        }

    except Exception as e:
        logger.error(f"[RUN_POSEY / {request_id}] Error running Posey: {str(e)}")
        logger.error(traceback.format_exc())
        # Log payload for debugging, be mindful of sensitive data/large files
        logger.info(f"[RUN_POSEY / {request_id}] Payload (first 200 chars): {payload[:200]}...")
        # Return error structure consistent with successful run data shape
        error_data = {
             "answer": f"An internal error occurred: {str(e)}",
             "confidence": 0.0,
             "sources": [],
             "metadata": {
                "processing_time": time.time() - start_time if 'start_time' in locals() else 0,
                "agent_count": 0,
                "abilities_used": [],
                "request_id": request_id,
                "status": "failed",
                "error_message": str(e),
                "contentHtml": None # Ensure contentHtml is None in error case too
             },
             "memory_updates": []
        }
        return {
             "success": False,
             "data": error_data
        }

@router.post(
    "/run", 
    response_model=AgentExecutionResult,
    summary="Run the Posey Orchestrator Agent",
    description="Executes the main Posey orchestration pipeline with the given prompt or messages."
)
async def run_posey_orchestration(
    fastapi_request: Request,
    payload: Dict[str, Any] = Body(...),
    db_session: AsyncSession = Depends(get_db),
):
    """Endpoint to run the full Posey agent orchestration."""
    start_time = time.time()
    request_id = str(uuid4())

    try:
        registry: MinionRegistry = fastapi_request.app.state.minion_registry
    except AttributeError:
        logger.critical("MinionRegistry not found in app state. Ensure it's initialized correctly.")
        raise HTTPException(status_code=500, detail="Internal server error: Orchestrator configuration failed.")
        
    try:
        user_id: str = fastapi_request.state.user_id 
    except AttributeError:
        logger.error(f"Request {request_id} failed: User ID not found in request state.")
        raise HTTPException(status_code=401, detail="Authentication required or user context missing.")

    logger.info(f"Received request {request_id} for Posey orchestration from user {user_id}")

    # Prepare context using the raw payload dictionary
    initial_context = payload.get("context", {}) or {} # Get context dict or default to empty
    initial_context["user_id"] = user_id
    initial_context["request_id"] = request_id
    
    # Extract prompt and messages directly from the payload dict
    prompt = payload.get("prompt")
    messages_data = payload.get("messages") # Messages might be passed directly
    
    # Use extract_messages_from_context which handles None prompt/messages
    messages = extract_messages_from_context(initial_context, prompt, messages_data)

    if not messages:
        logger.error(f"Request {request_id} failed: No prompt or messages could be determined from payload.")
        raise HTTPException(status_code=400, detail="Prompt or messages list is required in payload.")

    try:
        # Get pre-initialized minions from app state
        try:
            initialized_minions: Dict[str, BaseMinion] = fastapi_request.app.state.initialized_minions
            if not initialized_minions:
                 logger.warning(f"Request {request_id}: No minions were pre-initialized during startup. Posey may lack capabilities.")
        except AttributeError:
            logger.critical(f"Request {request_id}: initialized_minions not found in app state. Startup initialization likely failed.")
            raise HTTPException(status_code=500, detail="Internal server error: Orchestrator configuration failed (minions).")
            
        # Get user preferences
        query = text("""
            SELECT preferences FROM users WHERE id = :user_id
        """)
        result = await db_session.execute(query, {"user_id": user_id})
        row = result.fetchone()
        user_prefs = row[0] if row and row[0] else {}

        # Create PoseyAgent instance, passing the registry and session
        posey_agent = await PoseyAgent.create(
            db=db_session, 
            registry=registry,
            initialized_minions=initialized_minions,
            user_preferences=user_prefs
        )
        
        # Run the orchestration
        result: AgentExecutionResult = await posey_agent.run_with_messages(
            messages=messages,
            context=initial_context
        )
        
        end_time = time.time()
        logger.info(f"Posey orchestration request {request_id} completed internally in {end_time - start_time:.2f} seconds.")

        # Add request_id and processing_time to metadata if not present
        if not result.metadata:
             result.metadata = {}
        result.metadata.setdefault("request_id", request_id)
        result.metadata.setdefault("processing_time", end_time - start_time)

        # Check if the result indicates a pending background task
        if result.metadata and result.metadata.get("status") == "pending" and result.metadata.get("task_id"):
            logger.info(f"Orchestration resulted in a pending background task: {result.metadata['task_id']}")
            # Return the AgentExecutionResult containing the pending status and task_id
            # The schema already supports this via the metadata field.
            return result
        else:
            # Return the final computed result directly
            logger.info(f"Orchestration completed with a direct result.")
            return result

    except ValueError as ve:
        logger.error(f"Request {request_id} failed due to value error: {ve}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Request {request_id} failed due to unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred during orchestration.")
