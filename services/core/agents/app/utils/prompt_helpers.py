import os
import json

def load_prompts(relative_path: str) -> dict:
    """
    Load a JSON prompt file from a relative path under the /config/prompts directory.
    """
    base_path = os.path.join(os.path.dirname(__file__), "../config/prompts", relative_path)
    with open(base_path, "r", encoding="utf-8") as f:
        return json.load(f)

def getAgentPrompt(agent_name: str) -> dict:
    """
    Get the prompt JSON for a specific agent.
    """
    return load_prompts(f"minions/{agent_name}.json")

def sharedPrompt(group: str) -> dict:
    """
    Get the shared prompt JSON from a specific group.
    """
    return load_prompts(f"shared/{group}.json")

def systemPrompt(prompt_name: str) -> str:
    """
    Retrieve a system-level prompt by key.
    """
    PROMPT = sharedPrompt("system")
    return PROMPT.get(prompt_name, "")

def mergePrompts(orchestrator_prompt: str, instruction_prompt: str, error_prompt: str) -> str:
    """
    Combine the prompts into a composite system prompt.
    """
    return f"{orchestrator_prompt}\n\nInstructions: {instruction_prompt}\n\nNote: {error_prompt}"

def formatSystemSection(system_data: dict) -> str:
    """
    Format the system section from its nested structure into a cohesive string.
    """
    if isinstance(system_data, str):
        return system_data
    
    result = []
    
    # Add the base description
    if "base" in system_data:
        result.append(system_data["base"])
    
    # Add capabilities section if present
    if "capabilities" in system_data and system_data["capabilities"]:
        result.append("\n\nCapabilities:")
        for capability in system_data["capabilities"]:
            result.append(f"- {capability}")
    
    # Add guidelines section if present
    if "guidelines" in system_data and system_data["guidelines"]:
        result.append("\n\nGuidelines:")
        for guideline in system_data["guidelines"]:
            result.append(f"- {guideline}")
    
    return "\n".join(result)

def getSystemPrompt(agent_name: str) -> dict:
    """
    Build the final system prompt for an agent by merging its system prompt, instructions, and shared errors.
    Handles both flat string prompts and nested structured prompts.
    Returns a dictionary with keys 'system', 'instruction', and 'error'.
    """
    PROMPT = getAgentPrompt(agent_name)
    
    # Handle the system section, which could be a string or a nested object
    system_data = PROMPT.get('system', {})
    orchestrator_prompt = formatSystemSection(system_data)
    
    # Get instruction if available, otherwise use empty string
    instruction_prompt = PROMPT.get("instruction", "")
    
    # Get error prompt from shared system prompts
    error_prompt = systemPrompt("error")
    
    # Merge all components
    system_prompt = mergePrompts(orchestrator_prompt, instruction_prompt, error_prompt)

    return {
        "system": system_prompt,
        "instruction": instruction_prompt,
        "error": error_prompt
    } 
