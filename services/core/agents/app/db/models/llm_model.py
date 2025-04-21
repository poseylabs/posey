from sqlalchemy import (
    Column, String, Boolean, Integer, JSON, ForeignKey, DateTime, func, Float,
    Text, Numeric, UniqueConstraint, PrimaryKeyConstraint, ForeignKeyConstraint, Index # Added Index
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB # Added JSONB
from sqlalchemy.orm import relationship
from ..base import Base
import uuid

class LLMModel(Base):
    __tablename__ = 'llm_models'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='llm_models_pkey'), # Match DB name
        UniqueConstraint('provider_id', 'model_id', name='uq_llm_models_provider_model'), # Match DB name
        ForeignKeyConstraint(['provider_id'], ['llm_providers.id'], name='llm_models_provider_id_fkey'), # Match DB name
        Index('ix_llm_models_name', 'name'), # Added index
    )

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider_id = Column(PGUUID(as_uuid=True), ForeignKey('llm_providers.id'), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    model_id = Column(String(255), nullable=False, index=True) # The actual ID used by the provider API
    context_window = Column(Integer, nullable=False, default=0)
    max_tokens = Column(Integer, nullable=True)
    cost_per_token = Column(Float, nullable=True)
    is_active = Column(Boolean, default=False, nullable=False) # Default to False for new models
    capabilities = Column(JSONB, nullable=False, server_default='[]') # Stored as JSON list/array
    supports_embeddings = Column(Boolean, default=False, nullable=False)
    embedding_dimensions = Column(Integer, nullable=True)
    supports_thinking = Column(Boolean, default=False, nullable=False) # Added
    supports_tool_use = Column(Boolean, default=False, nullable=False) # Added
    supports_computer_use = Column(Boolean, default=False, nullable=False) # Added
    config = Column(JSONB, nullable=False, server_default='{}') # For provider-specific config
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now()) # Add nullable=False
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()) # Add nullable=False

    provider = relationship("LLMProvider", back_populates="models")
    minion_configs = relationship("MinionLLMConfig", back_populates="llm_model")

    def __repr__(self):
        return f"<LLMModel(model_id='{self.model_id}', provider={self.provider.name if self.provider else 'N/A'})>"
