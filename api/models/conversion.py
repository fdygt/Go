from pydantic import BaseModel, Field, validator
from typing import Optional, Dict
from datetime import datetime
from enum import Enum
from .balance import CurrencyType

class ConversionRate(BaseModel):
    currency: CurrencyType = Field(..., description="Currency type (WL/DL/BGL)")
    rate_rupiah: int = Field(..., gt=0, description="Rate in Rupiah")
    min_amount: int = Field(1, ge=1, description="Minimum amount for conversion")
    max_amount: int = Field(..., gt=0, description="Maximum amount for conversion")
    is_active: bool = Field(default=True)
    updated_at: datetime = Field(
        default_factory=lambda: datetime.strptime(
            "2025-05-29 15:43:09",
            "%Y-%m-%d %H:%M:%S"
        )
    )
    updated_by: str = Field(default="fdygg")

    @validator('currency')
    def validate_currency(cls, v):
        if v == CurrencyType.RUPIAH:
            raise ValueError("Cannot set conversion rate for Rupiah")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "currency": "wl",
                "rate_rupiah": 5000,
                "min_amount": 1,
                "max_amount": 10000,
                "is_active": True,
                "updated_at": "2025-05-29 15:43:09",
                "updated_by": "fdygg"
            }
        }

class ConversionRequest(BaseModel):
    user_id: str
    user_type: str  # Harus "discord"
    from_currency: CurrencyType
    to_currency: CurrencyType
    amount: int = Field(..., gt=0)

    @validator('user_type')
    def validate_user_type(cls, v):
        if v != "discord":
            raise ValueError("Only Discord users can perform currency conversion")
        return v

    @validator('to_currency')
    def validate_to_currency(cls, v, values):
        from_curr = values.get('from_currency')
        if from_curr == v:
            raise ValueError("Cannot convert to same currency")
        if from_curr == CurrencyType.RUPIAH:
            raise ValueError("Cannot convert from Rupiah")
        if v != CurrencyType.RUPIAH:
            raise ValueError("Can only convert to Rupiah")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "usr_123456",
                "user_type": "discord",
                "from_currency": "wl",
                "to_currency": "idr",
                "amount": 1000
            }
        }

class ConversionResponse(BaseModel):
    conversion_id: str
    user_id: str
    from_currency: CurrencyType
    to_currency: CurrencyType
    amount: int
    converted_amount: int
    rate_used: int
    timestamp: datetime = Field(
        default_factory=lambda: datetime.strptime(
            "2025-05-29 15:43:09",
            "%Y-%m-%d %H:%M:%S"
        )
    )
    status: str = Field(default="success")
    metadata: Dict = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "conversion_id": "conv_123456",
                "user_id": "usr_123456",
                "from_currency": "wl",
                "to_currency": "idr",
                "amount": 1000,
                "converted_amount": 5000000,
                "rate_used": 5000,
                "timestamp": "2025-05-29 15:43:09",
                "status": "success",
                "metadata": {
                    "growid": "PLAYER123"
                }
            }
        }