from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum
from decimal import Decimal

class CurrencyType(str, Enum):
    WL = "wl"      # World Lock
    DL = "dl"      # Diamond Lock
    BGL = "bgl"    # Blue Gem Lock
    RUPIAH = "idr" # Indonesian Rupiah

class TransactionType(str, Enum):
    ADD = "add"
    SUBTRACT = "subtract"
    CONVERT = "convert"    # Untuk konversi antar currency
    DONATION = "donation"
    PURCHASE = "purchase"
    REFUND = "refund"
    ADJUSTMENT = "adjustment"

class TransactionStatus(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    REVERSED = "reversed"
    CANCELLED = "cancelled"

class Balance(BaseModel):
    wl_balance: int = Field(0, ge=0, description="Balance in World Locks")
    dl_balance: int = Field(0, ge=0, description="Balance in Diamond Locks")
    bgl_balance: int = Field(0, ge=0, description="Balance in Blue Gem Locks")
    rupiah_balance: int = Field(0, ge=0, description="Balance in Rupiah")

    @validator('wl_balance', 'dl_balance', 'bgl_balance', 'rupiah_balance')
    def validate_non_negative(cls, v):
        if v < 0:
            raise ValueError("Balance cannot be negative")
        return v

class BalanceResponse(BaseModel):
    user_id: str
    user_type: str  # "discord" atau "web"
    growid: Optional[str] = None  # Wajib untuk Discord user
    balance: Balance
    last_updated: datetime = Field(
        default_factory=lambda: datetime.strptime(
            "2025-05-29 15:43:09",
            "%Y-%m-%d %H:%M:%S"
        )
    )
    updated_by: str = Field(default="fdygg")
    
    @validator('growid')
    def validate_growid(cls, v, values):
        if values.get('user_type') == "discord" and not v:
            raise ValueError("Growtopia ID wajib diisi untuk user Discord")
        elif values.get('user_type') == "web" and v:
            raise ValueError("User Web tidak boleh memiliki Growtopia ID")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "usr_123456",
                "user_type": "discord",
                "growid": "PLAYER123",
                "balance": {
                    "wl_balance": 1000,
                    "dl_balance": 100,
                    "bgl_balance": 10,
                    "rupiah_balance": 1000000
                },
                "last_updated": "2025-05-29 15:43:09",
                "updated_by": "fdygg"
            }
        }

class BalanceUpdateRequest(BaseModel):
    currency_type: CurrencyType
    amount: int = Field(..., gt=0)
    transaction_type: TransactionType
    reason: Optional[str] = Field(
        None,
        min_length=3,
        max_length=200
    )
    
    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError("Amount must be greater than 0")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "currency_type": "wl",
                "amount": 1000,
                "transaction_type": "add",
                "reason": "Diamond Lock donation"
            }
        }

class Transaction(BaseModel):
    id: str = Field(..., description="Unique transaction ID")
    user_id: str
    user_type: str
    currency_type: CurrencyType
    transaction_type: TransactionType
    amount: int = Field(..., gt=0)
    timestamp: datetime = Field(
        default_factory=lambda: datetime.strptime(
            "2025-05-29 15:43:09",
            "%Y-%m-%d %H:%M:%S"
        )
    )
    created_by: str = Field(default="fdygg")
    description: Optional[str] = None
    status: TransactionStatus = Field(default=TransactionStatus.SUCCESS)
    metadata: Dict = Field(default_factory=dict)

    @validator('currency_type')
    def validate_currency_access(cls, v, values):
        if values.get('user_type') == "web" and v != CurrencyType.RUPIAH:
            raise ValueError("Web users can only access Rupiah currency")
        return v

class BalanceHistoryResponse(BaseModel):
    user_id: str
    user_type: str
    growid: Optional[str] = None
    transactions: List[Transaction] = Field(default_factory=list)
    total_records: int = Field(..., ge=0)
    status: str = Field("success")
    page: Optional[int] = Field(1, ge=1)
    page_size: Optional[int] = Field(10, ge=1, le=100)
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "usr_123456",
                "user_type": "discord",
                "growid": "PLAYER123",
                "transactions": [
                    {
                        "id": "txn_123456",
                        "user_id": "usr_123456",
                        "user_type": "discord",
                        "currency_type": "wl",
                        "transaction_type": "donation",
                        "amount": 1000,
                        "timestamp": "2025-05-29 15:43:09",
                        "created_by": "fdygg",
                        "description": "World Lock donation",
                        "status": "success",
                        "metadata": {
                            "donor_name": "DONOR123"
                        }
                    }
                ],
                "total_records": 1,
                "status": "success",
                "page": 1,
                "page_size": 10
            }
        }