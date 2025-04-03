from fastapi import Request, HTTPException
from uuid import UUID
from app.db import db
from app.config import settings

async def check_media_quota(request: Request, agent_id: UUID, media_type: str):
    """Check if agent has exceeded media generation quota"""
    try:
        # Check against configured limits
        media_config = settings.MEDIA_GENERATION.get(media_type, {})
        if not media_config:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported media type: {media_type}"
            )

        # Check database quota
        has_quota = await db.check_media_quota(agent_id, media_type)
        if not has_quota:
            raise HTTPException(
                status_code=429,
                detail=f"Daily {media_type} generation quota exceeded"
            )

        return True
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500,
            detail=f"Error checking media quota: {str(e)}"
        ) 
