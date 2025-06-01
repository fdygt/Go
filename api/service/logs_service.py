from typing import Dict, List, Optional
from datetime import datetime, UTC
import logging
from uuid import uuid4
from .database_service import DatabaseService
from ..models.logs import (
    Log, LogLevel, LogCategory,
    AuditLog
)

logger = logging.getLogger(__name__)

class LogService:
    def __init__(self):
        self.db = DatabaseService()
        self.startup_time = datetime.now(UTC)
        logger.info(f"""
        LogService initialized:
        Time: 2025-05-29 17:11:23
        User: fdygg
        """)

    async def create_log(self, log: Log) -> Optional[Log]:
        """Create new log entry"""
        try:
            log_id = f"log_{uuid4().hex[:8]}"
            
            query = """
            INSERT INTO logs (
                id, level, category, message,
                source, timestamp, user_id, ip_address,
                metadata, stack_trace
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            await self.db.execute_query(
                query,
                (
                    log_id,
                    log.level.value,
                    log.category.value,
                    log.message,
                    log.source,
                    log.timestamp or datetime.now(UTC),
                    log.user_id,
                    log.ip_address,
                    str(log.metadata),
                    log.stack_trace
                ),
                fetch=False
            )
            
            return await self.get_log(log_id)
            
        except Exception as e:
            logger.error(f"Error creating log: {str(e)}")
            return None

    async def get_log(self, log_id: str) -> Optional[Log]:
        """Get log entry by ID"""
        query = "SELECT * FROM logs WHERE id = ?"
        result = await self.db.execute_query(query, (log_id,))
        
        if not result:
            return None
            
        log = result[0]
        return Log(
            id=log["id"],
            level=LogLevel(log["level"]),
            category=LogCategory(log["category"]),
            message=log["message"],
            source=log["source"],
            timestamp=log["timestamp"],
            user_id=log["user_id"],
            ip_address=log["ip_address"],
            metadata=eval(log["metadata"]) if log["metadata"] else {},
            stack_trace=log["stack_trace"]
        )

    async def get_logs(
        self,
        level: Optional[LogLevel] = None,
        category: Optional[LogCategory] = None,
        user_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Log]:
        """Get logs with filters"""
        conditions = ["1=1"]
        params = []
        
        if level:
            conditions.append("level = ?")
            params.append(level.value)
            
        if category:
            conditions.append("category = ?")
            params.append(category.value)
            
        if user_id:
            conditions.append("user_id = ?")
            params.append(user_id)
            
        if start_date:
            conditions.append("timestamp >= ?")
            params.append(start_date)
            
        if end_date:
            conditions.append("timestamp <= ?")
            params.append(end_date)
            
        query = f"""
        SELECT * 
        FROM logs 
        WHERE {' AND '.join(conditions)}
        ORDER BY timestamp DESC
        LIMIT ? OFFSET ?
        """
        
        params.extend([limit, offset])
        results = await self.db.execute_query(query, tuple(params))
        
        return [
            Log(
                id=log["id"],
                level=LogLevel(log["level"]),
                category=LogCategory(log["category"]),
                message=log["message"],
                source=log["source"],
                timestamp=log["timestamp"],
                user_id=log["user_id"],
                ip_address=log["ip_address"],
                metadata=eval(log["metadata"]) if log["metadata"] else {},
                stack_trace=log["stack_trace"]
            )
            for log in results
        ]

    async def create_audit_log(self, audit: AuditLog) -> Optional[AuditLog]:
        """Create new audit log entry"""
        try:
            audit_id = f"adt_{uuid4().hex[:8]}"
            
            query = """
            INSERT INTO audit_logs (
                id, user_id, action, resource_type,
                resource_id, changes, timestamp,
                ip_address, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            await self.db.execute_query(
                query,
                (
                    audit_id,
                    audit.user_id,
                    audit.action,
                    audit.resource_type,
                    audit.resource_id,
                    str(audit.changes),
                    audit.timestamp or datetime.now(UTC),
                    audit.ip_address,
                    str(audit.metadata)
                ),
                fetch=False
            )
            
            return await self.get_audit_log(audit_id)
            
        except Exception as e:
            logger.error(f"Error creating audit log: {str(e)}")
            return None

    async def get_audit_logs(
        self,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[AuditLog]:
        """Get audit logs with filters"""
        conditions = ["1=1"]
        params = []
        
        if user_id:
            conditions.append("user_id = ?")
            params.append(user_id)
            
        if action:
            conditions.append("action = ?")
            params.append(action)
            
        if resource_type:
            conditions.append("resource_type = ?")
            params.append(resource_type)
            
        if resource_id:
            conditions.append("resource_id = ?")
            params.append(resource_id)
            
        if start_date:
            conditions.append("timestamp >= ?")
            params.append(start_date)
            
        if end_date:
            conditions.append("timestamp <= ?")
            params.append(end_date)
            
        query = f"""
        SELECT * 
        FROM audit_logs 
        WHERE {' AND '.join(conditions)}
        ORDER BY timestamp DESC
        LIMIT ? OFFSET ?
        """
        
        params.extend([limit, offset])
        results = await self.db.execute_query(query, tuple(params))
        
        return [
            AuditLog(
                id=log["id"],
                user_id=log["user_id"],
                action=log["action"],
                resource_type=log["resource_type"],
                resource_id=log["resource_id"],
                changes=eval(log["changes"]) if log["changes"] else {},
                timestamp=log["timestamp"],
                ip_address=log["ip_address"],
                metadata=eval(log["metadata"]) if log["metadata"] else {}
            )
            for log in results
        ]