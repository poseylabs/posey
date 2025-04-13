from typing import List, Dict, Any, Optional
from pydantic_ai import RunContext, Agent
import json
import logging
from app.utils.json_encoder import CustomJSONEncoder

logger = logging.getLogger(__name__)

def prepare_system_user_messages(
    system_content: str,
    user_content: str,
    context_data: Optional[Dict[str, Any]] = None
) -> List[Dict[str, str]]:
    """
    Create a simple message array with system and user messages.
    
    Args:
        system_content: Content for the system message
        user_content: Content for the user message
        context_data: Optional data to include in user message
        
    Returns:
        List of message dictionaries with role and content
    """
    messages = [
        {
            "role": "system",
            "content": system_content
        }
    ]
    
    # If we have context data, add it to the user message
    if context_data:
        user_message = f"{user_content}\n\nCONTEXT: {json.dumps(context_data, indent=2, cls=CustomJSONEncoder)}"
    else:
        user_message = user_content
        
    messages.append({
        "role": "user",
        "content": user_message
    })
    
    return messages

def extract_messages_from_context(
    context: Dict[str, Any], 
    default_prompt: Optional[str] = None
) -> List[Dict[str, str]]:
    """
    Extract messages from context if available, or create a basic message array.
    
    Args:
        context: The context dictionary which may contain a messages key
        default_prompt: Default prompt to use if no messages are in context
        
    Returns:
        List of message dictionaries
    """
    # If context contains messages, use them
    if "messages" in context and isinstance(context["messages"], list):
        return context["messages"]
    
    # If we have a prompt in the context, create a single user message
    if "prompt" in context and context["prompt"]:
        return [{"role": "user", "content": context["prompt"]}]
    
    # If we have a default prompt, use that
    if default_prompt:
        return [{"role": "user", "content": default_prompt}]
    
    # No messages could be extracted
    return []

def get_last_user_message(messages: List[Dict[str, str]]) -> Optional[str]:
    """
    Get the content of the last user message in a message list.
    
    Args:
        messages: List of message dictionaries
        
    Returns:
        Content of the last user message, or None if no user messages
    """
    # Use attribute access (m.role) for MessageModel objects
    user_messages = [m for m in messages if hasattr(m, 'role') and m.role == "user"]
    if user_messages:
        # Use attribute access (m.content)
        return user_messages[-1].content
    return None

def add_assistant_message(
    messages: List[Dict[str, str]], 
    content: str
) -> List[Dict[str, str]]:
    """
    Add an assistant message to a message list.
    
    Args:
        messages: List of message dictionaries
        content: Content for the assistant message
        
    Returns:
        Updated message list
    """
    messages.append({
        "role": "assistant",
        "content": content
    })
    return messages

def log_messages(messages: List[Dict[str, str]], max_content_length: int = 200):
    """
    Log message list for debugging.
    
    Args:
        messages: List of message dictionaries
        max_content_length: Maximum length of content to log
    """
    logger.info("=" * 80)
    for i, msg in enumerate(messages):
        logger.info(f"Message {i} - Role: {msg['role']}")
        content = msg['content']
        if len(content) > max_content_length:
            content = f"{content[:max_content_length]}..."
        logger.info(f"Content: {content}")
        logger.info("-" * 40)
    logger.info("=" * 80)

class MessageHandler:
    def __init__(self):
        self.messages = []
        self.tool_usage = {}  # Track tool usage per message
    
    def add_message(self, role: str, content: str, tool_results: List[Dict[str, Any]] = None):
        message = {
            "role": role,
            "content": content
        }
        if tool_results:
            # Ensure tool results are serializable
            serialized_results = json.loads(json.dumps(tool_results, default=serialize_context))
            message["tool_results"] = serialized_results
        self.messages.append(message)
    
    def get_formatted_messages(self) -> List[Dict[str, Any]]:
        """Get messages with proper tool result formatting"""
        formatted = []
        for msg in self.messages:
            content = msg["content"]
            if msg.get("tool_results"):
                tool_blocks = []
                for result in msg["tool_results"]:
                    # Ensure result is serializable
                    serialized_result = json.dumps(result, default=serialize_context)
                    tool_blocks.append(f"<tool_result>{serialized_result}</tool_result>")
                content = f"""{''.join(tool_blocks)}\n\n{content}"""
            
            formatted.append({
                "role": msg["role"],
                "content": content
            })
        return formatted 
