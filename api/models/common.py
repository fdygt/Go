from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class BaseModelWithTimestamp(BaseModel):
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True

class PlatformSpecificModel(BaseModelWithTimestamp):
    platform: str
    platform_id: Optional[str] = None
    platform_metadata: Dict[str, Any] = Field(default_factory=dict)