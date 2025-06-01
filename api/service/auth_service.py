from typing import Dict, Optional, Tuple
from datetime import datetime, UTC, timedelta
import logging
import jwt
from passlib.hash import bcrypt
from uuid import uuid4
from .database_service import DatabaseService
from ..models.auth import Token, TokenData, LoginResponse
from ..models.user import UserType, UserRole, UserStatus, UserResponse

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self):
        self.db = DatabaseService()
        self.startup_time = datetime.now(UTC)
        self.SECRET_KEY = "your-secret-key-here"  # Should be in env vars
        self.ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours
        self.REFRESH_TOKEN_EXPIRE_DAYS = 30
        logger.info(f"""
        AuthService initialized:
        Time: 2025-05-29 16:33:55
        User: fdygg
        """)

    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return bcrypt.hash(password)

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password hash"""
        return bcrypt.verify(plain_password, hashed_password)

    def _create_token(self, data: dict, expires_delta: timedelta) -> str:
        """Create JWT token"""
        expire = datetime.now(UTC) + expires_delta
        to_encode = data.copy()
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self.SECRET_KEY, algorithm="HS256")

    def _create_tokens(self, user_data: Dict) -> Token:
        """Create access and refresh tokens"""
        access_token_expires = timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(days=self.REFRESH_TOKEN_EXPIRE_DAYS)

        access_token = self._create_token(
            data={
                "sub": user_data["id"],
                "username": user_data["username"],
                "user_type": user_data["user_type"],
                "role": user_data["role"]
            },
            expires_delta=access_token_expires
        )

        refresh_token = self._create_token(
            data={
                "sub": user_data["id"],
                "token_type": "refresh"
            },
            expires_delta=refresh_token_expires
        )

        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_at=datetime.now(UTC) + access_token_expires,
            refresh_token=refresh_token
        )

    async def authenticate_user(
        self,
        username: str,
        password: str,
        user_type: UserType
    ) -> Optional[UserResponse]:
        """Authenticate user and return user data"""
        query = """
        SELECT *
        FROM users
        WHERE username = ? AND user_type = ? AND status = ?
        """
        
        result = await self.db.execute_query(
            query,
            (username, user_type.value, UserStatus.ACTIVE.value)
        )
        
        if not result:
            return None
            
        user = result[0]
        if not self._verify_password(password, user["password"]):
            return None
            
        # Update last login
        await self.db.execute_query(
            "UPDATE users SET last_login = ? WHERE id = ?",
            (datetime.now(UTC), user["id"]),
            fetch=False
        )
            
        return UserResponse(
            id=user["id"],
            username=user["username"],
            email=user["email"],
            user_type=UserType(user["user_type"]),
            growid=user["growid"],
            role=UserRole(user["role"]),
            status=UserStatus(user["status"]),
            created_at=user["created_at"],
            created_by=user["created_by"],
            last_login=datetime.now(UTC)
        )

    async def login(
        self,
        username: str,
        password: str,
        user_type: UserType
    ) -> Tuple[bool, str, Optional[LoginResponse]]:
        """Login user and return tokens"""
        try:
            user = await self.authenticate_user(username, password, user_type)
            if not user:
                return False, "Invalid username or password", None

            tokens = self._create_tokens(user.dict())
            
            # Store refresh token
            await self.db.execute_query(
                """
                INSERT INTO refresh_tokens (
                    token, user_id, expires_at, created_at
                ) VALUES (?, ?, ?, ?)
                """,
                (
                    tokens.refresh_token,
                    user.id,
                    datetime.now(UTC) + timedelta(days=self.REFRESH_TOKEN_EXPIRE_DAYS),
                    datetime.now(UTC)
                ),
                fetch=False
            )

            return True, "Login successful", LoginResponse(
                access_token=tokens.access_token,
                token_type=tokens.token_type,
                expires_at=tokens.expires_at,
                user=user.dict()
            )

        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return False, "Login failed", None

    async def verify_token(self, token: str) -> Tuple[bool, Optional[TokenData]]:
        """Verify JWT token and return token data"""
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=["HS256"])
            token_data = TokenData(
                username=payload["username"],
                role=payload["role"],
                exp=datetime.fromtimestamp(payload["exp"], UTC)
            )
            return True, token_data
        except jwt.ExpiredSignatureError:
            return False, None
        except jwt.JWTError:
            return False, None
        except Exception as e:
            logger.error(f"Token verification error: {str(e)}")
            return False, None

    async def refresh_access_token(
        self,
        refresh_token: str
    ) -> Tuple[bool, str, Optional[Token]]:
        """Create new access token using refresh token"""
        try:
            # Verify refresh token
            payload = jwt.decode(
                refresh_token,
                self.SECRET_KEY,
                algorithms=["HS256"]
            )
            
            if payload.get("token_type") != "refresh":
                return False, "Invalid refresh token", None

            # Check if token exists and is not revoked
            token_valid = await self.db.execute_query(
                """
                SELECT * FROM refresh_tokens
                WHERE token = ? AND revoked = 0 AND expires_at > ?
                """,
                (refresh_token, datetime.now(UTC))
            )
            
            if not token_valid:
                return False, "Invalid or expired refresh token", None

            # Get user data
            user = await self.db.execute_query(
                "SELECT * FROM users WHERE id = ?",
                (payload["sub"],)
            )
            
            if not user:
                return False, "User not found", None

            # Create new tokens
            new_tokens = self._create_tokens(user[0])
            
            # Update refresh token
            await self.db.execute_query(
                "UPDATE refresh_tokens SET revoked = 1 WHERE token = ?",
                (refresh_token,),
                fetch=False
            )
            
            # Store new refresh token
            await self.db.execute_query(
                """
                INSERT INTO refresh_tokens (
                    token, user_id, expires_at, created_at
                ) VALUES (?, ?, ?, ?)
                """,
                (
                    new_tokens.refresh_token,
                    user[0]["id"],
                    datetime.now(UTC) + timedelta(days=self.REFRESH_TOKEN_EXPIRE_DAYS),
                    datetime.now(UTC)
                ),
                fetch=False
            )

            return True, "Token refreshed", new_tokens

        except Exception as e:
            logger.error(f"Token refresh error: {str(e)}")
            return False, "Failed to refresh token", None

    async def revoke_refresh_token(self, refresh_token: str) -> bool:
        """Revoke refresh token"""
        try:
            await self.db.execute_query(
                "UPDATE refresh_tokens SET revoked = 1 WHERE token = ?",
                (refresh_token,),
                fetch=False
            )
            return True
        except Exception as e:
            logger.error(f"Token revocation error: {str(e)}")
            return False

    async def check_permission(
        self,
        user_id: str,
        permission: str,
        user_type: UserType
    ) -> bool:
        """Check if user has specific permission"""
        try:
            query = """
            SELECT permissions
            FROM role_permissions rp
            JOIN users u ON u.role = rp.role
            WHERE u.id = ? AND u.user_type = ?
            """
            
            result = await self.db.execute_query(
                query,
                (user_id, user_type.value)
            )
            
            if not result:
                return False

            permissions = result[0]["permissions"].split(",")
            return "all" in permissions or permission in permissions

        except Exception as e:
            logger.error(f"Permission check error: {str(e)}")
            return False