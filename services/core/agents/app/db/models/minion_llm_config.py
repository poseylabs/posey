from sqlalchemy import Column, String, Boolean, Integer, JSON, ForeignKey, DateTime, func, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ..base import Base
import uuid

class MinionLLMConfig(Base):
    __tablename__ = 'minion_llm_configs'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Link to a specific minion/task type (e.g., 'content_analysis', 'reasoning', 'default')
    # Could also link to a minion_id if you have a Minion table
    config_key = Column(String, unique=True, nullable=False, index=True)
    llm_model_id = Column(UUID(as_uuid=True), ForeignKey('llm_models.id'), nullable=False)
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=1000)
    top_p = Column(Float, default=0.95)
    frequency_penalty = Column(Float, default=0.0)
    presence_penalty = Column(Float, default=0.0)
    # Store other specific settings as JSON
    additional_settings = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship: Use 'llm_model' for the attribute name to match back_populates in LLMModel
    llm_model = relationship("LLMModel", back_populates="minion_configs")

    def __repr__(self):
        return f"<MinionLLMConfig(key='{self.config_key}', model={self.llm_model.model_id if self.llm_model else 'N/A'})>"
