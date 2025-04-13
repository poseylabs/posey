import enum
from datetime import datetime
from uuid import uuid4
from sqlalchemy import (
    Column, String, DateTime, ForeignKey, Text, func,
    Boolean, CheckConstraint, Index, PrimaryKeyConstraint, UniqueConstraint, ForeignKeyConstraint
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from app.db.base import Base

class IntegrationLog(Base):
    __tablename__ = "integration_logs"
    __table_args__ = (
        PrimaryKeyConstraint('id', name='integration_logs_pkey'),
        CheckConstraint("status IN ('success', 'failure', 'pending')", name='valid_status'),
        Index('idx_integration_logs_created_at', 'created_at'),
        Index('idx_integration_logs_status', 'status'),
        Index('idx_integration_logs_type', 'integration_type'),
    )

    id = Column(PGUUID, primary_key=True, default=uuid4)
    integration_type = Column(Text, nullable=False)
    status = Column(Text, nullable=False)
    request_data = Column(JSONB, nullable=True)
    response_data = Column(JSONB, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

class IntegrationConfig(Base):
    __tablename__ = "integration_configs"
    __table_args__ = (
        PrimaryKeyConstraint('id', name='integration_configs_pkey'),
        UniqueConstraint('integration_type', name='uq_integration_configs_integration_type'),
        Index('idx_integration_permissions', 'agent_permissions', postgresql_using='gin'),
    )

    id = Column(PGUUID, primary_key=True, default=uuid4)
    integration_type = Column(Text, nullable=False, unique=True)
    config = Column(JSONB, nullable=False)
    is_active = Column(Boolean, default=True)

    # Added columns from 017_integrations.sql
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    provider = Column(String(100), nullable=False)
    base_url = Column(Text, nullable=True)
    version = Column(String(50), nullable=True)
    auth_type = Column(String(50), nullable=True)
    schema_def = Column(JSONB, name='schema', nullable=False, server_default=func.jsonb('{}')) # Renamed attribute
    agent_permissions = Column(ARRAY(Text), default=[])
    last_used = Column(DateTime(timezone=True), nullable=True)

    # Timestamps (ensure these match final state)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()) 