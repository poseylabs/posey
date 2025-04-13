from sqlalchemy import (
    Column, String, Boolean, Integer, JSON, ForeignKey, DateTime, func,
    PrimaryKeyConstraint, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship
from ..base import Base
import uuid

class LLMProvider(Base):
    __tablename__ = 'llm_providers'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='llm_providers_pkey'),
        UniqueConstraint('name', name='llm_providers_name_key'),
    )

    id = Column(PGUUID, primary_key=True)
    name = Column(String(255), unique=False, nullable=False)
    base_url = Column(String(255), nullable=True)
    api_version = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    models = relationship("LLMModel", back_populates="provider", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<LLMProvider(name='{self.name}', active={self.is_active})>" 