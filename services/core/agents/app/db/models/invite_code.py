import enum
from datetime import datetime
from sqlalchemy import (
    Column, String, DateTime, Text, func, CheckConstraint
)
from app.db.base import Base

class InviteCode(Base):
    __tablename__ = "invite_codes"
    __table_args__ = (
        CheckConstraint("char_length(code) > 0", name='code_length_check'),
    )

    code = Column(String(255), primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Optional future columns mentioned in SQL:
    # expires_at = Column(DateTime(timezone=True))
    # uses_remaining = Column(Integer)
    # created_by = Column(PGUUID, ForeignKey("users.id")) 