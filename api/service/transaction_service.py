from typing import Dict, List, Optional
from datetime import datetime, UTC
import logging
from .database_service import DatabaseService
from uuid import uuid4
from ..models.transaction import TransactionCreate, TransactionResponse, TransactionType, TransactionStatus, CurrencyType

logger = logging.getLogger(__name__)

class TransactionService:
    def __init__(self):
        self.db = DatabaseService()
        self.startup_time = datetime.now(UTC)
        logger.info(f"""
        TransactionService initialized:
        Time: 2025-05-29 16:27:04
        User: fdygg
        """)

    async def create_transaction(
        self,
        transaction: TransactionCreate
    ) -> Optional[TransactionResponse]:
        """Create new transaction"""
        transaction_id = f"txn_{uuid4().hex[:8]}"
        query = """
        INSERT INTO transactions (
            id, user_id, user_type, growid, type, 
            currency, amount, details, status, items,
            created_at, created_by, metadata
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        try:
            items_json = None
            if transaction.items:
                items_json = str(transaction.items)  # Convert to string for storage
                
            await self.db.execute_query(
                query,
                (
                    transaction_id,
                    transaction.user_id,
                    transaction.user_type,
                    transaction.growid,
                    transaction.type.value,
                    transaction.currency.value,
                    transaction.amount,
                    transaction.details,
                    TransactionStatus.PENDING.value,
                    items_json,
                    datetime.now(UTC),
                    "fdygg",
                    str(transaction.metadata)
                ),
                fetch=False
            )
            
            # Get the created transaction
            return await self.get_transaction_by_id(transaction_id)
        except Exception as e:
            logger.error(f"Error creating transaction: {str(e)}")
            return None

    async def get_transaction_by_id(self, transaction_id: str) -> Optional[TransactionResponse]:
        """Get transaction by ID"""
        query = """
        SELECT * FROM transactions WHERE id = ?
        """
        result = await self.db.execute_query(query, (transaction_id,))
        if not result:
            return None
            
        transaction = result[0]
        
        # Get updated balances
        balances = await self._get_user_balances(transaction['user_id'])
        
        return TransactionResponse(
            id=transaction['id'],
            user_id=transaction['user_id'],
            user_type=transaction['user_type'],
            growid=transaction['growid'],
            type=TransactionType(transaction['type']),
            currency=CurrencyType(transaction['currency']),
            amount=transaction['amount'],
            details=transaction['details'],
            balances=balances,
            status=TransactionStatus(transaction['status']),
            items=eval(transaction['items']) if transaction['items'] else None,
            created_at=transaction['created_at'],
            created_by=transaction['created_by'],
            metadata=eval(transaction['metadata']) if transaction['metadata'] else {}
        )

    async def get_user_transactions(
        self,
        user_id: str,
        user_type: str = "discord",
        limit: int = 10,
        offset: int = 0
    ) -> List[TransactionResponse]:
        """Get user transaction history"""
        query = """
        SELECT *
        FROM transactions
        WHERE user_id = ? AND user_type = ?
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
        """
        
        transactions = await self.db.execute_query(
            query, 
            (user_id, user_type, limit, offset)
        )
        
        # Get current balances
        balances = await self._get_user_balances(user_id)
        
        return [
            TransactionResponse(
                id=txn['id'],
                user_id=txn['user_id'],
                user_type=txn['user_type'],
                growid=txn['growid'],
                type=TransactionType(txn['type']),
                currency=CurrencyType(txn['currency']),
                amount=txn['amount'],
                details=txn['details'],
                balances=balances,
                status=TransactionStatus(txn['status']),
                items=eval(txn['items']) if txn['items'] else None,
                created_at=txn['created_at'],
                created_by=txn['created_by'],
                metadata=eval(txn['metadata']) if txn['metadata'] else {}
            )
            for txn in transactions
        ]

    async def update_transaction_status(
        self,
        transaction_id: str,
        status: TransactionStatus,
        metadata: Optional[Dict] = None
    ) -> bool:
        """Update transaction status"""
        query = """
        UPDATE transactions 
        SET status = ?, 
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
                    datetime.now(UTC),
                    metadata,
                    str(metadata) if metadata else None,
                    transaction_id
                ),
                fetch=False
            )
            return True
        except Exception as e:
            logger.error(f"Error updating transaction status: {str(e)}")
            return False

    async def _get_user_balances(self, user_id: str) -> Dict[str, int]:
        """Helper method to get user's current balances"""
        query = """
        SELECT 
            balance_wl as wl,
            balance_dl as dl,
            balance_bgl as bgl,
            balance_idr as idr
        FROM users 
        WHERE id = ?
        """
        result = await self.db.execute_query(query, (user_id,))
        if not result:
            return {"wl": 0, "dl": 0, "bgl": 0, "idr": 0}
        return result[0]