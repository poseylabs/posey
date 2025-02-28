from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod

class BaseAdapter(ABC):
    """Base class for LLM adapters"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.supports_tools = config.get("capabilities", {}).get("tools", False)
        
    async def format_tool_request(self, prompt: str, tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Format a request that includes tool definitions"""
        if self.supports_tools:
            return await self._format_native_tool_request(prompt, tools)
        else:
            return await self._format_simulated_tool_request(prompt, tools)
            
    async def _format_native_tool_request(self, prompt: str, tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Format request for models with native tool support"""
        return {
            "prompt": prompt,
            "tools": tools
        }
        
    async def _format_simulated_tool_request(self, prompt: str, tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Format request for models without native tool support"""
        # Create a system prompt that describes the available tools
        tools_description = "\n".join([
            f"Tool: {tool['name']}\nDescription: {tool['description']}\n"
            f"Parameters: {tool.get('parameters', {})}\n"
            for tool in tools
        ])
        
        system_prompt = f"""You have access to the following tools:

{tools_description}

To use a tool, respond in this format:
<tool_call>
{{
    "name": "tool_name",
    "parameters": {{
        "param1": "value1",
        "param2": "value2"
    }}
}}
</tool_call>

Only call one tool at a time. After calling a tool, wait for the result before proceeding."""

        return {
            "system": system_prompt,
            "prompt": prompt
        }
        
    async def parse_tool_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse response to extract tool calls"""
        if self.supports_tools:
            return await self._parse_native_tool_response(response)
        else:
            return await self._parse_simulated_tool_response(response)
            
    @abstractmethod
    async def _parse_native_tool_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse response from models with native tool support"""
        pass
        
    async def _parse_simulated_tool_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse response from models without native tool support"""
        import re
        
        # Look for tool calls in the format specified in the system prompt
        tool_call_match = re.search(r'<tool_call>\s*({[^}]+})\s*</tool_call>', response)
        if tool_call_match:
            try:
                import json
                tool_call = json.loads(tool_call_match.group(1))
                return {
                    "name": tool_call.get("name"),
                    "parameters": tool_call.get("parameters", {})
                }
            except json.JSONDecodeError:
                return None
                
        return None 
