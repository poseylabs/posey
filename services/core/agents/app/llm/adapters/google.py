from typing import List, Dict, Any
import json
from vertexai.language_models import ChatModel
from app.utils.agent import serialize_context
from app.config import logger
import os

class GoogleAdapter:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        # Initialize Google Cloud settings
        os.environ["GOOGLE_API_KEY"] = self.api_key
        
    async def generate_response(self, messages: List[Dict[str, Any]], **kwargs) -> str:
        try:
            # Format messages for Gemini
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
                    "author": "user" if msg["role"] == "user" else "assistant",
                    "content": content
                })

            # Initialize chat model
            chat_model = ChatModel.from_pretrained("gemini-1.0-pro")
            chat = chat_model.start_chat()

            # Send messages and get response
            response = chat.send_message(
                formatted_messages[-1]["content"],  # Send the last message
                **kwargs
            )
            
            return response.text

        except Exception as e:
            logger.error(f"Error in Google Gemini generation: {str(e)}")
            raise 
