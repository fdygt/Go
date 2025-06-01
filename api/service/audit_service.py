from typing import Dict, List, Optional
from datetime import datetime, UTC
import logging
from uuid import uuid4
from .database_service import DatabaseService
from ..models.audit import AuditLog, AuditAction, AuditCategory

logger = logging.getLogger(__name__)

class AuditService:
    def __init__(self):
        self.db = DatabaseService()
        self.startup_time = datetime.now(UTC)
        logger.info(f"""
        AuditService initialized:
        Time: 2025-05-29 17:08:40
        User: fdygg
        """)

    async def log_action(
        self,
        category: AuditCategory,
        action: AuditAction,
        actor_id: str,
        actor_type: str,
        target_id: Optional[str],
        target_type: str,
        description: str,
        metadata: Optional[Dict] = None
    ) -> Optional[AuditLog]:
        """Create new audit log entry"""
        try:
            audit_id = f"adt_{uuid4().hex[:8]}"
            
            query = """
            INSERT INTO audit_logs (
                id, category, action, actor_id,
                actor_type, target_id, target_type,
                description, metadata, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            await self.db.execute_query(
                query,
                (
                    audit_id,
                    category.value,
                    action.value,
                    actor_id,
                    actor_type,
                    target_id,
                    target_type,
                    description,
                    str(metadata or {}),
                    datetime.now(UTC)
                ),
                fetch=False
            )
            
            return await self.get_audit_log(audit_id)
            
        except Exception as e:
            logger.error(f"Error creating audit log: {str(e)}")
            return None

    async def get_audit_log(self, audit_id: str) -> Optional[AuditLog]:
        """Get single audit log entry"""
        query = "SELECT * FROM audit_logs WHERE id = ?"
        result = await self.db.execute_query(query, (audit_id,))
        
        if not result:
            return None
            
        log = result[0]
        return AuditLog(
            id=log["id"],
            category=AuditCategory(log["category"]),
            action=AuditAction(log["action"]),
            actor_id=log["actor_id"],
            actor_type=log["actor_type"],
            target_id=log["target_id"],
            target_type=log["target_type"],
            description=log["description"],
            metadata=eval(log["metadata"]) if log["metadata"] else {},
            created_at=log["created_at"]
        )

    async def get_audit_logs(
        self,
        category: Optional[AuditCategory] = None,
        action: Optional[AuditAction] = None,
        actor_id: Optional[str] = None,
        target_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[AuditLog]:
        """Get audit logs with filters"""
        conditions = ["1=1"]
        params = []
        
        if category:
            conditions.append("category = ?")
            params.append(category.value)
            
        if action:
            conditions.append("action = ?")
            params.append(action.value)
            
        if actor_id:
            conditions.append("actor_id = ?")
            params.append(actor_id)
            
        if target_id:
            conditions.append("target_id = ?")
            params.append(target_id)
            
        if start_date:
            conditions.append("created_at >= ?")
            params.append(start_date)
            
        if end_date:
            conditions.append("created_at <= ?")
            params.append(end_date)
            
        query = f"""
        SELECT * 
        FROM audit_logs 
        WHERE {' AND '.join(conditions)}
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
        """
        
        params.extend([limit, offset])
        results = await self.db.execute_query(query, tuple(params))
        
        return [
            AuditLog(
                id=log["id"],
                category=AuditCategory(log["category"]),
                action=AuditAction(log["action"]),
                actor_id=log["actor_id"],
                actor_type=log["actor_type"],
                target_id=log["target_id"],
                target_type=log["target_type"],
                description=log["description"],
                metadata=eval(log["metadata"]) if log["metadata"] else {},
                created_at=log["created_at"]
            )
            for log in results
        ]

    async def export_audit_logs(
        self,
        start_date: datetime,
        end_date: datetime,
        format: str = "csv"
    ) -> Optional[str]:
        """Export audit logs to file"""
        try:
            query = """
            SELECT * 
            FROM audit_logs 
            WHERE created_at BETWEEN ? AND ?
            ORDER BY created_at DESC
            """
            
            results = await self.db.execute_query(query, (start_date, end_date))
            
            if not results:
                return None
                
            if format == "csv":
                import csv
                import io
                
                output = io.StringIO()
                writer = csv.DictWriter(
                    output,
                    fieldnames=[
                        "id", "category", "action", "actor_id",
                        "actor_type", "target_id", "target_type",
                        "description", "metadata", "created_at"
                    ]
                )
                
                writer.writeheader()
                for row in results:
                    writer.writerow(row)
                    
                return output.getvalue()
                
            return None
            
        except Exception as e:
            logger.error(f"Error exporting audit logs: {str(e)}")
            return None