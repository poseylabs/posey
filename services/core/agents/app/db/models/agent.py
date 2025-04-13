from datetime import datetime
from uuid import uuid4
import enum
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, func, Index, PrimaryKeyConstraint, ForeignKeyConstraint, CheckConstraint, text, Integer
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB, ENUM
from sqlalchemy.orm import relationship
from app.db.base import Base

# Define Enums matching PostgreSQL types
class AgentTypeEnum(enum.Enum):
    default = 'default'
    creative = 'creative'
    research = 'research'

class AgentStatusEnum(enum.Enum):
    active = 'active'
    inactive = 'inactive'
    pending = 'pending'
    disabled = 'disabled'

class Agent(Base):
    __tablename__ = "agents"
    __table_args__ = (
        PrimaryKeyConstraint('id', name='agents_pkey'),
        ForeignKeyConstraint(['provider_id'], ['llm_providers.id'], name='agents_provider_id_fkey'),
        ForeignKeyConstraint(['model_id'], ['llm_models.id'], name='agents_model_id_fkey'),
        ForeignKeyConstraint(['created_by'], ['users.id'], name='agents_created_by_fkey'),
        CheckConstraint("status IN ('active', 'inactive', 'pending', 'disabled')", name='agents_status_check'),
        CheckConstraint("type IN ('default', 'creative', 'research')", name='agents_type_check'),
        CheckConstraint("jsonb_array_length(capabilities) >= 0", name='valid_capabilities'),
        CheckConstraint("validate_agent_abilities(capabilities)", name='validate_agent_abilities_check'),
        Index('idx_agents_model_id', 'model_id'),
        Index('idx_agents_provider_id', 'provider_id'),
        Index('idx_agents_status', 'status'),
        Index('idx_agents_type', 'type'),
        Index('idx_agent_type_creative', 'type', postgresql_where=text("type = 'creative'")),
        Index('idx_agents_created_by', 'created_by'),
    )

    id = Column(PGUUID, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    type = Column(ENUM(AgentTypeEnum, name='agent_type', create_type=False), default=AgentTypeEnum.default)
    status = Column(ENUM(AgentStatusEnum, name='agent_status', create_type=False), default=AgentStatusEnum.active)
    config = Column(JSONB, default={})
    provider_id = Column(PGUUID, nullable=True)
    model_id = Column(PGUUID, nullable=True)
    media_generation_config = Column(JSONB, nullable=True, server_default=func.jsonb('{}'))

    # Added columns from 018_agent_capabilities.sql
    capabilities = Column(JSONB, default=[])
    agent_metadata = Column(JSONB, name='metadata', default={})
    training_status = Column(JSONB, default={})
    last_training = Column(DateTime(timezone=True), nullable=True)
    capability_scores = Column(JSONB, default={})

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Added columns based on removed column log
    last_error = Column(JSONB, nullable=True)
    created_by = Column(PGUUID, nullable=True)
    last_active = Column(DateTime(timezone=True), nullable=True)
    error_count = Column(Integer, server_default=text('0'), nullable=True)

    # Define relationships if needed (e.g., to provider, model, projects?)
    # provider = relationship("LLMProvider") # Assuming LLMProvider model exists
    # model = relationship("LLMModel") # Assuming LLMModel model exists
    projects = relationship("Project", back_populates="agent") # Needs back_populates in Project

    # Note: `create_type=False` in ENUM tells SQLAlchemy not to try creating the TYPE
    # again, as it should already exist from your .sql file. 