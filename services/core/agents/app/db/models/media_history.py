import enum
from datetime import datetime
from uuid import uuid4
from sqlalchemy import (
    Column, String, DateTime, ForeignKey, Text, func,
    PrimaryKeyConstraint, ForeignKeyConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship
from app.db.base import Base

class MediaGenerationHistory(Base):
    __tablename__ = "media_generation_history"
    __table_args__ = (
        PrimaryKeyConstraint('id', name='media_generation_history_pkey'),
        ForeignKeyConstraint(['user_id'], ['users.id'], name='media_generation_history_user_id_fkey'),
        ForeignKeyConstraint(['agent_id'], ['agents.id'], name='media_generation_history_agent_id_fkey'),
        Index('idx_media_history_agent', 'agent_id'),
        Index('idx_media_history_type', 'media_type'),
        Index('idx_media_history_user', 'user_id'),
    )

    id = Column(PGUUID, primary_key=True)
    user_id = Column(PGUUID, nullable=True)
    agent_id = Column(PGUUID, nullable=True)
    media_type = Column(Text, nullable=False)
    prompt = Column(Text, nullable=False)
    result_url = Column(Text, nullable=True)
    media_metadata = Column(JSONB, name='metadata', default={})
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    # user = relationship("User")
    # agent = relationship("Agent") 