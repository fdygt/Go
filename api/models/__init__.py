from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field

# Base configuration
CURRENT_TIMESTAMP = "2025-05-29 15:55:50"
CURRENT_USER = "fdygg"

# Import all models
from .auth import (
    LoginRequest,
    LoginResponse,
    Token,
    TokenData,
    AdminLoginRequest,
    RefreshTokenRequest,
    PasswordResetRequest,
    TwoFactorSetupResponse,
    TwoFactorVerifyRequest
)

from .user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserRole,
    UserStatus,
    UserType
)

from .balance import (
    Balance,
    BalanceResponse,
    BalanceUpdateRequest,
    BalanceHistoryResponse,
    Transaction,
    TransactionType,
    TransactionStatus,
    CurrencyType
)

from .conversion import (
    ConversionRate,
    ConversionRequest,
    ConversionResponse
)

from .product import (
    ProductBase,
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductType,
    ProductStatus
)

from .stock import (
    StockItem,
    StockAddRequest,
    StockReduceRequest,
    StockHistoryResponse,
    StockFilter,
    StockStatus,
    PriceInfo
)

from .transaction import (
    TransactionCreate,
    TransactionResponse,
    TransactionFilter,
    TransactionType,
    TransactionStatus
)

from .blacklist import (
    BlacklistEntry,
    BlacklistType,
    BlacklistReason,
    BlacklistStatus,
    FraudDetectionRule
)

from .admin import (
    AdminRole,
    AdminPermission,
    Platform,
    AdminStats,
    AdminActivity,
    AdminDashboard,
    AdminSettings
)

from .settings import (
    Setting,
    SettingCategory,
    FeatureFlag
)

# Common base models
class BaseTimestampModel(BaseModel):
    """Base model with timestamp"""
    created_at: datetime = Field(
        default_factory=lambda: datetime.strptime(
            CURRENT_TIMESTAMP,
            "%Y-%m-%d %H:%M:%S"
        )
    )
    updated_at: Optional[datetime] = None
    created_by: str = CURRENT_USER
    updated_by: Optional[str] = None

class BaseStatusModel(BaseModel):
    """Base model with status"""
    is_active: bool = True
    status: str = "active"
    status_changed_at: Optional[datetime] = None
    status_changed_by: Optional[str] = None

# Common response models
class BaseResponse(BaseModel):
    """Base response model"""
    success: bool = True
    timestamp: str = CURRENT_TIMESTAMP
    user: str = CURRENT_USER

class ErrorResponse(BaseResponse):
    """Error response model"""
    success: bool = False
    error: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class PaginatedResponse(BaseResponse):
    """Paginated response model"""
    data: List[Any]
    total: int
    page: int = Field(1, ge=1)
    limit: int = Field(10, ge=1, le=100)
    has_next: bool
    has_prev: bool

# Common filter models
class BaseDateRangeFilter(BaseModel):
    """Base date range filter"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = Field(
        default_factory=lambda: datetime.strptime(
            CURRENT_TIMESTAMP,
            "%Y-%m-%d %H:%M:%S"
        )
    )

class BaseUserFilter(BaseModel):
    """Base user filter"""
    user_id: Optional[str] = None
    user_type: Optional[str] = None  # discord/web
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

class BasePaginationParams(BaseModel):
    """Base pagination parameters"""
    page: int = Field(1, ge=1)
    limit: int = Field(10, ge=1, le=100)
    sort_by: Optional[str] = None
    sort_desc: bool = False

# Export all models
__all__ = [
    # Auth models
    "LoginRequest", "LoginResponse", "Token", "TokenData",
    "AdminLoginRequest", "RefreshTokenRequest", "PasswordResetRequest",
    "TwoFactorSetupResponse", "TwoFactorVerifyRequest",
    
    # User models
    "UserBase", "UserCreate", "UserUpdate", "UserResponse",
    "UserRole", "UserStatus", "UserType",
    
    # Balance & Currency models
    "Balance", "BalanceResponse", "BalanceUpdateRequest",
    "BalanceHistoryResponse", "Transaction", "TransactionType",
    "TransactionStatus", "CurrencyType",
    
    # Conversion models
    "ConversionRate", "ConversionRequest", "ConversionResponse",
    
    # Product models
    "ProductBase", "ProductCreate", "ProductUpdate",
    "ProductResponse", "ProductType", "ProductStatus",
    
    # Stock models
    "StockItem", "StockAddRequest", "StockReduceRequest",
    "StockHistoryResponse", "StockFilter", "StockStatus", "PriceInfo",
    
    # Transaction models
    "TransactionCreate", "TransactionResponse", "TransactionFilter",
    
    # Blacklist models
    "BlacklistEntry", "BlacklistType", "BlacklistReason",
    "BlacklistStatus", "FraudDetectionRule",
    
    # Admin models
    "AdminRole", "AdminPermission", "Platform", "AdminStats",
    "AdminActivity", "AdminDashboard", "AdminSettings",
    
    # Settings models
    "Setting", "SettingCategory", "FeatureFlag",
    
    # Base models
    "BaseTimestampModel", "BaseStatusModel", "BaseResponse",
    "ErrorResponse", "PaginatedResponse",
    
    # Filter models
    "BaseDateRangeFilter", "BaseUserFilter", "BasePaginationParams",
    
    # Constants
    "CURRENT_TIMESTAMP", "CURRENT_USER"
]

# Version info
VERSION = "1.0.0"
API_VERSION = "v1"