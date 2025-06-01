from api.service.logs_service import LogsService
from api.service.notifications_service import NotificationService
from api.service.audit_service import AuditService
from datetime import datetime
import traceback
import uuid

class ErrorHandlingService:
    def __init__(self):
        self.logger = LogsService()
        self.notifier = NotificationService()
        self.auditor = AuditService()
        
    def handle_exception(self, request, exc):
        """Handle and format exception"""
        error_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()
        
        # Log error with stack trace
        self.logger.error(
            f"Error ID: {error_id}\n"
            f"Time: {timestamp}\n"
            f"Type: {type(exc).__name__}\n"
            f"Message: {str(exc)}\n"
            f"Path: {request.path}\n"
            f"Method: {request.method}\n"
            f"Traceback:\n{traceback.format_exc()}"
        )
        
        # Audit error event
        self.auditor.log_event(
            event_type="error",
            details={
                "error_id": error_id,
                "error_type": type(exc).__name__,
                "path": request.path,
                "method": request.method
            }
        )
        
        # Notify admin if critical error
        if self.is_critical_error(exc):
            self.notifier.send_alert(
                title=f"Critical Error: {type(exc).__name__}",
                message=f"Error ID: {error_id}\n{str(exc)}",
                level="critical"
            )
            
        # Format error response
        return {
            "error": {
                "id": error_id,
                "type": type(exc).__name__,
                "message": str(exc),
                "timestamp": timestamp.isoformat()
            }
        }
        
    def is_critical_error(self, exc):
        """Check if error is critical"""
        critical_exceptions = (
            DatabaseError,
            AuthenticationError,
            SecurityError
        )
        return isinstance(exc, critical_exceptions)