from typing import Dict, List, Optional
from datetime import datetime, UTC
import logging
from uuid import uuid4
from .database_service import DatabaseService
from .auth_service import AuthService
from ..models.admin import (
    AdminCreate, AdminUpdate, AdminResponse,
    AdminRole, AdminStatus, AdminPermission
)

logger = logging.getLogger(__name__)

class AdminService:
    def __init__(self):
        self.db = DatabaseService()
        self.auth = AuthService()
        self.startup_time = datetime.now(UTC)
        logger.info(f"""
        AdminService initialized:
        Time: 2025-05-29 16:38:49
        User: fdygg
        """)

    async def create_admin(
        self,
        admin: AdminCreate,
        created_by: str = "fdygg"
    ) -> Optional[AdminResponse]:
        """Create new admin"""
        try:
            # Generate admin ID
            admin_id = f"adm_{uuid4().hex[:8]}"
            
            # Check if username exists
            existing = await self.db.execute_query(
                "SELECT 1 FROM admins WHERE username = ?",
                (admin.username,)
            )
            if existing:
                raise ValueError("Username already exists")

            # Hash password
            hashed_password = self.auth._hash_password(admin.password)
            
            query = """
            INSERT INTO admins (
                id, username, email, password, role,
                permissions, status, created_at, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            await self.db.execute_query(
                query,
                (
                    admin_id,
                    admin.username,
                    admin.email,
                    hashed_password,
                    admin.role.value,
                    ",".join([p.value for p in admin.permissions]),
                    AdminStatus.ACTIVE.value,
                    datetime.now(UTC),
                    created_by
                ),
                fetch=False
            )
            
            return await self.get_admin_by_id(admin_id)

        except Exception as e:
            logger.error(f"Error creating admin: {str(e)}")
            return None

    async def get_admin_by_id(self, admin_id: str) -> Optional[AdminResponse]:
        """Get admin by ID"""
        query = "SELECT * FROM admins WHERE id = ?"
        result = await self.db.execute_query(query, (admin_id,))
        
        if not result:
            return None
            
        admin = result[0]
        return AdminResponse(
            id=admin["id"],
            username=admin["username"],
            email=admin["email"],
            role=AdminRole(admin["role"]),
            permissions=[AdminPermission(p) for p in admin["permissions"].split(",")],
            status=AdminStatus(admin["status"]),
            created_at=admin["created_at"],
            created_by=admin["created_by"],
            last_login=admin["last_login"]
        )

    async def update_admin(
        self,
        admin_id: str,
        update_data: AdminUpdate,
        updated_by: str
    ) -> Optional[AdminResponse]:
        """Update admin data"""
        try:
            # Get current admin
            current_admin = await self.get_admin_by_id(admin_id)
            if not current_admin:
                return None

            # Build update query
            update_fields = []
            params = []
            
            if update_data.email is not None:
                update_fields.append("email = ?")
                params.append(update_data.email)
                
            if update_data.role is not None:
                update_fields.append("role = ?")
                params.append(update_data.role.value)
                
            if update_data.permissions is not None:
                update_fields.append("permissions = ?")
                params.append(",".join([p.value for p in update_data.permissions]))
                
            if update_data.status is not None:
                update_fields.append("status = ?")
                params.append(update_data.status.value)
                
            if update_data.new_password:
                # Verify current password first
                admin = await self.db.execute_query(
                    "SELECT password FROM admins WHERE id = ?",
                    (admin_id,)
                )
                if not admin or not self.auth._verify_password(
                    update_data.current_password,
                    admin[0]["password"]
                ):
                    raise ValueError("Invalid current password")
                    
                update_fields.append("password = ?")
                params.append(self.auth._hash_password(update_data.new_password))

            if not update_fields:
                return current_admin

            # Add updated_at and admin_id
            update_fields.extend(["updated_at = ?", "updated_by = ?"])
            params.extend([datetime.now(UTC), updated_by, admin_id])

            query = f"""
            UPDATE admins 
            SET {', '.join(update_fields)}
            WHERE id = ?
            """
            
            await self.db.execute_query(query, tuple(params), fetch=False)
            return await self.get_admin_by_id(admin_id)

        except Exception as e:
            logger.error(f"Error updating admin: {str(e)}")
            return None

    async def delete_admin(self, admin_id: str) -> bool:
        """Soft delete admin by setting status to INACTIVE"""
        try:
            query = """
            UPDATE admins 
            SET 
                status = ?,
                updated_at = ?
            WHERE id = ?
            """
            
            await self.db.execute_query(
                query,
                (AdminStatus.INACTIVE.value, datetime.now(UTC), admin_id),
                fetch=False
            )
            return True
        except Exception as e:
            logger.error(f"Error deleting admin: {str(e)}")
            return False

    async def get_admins(
        self,
        role: Optional[AdminRole] = None,
        status: Optional[AdminStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[AdminResponse]:
        """Get admins with filters"""
        conditions = ["1=1"]
        params = []
        
        if role:
            conditions.append("role = ?")
            params.append(role.value)
            
        if status:
            conditions.append("status = ?")
            params.append(status.value)
            
        query = f"""
        SELECT * 
        FROM admins 
        WHERE {' AND '.join(conditions)}
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
        """
        
        params.extend([limit, offset])
        results = await self.db.execute_query(query, tuple(params))
        
        return [
            AdminResponse(
                id=admin["id"],
                username=admin["username"],
                email=admin["email"],
                role=AdminRole(admin["role"]),
                permissions=[AdminPermission(p) for p in admin["permissions"].split(",")],
                status=AdminStatus(admin["status"]),
                created_at=admin["created_at"],
                created_by=admin["created_by"],
                last_login=admin["last_login"]
            )
            for admin in results
        ]

    async def check_permission(
        self,
        admin_id: str,
        required_permission: AdminPermission
    ) -> bool:
        """Check if admin has specific permission"""
        try:
            admin = await self.get_admin_by_id(admin_id)
            if not admin or admin.status != AdminStatus.ACTIVE:
                return False
                
            if admin.role == AdminRole.SUPER_ADMIN:
                return True
                
            return (
                AdminPermission.ALL in admin.permissions or
                required_permission in admin.permissions
            )
            
        except Exception as e:
            logger.error(f"Error checking admin permission: {str(e)}")
            return False