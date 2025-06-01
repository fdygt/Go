from fastapi import HTTPException
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ValidationError
from api.Config.validation import (
    VALIDATION_RULES,
    REGEX_PATTERNS,
    ERROR_MESSAGES
)
import re

class ValidationError(BaseModel):
    field: str
    code: str
    message: str
    value: Optional[Any] = None

class Validator:
    @staticmethod
    def validate_field(
        field: str,
        value: Any,
        rules: Dict[str, Any]
    ) -> List[ValidationError]:
        errors = []
        
        # Check required
        if value is None and rules.get("required", False):
            errors.append(
                ValidationError(
                    field=field,
                    code="required",
                    message=ERROR_MESSAGES["required"]
                )
            )
            return errors
            
        # Skip further validation if value is None
        if value is None:
            return errors
            
        # Check type
        expected_type = rules.get("type")
        if expected_type and not isinstance(value, expected_type):
            errors.append(
                ValidationError(
                    field=field,
                    code="invalid_type",
                    message=ERROR_MESSAGES["invalid_type"],
                    value=value
                )
            )
            return errors
            
        # Check min length
        min_length = rules.get("min_length")
        if min_length and len(str(value)) < min_length:
            errors.append(
                ValidationError(
                    field=field,
                    code="min_length",
                    message=f"{ERROR_MESSAGES['min_length']} (min: {min_length})",
                    value=value
                )
            )
            
        # Check max length
        max_length = rules.get("max_length")
        if max_length and len(str(value)) > max_length:
            errors.append(
                ValidationError(
                    field=field,
                    code="max_length",
                    message=f"{ERROR_MESSAGES['max_length']} (max: {max_length})",
                    value=value
                )
            )
            
        # Check regex pattern
        pattern = rules.get("regex")
        if pattern and not re.match(pattern, str(value)):
            errors.append(
                ValidationError(
                    field=field,
                    code="pattern",
                    message=rules.get("error_message", ERROR_MESSAGES["pattern"]),
                    value=value
                )
            )
            
        # Check min value
        min_value = rules.get("min_value")
        if min_value is not None and value < min_value:
            errors.append(
                ValidationError(
                    field=field,
                    code="min_value",
                    message=f"{ERROR_MESSAGES['min_value']} (min: {min_value})",
                    value=value
                )
            )
            
        # Check max value
        max_value = rules.get("max_value")
        if max_value is not None and value > max_value:
            errors.append(
                ValidationError(
                    field=field,
                    code="max_value",
                    message=f"{ERROR_MESSAGES['max_value']} (max: {max_value})",
                    value=value
                )
            )
            
        return errors

    @classmethod
    def validate_model(
        cls,
        model_name: str,
        data: Dict[str, Any]
    ) -> List[ValidationError]:
        errors = []
        
        if model_name not in VALIDATION_RULES:
            raise ValueError(f"Unknown model: {model_name}")
            
        rules = VALIDATION_RULES[model_name]
        
        for field, field_rules in rules.items():
            value = data.get(field)
            field_errors = cls.validate_field(field, value, field_rules)
            errors.extend(field_errors)
            
        return errors

# Validation decorator
def validate(model_name: str):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            data = kwargs.get("data", {})
            if not data:
                raise HTTPException(
                    status_code=400,
                    detail="No data provided for validation"
                )
                
            errors = Validator.validate_model(model_name, data)
            if errors:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "message": "Validation error",
                        "errors": [error.dict() for error in errors]
                    }
                )
                
            return await func(*args, **kwargs)
        return wrapper
    return decorator

validator = Validator()