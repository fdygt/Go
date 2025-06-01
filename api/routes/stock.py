from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime, UTC
import logging

from ..models.stock import (
    StockResponse,
    StockItem,
    StockAddRequest,
    StockReduceRequest,
    StockHistoryResponse,
    StockFilter
)
from ..service.stock_service import StockService
from ..dependencies import get_bot, get_current_user, verify_admin

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/", response_model=List[StockResponse])
async def get_all_stock(
    page: int = Query(1, gt=0),
    limit: int = Query(10, gt=0, le=100),
    filters: StockFilter = Depends(),
    bot=Depends(get_bot)
):
    """Get all stock items with pagination and filtering"""
    service = StockService(bot)
    return await service.get_all_stock(
        page=page,
        limit=limit,
        filters=filters
    )

@router.post("/add", response_model=StockResponse)
async def add_stock(
    request: StockAddRequest,
    bot=Depends(get_bot),
    current_user: str = Depends(get_current_user)
):
    """Add stock for products"""
    try:
        service = StockService(bot)
        return await service.add_stock(
            request,
            added_by=current_user,
            added_at=datetime.strptime("2025-05-28 15:18:11", "%Y-%m-%d %H:%M:%S")
        )
    except Exception as e:
        logger.error(f"""
        Add stock error:
        Data: {request.dict()}
        User: {current_user}
        Time: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')} UTC
        Error: {str(e)}
        """)
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/reduce", response_model=StockResponse)
async def reduce_stock(
    request: StockReduceRequest,
    bot=Depends(get_bot),
    current_user: str = Depends(get_current_user)
):
    """Reduce stock for products"""
    try:
        service = StockService(bot)
        return await service.reduce_stock(
            request,
            reduced_by=current_user,
            reduced_at=datetime.strptime("2025-05-28 15:18:11", "%Y-%m-%d %H:%M:%S")
        )
    except Exception as e:
        logger.error(f"""
        Reduce stock error:
        Data: {request.dict()}
        User: {current_user}
        Time: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')} UTC
        Error: {str(e)}
        """)
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{product_code}", response_model=StockResponse)
async def get_stock(product_code: str, bot=Depends(get_bot)):
    """Get stock details for a product"""
    service = StockService(bot)
    stock = await service.get_stock(product_code)
    if not stock:
        raise HTTPException(status_code=404, detail="Product not found")
    return stock

@router.get("/{product_code}/history", response_model=StockHistoryResponse)
async def get_stock_history(
    product_code: str,
    page: int = Query(1, gt=0),
    limit: int = Query(10, gt=0, le=100),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    bot=Depends(get_bot)
):
    """Get stock history for a product"""
    service = StockService(bot)
    return await service.get_stock_history(
        product_code,
        page=page,
        limit=limit,
        start_date=start_date,
        end_date=end_date
    )

@router.get("/{product_code}/movements", response_model=List[StockItem])
async def get_stock_movements(
    product_code: str,
    movement_type: Optional[str] = None,
    page: int = Query(1, gt=0),
    limit: int = Query(10, gt=0, le=100),
    bot=Depends(get_bot)
):
    """Get stock movements (in/out) for a product"""
    service = StockService(bot)
    return await service.get_stock_movements(
        product_code,
        movement_type=movement_type,
        page=page,
        limit=limit
    )

@router.post("/{product_code}/audit", dependencies=[Depends(verify_admin)])
async def audit_stock(
    product_code: str,
    actual_quantity: int,
    notes: Optional[str] = None,
    bot=Depends(get_bot),
    current_user: str = Depends(get_current_user)
):
    """Perform stock audit (admin only)"""
    try:
        service = StockService(bot)
        return await service.audit_stock(
            product_code,
            actual_quantity,
            audited_by=current_user,
            audited_at=datetime.strptime("2025-05-28 15:18:11", "%Y-%m-%d %H:%M:%S"),
            notes=notes
        )
    except Exception as e:
        logger.error(f"""
        Stock audit error:
        Product: {product_code}
        Quantity: {actual_quantity}
        User: {current_user}
        Time: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')} UTC
        Error: {str(e)}
        """)
        raise HTTPException(status_code=400, detail=str(e))