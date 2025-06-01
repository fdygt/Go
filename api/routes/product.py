from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime, UTC
import logging

from ..models.product import (
    ProductCreate,
    ProductUpdate, 
    ProductResponse,
    ProductFilter
)
from ..service.product_service import ProductService
from ..dependencies import get_bot, get_current_user, verify_admin

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/", response_model=ProductResponse)
async def create_product(
    product: ProductCreate,
    bot=Depends(get_bot),
    current_user: str = Depends(get_current_user)
):
    """Create a new product"""
    try:
        service = ProductService(bot)
        product_dict = product.dict()
        product_dict["created_at"] = datetime.strptime("2025-05-28 15:18:11", "%Y-%m-%d %H:%M:%S")
        product_dict["created_by"] = current_user
        return await service.create_product(product_dict)
    except Exception as e:
        logger.error(f"""
        Create product error:
        Data: {product.dict()}
        User: {current_user}
        Time: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')} UTC
        Error: {str(e)}
        """)
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[ProductResponse])
async def get_products(
    page: int = Query(1, gt=0),
    limit: int = Query(10, gt=0, le=100),
    filters: ProductFilter = Depends(),
    bot=Depends(get_bot)
):
    """Get all products with pagination and filtering"""
    service = ProductService(bot)
    return await service.get_products(
        page=page,
        limit=limit,
        filters=filters
    )

@router.get("/{code}", response_model=ProductResponse)
async def get_product(code: str, bot=Depends(get_bot)):
    """Get a product by its code"""
    service = ProductService(bot)
    product = await service.get_product(code)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.put("/{code}", response_model=ProductResponse)
async def update_product(
    code: str,
    product: ProductUpdate,
    bot=Depends(get_bot),
    current_user: str = Depends(get_current_user)
):
    """Update a product"""
    try:
        service = ProductService(bot)
        product_dict = product.dict(exclude_unset=True)
        product_dict["updated_at"] = datetime.strptime("2025-05-28 15:18:11", "%Y-%m-%d %H:%M:%S")
        product_dict["updated_by"] = current_user
        updated = await service.update_product(code, product_dict)
        if not updated:
            raise HTTPException(status_code=404, detail="Product not found")
        return updated
    except Exception as e:
        logger.error(f"""
        Update product error:
        Code: {code}
        Data: {product.dict()}
        User: {current_user}
        Time: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')} UTC
        Error: {str(e)}
        """)
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{code}")
async def delete_product(
    code: str,
    bot=Depends(get_bot),
    current_user: str = Depends(verify_admin)
):
    """Delete a product (admin only)"""
    try:
        service = ProductService(bot)
        deleted = await service.delete_product(code, current_user)
        if not deleted:
            raise HTTPException(status_code=404, detail="Product not found")
        return {"message": "Product deleted successfully"}
    except Exception as e:
        logger.error(f"""
        Delete product error:
        Code: {code}
        User: {current_user}
        Time: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')} UTC
        Error: {str(e)}
        """)
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{code}/stock", response_model=int)
async def get_product_stock(code: str, bot=Depends(get_bot)):
    """Get current stock level for a product"""
    service = ProductService(bot)
    stock = await service.get_stock_level(code)
    if stock is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return stock