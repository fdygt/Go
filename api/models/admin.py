from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class AdminRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MODERATOR = "moderator"
    SUPPORT = "support"

class AdminPermission(str, Enum):
    MANAGE_USERS = "manage_users"
    MANAGE_PRODUCTS = "manage_products"
    MANAGE_STOCK = "manage_stock"
    MANAGE_TRANSACTIONS = "manage_transactions"
    MANAGE_BALANCE = "manage_balance"
    MANAGE_BLACKLIST = "manage_blacklist"
    VIEW_LOGS = "view_logs"
    MANAGE_SETTINGS = "manage_settings"

class Platform(str, Enum):
    DISCORD = "discord"
    WEB = "web"
    ALL = "all"

class AdminStats(BaseModel):
    total_users: Dict[str, int]  # Per platform stats
    total_transactions: Dict[str, int]
    total_products: int
    total_stock: Dict[str, int]
    total_balance: Dict[str, Dict[str, int]]  # Per currency, per platform
    active_users: Dict[str, int]
    updated_at: datetime = Field(
        default_factory=lambda: datetime.strptime(
            "2025-05-29 15:51:46",
            "%Y-%m-%d %H:%M:%S"
        )
    )

class AdminActivity(BaseModel):
    id: str
    admin_id: str
    action: str
    platform: Platform
    target_type: str
    target_id: str
    details: Dict[str, Any]
    metadata: Dict = Field(default_factory=dict)
    created_at: datetime = Field(
        default_factory=lambda: datetime.strptime(
            "2025-05-29 15:51:46",
            "%Y-%m-%d %H:%M:%S"
        )
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "act_123456",
                "admin_id": "adm_123456",
                "action": "update_balance",
                "platform": "discord",
                "target_type": "user",
                "target_id": "usr_123456",
                "details": {
                    "currency": "wl",
                    "amount": 1000,
                    "reason": "Manual adjustment"
                },
                "created_at": "2025-05-29 15:51:46"
            }
        }

class AdminDashboard(BaseModel):
    stats: AdminStats
    recent_activities: List[AdminActivity]
    alerts: List[Dict]
    fraud_alerts: List[Dict]
    system_health: Dict[str, str]
    updated_at: datetime = Field(
        default_factory=lambda: datetime.strptime(
            "2025-05-29 15:51:46",
            "%Y-%m-%d %H:%M:%S"
        )
    )

class AdminSettings(BaseModel):
    id: str
    admin_id: str
    role: AdminRole
    permissions: List[AdminPermission]
    platforms: List[Platform]
    is_active: bool = True
    metadata: Dict = Field(default_factory=dict)
    created_by: str = Field(default="fdygg")
    created_at: datetime = Field(
        default_factory=lambda: datetime.strptime(
            "2025-05-29 15:51:46",
            "%Y-%m-%d %H:%M:%S"
        )
    )
    updated_by: Optional[str] = None
    updated_at: Optional[datetime] = None

    @validator('platforms')
    def validate_platforms(cls, v):
        if Platform.ALL in v and len(v) > 1:
            raise ValueError("When ALL is specified, no other platforms should be listed")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "id": "adm_123456",
                "admin_id": "usr_123456",
                "role": "admin",
                "permissions": [
                    "manage_users",
                    "manage_products",
                    "manage_transactions"
                ],
                "platforms": ["discord", "web"],
                "is_active": True,
                "created_by": "fdygg",
                "created_at": "2025-05-29 15:51:46"
            }
        }