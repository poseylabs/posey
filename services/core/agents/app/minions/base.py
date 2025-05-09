from typing import Dict, Any, Protocol, Optional
from pydantic_ai import RunContext, Agent
from app.config.prompts import PromptLoader
from app.config import logger
import json
import re
from app.utils.ability_registry import AbilityRegistry

class BaseMinion:
    """Base class for all minions with shared functionality"""
    name: str
    display_name: str
    description: str
    prompts: Dict[str, Any]
    agent: Optional[Agent] = None
    prompt_category: str

    def __init__(self, name: str, display_name: str, description: str, prompt_category: str = "minions"):
        """Initialize minion with name, display_name, description and load prompts"""
        self.name = name
        self.display_name = display_name
        self.description = description
        self.prompt_category = prompt_category
        self._load_prompts()

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

    async def setup(self, *args, **kwargs) -> None:
        """Initialize minion-specific components. Should be overridden by subclasses.
        Accepts *args and **kwargs for compatibility with calling patterns, even if not used by the base class.
        """
        pass

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

    @staticmethod
    def extract_location_from_query(query: str) -> str:
        """Extract location from user query using regex (e.g., 'weather in Seattle')"""
        match = re.search(r"(?:in|for) ([A-Za-z ,]+)", query, re.IGNORECASE)
        if match:
            return match.group(1).strip().rstrip("?.!")
        return None

    @staticmethod
    def fetch_available_abilities() -> Dict[str, Dict[str, Any]]:
        """Fetch all available abilities and their configurations"""
        # Get abilities from the registry
        registry = AbilityRegistry()
        abilities_list = registry.get_available_abilities()
        
        # Convert to the expected format
        abilities_dict = {}
        for ability in abilities_list:
            # Ensure ability is a dict and has a 'name' key before processing
            if isinstance(ability, dict) and "name" in ability:
                abilities_dict[ability["name"]] = {
                    "description": ability.get("description", ""),
                    "capabilities": ability.get("capabilities", [])
                }
            else:
                logger.warning(f"Skipping ability due to unexpected format or missing name: {ability}")
                
        logger.debug(f"Fetched {len(abilities_dict)} available abilities: {list(abilities_dict.keys())}")
        return abilities_dict

# Optional: Add to __all__ if used in the project
__all__ = ['BaseMinion']
