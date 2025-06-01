from typing import Dict, List, Optional
from datetime import datetime, UTC
import logging
from uuid import uuid4
from .database_service import DatabaseService
from ..models.user import (
    UserCreate, UserResponse, UserUpdate,
    UserType, UserRole, UserStatus
)

logger = logging.getLogger(__name__)

class UserService:
    def __init__(self):
        self.db = DatabaseService()
        self.startup_time = datetime.now(UTC)
        logger.info(f"""
        UserService initialized:
        Time: 2025-05-29 16:33:55
        User: fdygg
        """)

    async def create_user(
        self,
        user: UserCreate,
        created_by: str = "fdygg"
    ) -> Optional[UserResponse]:
        """Create new user"""
        try:
            # Generate user ID
            user_id = f"usr_{uuid4().hex[:8]}"
            
            # Check if username exists
            existing = await self.db.execute_query(
                "SELECT 1 FROM users WHERE username = ? AND user_type = ?",
                (user.username, user.user_type.value)
            )
            if existing:
                raise ValueError("Username already exists")

            # Check if growid exists for Discord users
            if user.user_type == UserType.DISCORD and user.growid:
                existing = await self.db.execute_query(
                    "SELECT 1 FROM users WHERE growid = ? AND user_type = ?",
                    (user.growid, UserType.DISCORD.value)
                )
                if existing:
                    raise ValueError("Growtopia ID already registered")

            query = """
            INSERT INTO users (
                id, username, email, password, user_type,
                growid, role, status, created_at, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            await self.db.execute_query(
                query,
                (
                    user_id,
                    user.username,
                    user.email,
                    user.password,  # Should be hashed by auth service
                    user.user_type.value,
                    user.growid,
                    user.role.value,
                    user.status.value,
                    datetime.now(UTC),
                    created_by
                ),
                fetch=False
            )
            
            return await self.get_user_by_id(user_id)

        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            return None

    async def get_user_by_id(self, user_id: str) -> Optional[UserResponse]:
        """Get user by ID"""
        query = "SELECT * FROM users WHERE id = ?"
        result = await self.db.execute_query(query, (user_id,))
        
        if not result:
            return None
            
        user = result[0]
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
            last_login=user["last_login"]
        )

    async def get_user_by_username(
        self,
        username: str,
        user_type: UserType
    ) -> Optional[UserResponse]:
        """Get user by username"""
        query = "SELECT * FROM users WHERE username = ? AND user_type = ?"
        result = await self.db.execute_query(
            query,
            (username, user_type.value)
        )
        
        if not result:
            return None
            
        user = result[0]
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
            last_login=user["last_login"]
        )

    async def update_user(
        self,
        user_id: str,
        update_data: UserUpdate
    ) -> Optional[UserResponse]:
        """Update user data"""
        try:
            # Get current user data
            current_user = await self.get_user_by_id(user_id)
            if not current_user:
                return None

            # Build update query
            update_fields = []
            params = []
            
            if update_data.email is not None:
                update_fields.append("email = ?")
                params.append(update_data.email)
                
            if update_data.growid is not None:
                if current_user.user_type == UserType.WEB:
                    raise ValueError("Web users cannot have Growtopia ID")
                update_fields.append("growid = ?")
                params.append(update_data.growid)
                
            if update_data.status is not None:
                update_fields.append("status = ?")
                params.append(update_data.status.value)

            if not update_fields:
                return current_user

            # Add timestamp and user_id
            update_fields.append("updated_at = ?")
            params.extend([datetime.now(UTC), user_id])

            query = f"""
            UPDATE users 
            SET {', '.join(update_fields)}
            WHERE id = ?
            """
            
            await self.db.execute_query(query, tuple(params), fetch=False)
            return await self.get_user_by_id(user_id)

        except Exception as e:
            logger.error(f"Error updating user: {str(e)}")
            return None

    async def delete_user(self, user_id: str) -> bool:
        """Soft delete user by setting status to INACTIVE"""
        try:
            query = """
            UPDATE users 
            SET 
                status = ?,
                updated_at = ?
            WHERE id = ?
            """
            
            await self.db.execute_query(
                query,
                (UserStatus.INACTIVE.value, datetime.now(UTC), user_id),
                fetch=False
            )
            return True
        except Exception as e:
            logger.error(f"Error deleting user: {str(e)}")
            return False

    async def get_users(
        self,
        user_type: Optional[UserType] = None,
        status: Optional[UserStatus] = None,
        role: Optional[UserRole] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[UserResponse]:
        """Get users with filters"""
        conditions = ["1=1"]
        params = []
        
        if user_type:
            conditions.append("user_type = ?")
            params.append(user_type.value)
            
        if status:
            conditions.append("status = ?")
            params.append(status.value)
            
        if role:
            conditions.append("role = ?")
            params.append(role.value)
            
        query = f"""
        SELECT * 
        FROM users 
        WHERE {' AND '.join(conditions)}
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
        """
        
        params.extend([limit, offset])
        results = await self.db.execute_query(query, tuple(params))
        
        return [
            UserResponse(
                id=user["id"],
                username=user["username"],
                email=user["email"],
                user_type=UserType(user["user_type"]),
                growid=user["growid"],
                role=UserRole(user["role"]),
                status=UserStatus(user["status"]),
                created_at=user["created_at"],
                created_by=user["created_by"],
                last_login=user["last_login"]
            )
            for user in results
        ]