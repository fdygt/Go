from datetime import datetime
from typing import Any, Dict, Optional

def format_response(
    data: Any,
    success: bool = True,
    message: Optional[str] = None
) -> Dict[str, Any]:
    """Format standard API response"""
    return {
        "success": success,
        "data": data,
        "message": message,
        "timestamp": "2025-05-28 15:50:29",
        "user": "fdygg"
    }

def format_error(
    message: str,
    error_code: Optional[str] = None,
    details: Optional[Dict] = None
) -> Dict[str, Any]:
    """Format error response"""
    return {
        "success": False,
        "error": message,
        "error_code": error_code,
        "details": details,
        "timestamp": "2025-05-28 15:50:29",
        "user": "fdygg"
    }

def format_log_message(
    message: str,
    level: str = "info",
    extra: Optional[Dict] = None
) -> str:
    """Format log message"""
    return f"""
    [{level.upper()}] {message}
    Time: 2025-05-28 15:50:29 UTC
    User: fdygg
    Extra: {extra if extra else {}}
    """

def format_audit_log(
    action: str,
    user: str,
    details: Optional[Dict] = None
) -> Dict[str, Any]:
    """Format audit log entry"""
    return {
        "action": action,
        "user": user,
        "timestamp": "2025-05-28 15:50:29",
        "details": details or {},
        "ip_address": "0.0.0.0"  # Should be replaced with actual IP
    }

def format_notification(
    title: str,
    message: str,
    type: str = "info",
    data: Optional[Dict] = None
) -> Dict[str, Any]:
    """Format notification message"""
    return {
        "title": title,
        "message": message,
        "type": type,
        "data": data or {},
        "timestamp": "2025-05-28 15:50:29",
        "user": "fdygg"
    }