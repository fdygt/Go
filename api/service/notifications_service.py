from typing import Dict, List, Optional
from datetime import datetime, UTC
import logging
from uuid import uuid4
from .database_service import DatabaseService
from ..models.notifications import (
    Notification, NotificationType, NotificationPriority,
    NotificationChannel, NotificationStatus
)

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self):
        self.db = DatabaseService()
        self.startup_time = datetime.now(UTC)
        logger.info(f"""
        NotificationService initialized:
        Time: 2025-05-29 17:11:23
        User: fdygg
        """)

    async def create_notification(
        self,
        notification: Notification
    ) -> Optional[Notification]:
        """Create new notification"""
        try:
            notification_id = f"not_{uuid4().hex[:8]}"
            
            query = """
            INSERT INTO notifications (
                id, type, priority, channels, recipient_id,
                title, content, data, status, created_by,
                created_at, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            await self.db.execute_query(
                query,
                (
                    notification_id,
                    notification.type.value,
                    notification.priority.value,
                    ",".join([c.value for c in notification.channels]),
                    notification.recipient_id,
                    notification.title,
                    notification.content,
                    str(notification.data),
                    NotificationStatus.PENDING.value,
                    "fdygg",
                    datetime.now(UTC),
                    str(notification.metadata)
                ),
                fetch=False
            )
            
            return await self.get_notification(notification_id)
            
        except Exception as e:
            logger.error(f"Error creating notification: {str(e)}")
            return None

    async def get_notification(self, notification_id: str) -> Optional[Notification]:
        """Get notification by ID"""
        query = "SELECT * FROM notifications WHERE id = ?"
        result = await self.db.execute_query(query, (notification_id,))
        
        if not result:
            return None
            
        notif = result[0]
        return Notification(
            id=notif["id"],
            type=NotificationType(notif["type"]),
            priority=NotificationPriority(notif["priority"]),
            channels=[NotificationChannel(c) for c in notif["channels"].split(",")],
            recipient_id=notif["recipient_id"],
            title=notif["title"],
            content=notif["content"],
            data=eval(notif["data"]) if notif["data"] else {},
            status=NotificationStatus(notif["status"]),
            created_by=notif["created_by"],
            created_at=notif["created_at"],
            sent_at=notif["sent_at"],
            read_at=notif["read_at"],
            metadata=eval(notif["metadata"]) if notif["metadata"] else {}
        )

    async def update_status(
        self,
        notification_id: str,
        status: NotificationStatus,
        metadata: Optional[Dict] = None
    ) -> bool:
        """Update notification status"""
        try:
            update_fields = ["status = ?", "updated_at = ?"]
            params = [status.value, datetime.now(UTC)]
            
            if status == NotificationStatus.SENT:
                update_fields.append("sent_at = ?")
                params.append(datetime.now(UTC))
            elif status == NotificationStatus.READ:
                update_fields.append("read_at = ?")
                params.append(datetime.now(UTC))
                
            if metadata:
                update_fields.append("metadata = ?")
                params.append(str(metadata))
                
            query = f"""
            UPDATE notifications 
            SET {', '.join(update_fields)}
            WHERE id = ?
            """
            
            params.append(notification_id)
            await self.db.execute_query(query, tuple(params), fetch=False)
            return True
            
        except Exception as e:
            logger.error(f"Error updating notification status: {str(e)}")
            return False

    async def get_user_notifications(
        self,
        user_id: str,
        status: Optional[NotificationStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Notification]:
        """Get notifications for user"""
        conditions = ["recipient_id = ?"]
        params = [user_id]
        
        if status:
            conditions.append("status = ?")
            params.append(status.value)
            
        query = f"""
        SELECT * 
        FROM notifications 
        WHERE {' AND '.join(conditions)}
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
        """
        
        params.extend([limit, offset])
        results = await self.db.execute_query(query, tuple(params))
        
        return [
            Notification(
                id=notif["id"],
                type=NotificationType(notif["type"]),
                priority=NotificationPriority(notif["priority"]),
                channels=[NotificationChannel(c) for c in notif["channels"].split(",")],
                recipient_id=notif["recipient_id"],
                title=notif["title"],
                content=notif["content"],
                data=eval(notif["data"]) if notif["data"] else {},
                status=NotificationStatus(notif["status"]),
                created_by=notif["created_by"],
                created_at=notif["created_at"],
                sent_at=notif["sent_at"],
                read_at=notif["read_at"],
                metadata=eval(notif["metadata"]) if notif["metadata"] else {}
            )
            for notif in results
        ]

    async def delete_notification(self, notification_id: str) -> bool:
        """Delete notification"""
        try:
            query = "DELETE FROM notifications WHERE id = ?"
            await self.db.execute_query(query, (notification_id,), fetch=False)
            return True
        except Exception as e:
            logger.error(f"Error deleting notification: {str(e)}")
            return False