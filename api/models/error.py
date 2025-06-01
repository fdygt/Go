from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class ErrorDetail(BaseModel):
    message: str
    code: str
    field: Optional[str] = None
    value: Optional[Any] = None

class ErrorResponse(BaseModel):
    status: int
    type: str
    message: str
    details: List[ErrorDetail]
    timestamp: datetime
    request_id: Optional[str] = None
    path: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "status": 400,
                "type": "ValidationError",
                "message": "Invalid input data",
                "details": [
                    {
                        "field": "username",
                        "message": "Username must be between 3 and 50 characters",
                        "code": "LENGTH_ERROR",
                        "value": "ab"
                    }
                ],
                "timestamp": "2025-05-30T14:46:52Z",
                "request_id": "req_123456",
                "path": "/api/users",
                "metadata": {
                    "browser": "Chrome",
                    "platform": "Web"
                }
            }
        }