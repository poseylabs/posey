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
        UniqueConstraint('provider_id', 'model_id', name='llm_models_provider_id_model_id_key'), # Match DB name
        ForeignKeyConstraint(['provider_id'], ['llm_providers.id'], name='llm_models_provider_id_fkey'), # Match DB name
        Index('ix_llm_models_name', 'name'), # Added index
    )

    id = Column(PGUUID, primary_key=True)
    provider_id = Column(PGUUID, nullable=False) # FK defined in args
    name = Column(String(255), nullable=False, index=True) # Keep index?
    model_id = Column(String(255), nullable=False)
    context_window = Column(Integer, nullable=False)
    max_tokens = Column(Integer, nullable=True)
    supports_embeddings = Column(Boolean, default=False)
    embedding_dimensions = Column(Integer, nullable=True)
    cost_per_token = Column(Numeric(10, 8), nullable=True)
    is_active = Column(Boolean, default=True)
    capabilities = Column(JSONB, default=[])
    config = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now()) # Add nullable=False
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()) # Add nullable=False

    provider = relationship("LLMProvider", back_populates="models")

    def __repr__(self):
        return f"<LLMModel(model_id='{self.model_id}', provider={self.provider.name if self.provider else 'N/A'})>" 