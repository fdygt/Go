from typing import Dict, Any, List
import re
from datetime import datetime

# Regular expressions for validation
REGEX_PATTERNS = {
    "username": r"^[a-zA-Z0-9_]{3,20}$",
    "password": r"^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d@$!%*#?&]{8,}$",
    "email": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
    "growid": r"^[A-Za-z0-9_]{3,20}$",
    "product_code": r"^[A-Z0-9_]{2,50}$",
    "discord_id": r"^\d{17,19}$"
}

# Field validation rules
VALIDATION_RULES = {
    "user": {
        "username": {
            "min_length": 3,
            "max_length": 20,
            "regex": REGEX_PATTERNS["username"],
            "error_message": "Username must be 3-20 characters long and contain only letters, numbers, and underscores"
        },
        "password": {
            "min_length": 8,
            "regex": REGEX_PATTERNS["password"],
            "error_message": "Password must be at least 8 characters long and contain at least one letter and one number"
        },
        "email": {
            "regex": REGEX_PATTERNS["email"],
            "error_message": "Please enter a valid email address"
        },
        "growid": {
            "regex": REGEX_PATTERNS["growid"],
            "error_message": "GrowID must be 3-20 characters long and contain only letters, numbers, and underscores"
        }
    },
    "product": {
        "code": {
            "regex": REGEX_PATTERNS["product_code"],
            "error_message": "Product code must be 2-50 characters long and contain only uppercase letters, numbers, and underscores"
        },
        "name": {
            "min_length": 3,
            "max_length": 100,
            "error_message": "Product name must be 3-100 characters long"
        },
        "price": {
            "min_value": 1,
            "error_message": "Price must be greater than 0"
        }
    },
    "transaction": {
        "amount": {
            "min_value": 1,
            "error_message": "Amount must be greater than 0"
        }
    }
}

# Custom validators
def validate_date_range(start_date: datetime, end_date: datetime) -> bool:
    """Validate that end_date is after start_date and range is not too large"""
    if start_date >= end_date:
        return False
    
    # Maximum date range is 1 year
    max_range = datetime(start_date.year + 1, start_date.month, start_date.day)
    return end_date <= max_range

def validate_product_metadata(metadata: Dict[str, Any]) -> List[str]:
    """Validate product metadata"""
    errors = []
    required_fields = ["world_size", "has_magplant"]
    
    for field in required_fields:
        if field not in metadata:
            errors.append(f"Missing required metadata field: {field}")
    
    if "world_size" in metadata:
        if not isinstance(metadata["world_size"], str) or not re.match(r"^\d+x\d+$", metadata["world_size"]):
            errors.append("World size must be in format WxH (e.g., 100x60)")
    
    if "has_magplant" in metadata and not isinstance(metadata["has_magplant"], bool):
        errors.append("has_magplant must be a boolean value")
    
    return errors

# Error messages
ERROR_MESSAGES = {
    "required": "This field is required",
    "invalid_type": "Invalid type for this field",
    "min_length": "Value is too short",
    "max_length": "Value is too long",
    "min_value": "Value is too small",
    "max_value": "Value is too large",
    "pattern": "Value does not match the required pattern",
    "unique": "This value must be unique",
    "foreign_key": "Referenced resource does not exist",
    "date_range": "Invalid date range",
    "metadata": "Invalid metadata format"
}

# Validation response format
VALIDATION_RESPONSE_FORMAT = {
    "success": False,
    "errors": [
        {
            "field": "field_name",
            "code": "error_code",
            "message": "error_message"
        }
    ]
}