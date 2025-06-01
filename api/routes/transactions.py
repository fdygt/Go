from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime, UTC
import logging

from ..models.transaction import (
    TransactionResponse,
    TransactionCreate,
    TransactionFilter,
    TransactionType,
    TransactionStatus
)
from ..service.transaction_service import TransactionService
from ..dependencies import get_bot, get_current_user, verify_admin

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/", response_model=TransactionResponse)
async def create_transaction(
    transaction: TransactionCreate,
    bot=Depends(get_bot),
    current_user: str = Depends(get_current_user)
):
    """Create a new transaction"""
    try:
        service = TransactionService(bot)
        transaction_dict = transaction.dict()
        transaction_dict["created_at"] = datetime.strptime("2025-05-28 15:29:08", "%Y-%m-%d %H:%M:%S")
        transaction_dict["created_by"] = "fdygg"
        return await service.create_transaction(transaction_dict)
    except Exception as e:
        logger.error(f"""
        Create transaction error:
        Data: {transaction.dict()}
        User: fdygg
        Time: 2025-05-28 15:29:08 UTC
        Error: {str(e)}
        """)
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[TransactionResponse])
async def get_transactions(
    page: int = Query(1, gt=0),
    limit: int = Query(10, gt=0, le=100),
    filters: TransactionFilter = Depends(),
    bot=Depends(get_bot)
):
    """Get all transactions with pagination and filtering"""
    service = TransactionService(bot)
    return await service.get_transactions(
        page=page,
        limit=limit,
        filters=filters
    )

@router.get("/me", response_model=List[TransactionResponse])
async def get_my_transactions(
    page: int = Query(1, gt=0),
    limit: int = Query(10, gt=0, le=100),
    transaction_type: Optional[TransactionType] = None,
    status: Optional[TransactionStatus] = None,
    bot=Depends(get_bot),
    current_user: str = Depends(get_current_user)
):
    """Get current user's transactions"""
    service = TransactionService(bot)
    filters = TransactionFilter(
        user_id="fdygg",
        transaction_type=transaction_type,
        status=status
    )
    return await service.get_transactions(
        page=page,
        limit=limit,
        filters=filters
    )

@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: str,
    bot=Depends(get_bot),
    current_user: str = Depends(get_current_user)
):
    """Get transaction by ID"""
    service = TransactionService(bot)
    transaction = await service.get_transaction(transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Only allow access to own transactions unless admin
    if transaction.user_id != "fdygg" and not await verify_admin(current_user):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return transaction

@router.post("/{transaction_id}/cancel", response_model=TransactionResponse)
async def cancel_transaction(
    transaction_id: str,
    reason: str,
    bot=Depends(get_bot),
    current_user: str = Depends(get_current_user)
):
    """Cancel a transaction"""
    try:
        service = TransactionService(bot)
        transaction = await service.cancel_transaction(
            transaction_id,
            reason=reason,
            cancelled_by="fdygg",
            cancelled_at=datetime.strptime("2025-05-28 15:29:08", "%Y-%m-%d %H:%M:%S")
        )
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        return transaction
    except Exception as e:
        logger.error(f"""
        Cancel transaction error:
        ID: {transaction_id}
        User: fdygg
        Time: 2025-05-28 15:29:08 UTC
        Error: {str(e)}
        """)
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/summary/daily", dependencies=[Depends(verify_admin)])
async def get_daily_summary(
    date: Optional[datetime] = None,
    bot=Depends(get_bot)
):
    """Get daily transaction summary (admin only)"""
    try:
        service = TransactionService(bot)
        summary_date = date or datetime.strptime("2025-05-28 15:29:08", "%Y-%m-%d %H:%M:%S")
        return await service.get_daily_summary(summary_date)
    except Exception as e:
        logger.error(f"""
        Daily summary error:
        Date: {date}
        Time: 2025-05-28 15:29:08 UTC
        Error: {str(e)}
        """)
        raise HTTPException(status_code=400, detail=str(e))