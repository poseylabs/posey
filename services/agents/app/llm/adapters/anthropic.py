from typing import List, Dict, Any
import json
from app.utils.agent import serialize_context
from app.config import logger

class AnthropicAdapter:
    def __init__(self, client, model):
        self.client = client
        self.model = model

    async def generate_response(self, messages: List[Dict[str, Any]], **kwargs) -> str:
        try:
            # Format messages with tool results if needed
            formatted_messages = []
            for msg in messages:
                content = msg["content"]
                if msg.get("tool_results"):
                    tool_blocks = []
                    for result in msg["tool_results"]:
                        # Ensure result is serializable
                        serialized_result = json.dumps(result, default=serialize_context)
                        tool_blocks.append(f"<tool_result>{serialized_result}</tool_result>")
                    content = f"""{''.join(tool_blocks)}\n\n{content}"""
                
                formatted_messages.append({
                    "role": msg["role"],
                    "content": content
                })

            response = await self.client.messages.create(
                model=self.model,
                messages=formatted_messages,
                **kwargs
            )
            
            return response.content[0].text

        except Exception as e:
            logger.error(f"Error in Anthropic generation: {str(e)}")
            raise 
