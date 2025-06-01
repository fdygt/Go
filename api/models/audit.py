from pydantic import BaseModel, Field
from typing import Optional, Dict
from datetime import datetime
from enum import Enum

class AuditAction(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    STATUS_CHANGE = "status_change"

class AuditCategory(str, Enum):
    USER = "user"
    ADMIN = "admin"
    PRODUCT = "product"
    STOCK = "stock"
    ORDER = "order"
    BALANCE = "balance"
    SYSTEM = "system"

class AuditLog(BaseModel):
    id: str = Field(..., description="Unique audit log ID")
    category: AuditCategory
    action: AuditAction
    actor_id: str = Field(..., description="ID of user/admin who performed the action")
    actor_type: str = Field(..., description="Type of actor (admin/user/system)")
    target_id: Optional[str] = Field(None, description="ID of affected resource")
    target_type: str = Field(..., description="Type of resource affected")
    description: str = Field(..., description="Description of the action")
    metadata: Dict = Field(default_factory=dict)
    created_at: datetime = Field(
        default_factory=lambda: datetime.strptime(
            "2025-05-29 17:08:40",
            "%Y-%m-%d %H:%M:%S"
        )
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "adt_12345",
                "category": "product",
                "action": "create",
                "actor_id": "adm_67890",
                "actor_type": "admin",
                "target_id": "prd_12345",
                "target_type": "product",
                "description": "Created new product FARM_WORLD",
                "metadata": {
                    "old_value": None,
                    "new_value": {
                        "code": "FARM_WORLD",
                        "name": "Farm World Ready"
                    }
                },
                "created_at": "2025-05-29 17:08:40"
            }
        }