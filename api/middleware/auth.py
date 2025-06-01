from fastapi import Request, Response
from fastapi.responses import JSONResponse
from typing import Optional, Dict, List, Set, Tuple
from datetime import datetime, UTC, timedelta
import logging
import jwt
from urllib.parse import urlparse
import re

from ..service.auth_service import AuthService
from ..service.user_service import UserService
from ..models.user import UserType, UserRole, UserStatus
from ..models.auth import TokenData

logger = logging.getLogger(__name__)

class AuthMiddleware:
    def __init__(self):
        self.auth_service = AuthService()
        self.user_service = UserService()
        self.startup_time = datetime.now(UTC)
        
        # Endpoint settings
        self.PUBLIC_ENDPOINTS = {
            r"^/auth/login$",
            r"^/auth/register$",
            r"^/docs",
            r"^/redoc",
            r"^/openapi.json$"
        }
        
        self.ADMIN_ENDPOINTS = {
            r"^/admin/",
            r"^/users/",
            r"^/settings/"
        }
        
        self.ROLE_PERMISSIONS = {
            UserRole.ADMIN: {"all"},  # Admin has all permissions
            UserRole.MODERATOR: {
                "view_users", 
                "manage_stock",
                "view_transactions"
            },
            UserRole.DISCORD_USER: {
                "view_stock",
                "make_purchase",
                "view_own_transactions"
            },
            UserRole.WEB_USER: {
                "view_stock",
                "make_purchase",
                "view_own_transactions"
            }
        }
        
        # Auth settings
        self.TOKEN_HEADER = "Authorization"
        self.TOKEN_TYPE = "Bearer"
        self.MAX_TOKEN_AGE = timedelta(days=7)
        
        # Rate limiting
        self.MAX_FAILED_ATTEMPTS = 5
        self.LOCKOUT_DURATION = timedelta(minutes=15)
        self.failed_attempts = {}
        
        logger.info(f"""
        AuthMiddleware initialized:
        Time: 2025-05-30 15:19:25
        User: fdygg
        """)

    def _is_public_endpoint(self, path: str) -> bool:
        """Check if endpoint is public"""
        return any(
            re.match(pattern, path)
            for pattern in self.PUBLIC_ENDPOINTS
        )

    def _is_admin_endpoint(self, path: str) -> bool:
        """Check if endpoint requires admin access"""
        return any(
            re.match(pattern, path)
            for pattern in self.ADMIN_ENDPOINTS
        )

    def _get_token_from_header(
        self,
        request: Request
    ) -> Optional[str]:
        """Extract token from Authorization header"""
        auth_header = request.headers.get(self.TOKEN_HEADER)
        if not auth_header:
            return None
            
        parts = auth_header.split()
        if len(parts) != 2 or parts[0] != self.TOKEN_TYPE:
            return None
            
        return parts[1]

    async def _validate_token(
        self,
        token: str
    ) -> Tuple[bool, Optional[TokenData], Optional[str]]:
        """Validate JWT token"""
        try:
            success, token_data = await self.auth_service.verify_token(token)
            if not success:
                return False, None, "Invalid or expired token"
                
            # Check token age
            now = datetime.now(UTC)
            if token_data.exp - now > self.MAX_TOKEN_AGE:
                return False, None, "Token exceeds maximum age"
                
            return True, token_data, None
            
        except Exception as e:
            logger.error(f"Token validation error: {str(e)}")
            return False, None, "Token validation failed"

    async def _check_user_permissions(
        self,
        user_id: str,
        required_permission: str,
        user_type: UserType
    ) -> Tuple[bool, Optional[str]]:
        """Check if user has required permission"""
        try:
            # Get user data
            user = await self.user_service.get_user_by_id(user_id)
            if not user:
                return False, "User not found"
                
            # Check user status
            if user.status != UserStatus.ACTIVE:
                return False, f"User account is {user.status.value}"
                
            # Get role permissions
            role_perms = self.ROLE_PERMISSIONS.get(user.role, set())
            
            # Check permission
            if "all" in role_perms or required_permission in role_perms:
                return True, None
                
            return False, "Insufficient permissions"
            
        except Exception as e:
            logger.error(f"Permission check error: {str(e)}")
            return False, "Permission check failed"

    async def _handle_failed_attempt(
        self,
        user_id: str
    ) -> Tuple[bool, Optional[str]]:
        """Handle failed authentication attempt"""
        now = datetime.now(UTC)
        
        if user_id not in self.failed_attempts:
            self.failed_attempts[user_id] = {
                "count": 0,
                "locked_until": None
            }
            
        attempts = self.failed_attempts[user_id]
        
        # Check if currently locked out
        if attempts["locked_until"] and now < attempts["locked_until"]:
            remaining = (attempts["locked_until"] - now).seconds
            return False, f"Account locked for {remaining} seconds"
            
        # Reset if lockout expired
        if attempts["locked_until"] and now >= attempts["locked_until"]:
            attempts["count"] = 0
            attempts["locked_until"] = None
            
        # Increment counter
        attempts["count"] += 1
        
        # Check if should lock
        if attempts["count"] >= self.MAX_FAILED_ATTEMPTS:
            attempts["locked_until"] = now + self.LOCKOUT_DURATION
            return False, f"Account locked for {self.LOCKOUT_DURATION.seconds} seconds"
            
        remaining = self.MAX_FAILED_ATTEMPTS - attempts["count"]
        return True, f"{remaining} attempts remaining"

    async def _clear_failed_attempts(self, user_id: str) -> None:
        """Clear failed attempts for user"""
        if user_id in self.failed_attempts:
            del self.failed_attempts[user_id]

    async def __call__(
        self,
        request: Request,
        call_next
    ):
        path = request.url.path
        
        # Skip auth for public endpoints
        if self._is_public_endpoint(path):
            return await call_next(request)
            
        try:
            # Get token
            token = self._get_token_from_header(request)
            if not token:
                return JSONResponse(
                    status_code=401,
                    content={"error": "Missing authorization token"}
                )
                
            # Validate token
            success, token_data, error = await self._validate_token(token)
            if not success:
                return JSONResponse(
                    status_code=401,
                    content={"error": error}
                )
                
            # Handle failed attempts
            attempt_ok, attempt_msg = await self._handle_failed_attempt(token_data.username)
            if not attempt_ok:
                return JSONResponse(
                    status_code=429,
                    content={"error": attempt_msg}
                )
                
            # Check permissions for admin endpoints
            if self._is_admin_endpoint(path):
                perms_ok, error = await self._check_user_permissions(
                    token_data.username,
                    "admin_access",
                    UserType.WEB  # Admin endpoints are web-only
                )
                if not perms_ok:
                    return JSONResponse(
                        status_code=403,
                        content={"error": error}
                    )
                    
            # Clear failed attempts on success
            await self._clear_failed_attempts(token_data.username)
            
            # Add user data to request state
            request.state.user = {
                "id": token_data.username,
                "role": token_data.role,
                "exp": token_data.exp
            }
            
            # Add auth headers
            response = await call_next(request)
            response.headers["X-User-ID"] = token_data.username
            response.headers["X-User-Role"] = token_data.role
            
            return response
            
        except Exception as e:
            logger.error(f"""
            Auth middleware error:
            Error: {str(e)}
            Time: 2025-05-30 15:19:25
            User: fdygg
            Path: {path}
            """)
            return JSONResponse(
                status_code=500,
                content={"error": "Authentication failed"}
            )

    async def get_auth_stats(self) -> Dict[str, Any]:
        """Get authentication statistics"""
        now = datetime.now(UTC)
        return {
            "total_locked_users": len([
                user_id for user_id, data 
                in self.failed_attempts.items()
                if data["locked_until"] and data["locked_until"] > now
            ]),
            "users_with_failed_attempts": len(self.failed_attempts),
            "uptime": (now - self.startup_time).seconds
        }
