from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime, UTC
import logging

from ..models.audit import (
    AuditLog,
    AuditCategory,
    AuditLevel
)
from ..service.audit_service import AuditService
from ..dependencies import get_bot, verify_admin

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/logs", response_model=List[AuditLog])
async def get_audit_logs(
    page: int = Query(1, gt=0),
    limit: int = Query(10, gt=0, le=100),
    category: Optional[AuditCategory] = None,
    level: Optional[AuditLevel] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    user_id: Optional[str] = None,
    bot=Depends(get_bot),
    current_user: str = Depends(verify_admin)
):
    """Get audit logs with filtering and pagination (admin only)"""
    try:
        service = AuditService(bot)
        return await service.get_logs(
            page=page,
            limit=limit,
            filters={
                "category": category,
                "level": level,
                "start_date": start_date,
                "end_date": end_date,
                "user_id": user_id
            }
        )
    except Exception as e:
        logger.error(f"""
        Get audit logs error:
        Admin: {current_user}
        Filters: {{
            "category": {category},
            "level": {level},
            "start_date": {start_date},
            "end_date": {end_date},
            "user_id": {user_id}
        }}
        Time: {datetime.now(UTC)}
        Error: {str(e)}
        """)
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/metrics", response_model=dict)
async def get_audit_metrics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    bot=Depends(get_bot),
    current_user: str = Depends(verify_admin)
):
    """Get audit metrics (admin only)"""
    try:
        service = AuditService(bot)
        return await service.get_metrics(
            start_date=start_date,
            end_date=end_date
        )
    except Exception as e:
        logger.error(f"""
        Get audit metrics error:
        Admin: {current_user}
        Period: {start_date} - {end_date}
        Time: {datetime.now(UTC)}
        Error: {str(e)}
        """)
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/alerts", response_model=List[dict])
async def get_audit_alerts(
    bot=Depends(get_bot),
    current_user: str = Depends(verify_admin)
):
    """Get active audit alerts (admin only)"""
    try:
        service = AuditService(bot)
        return await service.get_alerts()
    except Exception as e:
        logger.error(f"""
        Get audit alerts error:
        Admin: {current_user}
        Time: {datetime.now(UTC)}
        Error: {str(e)}
        """)
        raise HTTPException(status_code=400, detail=str(e))