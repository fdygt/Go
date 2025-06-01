from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime, UTC
import logging

from ..models.reports import (
    Report,
    ReportType,
    ReportFormat,
    ReportStatus
)
from ..service.report_service import ReportService
from ..dependencies import get_bot, verify_admin

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/generate", response_model=dict)
async def generate_report(
    report_type: ReportType,
    format: ReportFormat = ReportFormat.PDF,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    filters: Optional[dict] = None,
    bot=Depends(get_bot),
    current_user: str = Depends(verify_admin)
):
    """Generate a new report (admin only)"""
    try:
        service = ReportService(bot)
        report = await service.generate_report(
            report_type=report_type,
            format=format,
            start_date=start_date,
            end_date=end_date,
            filters=filters,
            requested_by=current_user
        )
        return report
    except Exception as e:
        logger.error(f"""
        Generate report error:
        Admin: {current_user}
        Type: {report_type}
        Format: {format}
        Period: {start_date} - {end_date}
        Filters: {filters}
        Error: {str(e)}
        """)
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[Report])
async def get_reports(
    page: int = Query(1, gt=0),
    limit: int = Query(10, gt=0, le=100),
    report_type: Optional[ReportType] = None,
    status: Optional[ReportStatus] = None,
    bot=Depends(get_bot),
    current_user: str = Depends(verify_admin)
):
    """Get list of reports (admin only)"""
    try:
        service = ReportService(bot)
        return await service.get_reports(
            page=page,
            limit=limit,
            filters={
                "type": report_type,
                "status": status
            }
        )
    except Exception as e:
        logger.error(f"""
        Get reports error:
        Admin: {current_user}
        Type: {report_type}
        Status: {status}
        Error: {str(e)}
        """)
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{report_id}", response_model=Report)
async def get_report(
    report_id: str,
    bot=Depends(get_bot),
    current_user: str = Depends(verify_admin)
):
    """Get report details (admin only)"""
    try:
        service = ReportService(bot)
        report = await service.get_report(report_id)
        if not report:
            raise HTTPException(
                status_code=404,
                detail="Report not found"
            )
        return report
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"""
        Get report error:
        Admin: {current_user}
        Report ID: {report_id}
        Error: {str(e)}
        """)
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{report_id}")
async def delete_report(
    report_id: str,
    bot=Depends(get_bot),
    current_user: str = Depends(verify_admin)
):
    """Delete a report (admin only)"""
    try:
        service = ReportService(bot)
        success = await service.delete_report(report_id)
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Report not found"
            )
        return {"status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"""
        Delete report error:
        Admin: {current_user}
        Report ID: {report_id}
        Error: {str(e)}
        """)
        raise HTTPException(status_code=400, detail=str(e))