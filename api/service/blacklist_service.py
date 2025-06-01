from typing import Dict, List, Optional
from datetime import datetime, UTC
import logging
from uuid import uuid4
from .database_service import DatabaseService
from ..models.blacklist import (
    BlacklistEntry, BlacklistType, BlacklistReason,
    BlacklistStatus, FraudDetectionRule
)

logger = logging.getLogger(__name__)

class BlacklistService:
    def __init__(self):
        self.db = DatabaseService()
        self.startup_time = datetime.now(UTC)
        logger.info(f"""
        BlacklistService initialized:
        Time: 2025-05-29 17:17:02
        User: fdygg
        """)

    async def create_blacklist(
        self,
        entry: BlacklistEntry,
        created_by: str = "fdygg"
    ) -> Optional[BlacklistEntry]:
        """Create new blacklist entry"""
        try:
            blacklist_id = f"bl_{uuid4().hex[:8]}"
            
            # Check if entry already exists
            existing = await self.check_blacklist(
                entry.type,
                entry.value
            )
            if existing:
                if existing.status == BlacklistStatus.ACTIVE:
                    raise ValueError("Entry already blacklisted")
                # If entry exists but not active, reactivate it
                return await self.update_blacklist_status(
                    existing.id,
                    BlacklistStatus.ACTIVE,
                    created_by
                )

            query = """
            INSERT INTO blacklist (
                id, type, value, user_type, reason,
                description, evidence, status, expires_at,
                created_by, created_at, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            await self.db.execute_query(
                query,
                (
                    blacklist_id,
                    entry.type.value,
                    entry.value,
                    entry.user_type,
                    entry.reason.value,
                    entry.description,
                    str(entry.evidence),
                    entry.status.value,
                    entry.expires_at,
                    created_by,
                    datetime.now(UTC),
                    str(entry.metadata)
                ),
                fetch=False
            )
            
            return await self.get_blacklist_entry(blacklist_id)
            
        except Exception as e:
            logger.error(f"Error creating blacklist entry: {str(e)}")
            return None

    async def get_blacklist_entry(
        self,
        entry_id: str
    ) -> Optional[BlacklistEntry]:
        """Get blacklist entry by ID"""
        query = "SELECT * FROM blacklist WHERE id = ?"
        result = await self.db.execute_query(query, (entry_id,))
        
        if not result:
            return None
            
        entry = result[0]
        return BlacklistEntry(
            id=entry["id"],
            type=BlacklistType(entry["type"]),
            value=entry["value"],
            user_type=entry["user_type"],
            reason=BlacklistReason(entry["reason"]),
            description=entry["description"],
            evidence=eval(entry["evidence"]) if entry["evidence"] else [],
            status=BlacklistStatus(entry["status"]),
            expires_at=entry["expires_at"],
            created_by=entry["created_by"],
            created_at=entry["created_at"],
            updated_by=entry["updated_by"],
            updated_at=entry["updated_at"],
            metadata=eval(entry["metadata"]) if entry["metadata"] else {}
        )

    async def check_blacklist(
        self,
        entry_type: BlacklistType,
        value: str,
        include_expired: bool = False
    ) -> Optional[BlacklistEntry]:
        """Check if value is blacklisted"""
        conditions = ["type = ? AND value = ?"]
        params = [entry_type.value, value]
        
        if not include_expired:
            conditions.append("""
                (status = ? OR 
                (status = ? AND (expires_at IS NULL OR expires_at > ?)))
            """)
            params.extend([
                BlacklistStatus.ACTIVE.value,
                BlacklistStatus.ACTIVE.value,
                datetime.now(UTC)
            ])
            
        query = f"""
        SELECT * FROM blacklist 
        WHERE {' AND '.join(conditions)}
        ORDER BY created_at DESC 
        LIMIT 1
        """
        
        result = await self.db.execute_query(query, tuple(params))
        if not result:
            return None
            
        entry = result[0]
        return BlacklistEntry(
            id=entry["id"],
            type=BlacklistType(entry["type"]),
            value=entry["value"],
            user_type=entry["user_type"],
            reason=BlacklistReason(entry["reason"]),
            description=entry["description"],
            evidence=eval(entry["evidence"]) if entry["evidence"] else [],
            status=BlacklistStatus(entry["status"]),
            expires_at=entry["expires_at"],
            created_by=entry["created_by"],
            created_at=entry["created_at"],
            updated_by=entry["updated_by"],
            updated_at=entry["updated_at"],
            metadata=eval(entry["metadata"]) if entry["metadata"] else {}
        )

    async def update_blacklist_status(
        self,
        entry_id: str,
        new_status: BlacklistStatus,
        updated_by: str,
        metadata: Optional[Dict] = None
    ) -> Optional[BlacklistEntry]:
        """Update blacklist entry status"""
        try:
            query = """
            UPDATE blacklist 
            SET 
                status = ?,
                updated_by = ?,
                updated_at = ?,
                metadata = CASE 
                    WHEN ? IS NOT NULL THEN ?
                    ELSE metadata 
                END
            WHERE id = ?
            """
            
            await self.db.execute_query(
                query,
                (
                    new_status.value,
                    updated_by,
                    datetime.now(UTC),
                    metadata,
                    str(metadata) if metadata else None,
                    entry_id
                ),
                fetch=False
            )
            
            return await self.get_blacklist_entry(entry_id)
            
        except Exception as e:
            logger.error(f"Error updating blacklist status: {str(e)}")
            return None

    async def get_blacklist_entries(
        self,
        entry_type: Optional[BlacklistType] = None,
        reason: Optional[BlacklistReason] = None,
        status: Optional[BlacklistStatus] = None,
        user_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[BlacklistEntry]:
        """Get blacklist entries with filters"""
        conditions = ["1=1"]
        params = []
        
        if entry_type:
            conditions.append("type = ?")
            params.append(entry_type.value)
            
        if reason:
            conditions.append("reason = ?")
            params.append(reason.value)
            
        if status:
            conditions.append("status = ?")
            params.append(status.value)
            
        if user_type:
            conditions.append("user_type = ?")
            params.append(user_type)
            
        if start_date:
            conditions.append("created_at >= ?")
            params.append(start_date)
            
        if end_date:
            conditions.append("created_at <= ?")
            params.append(end_date)
            
        query = f"""
        SELECT * 
        FROM blacklist 
        WHERE {' AND '.join(conditions)}
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
        """
        
        params.extend([limit, offset])
        results = await self.db.execute_query(query, tuple(params))
        
        return [
            BlacklistEntry(
                id=entry["id"],
                type=BlacklistType(entry["type"]),
                value=entry["value"],
                user_type=entry["user_type"],
                reason=BlacklistReason(entry["reason"]),
                description=entry["description"],
                evidence=eval(entry["evidence"]) if entry["evidence"] else [],
                status=BlacklistStatus(entry["status"]),
                expires_at=entry["expires_at"],
                created_by=entry["created_by"],
                created_at=entry["created_at"],
                updated_by=entry["updated_by"],
                updated_at=entry["updated_at"],
                metadata=eval(entry["metadata"]) if entry["metadata"] else {}
            )
            for entry in results
        ]

    async def create_fraud_rule(
        self,
        rule: FraudDetectionRule
    ) -> Optional[FraudDetectionRule]:
        """Create new fraud detection rule"""
        try:
            rule_id = f"fr_{uuid4().hex[:8]}"
            
            query = """
            INSERT INTO fraud_rules (
                id, name, description, platform,
                conditions, actions, created_at, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            await self.db.execute_query(
                query,
                (
                    rule_id,
                    rule.name,
                    rule.description,
                    ",".join(rule.platform),
                    str(rule.conditions),
                    str(rule.actions),
                    datetime.now(UTC),
                    "fdygg"
                ),
                fetch=False
            )
            
            return await self.get_fraud_rule(rule_id)
            
        except Exception as e:
            logger.error(f"Error creating fraud rule: {str(e)}")
            return None

    async def get_fraud_rule(
        self,
        rule_id: str
    ) -> Optional[FraudDetectionRule]:
        """Get fraud detection rule by ID"""
        query = "SELECT * FROM fraud_rules WHERE id = ?"
        result = await self.db.execute_query(query, (rule_id,))
        
        if not result:
            return None
            
        rule = result[0]
        return FraudDetectionRule(
            id=rule["id"],
            name=rule["name"],
            description=rule["description"],
            platform=rule["platform"].split(","),
            conditions=eval(rule["conditions"]),
            actions=eval(rule["actions"])
        )

    async def check_fraud_rules(
        self,
        context: Dict
    ) -> List[Dict]:
        """Check context against all active fraud rules"""
        try:
            # Get all active rules
            query = "SELECT * FROM fraud_rules WHERE is_active = 1"
            rules = await self.db.execute_query(query)
            
            triggered_rules = []
            
            for rule in rules:
                conditions = eval(rule["conditions"])
                matches = True
                
                # Check platform
                if context.get("platform") not in rule["platform"].split(","):
                    continue
                    
                # Check all conditions
                for condition in conditions:
                    if condition["type"] == "equals":
                        if context.get(condition["field"]) != condition["value"]:
                            matches = False
                            break
                    elif condition["type"] == "contains":
                        if condition["value"] not in str(context.get(condition["field"], "")):
                            matches = False
                            break
                    elif condition["type"] == "greater_than":
                        if not context.get(condition["field"]) > condition["value"]:
                            matches = False
                            break
                    elif condition["type"] == "less_than":
                        if not context.get(condition["field"]) < condition["value"]:
                            matches = False
                            break
                
                if matches:
                    triggered_rules.append({
                        "rule_id": rule["id"],
                        "name": rule["name"],
                        "actions": eval(rule["actions"])
                    })
            
            return triggered_rules
            
        except Exception as e:
            logger.error(f"Error checking fraud rules: {str(e)}")
            return []

    async def get_fraud_rules(
        self,
        platform: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[FraudDetectionRule]:
        """Get fraud detection rules with filters"""
        conditions = ["1=1"]
        params = []
        
        if platform:
            conditions.append("platform LIKE ?")
            params.append(f"%{platform}%")
            
        if is_active is not None:
            conditions.append("is_active = ?")
            params.append(is_active)
            
        query = f"""
        SELECT * 
        FROM fraud_rules 
        WHERE {' AND '.join(conditions)}
        ORDER BY created_at DESC
        """
        
        results = await self.db.execute_query(query, tuple(params))
        
        return [
            FraudDetectionRule(
                id=rule["id"],
                name=rule["name"],
                description=rule["description"],
                platform=rule["platform"].split(","),
                conditions=eval(rule["conditions"]),
                actions=eval(rule["actions"])
            )
            for rule in results
        ]