from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum
from .balance import CurrencyType  # Import CurrencyType

class StockStatus(str, Enum):
    AVAILABLE = "available"
    SOLD = "sold"
    RESERVED = "reserved"
    EXPIRED = "expired"
    INVALID = "invalid"

class PriceInfo(BaseModel):
    wl_price: Optional[int] = Field(0, ge=0)
    dl_price: Optional[int] = Field(0, ge=0)
    bgl_price: Optional[int] = Field(0, ge=0)
    rupiah_price: int = Field(..., ge=0)  # Wajib ada harga Rupiah

    @validator('*')
    def validate_non_negative(cls, v):
        if v < 0:
            raise ValueError("Price cannot be negative")
        return v

class StockItem(BaseModel):
    id: Optional[int] = None
    product_code: str = Field(..., description="Product code this stock belongs to")
    content: str = Field(..., min_length=1, description="Stock content (world name, account details, etc)")
    prices: PriceInfo
    status: StockStatus = Field(default=StockStatus.AVAILABLE)
    available_for: List[str] = Field(
        default=["discord", "web"],
        description="User types that can purchase this item"
    )
    added_by: str = Field(default="fdygg")
    added_at: datetime = Field(
        default_factory=lambda: datetime.strptime(
            "2025-05-29 15:48:40",
            "%Y-%m-%d %H:%M:%S"
        )
    )
    updated_at: Optional[datetime] = None
    buyer_id: Optional[str] = None
    seller_id: Optional[str] = None
    metadata: Dict = Field(default_factory=dict)

    @validator('available_for')
    def validate_available_for(cls, v):
        valid_types = ["discord", "web"]
        if not all(t in valid_types for t in v):
            raise ValueError(f"Invalid user type. Must be one of: {valid_types}")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "product_code": "FARM_WORLD",
                "content": "FARMWORLD1",
                "prices": {
                    "wl_price": 100,
                    "dl_price": 1,
                    "bgl_price": 0,
                    "rupiah_price": 50000
                },
                "status": "available",
                "available_for": ["discord", "web"],
                "added_by": "fdygg",
                "added_at": "2025-05-29 15:48:40",
                "metadata": {
                    "world_type": "farm",
                    "has_magplant": True
                }
            }
        }

class StockAddRequest(BaseModel):
    product_code: str = Field(..., description="Product code to add stock to")
    items: List[str] = Field(..., min_items=1, description="List of stock contents to add")
    prices: PriceInfo
    available_for: List[str] = Field(
        default=["discord", "web"],
        description="User types that can purchase this item"
    )
    metadata: Optional[Dict] = Field(default_factory=dict)
    
    @validator('items')
    def validate_items(cls, v):
        if not all(item.strip() for item in v):
            raise ValueError("Stock items cannot be empty")
        return [item.strip() for item in v]

    @validator('available_for')
    def validate_available_for(cls, v):
        valid_types = ["discord", "web"]
        if not all(t in valid_types for t in v):
            raise ValueError(f"Invalid user type. Must be one of: {valid_types}")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "product_code": "FARM_WORLD",
                "items": ["FARMWORLD1", "FARMWORLD2"],
                "prices": {
                    "wl_price": 100,
                    "dl_price": 1,
                    "bgl_price": 0,
                    "rupiah_price": 50000
                },
                "available_for": ["discord", "web"],
                "metadata": {
                    "world_type": "farm",
                    "has_magplant": True
                }
            }
        }