from datetime import datetime
from sqlalchemy import (
    Column, String, DateTime, Text, func
)
from app.db.base import Base

class Migration(Base):
    __tablename__ = "migrations"

    version = Column(String(255), primary_key=True)
    applied_at = Column(DateTime(timezone=True), server_default=func.now()) 