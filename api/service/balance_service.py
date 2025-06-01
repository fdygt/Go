from typing import Dict, Optional, List
from datetime import datetime, UTC
import logging
from uuid import uuid4
from .database_service import DatabaseService
from ..models.balance import (
    Balance, BalanceResponse, BalanceUpdateRequest,
    Transaction, TransactionStatus, CurrencyType,
    TransactionType, BalanceHistoryResponse
)

logger = logging.getLogger(__name__)

class BalanceService:
    def __init__(self):
        self.db = DatabaseService()
        self.startup_time = datetime.now(UTC)
        logger.info(f"""
        BalanceService initialized:
        Time: 2025-05-29 16:27:04
        User: fdygg
        """)

    async def get_balance(
        self,
        user_id: str,
        user_type: str = "discord"
    ) -> Optional[BalanceResponse]:
        """Get user balance"""
        query = """
        SELECT 
            id,
            user_type,
            growid,
            balance_wl,
            balance_dl,
            balance_bgl,
            balance_idr as balance_rupiah,
            updated_at,
            updated_by
        FROM users 
        WHERE id = ? AND user_type = ?
        """
        
        result = await self.db.execute_query(query, (user_id, user_type))
        if not result:
            return None
            
        user = result[0]
        return BalanceResponse(
            user_id=user['id'],
            user_type=user['user_type'],
            growid=user['growid'],
            balance=Balance(
                wl_balance=user['balance_wl'],
                dl_balance=user['balance_dl'],
                bgl_balance=user['balance_bgl'],
                rupiah_balance=user['balance_rupiah']
            ),
            last_updated=user['updated_at'],
            updated_by=user['updated_by']
        )

    async def update_balance(
        self,
        user_id: str,
        user_type: str,
        update_request: BalanceUpdateRequest
    ) -> Optional[BalanceResponse]:
        """Update user balance with transaction tracking"""
        async with self.db.transaction():
            # Create transaction record
            transaction_id = f"txn_{uuid4().hex[:8]}"
            txn_query = """
            INSERT INTO balance_transactions (
                id, user_id, user_type, currency_type,
                transaction_type, amount, created_by,
                description, status, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            # Update balance based on transaction type
            multiplier = 1 if update_request.transaction_type in [
                TransactionType.ADD,
                TransactionType.DONATION
            ] else -1
            
            balance_query = f"""
            UPDATE users 
            SET 
                balance_{update_request.currency_type.value} = 
                    balance_{update_request.currency_type.value} + ?,
                updated_at = ?,
                updated_by = ?
            WHERE id = ? AND user_type = ?
            """
            
            try:
                # Create transaction record
                await self.db.execute_query(
                    txn_query,
                    (
                        transaction_id,
                        user_id,
                        user_type,
                        update_request.currency_type.value,
                        update_request.transaction_type.value,
                        update_request.amount,
                        "fdygg",
                        update_request.reason,
                        TransactionStatus.PENDING.value,
                        datetime.now(UTC)
                    ),
                    fetch=False
                )
                
                # Update balance
                await self.db.execute_query(
                    balance_query,
                    (
                        multiplier * update_request.amount,
                        datetime.now(UTC),
                        "fdygg",
                        user_id,
                        user_type
                    ),
                    fetch=False
                )
                
                # Update transaction status
                await self.db.execute_query(
                    "UPDATE balance_transactions SET status = ? WHERE id = ?",
                    (TransactionStatus.SUCCESS.value, transaction_id),
                    fetch=False
                )
                
                # Return updated balance
                return await self.get_balance(user_id, user_type)
                
            except Exception as e:
                logger.error(f"Error updating balance: {str(e)}")
                # Update transaction status to failed
                await self.db.execute_query(
                    "UPDATE balance_transactions SET status = ? WHERE id = ?",
                    (TransactionStatus.FAILED.value, transaction_id),
                    fetch=False
                )
                return None

    async def get_balance_history(
        self,
        user_id: str,
        user_type: str,
        page: int = 1,
        page_size: int = 10
    ) -> BalanceHistoryResponse:
        """Get user's balance transaction history"""
        offset = (page - 1) * page_size
        
        # Get total count
        count_query = """
        SELECT COUNT(*) as total
        FROM balance_transactions
        WHERE user_id = ? AND user_type = ?
        """
        
        # Get transactions
        txn_query = """
        SELECT *
        FROM balance_transactions
        WHERE user_id = ? AND user_type = ?
        ORDER BY timestamp DESC
        LIMIT ? OFFSET ?
        """
        
        count_result = await self.db.execute_query(count_query, (user_id, user_type))
        total_records = count_result[0]['total'] if count_result else 0
        
        transactions_result = await self.db.execute_query(
            txn_query,
            (user_id, user_type, page_size, offset)
        )
        
        # Get user info for growid
        user_query = "SELECT growid FROM users WHERE id = ? AND user_type = ?"
        user_result = await self.db.execute_query(user_query, (user_id, user_type))
        growid = user_result[0]['growid'] if user_result else None
        
        transactions = [
            Transaction(
                id=txn['id'],
                user_id=txn['user_id'],
                user_type=txn['user_type'],
                currency_type=CurrencyType(txn['currency_type']),
                transaction_type=TransactionType(txn['transaction_type']),
                amount=txn['amount'],
                timestamp=txn['timestamp'],
                created_by=txn['created_by'],
                description=txn['description'],
                status=TransactionStatus(txn['status']),
                metadata=eval(txn['metadata']) if txn.get('metadata') else {}
            )
            for txn in transactions_result
        ]
        
        return BalanceHistoryResponse(
            user_id=user_id,
            user_type=user_type,
            growid=growid,
            transactions=transactions,
            total_records=total_records,
            page=page,
            page_size=page_size
        )

    async def get_conversion_rates(self) -> Dict[str, float]:
        """Get current conversion rates"""
        query = """
        SELECT from_currency, to_currency, rate 
        FROM conversion_rates 
        WHERE is_active = 1
        """
        result = await self.db.execute_query(query)
        
        rates = {}
        for row in result:
            key = f"{row['from_currency']}_{row['to_currency']}"
            rates[key] = row['rate']
        return rates