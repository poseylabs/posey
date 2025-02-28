from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any

class TimeRange(BaseModel):
    start: Optional[str] = None
    end: Optional[str] = None

class AgentDelegation(BaseModel):
    required: bool = False
    primary_agent: Optional[str] = None
    supporting_agents: List[str] = Field(default_factory=list)
    delegation_reason: Optional[str] = None

class SearchAnalysis(BaseModel):
    requires_memory_search: bool = Field(default=True)
    enhanced_query: str
    search_categories: List[str] = Field(default_factory=lambda: ["general"])
    relevance_threshold: float = Field(default=0.7)
    context_boost: Dict[str, float] = Field(
        default_factory=lambda: {
            "technical": 1.0,
            "personal": 1.0,
            "recent": 1.0,
            "temporal": 1.0
        }
    )
    time_range: TimeRange = Field(default_factory=TimeRange)
    agent_delegation: AgentDelegation = Field(default_factory=AgentDelegation)

    @property
    def memory_search(self) -> Dict[str, Any]:
        """Compatibility layer for older code expecting dictionary access"""
        return {
            "required": self.requires_memory_search,
            "enhanced_query": self.enhanced_query,
            "search_categories": self.search_categories,
            "relevance_threshold": self.relevance_threshold,
            "context_boost": self.context_boost,
            "time_range": self.time_range.dict() if self.time_range else {}
        }