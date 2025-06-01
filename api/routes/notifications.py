from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime, UTC
import logging

from ..models.notifications import (
    Notification,
    NotificationType,
    NotificationPriority,
    NotificationChannel,
    NotificationStatus
)
from ..service.notification_service import NotificationService
from ..dependencies import get_bot, get_current_user, verify_admin

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/", response_model=List[Notification])
async def get_notifications(
    page: int = Query(1, gt=0),
    limit: int = Query(10, gt=0, le=100),
    type: Optional[NotificationType] = None,
    status: Optional[NotificationStatus] = None,
    priority: Optional[NotificationPriority] = None,
    bot=Depends(get_bot),
    current_user: str = Depends(get_current_user)
):
    """Get notifications with filtering and pagination"""
    try:
        service = NotificationService(bot)
        return await service.get_notifications(
            user_id=current_user,
            page=page,
            limit=limit,
            filters={
                "type": type,
                "status": status,
                "priority": priority
            }
        )
    except Exception as e:
        logger.error(f"""
        Get notifications error:
        User: {current_user}
        Filters: {{"type": {type}, "status": {status}, "priority": {priority}}}
        Time: {datetime.now(UTC)}
        Error: {str(e)}
        """)
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/read/{notification_id}")
async def mark_as_read(
    notification_id: str,
    bot=Depends(get_bot),
    current_user: str = Depends(get_current_user)
):
    """Mark notification as read"""
    try:
        service = NotificationService(bot)
        success = await service.mark_as_read(
            notification_id=notification_id,
            user_id=current_user
        )
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Notification not found"
            )
        return {"status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"""
        Mark notification read error:
        User: {current_user}
        Notification: {notification_id}
        Time: {datetime.now(UTC)}
        Error: {str(e)}
        """)
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/read/all")
async def mark_all_as_read(
    type: Optional[NotificationType] = None,
    bot=Depends(get_bot),
    current_user: str = Depends(get_current_user)
):
    """Mark all notifications as read"""
    try:
        service = NotificationService(bot)
        count = await service.mark_all_as_read(
            user_id=current_user,
            notification_type=type
        )
        return {
            "status": "success",
            "count": count
        }
    except Exception as e:
        logger.error(f"""
        Mark all notifications read error:
        User: {current_user}
        Type: {type}
        Time: {datetime.now(UTC)}
        Error: {str(e)}
        """)
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    bot=Depends(get_bot),
    current_user: str = Depends(get_current_user)
):
    """Delete a notification"""
    try:
        service = NotificationService(bot)
        success = await service.delete_notification(
            notification_id=notification_id,
            user_id=current_user
        )
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Notification not found"
            )
        return {"status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"""
        Delete notification error:
        User: {current_user}
        Notification: {notification_id}
        Time: {datetime.now(UTC)}
        Error: {str(e)}
        """)
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/settings", response_model=dict)
async def get_notification_settings(
    bot=Depends(get_bot),
    current_user: str = Depends(get_current_user)
):
    """Get user's notification settings"""
    try:
        service = NotificationService(bot)
        settings = await service.get_settings(current_user)
        return settings or {}
    except Exception as e:
        logger.error(f"""
        Get notification settings error:
        User: {current_user}
        Time: {datetime.now(UTC)}
        Error: {str(e)}
        """)
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/settings")
async def update_notification_settings(
    settings: dict,
    bot=Depends(get_bot),
    current_user: str = Depends(get_current_user)
):
    """Update user's notification settings"""
    try:
        service = NotificationService(bot)
        updated = await service.update_settings(
            user_id=current_user,
            settings=settings
        )
        return updated
    except Exception as e:
        logger.error(f"""
        Update notification settings error:
        User: {current_user}
        Settings: {settings}
        Time: {datetime.now(UTC)}
        Error: {str(e)}
        """)
        raise HTTPException(status_code=400, detail=str(e))