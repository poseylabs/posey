from fastapi import APIRouter, HTTPException, Request, Depends, Form, UploadFile, File
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

def format_run_result(result) -> Dict[str, Any]:
    """Format a RunResult into a standardized API response"""
    try:
        # If result is a string representation of RunResult, extract the AgentExecutionResult data
        if isinstance(result, str) and 'AgentExecutionResult' in result:
            # Extract the AgentExecutionResult portion using string manipulation
            start_idx = result.find('AgentExecutionResult(')
            end_idx = result.rfind(')')
            if start_idx != -1 and end_idx != -1:
                exec_result_str = result[start_idx:end_idx+1]
                # Parse the relevant fields
                answer = exec_result_str.split("answer='")[1].split("'")[0] if "answer='" in exec_result_str else ""
                confidence = float(exec_result_str.split("confidence=")[1].split(",")[0]) if "confidence=" in exec_result_str else 0.0
                abilities_used = []
                if "abilities_used=" in exec_result_str:
                    abilities_str = exec_result_str.split("abilities_used=")[1].split("]")[0] + "]"
                    try:
                        abilities_used = eval(abilities_str)
                    except:
                        pass
                
                metadata = {}
                if "metadata=" in exec_result_str:
                    metadata_str = exec_result_str.split("metadata=")[1].split("}")[0] + "}"
                    try:
                        metadata = eval(metadata_str)
                    except:
                        pass
                
                return {
                    "answer": answer,
                    "confidence": confidence,
                    "sources": [
                        {
                            "type": "agent_result",
                            "name": "posey",
                            "data": metadata
                        }
                    ],
                    "metadata": {
                        "processing_time": metadata.get("processing_time", 0.0),
                        "agent_count": metadata.get("agent_count", 0),
                        "abilities_used": abilities_used
                    },
                    "memory_updates": [],
                    "usage": None  # Usage info is lost in string representation
                }

        # Original handling for proper RunResult object
        if hasattr(result, 'data'):
            data = result.data
            return {
                "answer": data.answer if hasattr(data, 'answer') else str(data),
                "confidence": data.confidence if hasattr(data, 'confidence') else 0.0,
                "sources": [
                    {
                        "type": "agent_result",
                        "name": "posey",
                        "data": data.metadata if hasattr(data, 'metadata') else {}
                    }
                ],
                "metadata": {
                    "processing_time": data.metadata.get("processing_time", 0.0) if hasattr(data, 'metadata') else 0.0,
                    "agent_count": len(data.abilities_used) if hasattr(data, 'abilities_used') else 0,
                    "abilities_used": data.abilities_used if hasattr(data, 'abilities_used') else []
                },
                "memory_updates": data.memory_updates if hasattr(data, 'memory_updates') else [],
                "usage": {
                    "requests": result._usage.requests,
                    "request_tokens": result._usage.request_tokens,
                    "response_tokens": result._usage.response_tokens,
                    "total_tokens": result._usage.total_tokens
                } if hasattr(result, '_usage') else None
            }
        
        # Fallback for unexpected result structure
        return {
            "answer": str(result),
            "confidence": 0.0,
            "sources": [{"type": "agent_result", "name": "posey", "data": {}}],
            "metadata": {
                "processing_time": 0.0,
                "agent_count": 0,
                "abilities_used": []
            },
            "memory_updates": [],
            "usage": None
        }
    except Exception as e:
        logger.error(f"Error formatting run result: {str(e)}")
        return {
            "answer": "Error processing response",
            "confidence": 0.0,
            "sources": [{"type": "agent_result", "name": "posey", "data": {}}],
            "metadata": {
                "processing_time": 0.0,
                "agent_count": 0,
                "abilities_used": []
            },
            "memory_updates": [],
            "usage": None
        }

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

        # Instantiate agent using the async factory method
        posey_agent = await PoseyAgent.create(db=db_session)

        # Get user preferences
        query = text("""
            SELECT preferences FROM users WHERE id = :user_id
        """)
        result = await db_session.execute(query, {"user_id": request.state.user["id"]})
        row = result.fetchone()
        user_prefs = row[0] if row and row[0] else {}

        # Build context - include uploaded file info
        context = {
            "user_id": request.state.user["id"],
            "request_id": request_id,
            "conversation_id": run_request.conversation_id,
            "preferences": {
                "llm": {
                    "provider": user_prefs.get("llm", {}).get("provider", LLM_CONFIG["default"]["provider"]),
                    "model": user_prefs.get("llm", {}).get("model", LLM_CONFIG["default"]["model"])
                },
                "image": {
                    "provider": user_prefs.get("image", {}).get("provider", "openai"),
                    "model": user_prefs.get("image", {}).get("model", "dalle-3")
                }
            },
            "metadata": run_request.metadata,
            "messages": run_request.messages, # Use messages from parsed payload
            "uploaded_files": uploaded_file_info # Add info about uploaded files
            # Potential: Pass file objects or paths if saved temporarily
            # "file_objects": files # Be careful with large files in memory
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
        execution_result = await posey_agent.run(prompt, context)
        end_time = time.time()

        # Log the result
        logger.info(f"Posey agent execution completed in {end_time - start_time:.2f}s")
        logger.info(f"Result type: {type(execution_result)}")

        response_data = {
            "answer": execution_result.answer,
            "confidence": execution_result.confidence,
            "sources": [
                {
                    "type": "agent_result",
                    "name": "posey",
                    "data": execution_result.metadata.get('sources', [])
                }
            ],
            "metadata": {
                "processing_time": end_time - start_time,
                "agent_count": execution_result.metadata.get("agent_count", 0),
                "abilities_used": execution_result.abilities_used,
                "model": context["preferences"]["llm"]["model"],
                "provider": context["preferences"]["llm"]["provider"]
            },
            "memory_updates": execution_result.metadata.get("memory_updates", [])
        }
        
        # Add LLM usage data if available
        if hasattr(execution_result, '_usage'):
            response_data["metadata"]["usage"] = {
                'requests': execution_result._usage.requests if hasattr(execution_result._usage, 'requests') else 0,
                'request_tokens': execution_result._usage.request_tokens if hasattr(execution_result._usage, 'request_tokens') else 0,
                'response_tokens': execution_result._usage.response_tokens if hasattr(execution_result._usage, 'response_tokens') else 0,
                'total_tokens': execution_result._usage.total_tokens if hasattr(execution_result._usage, 'total_tokens') else 0
            }
        
        return {
            "success": True,
            "data": response_data
        }

    except Exception as e:
        logger.error(f"[RUN_POSEY / {request_id}] Error running Posey: {str(e)}")
        logger.error(traceback.format_exc())
        # Log payload for debugging, be mindful of sensitive data/large files
        logger.info(f"[RUN_POSEY / {request_id}] Payload (first 200 chars): {payload[:200]}...")
        raise HTTPException(status_code=500, detail=str(e))
