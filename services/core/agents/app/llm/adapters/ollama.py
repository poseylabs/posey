from .base_adapter import BaseAdapter
from typing import Dict, Any, Optional
import json

class OllamaAdapter(BaseAdapter):
    async def _parse_native_tool_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse native tool response from Ollama"""
        try:
            if isinstance(response, dict) and "tool_calls" in response:
                tool_call = response["tool_calls"][0]
                return {
                    "name": tool_call["function"]["name"],
                    "parameters": tool_call["function"]["arguments"]
                }
        except Exception:
            return None
            
        return None 
