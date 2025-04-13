from datetime import datetime
from sqlalchemy import (
    Column, String, DateTime, Text, func
)
from app.db.base import Base

class SeedVersion(Base):
    __tablename__ = "seed_versions"

    version = Column(Text, primary_key=True)
    name = Column(Text, nullable=False)
    applied_at = Column(DateTime(timezone=True), server_default=func.now()) 