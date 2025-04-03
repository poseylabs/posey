"""Utility modules for the Posey agents service"""

from .agent import create_agent, AgentExecutionResult, run_agent_with_messages
from .message_handler import (
    prepare_system_user_messages,
    extract_messages_from_context,
    get_last_user_message,
    add_assistant_message,
    log_messages
)

__all__ = [
    # Agent utilities
    'create_agent', 
    'AgentExecutionResult',
    'run_agent_with_messages',
    
    # Message handling utilities
    'prepare_system_user_messages',
    'extract_messages_from_context',
    'get_last_user_message',
    'add_assistant_message',
    'log_messages'
]
