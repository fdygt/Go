from typing import Dict, List, Optional, Tuple
from datetime import datetime, UTC
import logging
from .database_service import DatabaseService
from ..models.stock import StockItem, StockStatus, StockAddRequest, PriceInfo

logger = logging.getLogger(__name__)

class StockService:
    def __init__(self):
        self.db = DatabaseService()
        self.startup_time = datetime.now(UTC)
        logger.info(f"""
        StockService initialized:
        Time: 2025-05-29 16:27:04
        User: fdygg
        """)

    async def add_stock(
        self,
        stock_request: StockAddRequest
    ) -> Tuple[bool, List[StockItem]]:
        """Add new stock items"""
        added_items = []
        now = datetime.now(UTC)
        
        query = """
        INSERT INTO stock (
            product_code, content, status,
            wl_price, dl_price, bgl_price, rupiah_price,
            available_for, added_by, added_at,
            metadata
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        try:
            for content in stock_request.items:
                await self.db.execute_query(
                    query,
                    (
                        stock_request.product_code,
                        content,
                        StockStatus.AVAILABLE.value,
                        stock_request.prices.wl_price,
                        stock_request.prices.dl_price,
                        stock_request.prices.bgl_price,
                        stock_request.prices.rupiah_price,
                        ','.join(stock_request.available_for),
                        "fdygg",
                        now,
                        str(stock_request.metadata)
                    ),
                    fetch=False
                )
                
                # Get the added item
                added_item = await self.get_stock_by_content(
                    stock_request.product_code,
                    content
                )
                if added_item:
                    added_items.append(added_item)
                    
            return True, added_items
        except Exception as e:
            logger.error(f"Error adding stock: {str(e)}")
            return False, []

    async def get_available_stock(
        self,
        product_code: str,
        user_type: str = "discord",
        limit: int = 10
    ) -> List[StockItem]:
        """Get available stock for a product"""
        query = """
        SELECT s.*, p.name as product_name
        FROM stock s
        JOIN products p ON s.product_code = p.code
        WHERE s.product_code = ? 
        AND s.status = ?
        AND ? = ANY(string_to_array(s.available_for, ','))
        ORDER BY s.added_at
        LIMIT ?
        """
        
        results = await self.db.execute_query(
            query,
            (product_code, StockStatus.AVAILABLE.value, user_type, limit)
        )
        
        return [
            StockItem(
                id=item['id'],
                product_code=item['product_code'],
                content=item['content'],
                prices=PriceInfo(
                    wl_price=item['wl_price'],
                    dl_price=item['dl_price'],
                    bgl_price=item['bgl_price'],
                    rupiah_price=item['rupiah_price']
                ),
                status=StockStatus(item['status']),
                available_for=item['available_for'].split(','),
                added_by=item['added_by'],
                added_at=item['added_at'],
                buyer_id=item['buyer_id'],
                seller_id=item['seller_id'],
                metadata=eval(item['metadata']) if item['metadata'] else {}
            )
            for item in results
        ]

    async def update_stock_status(
        self,
        stock_id: int,
        status: StockStatus,
        buyer_id: Optional[str] = None,
        seller_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> bool:
        """Update stock status"""
        query = """
        UPDATE stock 
        SET 
            status = ?,
            buyer_id = ?,
            seller_id = ?,
            updated_at = ?,
            metadata = CASE 
                WHEN ? IS NOT NULL THEN ?
                ELSE metadata 
            END
        WHERE id = ?
        """
        
        try:
            await self.db.execute_query(
                query,
                (
                    status.value,
                    buyer_id,
                    seller_id,
                    datetime.now(UTC),
                    metadata,
                    str(metadata) if metadata else None,
                    stock_id
                ),
                fetch=False
            )
            return True
        except Exception as e:
            logger.error(f"Error updating stock status: {str(e)}")
            return False

    async def get_stock_by_id(self, stock_id: int) -> Optional[StockItem]:
        """Get stock item by ID"""
        query = """
        SELECT s.*, p.name as product_name
        FROM stock s
        JOIN products p ON s.product_code = p.code
        WHERE s.id = ?
        """
        
        result = await self.db.execute_query(query, (stock_id,))
        if not result:
            return None
            
        item = result[0]
        return StockItem(
            id=item['id'],
            product_code=item['product_code'],
            content=item['content'],
            prices=PriceInfo(
                wl_price=item['wl_price'],
                dl_price=item['dl_price'],
                bgl_price=item['bgl_price'],
                rupiah_price=item['rupiah_price']
            ),
            status=StockStatus(item['status']),
            available_for=item['available_for'].split(','),
            added_by=item['added_by'],
            added_at=item['added_at'],
            buyer_id=item['buyer_id'],
            seller_id=item['seller_id'],
            metadata=eval(item['metadata']) if item['metadata'] else {}
        )

    async def get_stock_by_content(
        self,
        product_code: str,
        content: str
    ) -> Optional[StockItem]:
        """Get stock item by content"""
        query = """
        SELECT s.*, p.name as product_name
        FROM stock s
        JOIN products p ON s.product_code = p.code
        WHERE s.product_code = ? AND s.content = ?
        """
        
        result = await self.db.execute_query(query, (product_code, content))
        if not result:
            return None
            
        item = result[0]
        return StockItem(
            id=item['id'],
            product_code=item['product_code'],
            content=item['content'],
            prices=PriceInfo(
                wl_price=item['wl_price'],
                dl_price=item['dl_price'],
                bgl_price=item['bgl_price'],
                rupiah_price=item['rupiah_price']
            ),
            status=StockStatus(item['status']),
            available_for=item['available_for'].split(','),
            added_by=item['added_by'],
            added_at=item['added_at'],
            buyer_id=item['buyer_id'],
            seller_id=item['seller_id'],
            metadata=eval(item['metadata']) if item['metadata'] else {}
        )