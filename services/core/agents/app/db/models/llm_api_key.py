from datetime import datetime
from uuid import uuid4
from sqlalchemy import (
    Column, String, DateTime, ForeignKey, Text, func, Boolean
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from app.db.base import Base

class LLMApiKey(Base):
    __tablename__ = "llm_api_keys"

    id = Column(PGUUID, primary_key=True, default=uuid4)
    provider_id = Column(PGUUID, ForeignKey("llm_providers.id"), nullable=True)
    key_name = Column(String(255), nullable=False)
    api_key = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    # provider = relationship("LLMProvider", back_populates="api_keys") 