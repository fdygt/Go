from typing import Dict, List, Optional, Tuple
from datetime import datetime, UTC
import logging
from .database_service import DatabaseService
from ..models.product import (
    ProductCreate, ProductUpdate, ProductResponse,
    ProductType, ProductStatus
)

logger = logging.getLogger(__name__)

class ProductService:
    def __init__(self):
        self.db = DatabaseService()
        self.startup_time = datetime.now(UTC)
        logger.info(f"""
        ProductService initialized:
        Time: 2025-05-29 16:38:49
        User: fdygg
        """)

    async def create_product(
        self,
        product: ProductCreate,
        created_by: str = "fdygg"
    ) -> Optional[ProductResponse]:
        """Create new product"""
        try:
            # Check if product code exists
            existing = await self.db.execute_query(
                "SELECT 1 FROM products WHERE code = ?",
                (product.code,)
            )
            if existing:
                raise ValueError("Product code already exists")

            query = """
            INSERT INTO products (
                code, name, price, type,
                description, status, created_at,
                created_by, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            await self.db.execute_query(
                query,
                (
                    product.code,
                    product.name,
                    product.price,
                    product.type.value,
                    product.description,
                    ProductStatus.ACTIVE.value,
                    datetime.now(UTC),
                    created_by,
                    str(product.metadata)
                ),
                fetch=False
            )
            
            return await self.get_product_by_code(product.code)

        except Exception as e:
            logger.error(f"Error creating product: {str(e)}")
            return None

    async def get_product_by_code(self, code: str) -> Optional[ProductResponse]:
        """Get product by code"""
        query = """
        SELECT p.*, 
            COUNT(CASE WHEN s.status = 'available' THEN 1 END) as stock_count,
            COUNT(s.id) as total_stock
        FROM products p
        LEFT JOIN stock s ON p.code = s.product_code
        WHERE p.code = ?
        GROUP BY p.id
        """
        
        result = await self.db.execute_query(query, (code,))
        if not result:
            return None
            
        product = result[0]
        return ProductResponse(
            id=product["id"],
            code=product["code"],
            name=product["name"],
            price=product["price"],
            type=ProductType(product["type"]),
            description=product["description"],
            status=ProductStatus(product["status"]),
            stock_count=product["stock_count"] or 0,
            total_stock=product["total_stock"] or 0,
            created_at=product["created_at"],
            metadata=eval(product["metadata"]) if product["metadata"] else {}
        )

    async def update_product(
        self,
        code: str,
        update_data: ProductUpdate,
        updated_by: str
    ) -> Optional[ProductResponse]:
        """Update product data"""
        try:
            # Check if product exists
            current_product = await self.get_product_by_code(code)
            if not current_product:
                return None

            # Build update query
            update_fields = []
            params = []
            
            if update_data.name is not None:
                update_fields.append("name = ?")
                params.append(update_data.name)
                
            if update_data.price is not None:
                update_fields.append("price = ?")
                params.append(update_data.price)
                
            if update_data.description is not None:
                update_fields.append("description = ?")
                params.append(update_data.description)
                
            if update_data.type is not None:
                update_fields.append("type = ?")
                params.append(update_data.type.value)
                
            if update_data.status is not None:
                update_fields.append("status = ?")
                params.append(update_data.status.value)
                
            if update_data.metadata is not None:
                update_fields.append("metadata = ?")
                params.append(str(update_data.metadata))

            if not update_fields:
                return current_product

            # Add updated_at and code
            update_fields.extend(["updated_at = ?", "updated_by = ?"])
            params.extend([datetime.now(UTC), updated_by, code])

            query = f"""
            UPDATE products 
            SET {', '.join(update_fields)}
            WHERE code = ?
            """
            
            await self.db.execute_query(query, tuple(params), fetch=False)
            return await self.get_product_by_code(code)

        except Exception as e:
            logger.error(f"Error updating product: {str(e)}")
            return None

    async def get_products(
        self,
        product_type: Optional[ProductType] = None,
        status: Optional[ProductStatus] = None,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        has_stock: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[ProductResponse]:
        """Get products with filters"""
        conditions = ["1=1"]
        params = []
        
        if product_type:
            conditions.append("p.type = ?")
            params.append(product_type.value)
            
        if status:
            conditions.append("p.status = ?")
            params.append(status.value)
            
        if min_price is not None:
            conditions.append("p.price >= ?")
            params.append(min_price)
            
        if max_price is not None:
            conditions.append("p.price <= ?")
            params.append(max_price)
            
        if has_stock is not None:
            if has_stock:
                conditions.append("(SELECT COUNT(*) FROM stock s WHERE s.product_code = p.code AND s.status = 'available') > 0")
            else:
                conditions.append("(SELECT COUNT(*) FROM stock s WHERE s.product_code = p.code AND s.status = 'available') = 0")
            
        query = f"""
        SELECT p.*, 
            COUNT(CASE WHEN s.status = 'available' THEN 1 END) as stock_count,
            COUNT(s.id) as total_stock
        FROM products p
        LEFT JOIN stock s ON p.code = s.product_code
        WHERE {' AND '.join(conditions)}
        GROUP BY p.id
        ORDER BY p.created_at DESC
        LIMIT ? OFFSET ?
        """
        
        params.extend([limit, offset])
        results = await self.db.execute_query(query, tuple(params))
        
        return [
            ProductResponse(
                id=product["id"],
                code=product["code"],
                name=product["name"],
                price=product["price"],
                type=ProductType(product["type"]),
                description=product["description"],
                status=ProductStatus(product["status"]),
                stock_count=product["stock_count"] or 0,
                total_stock=product["total_stock"] or 0,
                created_at=product["created_at"],
                metadata=eval(product["metadata"]) if product["metadata"] else {}
            )
            for product in results
        ]

    async def delete_product(self, code: str) -> bool:
        """Soft delete product by setting status to INACTIVE"""
        try:
            query = """
            UPDATE products 
            SET 
                status = ?,
                updated_at = ?
            WHERE code = ?
            """
            
            await self.db.execute_query(
                query,
                (ProductStatus.INACTIVE.value, datetime.now(UTC), code),
                fetch=False
            )
            return True
        except Exception as e:
            logger.error(f"Error deleting product: {str(e)}")
            return False