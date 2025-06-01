from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer
from datetime import datetime, UTC
import jwt
import logging
import traceback
from ..dependencies import get_bot, verify_admin, get_current_user
from ..models.admin import (
    AdminStats,
    AdminDashboard,
    SystemInfo,
    UserActivity
)
from database import get_connection

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()

@router.get("/stats", response_model=AdminStats)
async def get_admin_stats(
    current_user: str = Depends(verify_admin),
    bot=Depends(get_bot)
):
    """Get admin statistics"""
    try:
        logger.info(f"""
        Admin stats request:
        Admin: {current_user}
        Time: 2025-05-28 15:24:29 UTC
        """)
        
        stats = await get_system_stats(bot)
        return stats
    except Exception as e:
        logger.error(f"""
        Admin stats error:
        Admin: {current_user}
        Error: {str(e)}
        Time: 2025-05-28 15:24:29 UTC
        Stack Trace:
        {traceback.format_exc()}
        """)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboard", response_model=AdminDashboard)
async def get_admin_dashboard(
    current_user: str = Depends(verify_admin),
    bot=Depends(get_bot)
):
    """Get admin dashboard data"""
    try:
        logger.info(f"""
        Admin dashboard request:
        Admin: {current_user}
        Time: 2025-05-28 15:24:29 UTC
        """)
        
        system_info = await get_system_info(bot)
        user_activity = await get_user_activity()
        stock_alerts = await get_stock_alerts(bot)
        recent_transactions = await get_recent_transactions(bot)
        
        return {
            "system_info": system_info,
            "user_activity": user_activity,
            "stock_alerts": stock_alerts,
            "recent_transactions": recent_transactions,
            "timestamp": datetime.strptime("2025-05-28 15:24:29", "%Y-%m-%d %H:%M:%S"),
            "admin": current_user
        }
    except Exception as e:
        logger.error(f"""
        Admin dashboard error:
        Admin: {current_user}
        Error: {str(e)}
        Time: 2025-05-28 15:24:29 UTC
        Stack Trace:
        {traceback.format_exc()}
        """)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/activity", response_model=UserActivity)
async def get_activity_log(
    start_date: datetime = None,
    end_date: datetime = None,
    current_user: str = Depends(verify_admin)
):
    """Get user activity logs"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT al.timestamp, al.user_id, al.action, al.details
            FROM activity_log al
            WHERE al.timestamp BETWEEN ? AND ?
            ORDER BY al.timestamp DESC
        """
        
        start = start_date or datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        end = end_date or datetime.strptime("2025-05-28 15:24:29", "%Y-%m-%d %H:%M:%S")
        
        cursor.execute(query, (start, end))
        activities = cursor.fetchall()
        
        return {
            "activities": [
                {
                    "timestamp": activity[0],
                    "user_id": activity[1],
                    "action": activity[2],
                    "details": activity[3]
                }
                for activity in activities
            ],
            "start_date": start,
            "end_date": end,
            "total": len(activities)
        }
    except Exception as e:
        logger.error(f"""
        Activity log error:
        Admin: {current_user}
        Error: {str(e)}
        Time: 2025-05-28 15:24:29 UTC
        Stack Trace:
        {traceback.format_exc()}
        """)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()

async def get_system_stats(bot) -> AdminStats:
    """Get system statistics"""
    return {
        "total_users": await bot.db.users.count_documents({}),
        "active_users": await bot.db.users.count_documents({"status": "active"}),
        "total_products": await bot.db.products.count_documents({}),
        "low_stock_alerts": await bot.db.products.count_documents({"stock": {"$lt": 10}}),
        "transactions_today": await bot.db.transactions.count_documents({
            "created_at": {
                "$gte": datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
            }
        }),
        "total_balance": await bot.db.balances.aggregate([
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]).next(),
        "timestamp": datetime.strptime("2025-05-28 15:24:29", "%Y-%m-%d %H:%M:%S"),
        "updated_by": "fdygg"
    }