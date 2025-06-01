from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class RateLimit(BaseModel):
    user_id: str
    endpoint: str 
    requests: int
    window: int
    reset_time: datetime
    remaining: int

class RateLimitLog(BaseModel):  
    id: Optional[str]
    user_id: str
    endpoint: str
    ip_address: str
    timestamp: datetime