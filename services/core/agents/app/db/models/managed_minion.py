from sqlalchemy import (
    Column, String, Boolean, JSON, DateTime, func, Text
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from ..base import Base
import uuid # Keep uuid import consistent if other models use it

class ManagedMinion(Base):
    __tablename__ = 'managed_minions'

    # Unique key derived from the entry point name (e.g., 'research')
    minion_key = Column(String(255), primary_key=True)
    
    display_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Reference to the entry point (e.g., 'app.minions.research:ResearchMinion')
    # We store this to load the class later
    entry_point_ref = Column(String(512), nullable=False, unique=True)
    
    # Flag to enable/disable the minion at runtime
    is_active = Column(Boolean, default=False, nullable=False, index=True)
    
    # Source indicates if it's built-in or from a third-party package
    source = Column(String(50), default='core', nullable=False, index=True)
    
    # Optional JSON field for minion-specific configurations
    configuration = Column(JSONB, nullable=True, server_default='{}')
    
    # List of abilities this minion provides (for dynamic mapping)
    associated_abilities = Column(JSONB, nullable=True, server_default='[]')
    
    # Standard timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<ManagedMinion(key='{self.minion_key}', active={self.is_active}, source='{self.source}')>" 