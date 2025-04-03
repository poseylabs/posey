from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class DelegationConfig(BaseModel):
    """Configuration for agent delegation"""
    should_delegate: bool = False
    abilities: List[str] = Field(default_factory=list)
    priority: List[str] = Field(default_factory=list)
    configs: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    fallback_strategies: List[str] = Field(default_factory=list)

class ContentIntent(BaseModel):
    """Model for content intent analysis"""
    primary_intent: str
    secondary_intents: List[str] = Field(default_factory=list)
    requires_memory: bool = False
    memory_operations: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    needs_clarification: bool = False
    clarification_questions: List[str] = Field(default_factory=list)

class ContentAnalysis(BaseModel):
    """Model for content analysis results"""
    intent: ContentIntent  # Changed from Dict to ContentIntent
    delegation: DelegationConfig  # Changed from Dict to DelegationConfig
    reasoning: Optional[str] = None
    confidence: Optional[float] = 0.8 
