class PoseyError(Exception):
    """Base exception class for all Posey-related errors"""
    def __init__(self, message: str, operation: str = None, code: int = None):
        self.message = message
        self.operation = operation
        self.code = code
        super().__init__(self.message)

# System-level exceptions
class ConfigError(PoseyError):
    """Raised when there is an error in system configuration"""
    def __init__(self, message: str, operation: str = "configuration"):
        super().__init__(message, operation, 400)

class DatabaseError(PoseyError):
    """Raised when there is a database-related error"""
    def __init__(self, message: str, operation: str = "database"):
        super().__init__(message, operation, 500)

class AuthorizationError(PoseyError):
    """Raised when there is an authorization error"""
    def __init__(self, message: str, operation: str = "authorization"):
        super().__init__(message, operation, 403)

# Agent-specific exceptions
class AgentError(PoseyError):
    """Base exception class for all agent-related errors"""
    pass

class AgentConfigError(AgentError):
    """Raised when there is an error in agent configuration"""
    def __init__(self, message: str, operation: str = "configuration"):
        super().__init__(message, operation, 400)

class AgentOperationError(AgentError):
    """Raised when an agent operation fails"""
    def __init__(self, message: str, operation: str = None, code: int = 500):
        super().__init__(message, operation, code)

class AgentCommunicationError(AgentError):
    """Raised when there is an error in agent-to-agent communication"""
    def __init__(self, message: str, operation: str = "communication"):
        super().__init__(message, operation, 503)

class AgentMemoryError(AgentError):
    """Raised when there is an error in memory operations"""
    def __init__(self, message: str, operation: str = "memory"):
        super().__init__(message, operation, 500)

# Memory-specific exceptions
class MemoryError(PoseyError):
    """Base exception class for memory-related errors"""
    pass

class MemoryStorageError(MemoryError):
    """Raised when there is an error storing memories"""
    def __init__(self, message: str, operation: str = "storage"):
        super().__init__(message, operation, 500)

class MemoryRetrievalError(MemoryError):
    """Raised when there is an error retrieving memories"""
    def __init__(self, message: str, operation: str = "retrieval"):
        super().__init__(message, operation, 500)

class MemoryOperationError(PoseyError):
    """Raised when there is an error in memory operations."""
    def __init__(self, message: str, operation: str = "memory"):
        super().__init__(message, operation, 500)

class SearchError(PoseyError):
    """Raised when there is an error during a search operation."""
    def __init__(self, message: str, operation: str = "search"):
        super().__init__(message, operation, 500)

class ValidationError(PoseyError):
    """Raised when there is a validation error."""
    def __init__(self, message: str, operation: str = "validation"):
        super().__init__(message, operation, 400)

# Add new exception type
class AnalysisParsingError(Exception):
    """Raised when analysis response cannot be parsed as valid JSON"""
    pass
