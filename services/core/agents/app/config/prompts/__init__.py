import json
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class PromptLoader:
    _prompts: Dict[str, Any] = {}
    _base_path = Path(__file__).parent

    @classmethod
    def load_prompt(cls, category: str, name: str) -> Dict[str, Any]:
        key = f"{category}/{name}"
        if key not in cls._prompts:
            path = cls._base_path / category / f"{name}.json"
            with open(path) as f:
                cls._prompts[key] = json.load(f)
        return cls._prompts[key]

    @classmethod
    def get_agent_prompt(cls, agent_name: str):
        return cls.load_prompt("agents", agent_name)

    @classmethod
    def get_shared_prompt(cls, name: str):
        return cls.load_prompt("shared", name)

    @classmethod
    def get_prompt_with_shared_config(cls, agent_name: str) -> Dict[str, Any]:
        """
        Load an agent prompt and resolve any shared configurations.
        
        This method loads an agent's configuration and automatically
        resolves and merges any referenced shared configurations.
        
        Args:
            agent_name: The name of the agent
            
        Returns:
            Dict[str, Any]: The complete agent configuration with shared configs resolved
        """
        # Load the agent prompt
        agent_prompt = cls.get_agent_prompt(agent_name)
        
        # Check if it has shared config references
        shared_config = agent_prompt.get("shared_config", {})
        if not shared_config:
            return agent_prompt
        
        # Make a deep copy of the agent prompt to avoid modifying the cached version
        import copy
        result = copy.deepcopy(agent_prompt)
        
        # Process each shared config reference
        for config_key, shared_name in shared_config.items():
            if config_key != "description" and isinstance(shared_name, str):
                try:
                    shared_content = cls.get_shared_prompt(shared_name)
                    
                    # Different handling for response_examples which should map to common_examples
                    if config_key == "response_examples":
                        if "common_examples" in shared_content:
                            # Use common_examples from shared content for response_examples
                            result["response_examples"] = shared_content["common_examples"]
                            logger.info(f"Mapped common_examples from '{shared_name}' to response_examples for agent '{agent_name}'")
                    else:
                        # For other keys, just add the entire shared content to the result
                        if config_key in shared_content:
                            result[config_key] = shared_content[config_key]
                            logger.info(f"Loaded {config_key} from shared config '{shared_name}' for agent '{agent_name}'")
                        else:
                            # If the key isn't directly in shared content, use the entire shared content
                            result[config_key] = shared_content
                            logger.info(f"Loaded entire shared config '{shared_name}' as {config_key} for agent '{agent_name}'")
                except Exception as e:
                    logger.error(f"Failed to load shared config '{shared_name}' for agent '{agent_name}': {e}")
        
        return result

def load_prompt(name: str, prompt_type: Optional[str] = None) -> str:
    """Load a prompt template from file"""
    try:
        base_path = Path(__file__).parent
        
        if prompt_type:
            path = base_path / prompt_type / f"{name}.txt"
        else:
            path = base_path / f"{name}.txt"
            
        if not path.exists():
            raise FileNotFoundError(f"Prompt file not found: {path}")
            
        return path.read_text().strip()
        
    except Exception as e:
        raise ImportError(f"Error loading prompt {name}: {str(e)}")
