from datetime import datetime
from uuid import uuid4
from sqlalchemy import (
    Column, String, DateTime, ForeignKey, Text, func
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship
from app.db.base import Base

class AgentTrainingHistory(Base):
    __tablename__ = "agent_training_history"

    id = Column(PGUUID, primary_key=True, default=uuid4)
    agent_id = Column(PGUUID, ForeignKey("agents.id", ondelete="CASCADE"), nullable=True) # Assuming FK to agents
    capability = Column(Text, nullable=False)
    training_data = Column(JSONB, nullable=False)
    results = Column(JSONB, nullable=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(Text, default='pending')
    metrics = Column(JSONB, default={})

    # Relationships
    # agent = relationship("Agent") 