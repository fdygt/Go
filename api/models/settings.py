from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class SettingCategory(str, Enum):
    BOT = "bot"
    API = "api"
    SECURITY = "security"
    NOTIFICATION = "notification"
    TRANSACTION = "transaction"
    SYSTEM = "system"

class Setting(BaseModel):
    id: Optional[str] = None
    category: SettingCategory
    key: str
    value: Any
    description: Optional[str] = None
    is_public: bool = Field(default=False)
    created_by: str = Field(default="fdygg")
    created_at: datetime = Field(
        default_factory=lambda: datetime.strptime(
            "2025-05-29 07:48:17",
            "%Y-%m-%d %H:%M:%S"
        )
    )
    updated_by: Optional[str] = None
    updated_at: Optional[datetime] = None
    metadata: Dict = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "set_123456",
                "category": "bot",
                "key": "command_prefix",
                "value": "!",
                "description": "Bot command prefix",
                "is_public": True,
                "created_by": "fdygg",
                "created_at": "2025-05-29 07:48:17"
            }
        }

class FeatureFlag(BaseModel):
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    enabled: bool = Field(default=True)
    conditions: Dict = Field(
        default_factory=dict,
        description="Conditions for feature enablement"
    )
    created_by: str = Field(default="fdygg")
    created_at: datetime = Field(
        default_factory=lambda: datetime.strptime(
            "2025-05-29 07:48:17",
            "%Y-%m-%d %H:%M:%S"
        )
    )
    updated_by: Optional[str] = None
    updated_at: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "flag_123456",
                "name": "new_trading_system",
                "description": "Enable new trading system",
                "enabled": True,
                "conditions": {
                    "user_roles": ["admin", "moderator"],
                    "percentage": 50
                },
                "created_by": "fdygg",
                "created_at": "2025-05-29 07:48:17"
            }
        }