from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.schemas import User
import uuid

async def get_or_create_user(db: AsyncSession, user_id: str) -> User:
    """Get existing user or create if doesn't exist"""
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        user = User(id=user_id)
        db.add(user)
        await db.commit()
        await db.refresh(user)
    
    return user 
