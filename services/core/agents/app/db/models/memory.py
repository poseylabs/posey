import enum
from datetime import datetime
from uuid import uuid4
from sqlalchemy import (
    Column, String, DateTime, ForeignKey, Text, func,
    Float, CheckConstraint, PrimaryKeyConstraint, ForeignKeyConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from app.db.base import Base

# Define Enum based on CHECK constraint
class MemoryTypeEnum(enum.Enum):
    fact = 'fact'
    preference = 'preference'
    experience = 'experience'
    skill = 'skill'

class MemoryVector(Base):
    __tablename__ = "memory_vectors"
    __table_args__ = (
        PrimaryKeyConstraint('id', name='memory_vectors_pkey'),
        ForeignKeyConstraint(['agent_id'], ['agents.id'], name='memory_vectors_agent_id_fkey'),
        CheckConstraint("memory_type IN ('fact', 'preference', 'experience', 'skill')", name='valid_memory_type'),
        CheckConstraint("importance_score >= 0 AND importance_score <= 1", name='valid_importance'),
        Index('idx_memory_agent', 'agent_id'),
        Index('idx_memory_categories', 'categories', postgresql_using='gin'),
        Index('idx_memory_temporal', 'temporal_context'),
        Index('idx_memory_type', 'memory_type'),
    )

    id = Column(PGUUID, primary_key=True)
    agent_id = Column(PGUUID, nullable=False) # FK defined in args
    content = Column(Text, nullable=False)
    vector_id = Column(Text, nullable=False)
    memory_type = Column(Text, nullable=False)
    importance_score = Column(Float, default=0.5)
    temporal_context = Column(DateTime(timezone=True), nullable=True)
    categories = Column(ARRAY(Text), default=[])
    mem_metadata = Column(JSONB, name='metadata', default={})
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships (e.g., to Agent if FK exists)
    # agent = relationship("Agent") 