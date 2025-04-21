from typing import Dict, Any, List, Optional, Union, Literal
from pydantic import BaseModel, Field, ConfigDict

class Param(BaseModel):
    """A simple key-value pair for configuration parameters."""
    key: str = Field(..., description="The name of the parameter.")
    value: Union[str, int, float, bool, None, List[Any], Dict[str, Any]] = Field(..., description="The value of the parameter.")

class DelegationTarget(BaseModel):
    """Represents the request to delegate to a minion or execute an ability."""
    target_type: Literal['minion', 'ability'] = Field(..., description="Specifies whether the target is a minion or an ability (tool).")
    target_key: str = Field(..., description="The unique key of the minion or ability to target.")
    config_params: List[Param] = Field(
        default_factory=list,
        description="Specific parameters needed for this target, represented as a list of key-value pairs."
    )

class DelegationConfig(BaseModel):
    """Configuration for agent delegation or ability execution"""
    should_delegate: bool = Field(False, description="True if any minion or ability needs to be invoked.")
    delegation_targets: List[DelegationTarget] = Field(
        default_factory=list,
        description="List of minions or abilities to invoke, including their specific parameters."
    )

    priority: List[str] = Field(
        default_factory=list,
        description="Ordered list of target_key values (minion keys or ability names) indicating the preferred execution sequence."
    )

    fallback_strategies: List[str] = Field(default_factory=list)

    model_config = ConfigDict(extra='forbid')

class ContentIntent(BaseModel):
    """Model for content intent analysis"""
    primary_intent: str
    secondary_intents: List[str] = Field(default_factory=list)
    requires_memory: bool = False

    memory_operations: List[Param] = Field(
        default_factory=list,
        description="List of key-value pairs representing memory operations (e.g., [{'key': 'action', 'value': 'search'}, {'key': 'query', 'value': 'user question'}])"
    )
    metadata: List[Param] = Field(
        default_factory=list,
        description="List of key-value pairs representing metadata related to the intent."
    )
    needs_clarification: bool = False
    clarification_questions: List[str] = Field(default_factory=list)

    model_config = ConfigDict(extra='forbid')

class ContentAnalysis(BaseModel):
    """Model for content analysis results"""
    intent: ContentIntent
    delegation: DelegationConfig
    reasoning: Optional[str] = None
    confidence: Optional[float] = Field(0.8, description="Confidence score of the analysis (0.0 to 1.0)")

    model_config = ConfigDict(extra='forbid') 
