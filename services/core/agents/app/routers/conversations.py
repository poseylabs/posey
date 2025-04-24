from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
from sqlalchemy import select
from pydantic import ValidationError

from app.db import get_db
from app.models.api import ConversationCreate, ConversationResponse, MessageCreate, MessageResponse
from app.models.schemas import Conversation, ConversationMessage, User
from app.models.responses import StandardResponse
from app.config import logger
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/conversations", tags=["conversations"])

logger.info("Conversations router initialized")

@router.get("/", response_model=StandardResponse[List[ConversationResponse]])
async def list_conversations(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """List conversations"""
    try:
        logger.info(f"User: {request.state.user['id']}")
        logger.info(f"Request method: {request.method}")
        logger.info(f"Request URL: {request.url}")

        stmt = (
            select(
                Conversation.id,
                Conversation.user_id,
                Conversation.title,
                Conversation.status,
                Conversation.meta,
                Conversation.created_at,
                Conversation.updated_at,
                Conversation.project_id
            )
            .where(Conversation.user_id == request.state.user["id"])
            .order_by(Conversation.created_at.desc())
        )
        
        logger.debug(f"SQL Query: {stmt}")
        
        result = await db.execute(stmt)
        conversations = result.mappings().all()
        logger.info(f"Found {len(conversations)} conversations")
        
        return StandardResponse.success_response([
            ConversationResponse(
                id=conv['id'],
                user_id=conv['user_id'],
                title=conv['title'],
                status=conv['status'],
                meta=conv['meta'],
                project_id=conv['project_id'],
            ) for conv in conversations
        ])
    except AttributeError as e:
        logger.error(f"Table reflection error: {str(e)}")
        return StandardResponse.success_response([])
    except Exception as e:
        logger.error(f"Error in list_conversations: {str(e)}")
        logger.exception("Full traceback:")
        raise HTTPException(status_code=500, detail="Internal server error")

# Start new conversation
@router.post("/", response_model=StandardResponse[ConversationResponse])
async def create_conversation(
    conversation: ConversationCreate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Create new conversation"""
    try:
        # Ensure user exists
        user_id = request.state.user['id']
        user = await get_user(db, user_id)

        # Create conversation
        new_conversation = Conversation(
            user_id=user_id,
            title=conversation.title,
            meta=conversation.meta,
            project_id=conversation.project_id,
            status="new"
        )
        db.add(new_conversation)
        await db.commit()
        await db.refresh(new_conversation)
        
        return StandardResponse.success_response(ConversationResponse.from_orm(new_conversation))
        
    except Exception as e:
        logger.error(f"Error creating conversation: {str(e)}")
        logger.exception("Full traceback:")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Error creating conversation")

# Add message to conversation
@router.post("/{conversation_id}/message", response_model=StandardResponse[MessageResponse])
async def add_message(
    request: Request,
    conversation_id: UUID,
    message: MessageCreate,
    db: AsyncSession = Depends(get_db)
):
    """Add a message to a conversation"""
    logger.debug("=== Starting add_message handler ===")
    logger.debug(f"conversation_id: {conversation_id}")
    logger.debug(f"message: {message}")
    logger.debug(f"user: {request.state.user}")

    try:
        # Validate conversation exists and belongs to user
        stmt = select(Conversation).where(Conversation.id == conversation_id)
        logger.debug(f"Executing query: {stmt}")
        
        result = await db.execute(stmt)
        convo = result.scalar_one_or_none()
        
        if not convo:
            logger.error(f"Conversation {conversation_id} not found")
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        logger.info(f"Found conversation: {convo.id}")
        logger.info(f"Conversation user_id: {convo.user_id}")
        logger.info(f"Current user id: {request.state.user['id']}")
        
        # Convert both to strings before comparison to handle UUID vs string issues
        convo_user_id = str(convo.user_id).lower()
        current_user_id = str(request.state.user["id"]).lower()
        
        logger.info(f"Comparing {convo_user_id} == {current_user_id}")
        
        if convo_user_id != current_user_id:
            logger.error(f"Access denied - conversation belongs to {convo_user_id}, request from {current_user_id}")
            raise HTTPException(status_code=403, detail="Access denied")

        # The raw content is already passed correctly from the frontend
        # for both user and AI messages. No need for special AI handling here.
        content = message.content
        # if message.sender_type == "ai":
        #     if hasattr(message.content, "data") and hasattr(message.content.data, "answer"):
        #         content = message.content.data.answer
        #     elif isinstance(message.content, dict) and "answer" in message.content:
        #         content = message.content["answer"]
        #     else:
        #         content = str(message.content)

        # Log the received metadata type and value before creating the DB object
        logger.debug(f"Type of message.metadata before DB save: {type(message.metadata)}")
        logger.debug(f"Value of message.metadata before DB save: {message.metadata!r}") # Use !r for repr

        # Create message
        db_message = ConversationMessage(
            id=uuid4(),
            conversation_id=conversation_id,
            content=content,
            role=message.role,
            sender_type=message.sender_type,
            meta=message.metadata
        )
        
        db.add(db_message)
        await db.commit()
        await db.refresh(db_message)

        # Log the type AFTER refreshing from DB to see what SQLAlchemy loaded
        logger.debug(f"Type of db_message.meta AFTER DB refresh: {type(db_message.meta)}")
        logger.debug(f"Value of db_message.meta AFTER DB refresh: {db_message.meta!r}")

        # --- Workaround for MetaData type issue --- 
        # Attempt to convert db_message.meta to dict if it's not already one
        response_metadata = db_message.meta
        if not isinstance(response_metadata, dict) and response_metadata is not None:
            logger.warning(f"db_message.meta is type {type(response_metadata)}, attempting conversion.")
            try:
                # Common ways to convert custom objects might involve .dict(), .model_dump(), vars()
                if hasattr(response_metadata, 'model_dump'): # Pydantic V2
                    response_metadata = response_metadata.model_dump()
                elif hasattr(response_metadata, 'dict'): # Pydantic V1
                    response_metadata = response_metadata.dict()
                elif hasattr(response_metadata, '__dict__'): # Standard attribute dictionary
                    response_metadata = vars(response_metadata)
                else:
                    logger.error("Cannot automatically convert db_message.meta to dict.")
                    response_metadata = {} # Default to empty dict on failure
            except Exception as conversion_err:
                logger.error(f"Failed to convert db_message.meta to dict: {conversion_err}")
                response_metadata = {} # Default to empty dict on error

        # Final check if conversion worked
        if not isinstance(response_metadata, dict) and response_metadata is not None:
            logger.error("Conversion failed, metadata is still not a dict. Returning empty dict.")
            response_metadata = {}
        # --- End Workaround ---
        
        # Manually construct the response payload, ensuring metadata is a dict
        response_payload = MessageResponse(
            id=db_message.id,
            content=db_message.content, 
            role=db_message.role,
            sender_type=db_message.sender_type,
            created_at=db_message.created_at,
            metadata=response_metadata # Use the explicitly prepared dictionary
        )
        
        return StandardResponse.success_response(response_payload)

    except Exception as e:
        logger.error(f"Error adding message: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add message: {str(e)}"
        )

# Get conversation context
@router.get("/{conversation_id}/context", response_model=StandardResponse[Dict[str, Any]])
async def get_conversation_context(
    request: Request,
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get conversation context"""
    convo = await db.get(Conversation, conversation_id)
    if not convo or convo.user_id != request.state.user["id"]:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return StandardResponse.success_response({
        "context": convo.context,
        "metadata": convo.metadata
    })

@router.post("/{conversation_id}/analyze")
async def analyze_conversation(
    request: Request,
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Analyze conversation"""
    convo = await db.get(Conversation, conversation_id)
    if not convo or convo.user_id != request.state.user["id"]:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Add your conversation analysis logic here
    analysis_result = {"sentiment": "positive", "key_topics": ["ai", "development"]}
    
    return StandardResponse.success_response(analysis_result)

@router.get("/{conversation_id}")
async def get_conversation(
    request: Request,
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a conversation with its messages"""
    logger.info(f"Getting conversation {conversation_id}")
    
    # Get conversation and its messages in a single query using join
    stmt = (
        select(
            Conversation.id.label('conversation_id'),
            Conversation.user_id,
            Conversation.title,
            Conversation.status,
            Conversation.meta.label('metadata'),
            Conversation.project_id,
            Conversation.created_at,
            Conversation.updated_at,
            ConversationMessage.id.label('message_id'),
            ConversationMessage.conversation_id,
            ConversationMessage.content,
            ConversationMessage.role,
            ConversationMessage.sender_type,
            ConversationMessage.meta.label('message_metadata'),
            ConversationMessage.created_at.label('message_created_at')
        )
        .outerjoin(
            ConversationMessage,
            ConversationMessage.conversation_id == Conversation.id
        )
        .where(Conversation.id == conversation_id)
        .order_by(ConversationMessage.created_at)
    )
    
    result = await db.execute(stmt)
    rows = result.mappings().all()
    
    if not rows:
        raise HTTPException(status_code=404, detail="Conversation not found")

    logger.debug(f"Keys in rows[0]: {rows[0].keys()}")

    return {
        'success': True,
        'data': {
            'id': rows[0]['conversation_id'],
            'user_id': rows[0]['user_id'],
            'title': rows[0]['title'],
            'status': rows[0]['status'],
            'metadata': rows[0]['metadata'],
            'project_id': rows[0]['project_id'],
            'created_at': rows[0]['created_at'],
            'updated_at': rows[0]['updated_at'],
            'messages': [
                {
                    'id': row['message_id'],
                    'conversation_id': row['conversation_id'],
                    'content': row['content'],
                    'role': row['role'],
                    'sender_type': row['sender_type'],
                    'metadata': row['message_metadata'],
                    'created_at': row['message_created_at'],
                }
                for row in rows if row['message_id'] is not None
            ]
        },
    }

# Delete conversation
@router.delete("/{conversation_id}")
async def delete_conversation(
    request: Request,
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete conversation"""
    convo = await db.get(Conversation, conversation_id)
    if not convo or convo.user_id != request.state.user['id']:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    await db.delete(convo)
    await db.commit()
    return StandardResponse.success_response(message="Conversation deleted")

# Summarize conversation
@router.post("/{conversation_id}/summarize")
async def summarize_conversation(
    request: Request,
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Generate conversation summary"""
    convo = await db.get(Conversation, conversation_id)
    if not convo or convo.user_id != request.state.user['id']:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Add summarization logic here
    return StandardResponse.success_response({
        "summary": "Conversation summary...",
        "key_points": ["Point 1", "Point 2"]
    })

# Branch conversation
@router.post("/{conversation_id}/branch")
async def branch_conversation(
    request: Request,
    conversation_id: UUID,
    branch_point: UUID,  # Message ID to branch from
    db: AsyncSession = Depends(get_db)
):
    """Create a new conversation branch from a specific point"""
    original = await db.get(Conversation, conversation_id)
    if not original:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Create new conversation with copied context
    new_convo = Conversation(
        id=UUID(),
        title=f"{original.title} (Branch)",
        context=original.context,
        user_id=request.state.user['id'],
        parent_id=conversation_id,
        branch_point=branch_point
    )
    db.add(new_convo)
    await db.commit()
    
    return StandardResponse.success_response(ConversationResponse.from_orm(new_convo))

# Export conversation
@router.get("/{conversation_id}/export")
async def export_conversation(
    request: Request,
    conversation_id: UUID,
    format: str = "json",
    db: AsyncSession = Depends(get_db)
):
    """Export conversation in various formats"""
    convo = await db.get(Conversation, conversation_id)
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    messages = await db.query(ConversationMessage).filter(
        ConversationMessage.conversation_id == conversation_id
    ).order_by(ConversationMessage.created_at).all()
    
    if format == "json":
        return StandardResponse.success_response({
            "conversation": ConversationResponse.from_orm(convo),
            "messages": [MessageResponse.from_orm(m) for m in messages]
        })
    elif format == "markdown":
        return StandardResponse.success_response({
            "content": generate_markdown(convo, messages)
        })

# Generate markdown from conversation and messages
def generate_markdown(conversation, messages):
    """Generate markdown from conversation and messages"""
    result = f"# {conversation.title}\n\n"
    for msg in messages:
        prefix = "🤖 Assistant" if msg.role == "assistant" else "👤 User"
        result += f"### {prefix}\n{msg.content}\n\n"
    return result 

async def get_user(db: AsyncSession, user_id: UUID) -> User:
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user 

