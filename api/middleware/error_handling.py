from fastapi import Request, Response
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from typing import Optional, Dict, Any, Type, Tuple
import logging
from datetime import datetime, UTC
import traceback
import sys
from uuid import uuid4
import json

from ..service.error_handling_service import ErrorHandlingService
from ..service.notifications_service import NotificationService
from ..models.notifications import (
    Notification,
    NotificationType,
    NotificationPriority,
    NotificationChannel,
    NotificationStatus
)

logger = logging.getLogger(__name__)

class ErrorHandlingMiddleware:
    def __init__(self):
        self.error_service = ErrorHandlingService()
        self.notification_service = NotificationService()
        self.startup_time = datetime.now(UTC)
        
        # Error mapping
        self.status_codes = {
            RequestValidationError: 422,
            ValueError: 400,
            KeyError: 400,
            HTTPException: None,  # Use exception's status_code
            Exception: 500
        }
        
        # Notification settings
        self.NOTIFY_ON_STATUS = {500, 503}  # Status codes that trigger notifications
        self.ERROR_AGGREGATION_WINDOW = 300  # 5 minutes
        self.ERROR_NOTIFICATION_THRESHOLD = 5  # Errors within window to trigger notification
        
        # Error tracking
        self.error_counts = {}
        
        logger.info(f"""
        ErrorHandlingMiddleware initialized:
        Time: 2025-05-30 15:13:31
        User: fdygg
        """)

    def _get_error_details(
        self,
        request: Request,
        exc: Exception
    ) -> Dict[str, Any]:
        """Get detailed error information"""
        error_id = str(uuid4())
        timestamp = datetime.now(UTC)
        
        # Get error location
        tb = traceback.extract_tb(sys.exc_info()[2])
        location = f"{tb[-1].filename}:{tb[-1].lineno}" if tb else "Unknown"
        
        # Get request context
        context = {
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "client_host": request.client.host,
            "headers": dict(request.headers)
        }
        
        # Get user context if available
        user_id = getattr(request.state, "user", {}).get("id", "anonymous")
        
        return {
            "id": error_id,
            "timestamp": timestamp,
            "type": type(exc).__name__,
            "message": str(exc),
            "location": location,
            "traceback": traceback.format_exc(),
            "context": context,
            "user_id": user_id
        }

    async def _should_notify(
        self,
        error_type: str,
        status_code: int
    ) -> bool:
        """Determine if error should trigger notification"""
        if status_code in self.NOTIFY_ON_STATUS:
            current_time = datetime.now(UTC).timestamp()
            window_start = current_time - self.ERROR_AGGREGATION_WINDOW
            
            # Clean old errors
            self.error_counts = {
                k: v for k, v in self.error_counts.items()
                if v["timestamp"] > window_start
            }
            
            # Update error count
            if error_type not in self.error_counts:
                self.error_counts[error_type] = {
                    "count": 0,
                    "timestamp": current_time
                }
            self.error_counts[error_type]["count"] += 1
            
            return (
                self.error_counts[error_type]["count"] >=
                self.ERROR_NOTIFICATION_THRESHOLD
            )
            
        return False

    async def _create_error_notification(
        self,
        error_details: Dict[str, Any],
        status_code: int
    ) -> None:
        """Create error notification"""
        try:
            notification = Notification(
                type=NotificationType.SYSTEM,
                priority=(
                    NotificationPriority.CRITICAL
                    if status_code >= 500
                    else NotificationPriority.HIGH
                ),
                channels=[
                    NotificationChannel.DISCORD,
                    NotificationChannel.EMAIL
                ],
                recipient_id="admin",  # Admin/DevOps team
                title=f"Critical Error: {error_details['type']}",
                content=f"""
                Error ID: {error_details['id']}
                Type: {error_details['type']}
                Message: {error_details['message']}
                Location: {error_details['location']}
                Time: {error_details['timestamp']}
                Path: {error_details['context']['path']}
                Method: {error_details['context']['method']}
                User: {error_details['user_id']}
                """,
                data={
                    "error_id": error_details["id"],
                    "status_code": status_code,
                    "traceback": error_details["traceback"],
                    "context": error_details["context"]
                },
                metadata={
                    "environment": "production",
                    "service": "api",
                    "severity": "critical" if status_code >= 500 else "high"
                }
            )
            
            await self.notification_service.create_notification(notification)
            
        except Exception as e:
            logger.error(f"Error creating notification: {str(e)}")

    def _get_response_data(
        self,
        error_details: Dict[str, Any],
        status_code: int
    ) -> Dict[str, Any]:
        """Get formatted response data"""
        response = {
            "error": {
                "id": error_details["id"],
                "type": error_details["type"],
                "message": error_details["message"],
                "timestamp": error_details["timestamp"].isoformat()
            }
        }
        
        # Add validation errors for 422
        if status_code == 422 and hasattr(error_details.get("data"), "errors"):
            response["error"]["details"] = error_details["data"].errors()
            
        # Add debug info for 500 in development
        if status_code >= 500 and logger.getEffectiveLevel() == logging.DEBUG:
            response["error"]["debug"] = {
                "location": error_details["location"],
                "traceback": error_details["traceback"]
            }
            
        return response

    async def __call__(self, request: Request, call_next):
        try:
            return await call_next(request)
            
        except Exception as exc:
            try:
                # Get error details
                error_details = self._get_error_details(request, exc)
                
                # Get status code
                status_code = (
                    getattr(exc, "status_code", None) or
                    self.status_codes.get(type(exc)) or
                    self.status_codes.get(Exception)
                )
                
                # Log error
                log_level = logging.ERROR if status_code >= 500 else logging.WARNING
                logger.log(log_level, json.dumps(error_details, default=str))
                
                # Check if should notify
                if await self._should_notify(error_details["type"], status_code):
                    await self._create_error_notification(error_details, status_code)
                
                # Get response data
                response_data = self._get_response_data(error_details, status_code)
                
                # Create response
                response = JSONResponse(
                    status_code=status_code,
                    content=response_data
                )
                
                # Add headers
                response.headers["X-Error-ID"] = error_details["id"]
                response.headers["X-Error-Type"] = error_details["type"]
                
                return response
                
            except Exception as e:
                # Fallback error handling
                logger.error(f"Error in error handler: {str(e)}")
                return JSONResponse(
                    status_code=500,
                    content={
                        "error": {
                            "type": "InternalServerError",
                            "message": "An unexpected error occurred"
                        }
                    }
                )

    async def clear_error_counts(self) -> None:
        """Clear error count tracking"""
        self.error_counts.clear()
        
    async def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics"""
        current_time = datetime.now(UTC).timestamp()
        window_start = current_time - self.ERROR_AGGREGATION_WINDOW
        
        # Clean old errors
        self.error_counts = {
            k: v for k, v in self.error_counts.items()
            if v["timestamp"] > window_start
        }
        
        return {
            "window_size": self.ERROR_AGGREGATION_WINDOW,
            "notification_threshold": self.ERROR_NOTIFICATION_THRESHOLD,
            "error_counts": {
                k: v["count"] for k, v in self.error_counts.items()
            },
            "total_errors": sum(v["count"] for v in self.error_counts.values())
        }