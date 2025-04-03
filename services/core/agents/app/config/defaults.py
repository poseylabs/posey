DEFAULT_SETTINGS = {
    "temperature": 0.7,
    "max_tokens": 1000,
    "top_p": 0.95,
    "frequency_penalty": 0.0,
    "presence_penalty": 0.0,
    "config": {
        "context_window": 100000,
        "max_tokens": 4096,
        "default_temp": 0.7
    }
}

OLLAMA_URL = "http://host.docker.internal:11434/v1"

# Default configurations
LLM_CONFIG = {
    "reasoning": {
        "provider": "anthropic",
        "model": "claude-3-7-sonnet-latest",
        **DEFAULT_SETTINGS,
        "capabilities": {
            "tools": True
        }
    },
    "coder": {
        "provider": "anthropic",
        "model": "claude-3-7-sonnet-latest",
        **DEFAULT_SETTINGS,
        "capabilities": {
            "tools": True
        }
    },
    "memory": {
        "provider": "anthropic",
        "model": "claude-3-haiku-latest",
        **DEFAULT_SETTINGS,
        "capabilities": {
            "tools": False
        }
    },
    "default": {
        "provider": "anthropic",
        "model": "claude-3-7-sonnet-latest",
        **DEFAULT_SETTINGS,
        "capabilities": {
            "tools": True
        }
    },
    "fallback": {
        "provider": "anthropic",
        "model": "claude-3-7-sonnet-latest",
        **DEFAULT_SETTINGS,
        "capabilities": {
            "tools": True
        }
    }
}
# LLM_CONFIG = {
#     "reasoning": {
#         "provider": "ollama",
#         "model": "MFDoom/deepseek-r1-tool-calling:8b",
#         "base_url": OLLAMA_URL,
#         "capabilities": {
#             "tools": True
#         }
#     },
#     "coder": {
#         "provider": "ollama",
#         "model": "qwen2.5-coder:7b",
#         **DEFAULT_SETTINGS,
#         "capabilities": {
#             "tools": True
#         }
#     },
#     "default": {
#         "provider": "anthropic",
#         "model": "claude-3-7-sonnet-latest",
#         **DEFAULT_SETTINGS,
#         "capabilities": {
#             "tools": True
#         }
#     },
#     "fallback": {
#         "provider": "ollama",
#         "model": "deepseek-r1:8b",
#         **DEFAULT_SETTINGS,
#         "capabilities": {
#             "tools": False
#         }
#     }
# }

DEFAULT_AGENT_CONFIG = {
    "llm": LLM_CONFIG,
    "memory": {
        "enabled": True,
        "type": "vector",
        "config": {
            "collection": "agent_memory",
            "dimensions": 1536
        }
    },
    "abilities": [],
    "metadata": {}
}

DEFAULT_MINION_CONFIG = {
    "llm": LLM_CONFIG,
    "abilities": [],
    "metadata": {}
}

DEFAULT_ABILITY_CONFIG = {
    "enabled": True,
    "config": {},
    "metadata": {}
}

# Provider-specific defaults
DEFAULT_PROVIDERS = {
    "llm": "anthropic",
    "image": "flux",
    "video": "runway",
    "audio": "musicgen"
}

# Model-specific defaults
DEFAULT_MODELS = {
    "anthropic": "claude-3-sonnet",
    "openai": "gpt-4",
    "ollama": "llama3.2",
    "flux": "flux-pro-1.1-ultra",
    "stability": "stable-diffusion-3.5",
    "dalle": "dall-e-3"
}

# Export all defaults
__all__ = [
    'LLM_CONFIG',
    'DEFAULT_AGENT_CONFIG',
    'DEFAULT_MINION_CONFIG',
    'DEFAULT_ABILITY_CONFIG',
    'DEFAULT_PROVIDERS',
    'DEFAULT_MODELS'
] 
