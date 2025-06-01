from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum

class NotificationType(str, Enum):
    TRANSACTION = "transaction"
    SYSTEM = "system"
    PRICE_ALERT = "price_alert"
    STOCK = "stock"
    SECURITY = "security"
    SUPPORT = "support"

class NotificationPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class NotificationChannel(str, Enum):
    DISCORD = "discord"
    EMAIL = "email"
    IN_APP = "in_app"
    WEBHOOK = "webhook"

class NotificationStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    READ = "read"

class Notification(BaseModel):
    id: Optional[str] = None
    type: NotificationType
    priority: NotificationPriority = Field(default=NotificationPriority.MEDIUM)
    channels: List[NotificationChannel]
    recipient_id: str
    title: str
    content: str
    data: Dict = Field(default_factory=dict)
    status: NotificationStatus = Field(default=NotificationStatus.PENDING)
    created_by: str = Field(default="fdygg")
    created_at: datetime = Field(
        default_factory=lambda: datetime.strptime(
            "2025-05-29 07:48:17",
            "%Y-%m-%d %H:%M:%S"
        )
    )
    sent_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    metadata: Dict = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "notif_123456",
                "type": "transaction",
                "priority": "high",
                "channels": ["discord", "in_app"],
                "recipient_id": "123456789",
                "title": "Transaction Successful",
                "content": "Your purchase of 100 WL has been completed",
                "data": {
                    "transaction_id": "tx_123456",
                    "amount": 100,
                    "currency": "wl"
                },
                "status": "pending",
                "created_by": "fdygg",
                "created_at": "2025-05-29 07:48:17"
            }
        }