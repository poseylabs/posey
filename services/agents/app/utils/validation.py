from enum import Enum
from typing import Any, Dict, Optional, Type
from pydantic import BaseModel, ValidationError
import json
from app.config import logger

class ResponseValidation(Enum):
    JSON_LOADS = "json_loads"
    JSON_STRICT = "json_strict"
    SCHEMA_VALIDATION = "schema_validation"

class ValidationResult:
    """Container for validation results"""
    def __init__(self, is_valid: bool, data: Optional[Dict[str, Any]] = None, error: Optional[str] = None):
        self.is_valid = is_valid
        self.data = data
        self.error = error

def validate_json_structure(response: str) -> ValidationResult:
    """Validate basic JSON structure"""
    try:
        # Check if response starts/ends with curly braces
        stripped = response.strip()
        if not (stripped.startswith('{') and stripped.endswith('}')):
            return ValidationResult(
                False, 
                error="Response must be a JSON object starting with { and ending with }"
            )
        
        # Try to parse JSON
        data = json.loads(stripped)
        if not isinstance(data, dict):
            return ValidationResult(
                False,
                error="Response must be a JSON object, not an array or primitive"
            )
            
        return ValidationResult(True, data=data)
        
    except json.JSONDecodeError as e:
        return ValidationResult(False, error=f"Invalid JSON: {str(e)}")

def validate_schema(data: Dict[str, Any], schema_model: Type[BaseModel]) -> ValidationResult:
    """Validate data against a Pydantic schema"""
    try:
        validated = schema_model(**data)
        return ValidationResult(True, data=validated.model_dump())
    except ValidationError as e:
        return ValidationResult(False, error=f"Schema validation failed: {str(e)}")

def validate_response(
    response: str,
    validation_type: str,
    schema_model: Optional[Type[BaseModel]] = None
) -> ValidationResult:
    """Validate a response string according to the specified validation type"""
    try:
        if validation_type == ResponseValidation.JSON_LOADS.value:
            try:
                data = json.loads(response)
                return ValidationResult(True, data=data)
            except json.JSONDecodeError as e:
                return ValidationResult(False, error=f"JSON parsing failed: {str(e)}")
            
        elif validation_type == ResponseValidation.JSON_STRICT.value:
            # Validate JSON structure first
            result = validate_json_structure(response)
            if not result.is_valid:
                return result
                
            return ValidationResult(True, data=result.data)
            
        elif validation_type == ResponseValidation.SCHEMA_VALIDATION.value:
            if not schema_model:
                return ValidationResult(False, error="Schema model required for schema validation")
                
            # First validate JSON structure
            result = validate_json_structure(response)
            if not result.is_valid:
                return result
                
            # Then validate against schema
            return validate_schema(result.data, schema_model)
            
        else:
            return ValidationResult(False, error=f"Unknown validation type: {validation_type}")
            
    except Exception as e:
        logger.error(f"Validation error: {str(e)}")
        return ValidationResult(False, error=f"Validation failed: {str(e)}") 
