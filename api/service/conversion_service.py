from typing import Dict, List, Optional, Tuple
from datetime import datetime, UTC
import logging
from uuid import uuid4
from .database_service import DatabaseService
from .balance_service import BalanceService
from ..models.conversion import (
    ConversionRate, ConversionRequest, ConversionResponse
)
from ..models.balance import CurrencyType

logger = logging.getLogger(__name__)

class ConversionService:
    def __init__(self):
        self.db = DatabaseService()
        self.balance_service = BalanceService()
        self.startup_time = datetime.now(UTC)
        logger.info(f"""
        ConversionService initialized:
        Time: 2025-05-29 17:13:27
        User: fdygg
        """)

    async def get_conversion_rate(
        self,
        currency: CurrencyType
    ) -> Optional[ConversionRate]:
        """Get current conversion rate for currency"""
        if currency == CurrencyType.RUPIAH:
            raise ValueError("Cannot get conversion rate for Rupiah")
            
        query = """
        SELECT * FROM conversion_rates 
        WHERE currency = ? AND is_active = 1
        ORDER BY updated_at DESC 
        LIMIT 1
        """
        
        result = await self.db.execute_query(query, (currency.value,))
        if not result:
            return None
            
        rate = result[0]
        return ConversionRate(
            currency=CurrencyType(rate["currency"]),
            rate_rupiah=rate["rate_rupiah"],
            min_amount=rate["min_amount"],
            max_amount=rate["max_amount"],
            is_active=rate["is_active"],
            updated_at=rate["updated_at"],
            updated_by=rate["updated_by"]
        )

    async def update_conversion_rate(
        self,
        currency: CurrencyType,
        rate_rupiah: int,
        min_amount: int = 1,
        max_amount: int = 999999,
        updated_by: str = "fdygg"
    ) -> Optional[ConversionRate]:
        """Update conversion rate for currency"""
        try:
            if currency == CurrencyType.RUPIAH:
                raise ValueError("Cannot set conversion rate for Rupiah")

            # Validate rates
            if rate_rupiah <= 0:
                raise ValueError("Rate must be greater than 0")
            if min_amount < 1:
                raise ValueError("Minimum amount must be at least 1")
            if max_amount <= min_amount:
                raise ValueError("Maximum amount must be greater than minimum amount")

            # Insert new rate
            query = """
            INSERT INTO conversion_rates (
                currency, rate_rupiah, min_amount,
                max_amount, is_active, updated_at, updated_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            
            await self.db.execute_query(
                query,
                (
                    currency.value,
                    rate_rupiah,
                    min_amount,
                    max_amount,
                    True,
                    datetime.now(UTC),
                    updated_by
                ),
                fetch=False
            )
            
            return await self.get_conversion_rate(currency)
            
        except Exception as e:
            logger.error(f"Error updating conversion rate: {str(e)}")
            return None

    async def get_all_rates(
        self,
        include_inactive: bool = False
    ) -> Dict[CurrencyType, ConversionRate]:
        """Get all current conversion rates"""
        conditions = ["1=1"]
        params = []
        
        if not include_inactive:
            conditions.append("is_active = 1")
            
        query = f"""
        SELECT DISTINCT currency, 
            FIRST_VALUE(rate_rupiah) OVER (
                PARTITION BY currency 
                ORDER BY updated_at DESC
            ) as rate_rupiah,
            FIRST_VALUE(min_amount) OVER (
                PARTITION BY currency 
                ORDER BY updated_at DESC
            ) as min_amount,
            FIRST_VALUE(max_amount) OVER (
                PARTITION BY currency 
                ORDER BY updated_at DESC
            ) as max_amount,
            FIRST_VALUE(is_active) OVER (
                PARTITION BY currency 
                ORDER BY updated_at DESC
            ) as is_active,
            FIRST_VALUE(updated_at) OVER (
                PARTITION BY currency 
                ORDER BY updated_at DESC
            ) as updated_at,
            FIRST_VALUE(updated_by) OVER (
                PARTITION BY currency 
                ORDER BY updated_at DESC
            ) as updated_by
        FROM conversion_rates
        WHERE {' AND '.join(conditions)}
        """
        
        results = await self.db.execute_query(query, tuple(params))
        
        return {
            CurrencyType(rate["currency"]): ConversionRate(
                currency=CurrencyType(rate["currency"]),
                rate_rupiah=rate["rate_rupiah"],
                min_amount=rate["min_amount"],
                max_amount=rate["max_amount"],
                is_active=rate["is_active"],
                updated_at=rate["updated_at"],
                updated_by=rate["updated_by"]
            )
            for rate in results
        }

    async def convert_currency(
        self,
        request: ConversionRequest
    ) -> Tuple[bool, str, Optional[ConversionResponse]]:
        """Convert currency based on current rates"""
        try:
            # Validate conversion direction
            if request.from_currency == CurrencyType.RUPIAH:
                return False, "Cannot convert from Rupiah", None
                
            if request.to_currency != CurrencyType.RUPIAH:
                return False, "Can only convert to Rupiah", None

            # Get current rate
            rate = await self.get_conversion_rate(request.from_currency)
            if not rate:
                return False, f"No conversion rate found for {request.from_currency.value}", None
                
            if not rate.is_active:
                return False, f"Conversion for {request.from_currency.value} is currently inactive", None

            # Validate amount
            if request.amount < rate.min_amount:
                return False, f"Amount below minimum ({rate.min_amount})", None
                
            if request.amount > rate.max_amount:
                return False, f"Amount above maximum ({rate.max_amount})", None

            # Check user balance
            balance = await self.balance_service.get_balance(
                request.user_id,
                request.user_type
            )
            if not balance:
                return False, "User balance not found", None

            currency_balance = getattr(balance, f"{request.from_currency.value}_balance")
            if currency_balance < request.amount:
                return False, f"Insufficient {request.from_currency.value} balance", None

            # Calculate conversion
            converted_amount = request.amount * rate.rate_rupiah

            # Generate conversion ID
            conversion_id = f"conv_{uuid4().hex[:8]}"

            # Create conversion record
            query = """
            INSERT INTO conversions (
                id, user_id, from_currency,
                to_currency, amount, converted_amount,
                rate_used, timestamp, status, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            await self.db.execute_query(
                query,
                (
                    conversion_id,
                    request.user_id,
                    request.from_currency.value,
                    request.to_currency.value,
                    request.amount,
                    converted_amount,
                    rate.rate_rupiah,
                    datetime.now(UTC),
                    "success",
                    "{}"
                ),
                fetch=False
            )

            # Update balances
            success = await self.balance_service.update_balance(
                user_id=request.user_id,
                user_type=request.user_type,
                updates={
                    request.from_currency: -request.amount,
                    request.to_currency: converted_amount
                }
            )
            
            if not success:
                return False, "Failed to update balances", None

            return True, "Conversion successful", ConversionResponse(
                conversion_id=conversion_id,
                user_id=request.user_id,
                from_currency=request.from_currency,
                to_currency=request.to_currency,
                amount=request.amount,
                converted_amount=converted_amount,
                rate_used=rate.rate_rupiah,
                timestamp=datetime.now(UTC),
                status="success"
            )

        except Exception as e:
            logger.error(f"Error converting currency: {str(e)}")
            return False, "Conversion failed", None

    async def get_conversion_history(
        self,
        user_id: Optional[str] = None,
        from_currency: Optional[CurrencyType] = None,
        to_currency: Optional[CurrencyType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[ConversionResponse]:
        """Get conversion history with filters"""
        conditions = ["1=1"]
        params = []
        
        if user_id:
            conditions.append("user_id = ?")
            params.append(user_id)
            
        if from_currency:
            conditions.append("from_currency = ?")
            params.append(from_currency.value)
            
        if to_currency:
            conditions.append("to_currency = ?")
            params.append(to_currency.value)
            
        if start_date:
            conditions.append("timestamp >= ?")
            params.append(start_date)
            
        if end_date:
            conditions.append("timestamp <= ?")
            params.append(end_date)
            
        query = f"""
        SELECT * 
        FROM conversions 
        WHERE {' AND '.join(conditions)}
        ORDER BY timestamp DESC
        LIMIT ? OFFSET ?
        """
        
        params.extend([limit, offset])
        results = await self.db.execute_query(query, tuple(params))
        
        return [
            ConversionResponse(
                conversion_id=conv["id"],
                user_id=conv["user_id"],
                from_currency=CurrencyType(conv["from_currency"]),
                to_currency=CurrencyType(conv["to_currency"]),
                amount=conv["amount"],
                converted_amount=conv["converted_amount"],
                rate_used=conv["rate_used"],
                timestamp=conv["timestamp"],
                status=conv["status"],
                metadata=eval(conv["metadata"]) if conv["metadata"] else {}
            )
            for conv in results
        ]

    async def get_conversion_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict:
        """Get conversion statistics"""
        try:
            conditions = ["1=1"]
            params = []
            
            if start_date:
                conditions.append("timestamp >= ?")
                params.append(start_date)
                
            if end_date:
                conditions.append("timestamp <= ?")
                params.append(end_date)
                
            query = f"""
            SELECT 
                from_currency,
                COUNT(*) as total_conversions,
                SUM(amount) as total_amount,
                SUM(converted_amount) as total_converted,
                AVG(rate_used) as avg_rate
            FROM conversions
            WHERE {' AND '.join(conditions)}
            GROUP BY from_currency
            """
            
            results = await self.db.execute_query(query, tuple(params))
            
            return {
                CurrencyType(stat["from_currency"]): {
                    "total_conversions": stat["total_conversions"],
                    "total_amount": stat["total_amount"],
                    "total_converted": stat["total_converted"],
                    "avg_rate": stat["avg_rate"]
                }
                for stat in results
            }
            
        except Exception as e:
            logger.error(f"Error getting conversion stats: {str(e)}")
            return {}