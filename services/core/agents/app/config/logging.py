import logging
import logging.config
import sys
from typing import Optional

# Create logger
logger = logging.getLogger("app")

def setup_logging(log_level: Optional[str] = None) -> None:
    """
    Setup logging configuration with specific logger levels and formatters
    """
    if log_level:
        level = getattr(logging, log_level.upper())
    else:
        level = logging.INFO

    # Define logging configuration
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "detailed": {
                "format": "%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "stream": "ext://sys.stdout",
            },
            "detailed_console": {
                "class": "logging.StreamHandler",
                "formatter": "detailed",
                "stream": "ext://sys.stdout",
            }
        },
        "loggers": {
            "": {  # Root logger
                "handlers": ["console"],
                "level": level,
            },
            "app": {  # Main app logger
                "handlers": ["console"],
                "level": level,
                "propagate": False,
            },
            "app.orchestrators": {  # Orchestrator-specific logger
                "handlers": ["detailed_console"],
                "level": logging.DEBUG,
                "propagate": False,
            },
            "app.utils.agent": {  # Agent utilities logger
                "handlers": ["detailed_console"],
                "level": logging.DEBUG,
                "propagate": False,
            },
            "app.utils.message_handler": {  # Message handler logger
                "handlers": ["detailed_console"],
                "level": logging.DEBUG,
                "propagate": False,
            },
            "app.llm": {  # LLM-specific logger
                "handlers": ["detailed_console"],
                "level": logging.DEBUG,
                "propagate": False,
            },
            "app.llm.adapters": {  # LLM adapters logger
                "handlers": ["console"],
                "level": logging.INFO,
                "propagate": False,
            },
            "app.config": {  # Config logger
                "handlers": ["console"],
                "level": logging.INFO,
                "propagate": False,
            },
            "sqlalchemy.engine": {  # SQL logging
                "handlers": ["console"],
                "level": logging.ERROR,
                "propagate": False,
            },
            "sqlalchemy": {  # All SQLAlchemy components
                "handlers": ["console"],
                "level": logging.ERROR,
                "propagate": False,
            },
            "sqlalchemy.pool": {  # Connection pool logging
                "handlers": ["console"],
                "level": logging.ERROR,
                "propagate": False,
            },
            "sqlalchemy.orm": {  # ORM logging
                "handlers": ["console"],
                "level": logging.ERROR,
                "propagate": False,
            },
        }
    }

    # Apply configuration
    logging.config.dictConfig(logging_config)

    # Set specific module loggers to DEBUG level regardless of overall level
    critical_modules = ["app.orchestrators.posey", "app.utils.agent", "app.utils.message_handler"]
    for module in critical_modules:
        module_logger = logging.getLogger(module)
        module_logger.setLevel(logging.DEBUG)
        if module_logger.level != logging.DEBUG:
            logger.warning(f"Failed to set {module} logger level to DEBUG, current level: {module_logger.level}")
        else:
            logger.info(f"Successfully set {module} logger level to DEBUG")

    # Log startup message
    logger.info(f"Logging configured with level: {log_level or 'INFO'}")
    
    # Print logging levels for key modules
    for module_name in ["app", "app.orchestrators", "app.utils.agent"]:
        module_logger = logging.getLogger(module_name)
        logger.info(f"Logger '{module_name}' level: {logging.getLevelName(module_logger.level)}")

# Export logger and setup function
__all__ = ["logger", "setup_logging"] 
