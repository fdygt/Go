from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class LogLevel(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class LogCategory(str, Enum):
    SYSTEM = "system"
    SECURITY = "security"
    TRANSACTION = "transaction"
    USER = "user"
    BOT = "bot"
    API = "api"
    AUDIT = "audit"

class Log(BaseModel):
    id: Optional[str] = None
    level: LogLevel
    category: LogCategory
    message: str
    source: str = Field(..., description="Origin of the log")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.strptime(
            "2025-05-29 07:48:17",
            "%Y-%m-%d %H:%M:%S"
        )
    )
    user_id: Optional[str] = None
    ip_address: Optional[str] = None
    metadata: Dict = Field(default_factory=dict)
    stack_trace: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "log_123456",
                "level": "error",
                "category": "transaction",
                "message": "Failed to process transaction",
                "source": "payment_service",
                "timestamp": "2025-05-29 07:48:17",
                "user_id": "123456789",
                "ip_address": "192.168.1.1",
                "metadata": {
                    "transaction_id": "tx_123456",
                    "error_code": "PAYMENT_FAILED"
                },
                "stack_trace": "Error at line 42..."
            }
        }

class AuditLog(BaseModel):
    id: Optional[str] = None
    user_id: str
    action: str
    resource_type: str
    resource_id: str
    changes: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Changes made {field: {old: value, new: value}}"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.strptime(
            "2025-05-29 07:48:17",
            "%Y-%m-%d %H:%M:%S"
        )
    )
    ip_address: Optional[str] = None
    metadata: Dict = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "audit_123456",
                "user_id": "usr_123456",
                "action": "update",
                "resource_type": "product",
                "resource_id": "prod_123456",
                "changes": {
                    "price": {
                        "old": 1000,
                        "new": 1100
                    }
                },
                "timestamp": "2025-05-29 07:48:17",
                "ip_address": "192.168.1.1"
            }
        }