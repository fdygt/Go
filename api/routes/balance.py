from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from typing import Optional, List
from datetime import datetime, UTC, timedelta
import logging

from ..models.balance import (
    BalanceResponse,
    BalanceUpdateRequest,
    BalanceHistoryResponse,
    BalanceFilter,
    BalanceType
)
from ..service.balance_service import BalanceService
from ..dependencies import get_bot, get_current_user, verify_admin

logger = logging.getLogger(__name__)
router = APIRouter()

def create_cached_response(data: dict, cache_time: int = 60):
    """Create response with cache headers"""
    headers = {
        "Cache-Control": f"public, max-age={cache_time}",
        "Expires": (datetime.strptime("2025-05-28 15:29:08", "%Y-%m-%d %H:%M:%S") + 
                   timedelta(seconds=cache_time)).strftime("%a, %d %b %Y %H:%M:%S GMT"),
    }
    return JSONResponse(content=data, headers=headers)

@router.get("/me", response_model=BalanceResponse)
async def get_my_balance(
    bot=Depends(get_bot),
    current_user: str = Depends(get_current_user)
):
    """Get current user's balance"""
    try:
        service = BalanceService(bot)
        balance = await service.get_balance("fdygg")
        if not balance:
            balance = {
                "user_id": "fdygg",
                "balance": 0,
                "last_updated": datetime.strptime("2025-05-28 15:29:08", "%Y-%m-%d %H:%M:%S")
            }
        return create_cached_response(balance, cache_time=30)
    except Exception as e:
        logger.error(f"""
        Get balance error:
        User: fdygg
        Time: 2025-05-28 15:29:08 UTC
        Error: {str(e)}
        """)
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/update", response_model=BalanceResponse)
async def update_balance(
    request: BalanceUpdateRequest,
    bot=Depends(get_bot),
    current_user: str = Depends(verify_admin)
):
    """Update user balance (admin only)"""
    try:
        service = BalanceService(bot)
        update_dict = request.dict()
        update_dict["updated_at"] = datetime.strptime("2025-05-28 15:29:08", "%Y-%m-%d %H:%M:%S")
        update_dict["updated_by"] = "fdygg"
        
        return await service.update_balance(update_dict)
    except Exception as e:
        logger.error(f"""
        Update balance error:
        Data: {request.dict()}
        Admin: fdygg
        Time: 2025-05-28 15:29:08 UTC
        Error: {str(e)}
        """)
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/history", response_model=List[BalanceHistoryResponse])
async def get_balance_history(
    page: int = Query(1, gt=0),
    limit: int = Query(10, gt=0, le=100),
    balance_type: Optional[BalanceType] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    bot=Depends(get_bot),
    current_user: str = Depends(get_current_user)
):
    """Get balance history"""
    try:
        service = BalanceService(bot)
        filters = BalanceFilter(
            user_id="fdygg",
            balance_type=balance_type,
            start_date=start_date,
            end_date=end_date or datetime.strptime("2025-05-28 15:29:08", "%Y-%m-%d %H:%M:%S")
        )
        return await service.get_balance_history(
            page=page,
            limit=limit,
            filters=filters
        )
    except Exception as e:
        logger.error(f"""
        Balance history error:
        User: fdygg
        Time: 2025-05-28 15:29:08 UTC
        Error: {str(e)}
        """)
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/summary", dependencies=[Depends(verify_admin)])
async def get_balance_summary(
    date: Optional[datetime] = None,
    bot=Depends(get_bot)
):
    """Get balance summary for all users (admin only)"""
    try:
        service = BalanceService(bot)
        summary_date = date or datetime.strptime("2025-05-28 15:29:08", "%Y-%m-%d %H:%M:%S")
        return await service.get_balance_summary(summary_date)
    except Exception as e:
        logger.error(f"""
        Balance summary error:
        Date: {date}
        Time: 2025-05-28 15:29:08 UTC
        Error: {str(e)}
        """)
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/transfer", response_model=BalanceResponse)
async def transfer_balance(
    to_user: str,
    amount: float,
    notes: Optional[str] = None,
    bot=Depends(get_bot),
    current_user: str = Depends(get_current_user)
):
    """Transfer balance to another user"""
    try:
        service = BalanceService(bot)
        transfer_data = {
            "from_user": "fdygg",
            "to_user": to_user,
            "amount": amount,
            "notes": notes,
            "transferred_at": datetime.strptime("2025-05-28 15:29:08", "%Y-%m-%d %H:%M:%S")
        }
        return await service.transfer_balance(transfer_data)
    except Exception as e:
        logger.error(f"""
        Balance transfer error:
        From: fdygg
        To: {to_user}
        Amount: {amount}
        Time: 2025-05-28 15:29:08 UTC
        Error: {str(e)}
        """)
        raise HTTPException(status_code=400, detail=str(e))