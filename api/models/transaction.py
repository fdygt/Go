from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, Dict, List
from enum import Enum
from decimal import Decimal

class TransactionType(str, Enum):
    PURCHASE = "purchase"
    REFUND = "refund"
    RESTOCK = "restock"
    VOID = "void"
    ADJUSTMENT = "adjustment"
    CONVERSION = "conversion"  # Untuk konversi currency
    TRANSFER = "transfer"     # Untuk transfer antar user

class TransactionStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    VOIDED = "voided"
    REFUNDED = "refunded"

class CurrencyType(str, Enum):
    WL = "wl"      # World Lock
    DL = "dl"      # Diamond Lock
    BGL = "bgl"    # Blue Gem Lock
    RUPIAH = "idr" # Indonesian Rupiah

class TransactionCreate(BaseModel):
    user_id: str = Field(..., description="User's ID")
    user_type: str = Field(..., description="User type (discord/web)")
    growid: Optional[str] = Field(None, min_length=3, description="Growtopia ID (required for Discord users)")
    type: TransactionType = Field(..., description="Type of transaction")
    currency: CurrencyType = Field(..., description="Currency type")
    amount: int = Field(..., gt=0, description="Transaction amount")
    details: str = Field(..., min_length=3, description="Transaction details")
    items: Optional[List[int]] = Field(None, description="List of stock item IDs")
    metadata: Dict = Field(default_factory=dict)
    
    @validator('growid')
    def validate_growid(cls, v, values):
        if values.get('user_type') == "discord" and not v:
            raise ValueError("Growtopia ID required for Discord users")
        elif values.get('user_type') == "web" and v:
            raise ValueError("Web users cannot have Growtopia ID")
        return v
    
    @validator('currency')
    def validate_currency_type(cls, v, values):
        if values.get('user_type') == "web" and v != CurrencyType.RUPIAH:
            raise ValueError("Web users can only use Rupiah")
        return v
    
    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError("Amount must be greater than 0")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "usr_123456",
                "user_type": "discord",
                "growid": "PLAYER123",
                "type": "purchase",
                "currency": "wl",
                "amount": 100,
                "details": "Purchase of 1x Farm World",
                "items": [1],
                "metadata": {
                    "world_name": "FARMWORLD1",
                    "purchase_method": "manual"
                }
            }
        }

class TransactionResponse(BaseModel):
    id: str = Field(..., description="Transaction ID")
    user_id: str
    user_type: str
    growid: Optional[str]
    type: TransactionType
    currency: CurrencyType
    details: str
    amount: int
    balances: Dict[str, int] = Field(
        ...,
        description="Updated balances after transaction"
    )
    status: TransactionStatus = Field(default=TransactionStatus.COMPLETED)
    items: Optional[List[Dict]] = None
    created_at: datetime = Field(
        default_factory=lambda: datetime.strptime(
            "2025-05-29 15:45:52",
            "%Y-%m-%d %H:%M:%S"
        )
    )
    created_by: str = Field(default="fdygg")
    updated_at: Optional[datetime] = None
    metadata: Dict = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "txn_123456",
                "user_id": "usr_123456",
                "user_type": "discord",
                "growid": "PLAYER123",
                "type": "purchase",
                "currency": "wl",
                "details": "Purchase of 1x Farm World",
                "amount": 100,
                "balances": {
                    "wl": 900,
                    "dl": 10,
                    "bgl": 1,
                    "idr": 1000000
                },
                "status": "completed",
                "items": [
                    {
                        "id": 1,
                        "content": "FARMWORLD1",
                        "type": "world"
                    }
                ],
                "created_at": "2025-05-29 15:45:52",
                "created_by": "fdygg",
                "metadata": {
                    "world_name": "FARMWORLD1",
                    "purchase_method": "manual"
                }
            }
        }

class TransactionFilter(BaseModel):
    user_id: Optional[str] = None
    user_type: Optional[str] = None
    growid: Optional[str] = None
    type: Optional[TransactionType] = None
    currency: Optional[CurrencyType] = None
    status: Optional[TransactionStatus] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    min_amount: Optional[int] = Field(None, ge=0)
    max_amount: Optional[int] = Field(None, ge=0)
    
    @validator('end_date')
    def validate_dates(cls, v, values):
        if v and 'start_date' in values and values['start_date']:
            if v < values['start_date']:
                raise ValueError("End date must be after start date")
        return v
    
    @validator('max_amount')
    def validate_amounts(cls, v, values):
        if v and 'min_amount' in values and values['min_amount']:
            if v < values['min_amount']:
                raise ValueError("Max amount must be greater than min amount")
        return v