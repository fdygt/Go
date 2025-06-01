from fastapi import APIRouter, HTTPException, Depends
from typing import List
from datetime import datetime, UTC
import logging

from ..models.user import (
    UserCreate, 
    UserUpdate, 
    UserResponse,
    UserRole,
    UserStatus
)
from ..service.user_service import UserService
from ..dependencies import get_bot, get_current_user, verify_admin

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/", response_model=UserResponse)
async def create_user(
    user: UserCreate,
    bot=Depends(get_bot)
):
    """Create a new user"""
    try:
        service = UserService(bot)
        return await service.create_user(user)
    except Exception as e:
        logger.error(f"""
        Create user error:
        Data: {user.dict(exclude={'password', 'confirm_password'})}
        Error: {str(e)}
        Time: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')} UTC
        """)
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: str = Depends(get_current_user),
    bot=Depends(get_bot)
):
    """Get current user's profile"""
    service = UserService(bot)
    user = await service.get_user_by_username(current_user)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    return user

@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: str = Depends(get_current_user),
    bot=Depends(get_bot)
):
    """Update current user's profile"""
    try:
        service = UserService(bot)
        return await service.update_user(current_user, user_update)
    except Exception as e:
        logger.error(f"""
        Update user error:
        Username: {current_user}
        Data: {user_update.dict(exclude={'current_password', 'new_password', 'confirm_new_password'})}
        Error: {str(e)}
        Time: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')} UTC
        """)
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

# Admin routes
@router.get("/", response_model=List[UserResponse], dependencies=[Depends(verify_admin)])
async def get_all_users(
    status: UserStatus = None,
    role: UserRole = None,
    bot=Depends(get_bot)
):
    """Get all users (admin only)"""
    service = UserService(bot)
    return await service.get_all_users(status=status, role=role)

@router.get("/{username}", response_model=UserResponse, dependencies=[Depends(verify_admin)])
async def get_user(
    username: str,
    bot=Depends(get_bot)
):
    """Get user by username (admin only)"""
    service = UserService(bot)
    user = await service.get_user_by_username(username)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    return user

@router.put("/{username}/status", response_model=UserResponse, dependencies=[Depends(verify_admin)])
async def update_user_status(
    username: str,
    status: UserStatus,
    bot=Depends(get_bot),
    current_user: str = Depends(get_current_user)
):
    """Update user status (admin only)"""
    try:
        service = UserService(bot)
        return await service.update_user_status(username, status, current_user)
    except Exception as e:
        logger.error(f"""
        Update user status error:
        Username: {username}
        New Status: {status}
        Updated By: {current_user}
        Error: {str(e)}
        Time: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')} UTC
        """)
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

@router.put("/{username}/role", response_model=UserResponse, dependencies=[Depends(verify_admin)])
async def update_user_role(
    username: str,
    role: UserRole,
    bot=Depends(get_bot),
    current_user: str = Depends(get_current_user)
):
    """Update user role (admin only)"""
    try:
        service = UserService(bot)
        return await service.update_user_role(username, role, current_user)
    except Exception as e:
        logger.error(f"""
        Update user role error:
        Username: {username}
        New Role: {role}
        Updated By: {current_user}
        Error: {str(e)}
        Time: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')} UTC
        """)
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )