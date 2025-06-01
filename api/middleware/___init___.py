from fastapi import Request, Response
from functools import wraps
from datetime import datetime, UTC
import logging
from typing import Callable, Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
CURRENT_TIMESTAMP = "2025-05-28 15:44:14"
CURRENT_USER = "fdygg"

def get_current_time() -> str:
    """Get current timestamp in consistent format"""
    return CURRENT_TIMESTAMP

def get_current_user() -> str:
    """Get current user's login"""
    return CURRENT_USER

def format_log_message(message: str) -> str:
    """Format log message with timestamp and user"""
    return f"""
    {message}
    Timestamp: {CURRENT_TIMESTAMP}
    User: {CURRENT_USER}
    """

def skip_auth(func: Callable) -> Callable:
    """Decorator to skip authentication for specific routes"""
    setattr(func, "skip_auth", True)
    return func

# Import all middleware components
from .auth import (
    JWTAuthMiddleware,
    verify_token,
    create_access_token,
    decode_token,
    get_token_from_header
)

from .logging import (
    RequestLoggingMiddleware,
    log_request,
    log_response,
    format_request_log,
    format_response_log
)

from .error_handling import (
    ErrorHandlingMiddleware,
    handle_http_exception,
    handle_validation_error,
    handle_database_error
)

from .rate_limiting import (
    RateLimitingMiddleware,
    check_rate_limit,
    update_rate_limit,
    get_rate_limit_key
)

from .caching import (
    CacheMiddleware,
    get_cache_key,
    set_cache,
    get_cache,
    clear_cache
)

# Export all middleware components
__all__ = [
    # Auth middleware
    "JWTAuthMiddleware",
    "verify_token",
    "create_access_token",
    "decode_token",
    "get_token_from_header",
    
    # Logging middleware
    "RequestLoggingMiddleware",
    "log_request",
    "log_response",
    "format_request_log",
    "format_response_log",
    
    # Error handling middleware
    "ErrorHandlingMiddleware",
    "handle_http_exception",
    "handle_validation_error",
    "handle_database_error",
    
    # Rate limiting middleware
    "RateLimitingMiddleware",
    "check_rate_limit",
    "update_rate_limit",
    "get_rate_limit_key",
    
    # Cache middleware
    "CacheMiddleware",
    "get_cache_key",
    "set_cache",
    "get_cache",
    "clear_cache",
    
    # Utility functions
    "get_current_time",
    "get_current_user",
    "format_log_message",
    "skip_auth",
    
    # Constants
    "CURRENT_TIMESTAMP",
    "CURRENT_USER"
]