from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

# Tipe user (Discord atau Web)
class UserType(str, Enum):
    DISCORD = "discord"    # User Discord (Growtopia Players)
    WEB = "web"           # User Web/App

# Role untuk user
class UserRole(str, Enum):
    ADMIN = "admin"           # Admin sistem
    MODERATOR = "moderator"   # Moderator
    DISCORD_USER = "discord_user"  # User biasa Discord
    WEB_USER = "web_user"         # User biasa Web

# Status akun user
class UserStatus(str, Enum):
    ACTIVE = "active"         # Akun aktif
    INACTIVE = "inactive"     # Akun tidak aktif
    SUSPENDED = "suspended"   # Akun disuspend
    BANNED = "banned"         # Akun dibanned

# Model dasar untuk User
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    user_type: UserType  # Wajib diisi (Discord/Web)
    growid: Optional[str] = Field(None, min_length=3, max_length=30)
    role: UserRole = Field(default=None)  # Role akan di-set berdasarkan user_type
    status: UserStatus = Field(default=UserStatus.ACTIVE)
    
    # Validasi untuk memastikan data sesuai tipe user
    @validator('role', pre=True, always=True)
    def set_role_based_on_type(cls, v, values):
        if not v:  # Jika role belum diset
            user_type = values.get('user_type')
            if user_type == UserType.DISCORD:
                return UserRole.DISCORD_USER
            elif user_type == UserType.WEB:
                return UserRole.WEB_USER
        return v
    
    # Validasi Growtopia ID
    @validator('growid')
    def validate_growid(cls, v, values):
        user_type = values.get('user_type')
        # Jika user Discord, growid wajib diisi
        if user_type == UserType.DISCORD and not v:
            raise ValueError('Growtopia ID wajib diisi untuk user Discord')
        # Jika user Web, growid tidak boleh diisi
        elif user_type == UserType.WEB and v:
            raise ValueError('User Web tidak boleh memiliki Growtopia ID')
        return v

# Model untuk membuat user baru
class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="Password minimal 8 karakter")
    confirm_password: str = Field(..., min_length=8)
    
    # Validasi password
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Password tidak cocok')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "player123",
                "email": "player@example.com",
                "user_type": "discord",
                "growid": "PLAYER123",  # Wajib untuk Discord user
                "password": "securepassword123",
                "confirm_password": "securepassword123"
            }
        }

# Model untuk response data user
class UserResponse(UserBase):
    id: str
    created_at: datetime = Field(
        default_factory=lambda: datetime.strptime(
            "2025-05-29 15:35:27",  # Menggunakan current timestamp
            "%Y-%m-%d %H:%M:%S"
        )
    )
    created_by: str = Field(default="fdygg")  # Menggunakan current user
    last_login: Optional[datetime] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "usr_123456",
                "username": "player123",
                "email": "player@example.com",
                "user_type": "discord",
                "growid": "PLAYER123",
                "role": "discord_user",
                "status": "active",
                "created_at": "2025-05-29 15:35:27",
                "created_by": "fdygg",
                "last_login": "2025-05-29 15:35:27"
            }
        }

# Model untuk update data user
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    growid: Optional[str] = Field(None, min_length=3, max_length=30)
    current_password: Optional[str] = None
    new_password: Optional[str] = None
    confirm_new_password: Optional[str] = None
    status: Optional[UserStatus] = None
    
    # Validasi password baru
    @validator('confirm_new_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and values['new_password'] and v != values['new_password']:
            raise ValueError('Password baru tidak cocok')
        return v
    
    # Validasi update growid
    @validator('growid')
    def validate_growid_update(cls, v, values, **kwargs):
        if v and len(v) < 3:
            raise ValueError('Growtopia ID minimal 3 karakter')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "email": "newemail@example.com",
                "growid": "NEWPLAYER123",
                "current_password": "oldpassword123",
                "new_password": "newpassword123",
                "confirm_new_password": "newpassword123",
                "status": "active"
            }
        }