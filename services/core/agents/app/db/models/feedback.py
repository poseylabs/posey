import enum
from datetime import datetime
from uuid import uuid4
from sqlalchemy import (
    Column, String, DateTime, ForeignKey, Text, func,
    Integer, CheckConstraint, PrimaryKeyConstraint, ForeignKeyConstraint, Index, Enum
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB, ENUM
from sqlalchemy.orm import relationship
from app.db.base import Base

class AgentFeedback(Base):
    __tablename__ = "agent_feedback"
    __table_args__ = (
        PrimaryKeyConstraint('id', name='agent_feedback_pkey'),
        ForeignKeyConstraint(['agent_id'], ['agents.id'], name='agent_feedback_agent_id_fkey'),
        CheckConstraint("rating >= 1 AND rating <= 5", name='valid_rating'),
        CheckConstraint("feedback_type IN ('rating', 'text', 'issue')", name='valid_feedback_type'),
        CheckConstraint(
            "(feedback_type = 'rating' AND rating IS NOT NULL) OR "
            "(feedback_type IN ('text', 'issue') AND feedback_text IS NOT NULL)",
            name='valid_feedback_content'
        ),
        Index('idx_agent_feedback_agent_id', 'agent_id'),
        Index('idx_agent_feedback_created_at', 'created_at'),
        Index('idx_agent_feedback_type', 'feedback_type'),
    )

    id = Column(PGUUID, primary_key=True)
    agent_id = Column(PGUUID, nullable=False) # FK defined in args
    feedback_type = Column(ENUM('rating', 'text', 'issue', name='feedback_type'), nullable=False)
    rating = Column(Integer, nullable=True)
    feedback_text = Column(Text, nullable=True)
    category = Column(Text, nullable=True)
    feedback_metadata = Column(JSONB, name='metadata', default={}) # Renamed attribute
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships (e.g., to Agent)
    # agent = relationship("Agent") 