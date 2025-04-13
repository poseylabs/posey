from typing import Dict, Any, Protocol, Optional, Type
from pydantic_ai import RunContext, Agent
from app.config.prompts import PromptLoader
from app.config import logger
from app.config.defaults import LLM_CONFIG
from app.utils.result_types import AgentExecutionResult
import json

class BaseMinion:
    """Base class for all minions with shared functionality"""
    
    name: str
    description: str
    prompts: Dict[str, Any]
    agent: Optional[Agent] = None
    
    def __init__(self, name: str, description: str, prompt_category: str = "agents"):
        """Initialize minion with name, description and load prompts"""
        self.name = name
        self.description = description
        self.prompt_category = prompt_category
        self._load_prompts()
        self.setup()
    
    def _load_prompts(self) -> None:
        """Load prompts from configuration files"""
        try:
            # Load prompts from the corresponding JSON file
            self.prompts = PromptLoader.load_prompt(self.prompt_category, self.name)
            logger.info(f"Loaded prompts for {self.name} minion")
        except Exception as e:
            logger.error(f"Failed to load prompts for {self.name} minion: {e}")
            # Initialize with empty dict to prevent errors
            self.prompts = {}
    
    def setup(self) -> None:
        """Initialize minion-specific components"""
        pass
    
    def create_agent(self, result_type: Optional[Any] = None, model_key: str = "default") -> Agent:
        """Create a properly configured agent with appropriate model and abilities"""
        # Get model configuration for the agent
        model_config = LLM_CONFIG.get(model_key, LLM_CONFIG["default"])
        provider = model_config.get("provider", "anthropic")
        model = model_config.get("model", "claude-3-7-sonnet-latest")
        
        # Enhanced logging for LLM adapter usage
        adapter_module = f"app.llm.adapters.{provider}"
        logger.info(f"[{self.name}] Creating agent with adapter: {provider} (module: {adapter_module})")
        logger.info(f"[{self.name}] Using model: {model}")
        logger.info(f"[{self.name}] Config reference: {model_key}")
        
        # Get system prompt from prompts
        system_prompt = self.get_system_prompt()
        
        # Create and return the agent
        return Agent(
            f"{provider}:{model}",
            system_prompt=system_prompt,
            result_type=result_type
        )
    
    def get_system_prompt(self) -> str:
        """Get the system prompt from loaded configuration"""
        if not self.prompts or "system" not in self.prompts:
            logger.warning(f"No system prompt found for {self.name} minion")
            return f"You are the {self.name} minion. {self.description}"
        
        # If there's a predefined system prompt string, use it
        if isinstance(self.prompts["system"], str):
            return self.prompts["system"]
        
        # If there's a system.base field, use that as the base
        if "base" in self.prompts["system"]:
            base = self.prompts["system"]["base"]
        else:
            base = f"You are the {self.name} minion. {self.description}"
        
        # Combine components if they exist
        components = []
        components.append(base)
        
        if "capabilities" in self.prompts["system"]:
            components.append("\nCapabilities:")
            capabilities = self.prompts["system"]["capabilities"]
            if isinstance(capabilities, list):
                components.extend(capabilities)
            else:
                components.append(capabilities)
        
        if "guidelines" in self.prompts["system"]:
            components.append("\nGuidelines:")
            guidelines = self.prompts["system"]["guidelines"]
            if isinstance(guidelines, list):
                components.extend(guidelines)
            else:
                components.append(guidelines)
                
        if "instructions" in self.prompts["system"]:
            components.append("\nInstructions:")
            instructions = self.prompts["system"]["instructions"]
            if isinstance(instructions, list):
                components.extend(instructions)
            else:
                components.append(instructions)
        
        return "\n".join(components)
    
    def get_task_prompt(self, task_name: str, **kwargs) -> str:
        """Get task prompt with variables substituted"""
        if not self.prompts or "tasks" not in self.prompts or task_name not in self.prompts["tasks"]:
            logger.warning(f"No task prompt found for {task_name} in {self.name} minion")
            return ""
        
        task = self.prompts["tasks"][task_name]
        if isinstance(task, str):
            prompt = task
        elif isinstance(task, dict) and "prompt" in task:
            prompt = task["prompt"]
        else:
            logger.warning(f"Invalid task prompt format for {task_name} in {self.name} minion")
            return ""
        
        # Replace placeholders with values
        for key, value in kwargs.items():
            if isinstance(value, (dict, list)):
                value = json.dumps(value, indent=2)
            placeholder = f"{{{key}}}"
            prompt = prompt.replace(placeholder, str(value))
        
        return prompt
        
    async def execute(self, params: Dict[str, Any], context: RunContext) -> Dict[str, Any]:
        """Execute minion operation"""
        raise NotImplementedError("Minions must implement the execute method")

# For backwards compatibility with Protocol interface
class MinionProtocol(Protocol):
    """Protocol definition for minions - for type checking"""
    
    name: str
    description: str
    
    def setup(self) -> None: ...
        
    async def execute(self, params: Dict[str, Any], context: RunContext) -> Dict[str, Any]: ... 
