from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import Column, String, DateTime
from app.config import Base
import json

class User(Base):
    __tablename__ = "users"
    
    # ... other columns ...
    metadata = Column(JSONB, nullable=True)
    
    def update(self, **kwargs):
        if 'metadata' in kwargs:
            # Convert dict to JSON string and then to JSONB-compatible format
            if isinstance(kwargs['metadata'], dict):
                kwargs['metadata'] = kwargs['metadata']  # SQLAlchemy will handle JSONB conversion
            elif isinstance(kwargs['metadata'], str):
                kwargs['metadata'] = json.loads(kwargs['metadata'])
        
        for key, value in kwargs.items():
            setattr(self, key, value) 
