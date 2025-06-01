from fastapi import APIRouter, HTTPException, Request, Form, Depends
from fastapi.responses import JSONResponse
from datetime import datetime, UTC, timedelta
import logging
from typing import Optional

from ..config import config
from ..middleware import get_current_time, get_current_user, format_log_message
from ..models.auth import (
    LoginRequest,
    LoginResponse,
    TokenResponse,
    AdminLoginRequest,
    RefreshTokenRequest,
    PasswordResetRequest,
    TwoFactorSetupResponse,
    TwoFactorVerifyRequest
)
from ..service.auth_service import AuthService
from ..dependencies import get_bot, verify_admin

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/login", response_model=LoginResponse)
async def login(request: Request, login_data: LoginRequest):
    """Handle login form submission"""
    try:
        # Log login attempt
        logger.info(format_log_message(f"""
        Login attempt:
        IP: {request.client.host}
        User-Agent: {request.headers.get("user-agent")}
        Username: {login_data.username}
        Time: 2025-05-28 15:31:09 UTC
        """))
        
        if not login_data.username or not login_data.api_key:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Username and API key are required",
                    "type": "ValidationError",
                    "timestamp": "2025-05-28 15:31:09",
                    "path": request.url.path
                }
            )
        
        # Verify API key
        bot = get_bot()
        auth_service = AuthService(bot)
        
        if not await auth_service.verify_api_key(login_data.api_key, login_data.username):
            logger.warning(format_log_message(f"""
            Invalid login attempt:
            Username: {login_data.username}
            IP: {request.client.host}
            Time: 2025-05-28 15:31:09 UTC
            """))
            
            raise HTTPException(
                status_code=401,
                detail={
                    "message": "Invalid credentials",
                    "type": "AuthenticationError",
                    "timestamp": "2025-05-28 15:31:09",
                    "path": request.url.path
                }
            )
        
        # Create token
        token_data = await auth_service.create_access_token(
            username=login_data.username,
            api_key=login_data.api_key
        )
        
        # Update last login
        await auth_service.update_last_login(
            login_data.username,
            datetime.strptime("2025-05-28 15:31:09", "%Y-%m-%d %H:%M:%S")
        )
        
        # Log successful login
        logger.info(format_log_message(f"""
        Login successful:
        Username: {login_data.username}
        IP: {request.client.host}
        Time: 2025-05-28 15:31:09 UTC
        """))
        
        return JSONResponse(
            content={
                "access_token": token_data.access_token,
                "refresh_token": token_data.refresh_token,
                "token_type": "bearer",
                "username": login_data.username,
                "timestamp": "2025-05-28 15:31:09",
                "expires_in": 3600
            },
            headers={
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY",
                "X-XSS-Protection": "1; mode=block"
            }
        )
        
    except HTTPException:
        raise
        
    except Exception as e:
        logger.error(format_log_message(f"""
        Login error:
        Username: {login_data.username if login_data else None}
        Error: {str(e)}
        Time: 2025-05-28 15:31:09 UTC
        Path: {request.url.path}
        """))
        
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Login failed",
                "type": "InternalServerError",
                "timestamp": "2025-05-28 15:31:09",
                "path": request.url.path
            }
        )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_request: RefreshTokenRequest,
    bot=Depends(get_bot)
):
    """Refresh access token"""
    try:
        auth_service = AuthService(bot)
        new_tokens = await auth_service.refresh_token(refresh_request.refresh_token)
        
        return {
            "access_token": new_tokens.access_token,
            "refresh_token": new_tokens.refresh_token,
            "token_type": "bearer",
            "timestamp": "2025-05-28 15:31:09",
            "expires_in": 3600
        }
    except Exception as e:
        logger.error(f"""
        Token refresh error:
        Error: {str(e)}
        Time: 2025-05-28 15:31:09 UTC
        """)
        raise HTTPException(
            status_code=401,
            detail="Invalid refresh token"
        )

