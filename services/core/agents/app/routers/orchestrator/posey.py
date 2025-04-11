from fastapi import APIRouter, HTTPException, Request, Depends
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, UUID4, Field, model_validator
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

class RunRequest(BaseModel):
    """Request model for running Posey"""
    prompt: Optional[str] = None
    messages: Optional[List[Dict[str, str]]] = None
    conversation_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @model_validator(mode='after')
    def validate_input(self) -> 'RunRequest':
        """Validate that either prompt or messages is provided"""
        prompt = self.prompt
        messages = self.messages
        
        if prompt is None and (messages is None or len(messages) == 0):
            raise ValueError("Either 'prompt' or 'messages' must be provided")
            
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
    run_request: RunRequest,
    db_session: AsyncSession = Depends(get_db)
):
    """Run Posey with the given prompt or messages and return a standardized execution response"""
    # Log entry and client status IMMEDIATELY
    request_id = str(uuid4())
    logger.info(f"[RUN_POSEY / {request_id}] Request received.")
    if db._qdrant_client:
        logger.info(f"[RUN_POSEY / {request_id}] db._qdrant_client is SET at request start. Type: {type(db._qdrant_client)}")
    else:
        logger.warning(f"[RUN_POSEY / {request_id}] db._qdrant_client is NONE at request start.")
    
    try:
        # Instantiate agent inside the request handler
        posey_agent = PoseyAgent()

        # Get user preferences from database with defaults fallback
        query = text("""
            SELECT preferences FROM users WHERE id = :user_id
        """)
        result = await db_session.execute(query, {"user_id": request.state.user["id"]})
        row = result.fetchone()
        
        # Use preferences from DB or defaults
        user_prefs = row[0] if row and row[0] else {}
        
        # Build context with user info and preferences
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
            "metadata": run_request.metadata
        }

        # Check if we're using messages or prompt
        if run_request.messages:
            # Add messages to context
            context["messages"] = run_request.messages
            
            # Get the last user message as prompt if no explicit prompt is provided
            if not run_request.prompt:
                user_messages = [m for m in run_request.messages if m["role"] == "user"]
                if user_messages:
                    run_request.prompt = user_messages[-1]["content"]
                else:
                    raise ValueError("No user messages found in the provided messages list")
        
        # Execute Posey with context and get AgentExecutionResult
        logger.info(f"Running Posey agent with {'messages' if run_request.messages else 'prompt'}")
        if run_request.messages:
            logger.info(f"Message count: {len(run_request.messages)}")
            for idx, msg in enumerate(run_request.messages[-3:]):  # Log only the last 3 messages
                logger.info(f"Message {idx}: {msg['role']} - {msg['content'][:100]}...")
        else:
            logger.info(f"Prompt: {run_request.prompt[:100]}...")
        
        start_time = time.time()
        # The PoseyAgent.run method now handles both prompt and message-based inputs
        execution_result = await posey_agent.run(run_request.prompt, context)
        end_time = time.time()
        
        # Log the result
        logger.info(f"Posey agent execution completed in {end_time - start_time:.2f}s")
        logger.info(f"Result type: {type(execution_result)}")
        
        # Construct the API response
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
        logger.info(f"[RUN_POSEY / {request_id}] Request: {json.dumps(run_request.model_dump(), indent=4)}")
        raise HTTPException(status_code=500, detail=str(e))
