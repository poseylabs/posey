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
        UniqueConstraint('slug', name='llm_providers_slug_key'),
    )

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), unique=False, nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    api_base_url = Column("base_url", String(255), nullable=True)
    api_key_secret_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    models = relationship("LLMModel", back_populates="provider", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<LLMProvider(name='{self.name}', slug='{self.slug}', active={self.is_active})>" 