@router.post("/admin/login", response_model=LoginResponse)
async def admin_login(
    request: Request,
    login_data: AdminLoginRequest,
    bot=Depends(get_bot)
):
    """Handle admin login"""
    try:
        # Log admin login attempt
        logger.info(format_log_message(f"""
        Admin login attempt:
        IP: {request.client.host}
        Username: {login_data.username}
        Time: 2025-05-28 15:31:09 UTC
        """))

        auth_service = AuthService(bot)
        
        # Verify admin credentials
        if not await auth_service.verify_admin_credentials(
            login_data.username,
            login_data.password
        ):
            logger.warning(format_log_message(f"""
            Invalid admin login attempt:
            Username: {login_data.username}
            IP: {request.client.host}
            Time: 2025-05-28 15:31:09 UTC
            """))
            
            raise HTTPException(
                status_code=401,
                detail={
                    "message": "Invalid credentials",
                    "type": "AuthenticationError",
                    "timestamp": "2025-05-28 15:31:09"
                }
            )
            
        # Create admin token
        token_data = await auth_service.create_admin_token(login_data.username)
        
        # Update last login
        await auth_service.update_last_login(
            login_data.username,
            datetime.strptime("2025-05-28 15:31:09", "%Y-%m-%d %H:%M:%S")
        )
        
        return {
            "access_token": token_data.access_token,
            "refresh_token": token_data.refresh_token,
            "token_type": "bearer",
            "username": login_data.username,
            "timestamp": "2025-05-28 15:31:09",
            "expires_in": 3600
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"""
        Admin login error:
        Username: {login_data.username}
        Error: {str(e)}
        Time: 2025-05-28 15:31:09 UTC
        """)
        raise HTTPException(status_code=500, detail="Login failed")

@router.post("/2fa/setup", response_model=TwoFactorSetupResponse)
async def setup_2fa(
    current_user: str = Depends(get_current_user),
    bot=Depends(get_bot)
):
    """Setup 2FA for user"""
    try:
        auth_service = AuthService(bot)
        setup_data = await auth_service.setup_2fa("fdygg")
        
        return {
            "secret": setup_data.secret,
            "qr_code": setup_data.qr_code,
            "timestamp": "2025-05-28 15:31:09"
        }
    except Exception as e:
        logger.error(f"""
        2FA setup error:
        User: fdygg
        Error: {str(e)}
        Time: 2025-05-28 15:31:09 UTC
        """)
        raise HTTPException(status_code=400, detail="2FA setup failed")

@router.post("/2fa/verify")
async def verify_2fa(
    verify_request: TwoFactorVerifyRequest,
    current_user: str = Depends(get_current_user),
    bot=Depends(get_bot)
):
    """Verify 2FA code"""
    try:
        auth_service = AuthService(bot)
        is_valid = await auth_service.verify_2fa(
            "fdygg",
            verify_request.code
        )
        
        if not is_valid:
            raise HTTPException(
                status_code=401,
                detail="Invalid 2FA code"
            )
            
        return {
            "message": "2FA verification successful",
            "timestamp": "2025-05-28 15:31:09"
        }
    except Exception as e:
        logger.error(f"""
        2FA verification error:
        User: fdygg
        Error: {str(e)}
        Time: 2025-05-28 15:31:09 UTC
        """)
        raise HTTPException(status_code=400, detail="2FA verification failed")

@router.post("/reset-password")
async def request_password_reset(
    reset_request: PasswordResetRequest,
    bot=Depends(get_bot)
):
    """Request password reset"""
    try:
        auth_service = AuthService(bot)
        await auth_service.request_password_reset(
            reset_request.email,
            request_time=datetime.strptime("2025-05-28 15:31:09", "%Y-%m-%d %H:%M:%S")
        )
        
        return {
            "message": "Password reset instructions sent",
            "timestamp": "2025-05-28 15:31:09"
        }
    except Exception as e:
        logger.error(f"""
        Password reset request error:
        Email: {reset_request.email}
        Error: {str(e)}
        Time: 2025-05-28 15:31:09 UTC
        """))
        # Return success even if email not found for security
        return {
            "message": "Password reset instructions sent if email exists",
            "timestamp": "2025-05-28 15:31:09"
        }