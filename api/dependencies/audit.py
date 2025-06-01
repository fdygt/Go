from datetime import datetime
from typing import Any, Dict, Optional
from .logger import logger
from api.Config.audit import (
    AUDIT_CONFIG,
    AUDIT_EVENTS,
    AuditCategory,
    AuditLevel,
    AUDIT_LOG_FORMAT
)
from .database import SessionLocal

class AuditLogger:
    def __init__(self):
        self.config = AUDIT_CONFIG
        self.events = AUDIT_EVENTS
        self.enabled = self.config["enabled"]
        
    async def log(
        self,
        category: AuditCategory,
        event: str,
        user_id: str,
        ip_address: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ):
        if not self.enabled:
            return
            
        try:
            # Get event configuration
            event_config = self.events.get(category, {}).get(event)
            if not event_config:
                logger.warning(f"Undefined audit event: {category}.{event}")
                return
                
            # Prepare audit log entry
            log_entry = {
                **AUDIT_LOG_FORMAT,
                "timestamp": datetime.utcnow().isoformat(),
                "category": category,
                "level": event_config["level"],
                "event": event,
                "user_id": user_id,
                "ip_address": ip_address,
                "data": {
                    k: v for k, v in data.items()
                    if k in event_config["fields"]
                },
                "metadata": metadata or {}
            }
            
            # Store audit log
            if self.config["storage"]["type"] == "database":
                await self._store_in_database(log_entry)
            else:
                logger.warning(
                    f"Unsupported audit storage type: {self.config['storage']['type']}"
                )
                
        except Exception as e:
            logger.error(f"Audit logging error: {str(e)}")
            
    async def _store_in_database(self, log_entry: Dict[str, Any]):
        """Store audit log in database"""
        db = SessionLocal()
        try:
            # Convert log entry to database model
            from api.models.audit import AuditLog
            
            audit_log = AuditLog(
                category=log_entry["category"],
                level=log_entry["level"],
                event=log_entry["event"],
                user_id=log_entry["user_id"],
                ip_address=log_entry["ip_address"],
                data=log_entry["data"],
                metadata=log_entry["metadata"],
                created_at=datetime.fromisoformat(log_entry["timestamp"])
            )
            
            db.add(audit_log)
            await db.commit()
            
        except Exception as e:
            await db.rollback()
            raise e
        finally:
            await db.close()

audit_logger = AuditLogger()

# Audit decorator
def audit(category: AuditCategory, event: str):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Get user_id and ip_address from request context
            # This should be adapted based on your authentication system
            user_id = kwargs.get("user_id", "system")
            ip_address = kwargs.get("ip_address", "0.0.0.0")
            
            try:
                # Execute original function
                result = await func(*args, **kwargs)
                
                # Log audit event
                await audit_logger.log(
                    category=category,
                    event=event,
                    user_id=user_id,
                    ip_address=ip_address,
                    data=kwargs,
                    metadata={"success": True, "result": str(result)}
                )
                
                return result
                
            except Exception as e:
                # Log audit event with error
                await audit_logger.log(
                    category=category,
                    event=event,
                    user_id=user_id,
                    ip_address=ip_address,
                    data=kwargs,
                    metadata={
                        "success": False,
                        "error": str(e),
                        "error_type": type(e).__name__
                    }
                )
                raise
                
        return wrapper
    return decorator