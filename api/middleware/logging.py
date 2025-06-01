from datetime import datetime, UTC
from typing import Dict, Optional
from functools import wraps
import traceback
import logging
from fastapi import Request, Response
from ..service.logs_service import LogService
from ..service.audit_service import AuditService
from ..models.logs import Log, LogLevel, LogCategory
from ..models.audit import AuditLog, AuditAction, AuditCategory

logger = logging.getLogger(__name__)

class LoggingMiddleware:
    def __init__(self):
        self.log_service = LogService()
        self.audit_service = AuditService()
        self.startup_time = datetime.now(UTC)
        logger.info(f"""
        LoggingMiddleware initialized:
        Time: 2025-05-30 14:36:04
        User: fdygg
        """)

    async def __call__(self, request: Request, call_next):
        # Generate request ID
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        request.state.request_id = request_id

        # Get user info from request if available
        user_id = request.headers.get("X-User-ID")
        ip_address = request.client.host

        # Start timer
        start_time = datetime.now(UTC)

        try:
            # Create request log
            await self.log_service.create_log(
                Log(
                    level=LogLevel.INFO,
                    category=LogCategory.API,
                    message=f"Incoming {request.method} request to {request.url.path}",
                    source="LoggingMiddleware",
                    timestamp=start_time,
                    user_id=user_id,
                    ip_address=ip_address,
                    metadata={
                        "request_id": request_id,
                        "method": request.method,
                        "path": str(request.url.path),
                        "query_params": dict(request.query_params),
                        "headers": dict(request.headers),
                    }
                )
            )

            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration = (datetime.now(UTC) - start_time).total_seconds()

            # Create response log
            await self.log_service.create_log(
                Log(
                    level=LogLevel.INFO,
                    category=LogCategory.API,
                    message=f"Completed {request.method} request to {request.url.path}",
                    source="LoggingMiddleware",
                    timestamp=datetime.now(UTC),
                    user_id=user_id,
                    ip_address=ip_address,
                    metadata={
                        "request_id": request_id,
                        "status_code": response.status_code,
                        "duration": duration,
                        "headers": dict(response.headers)
                    }
                )
            )

            # Create audit log for important operations
            if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
                await self.audit_service.log_action(
                    category=AuditCategory.SYSTEM,
                    action=AuditAction(request.method.lower()),
                    actor_id=user_id or "anonymous",
                    actor_type="user",
                    target_id=request_id,
                    target_type="api_request",
                    description=f"{request.method} request to {request.url.path}",
                    metadata={
                        "request_id": request_id,
                        "method": request.method,
                        "path": str(request.url.path),
                        "status_code": response.status_code,
                        "duration": duration
                    }
                )

            return response

        except Exception as e:
            # Log error
            error_log = await self.log_service.create_log(
                Log(
                    level=LogLevel.ERROR,
                    category=LogCategory.API,
                    message=f"Error processing {request.method} request: {str(e)}",
                    source="LoggingMiddleware",
                    timestamp=datetime.now(UTC),
                    user_id=user_id,
                    ip_address=ip_address,
                    metadata={
                        "request_id": request_id,
                        "error": str(e),
                        "error_type": e.__class__.__name__
                    },
                    stack_trace=traceback.format_exc()
                )
            )

            # Create audit log for error
            await self.audit_service.log_action(
                category=AuditCategory.SYSTEM,
                action=AuditAction.STATUS_CHANGE,
                actor_id=user_id or "anonymous",
                actor_type="user",
                target_id=request_id,
                target_type="api_request",
                description=f"Error in {request.method} request to {request.url.path}",
                metadata={
                    "request_id": request_id,
                    "error": str(e),
                    "error_type": e.__class__.__name__,
                    "log_id": error_log.id if error_log else None
                }
            )

            # Re-raise the exception
            raise

def log_function(
    level: LogLevel = LogLevel.INFO,
    category: LogCategory = LogCategory.SYSTEM
):
    """Decorator for logging function calls"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            function_name = func.__name__
            start_time = datetime.now(UTC)

            try:
                # Execute function
                result = await func(*args, **kwargs)

                # Calculate duration
                duration = (datetime.now(UTC) - start_time).total_seconds()

                # Log success
                await LogService().create_log(
                    Log(
                        level=level,
                        category=category,
                        message=f"Function {function_name} completed successfully",
                        source=func.__module__,
                        timestamp=datetime.now(UTC),
                        metadata={
                            "function": function_name,
                            "duration": duration,
                            "args": str(args),
                            "kwargs": str(kwargs),
                        }
                    )
                )

                return result

            except Exception as e:
                # Log error
                await LogService().create_log(
                    Log(
                        level=LogLevel.ERROR,
                        category=category,
                        message=f"Error in function {function_name}: {str(e)}",
                        source=func.__module__,
                        timestamp=datetime.now(UTC),
                        metadata={
                            "function": function_name,
                            "error": str(e),
                            "error_type": e.__class__.__name__,
                            "args": str(args),
                            "kwargs": str(kwargs)
                        },
                        stack_trace=traceback.format_exc()
                    )
                )
                raise

        return wrapper
    return decorator