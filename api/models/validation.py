from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime

class ValidationType(str, Enum):
    REQUIRED = "required"
    LENGTH = "length"
    RANGE = "range"
    REGEX = "regex"
    CUSTOM = "custom"
    PLATFORM = "platform"
    PERMISSION = "permission"

class ValidationRule(BaseModel):
    field: str
    type: ValidationType
    value: Any
    message: str
    platform: Optional[List[str]] = None
    roles: Optional[List[str]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "field": "username",
                "type": "length",
                "value": {"min": 3, "max": 50},
                "message": "Username must be between 3 and 50 characters",
                "platform": ["discord", "web"],
                "roles": ["admin", "user"]
            }
        }

class ValidationError(BaseModel):
    field: str
    message: str
    code: str
    value: Optional[Any] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "field": "username",
                "message": "Username must be between 3 and 50 characters",
                "code": "LENGTH_ERROR",
                "value": "ab"
            }
        }