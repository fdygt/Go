from datetime import datetime, UTC
from typing import Dict, Any, Optional

# Constants
CURRENT_TIMESTAMP = "2025-05-28 15:50:29"
CURRENT_USER = "fdygg"

# Import utility functions
from .date_utils import (
    format_datetime,
    parse_datetime,
    get_date_range,
    calculate_date_diff,
    is_valid_date
)

from .string_utils import (
    format_currency,
    sanitize_string,
    generate_random_string,
    mask_sensitive_data,
    validate_phone_number
)

from .validation_utils import (
    validate_email,
    validate_password,
    validate_username,
    validate_api_key,
    validate_jwt_token
)

from .format_utils import (
    format_response,
    format_error,
    format_log_message,
    format_audit_log,
    format_notification
)

from .security_utils import (
    hash_password,
    verify_password,
    generate_salt,
    encrypt_data,
    decrypt_data
)

# Export all utilities
__all__ = [
    # Constants
    "CURRENT_TIMESTAMP",
    "CURRENT_USER",
    
    # Date utilities
    "format_datetime",
    "parse_datetime",
    "get_date_range",
    "calculate_date_diff",
    "is_valid_date",
    
    # String utilities
    "format_currency",
    "sanitize_string",
    "generate_random_string",
    "mask_sensitive_data",
    "validate_phone_number",
    
    # Validation utilities
    "validate_email",
    "validate_password",
    "validate_username",
    "validate_api_key",
    "validate_jwt_token",
    
    # Format utilities
    "format_response",
    "format_error",
    "format_log_message",
    "format_audit_log",
    "format_notification",
    
    # Security utilities
    "hash_password",
    "verify_password",
    "generate_salt",
    "encrypt_data",
    "decrypt_data"
]