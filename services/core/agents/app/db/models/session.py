from sqlalchemy import (
    Column, DateTime, Text, func, PrimaryKeyConstraint, ForeignKeyConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship
from app.db.base import Base

class Session(Base):
    __tablename__ = "sessions"
    __table_args__ = (
        PrimaryKeyConstraint('id', name='sessions_pkey'),
        ForeignKeyConstraint(['user_id'], ['users.id'], name='sessions_user_id_fkey', ondelete="CASCADE"),
        Index('idx_sessions_expires', 'expires_at'),
        Index('idx_sessions_token', 'token'),
        Index('idx_sessions_user', 'user_id'),
    )

    id = Column(PGUUID, primary_key=True)
    user_id = Column(PGUUID, nullable=False)
    token = Column(Text, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    session_metadata = Column(JSONB, name='metadata', default={})

    # Relationships
    # user = relationship("User", back_populates="sessions") # Add back_populates="sessions" to User model 