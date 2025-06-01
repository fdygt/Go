from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum

class BlacklistType(str, Enum):
    USER = "user"          # User ID (Discord/Web)
    GROWTOPIA = "growid"   # Growtopia ID
    IP = "ip"              # IP Address
    DEVICE = "device"      # Device ID
    PAYMENT = "payment"    # Payment Method

class BlacklistReason(str, Enum):
    SPAM = "spam"
    FRAUD = "fraud"
    ABUSE = "abuse"
    SUSPICIOUS = "suspicious"
    SCAM = "scam"          # Scam reports
    TOS_VIOLATION = "tos"  # Terms of Service violation
    MANUAL = "manual"

class BlacklistStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REMOVED = "removed"
    APPEALED = "appealed"  # Allow for appeals

class BlacklistEntry(BaseModel):
    id: Optional[str] = None
    type: BlacklistType
    value: str = Field(..., description="User ID, Growtopia ID, IP, or other identifier")
    user_type: Optional[str] = Field(None, description="discord/web if applicable")
    reason: BlacklistReason
    description: Optional[str] = None
    evidence: List[Dict] = Field(default_factory=list)
    status: BlacklistStatus = Field(default=BlacklistStatus.ACTIVE)
    expires_at: Optional[datetime] = None
    created_by: str = Field(default="fdygg")
    created_at: datetime = Field(
        default_factory=lambda: datetime.strptime(
            "2025-05-29 15:51:46",
            "%Y-%m-%d %H:%M:%S"
        )
    )
    updated_by: Optional[str] = None
    updated_at: Optional[datetime] = None
    metadata: Dict = Field(default_factory=dict)

    @validator('user_type')
    def validate_user_type(cls, v, values):
        if values.get('type') == BlacklistType.USER and not v:
            raise ValueError("user_type is required for USER blacklist type")
        if v and v not in ["discord", "web"]:
            raise ValueError("user_type must be either 'discord' or 'web'")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "id": "bl_123456",
                "type": "user",
                "value": "usr_123456",
                "user_type": "discord",
                "reason": "fraud",
                "description": "Multiple chargeback attempts",
                "evidence": [
                    {
                        "type": "transaction",
                        "id": "tx_123456",
                        "details": "Chargeback on WL purchase"
                    }
                ],
                "status": "active",
                "created_by": "fdygg",
                "created_at": "2025-05-29 15:51:46"
            }
        }

class FraudDetectionRule(BaseModel):
    id: Optional[str] = None
    name: str
    description: str
    platform: List[str] = Field(
        default=["discord", "web"],
        description="Platforms where rule applies"
    )
    conditions: Dict = Field(..., description="Rule conditions")
    actions: List[Dict] = Field(..., description="Actions to take when triggered")
    is_active: bool = Field(default=True)
    priority: int = Field(default=1, ge=1, le=10)
    created_by: str = Field(default="fdygg")
    created_at: datetime = Field(
        default_factory=lambda: datetime.strptime(
            "2025-05-29 15:51:46",
            "%Y-%m-%d %H:%M:%S"
        )
    )
    updated_by: Optional[str] = None
    updated_at: Optional[datetime] = None

    @validator('platform')
    def validate_platform(cls, v):
        valid = ["discord", "web"]
        if not all(p in valid for p in v):
            raise ValueError(f"Platform must be one of: {valid}")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "id": "rule_123456",
                "name": "Multiple Account Detection",
                "description": "Detect multiple accounts from same IP",
                "platform": ["discord", "web"],
                "conditions": {
                    "type": "ip_address",
                    "threshold": 5,
                    "time_window": 3600
                },
                "actions": [
                    {
                        "type": "blacklist",
                        "target": "ip",
                        "duration": 86400
                    },
                    {
                        "type": "notify",
                        "channel": "discord",
                        "role": "moderator"
                    }
                ],
                "priority": 1,
                "is_active": True,
                "created_by": "fdygg",
                "created_at": "2025-05-29 15:51:46"
            }
        }