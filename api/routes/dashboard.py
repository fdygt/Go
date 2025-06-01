from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime, UTC, timedelta
import logging
from pathlib import Path

from ..dependencies import get_bot, get_current_user
from ..models.dashboard import (
    DashboardStats,
    UserDashboard,
    SystemStatus,
    UserStats,
    StockAlert,
    DashboardSettings,
    UserActivity
)

router = APIRouter()
logger = logging.getLogger(__name__)

templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))

@router.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    current_user: str = Depends(get_current_user)
):
    """Render dashboard page"""
    try:
        bot = get_bot()
        uptime = datetime.now(UTC) - bot.startup_time
        
        # Get user data
        user_data = await bot.db.users.find_one({"username": "fdygg"})
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get user stats
        user_stats = UserStats(
            total_transactions=await bot.db.transactions.count_documents({"user_id": "fdygg"}),
            total_balance=await get_user_balance(bot, "fdygg"),
            stock_count=await bot.db.stocks.count_documents({"user_id": "fdygg"}),
            last_activity=await get_last_activity(bot, "fdygg")
        )
        
        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "title": "Dashboard - Bot Control Panel",
                "username": "fdygg",
                "current_time": "2025-05-28 15:35:49",
                "bot_uptime": str(uptime).split('.')[0],
                "version": "1.0.0",
                "user_data": user_data,
                "user_stats": user_stats.dict()
            }
        )
    except Exception as e:
        logger.error(f"""
        Dashboard error:
        User: fdygg
        Error: {str(e)}
        Time: 2025-05-28 15:35:49 UTC
        """)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats", response_model=DashboardStats)
async def get_stats(
    request: Request,
    current_user: str = Depends(get_current_user)
):
    """Get real-time dashboard stats"""
    try:
        bot = get_bot()
        
        # Get user's recent activity
        recent_activity = await bot.db.activity_log.find(
            {"user_id": "fdygg"}
        ).sort("timestamp", -1).limit(10).to_list(None)
        
        # Get system status
        system_status = await get_system_status(bot)
        
        return DashboardStats(
            timestamp=datetime.strptime("2025-05-28 15:35:49", "%Y-%m-%d %H:%M:%S"),
            user={
                "username": "fdygg",
                "last_activity": recent_activity
            },
            system=system_status,
            stats=await get_user_stats(bot, "fdygg")
        )
    except Exception as e:
        logger.error(f"""
        Stats error:
        User: fdygg
        Error: {str(e)}
        Time: 2025-05-28 15:35:49 UTC
        """)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/me", response_model=UserDashboard)
async def get_user_dashboard(
    current_user: str = Depends(get_current_user),
    bot=Depends(get_bot)
):
    """Get user's personalized dashboard"""
    try:
        return UserDashboard(
            username="fdygg",
            timestamp=datetime.strptime("2025-05-28 15:35:49", "%Y-%m-%d %H:%M:%S"),
            stats=await get_user_stats(bot, "fdygg"),
            recent_transactions=await get_user_transactions(bot, "fdygg"),
            stock_alerts=await get_user_stock_alerts(bot, "fdygg")
        )
    except Exception as e:
        logger.error(f"""
        User dashboard error:
        User: fdygg
        Error: {str(e)}
        Time: 2025-05-28 15:35:49 UTC
        """)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/settings", response_model=DashboardSettings)
async def get_dashboard_settings(
    current_user: str = Depends(get_current_user),
    bot=Depends(get_bot)
):
    """Get user's dashboard settings"""
    try:
        settings = await bot.db.dashboard_settings.find_one({"user_id": "fdygg"})
        return DashboardSettings(**(settings or {}))
    except Exception as e:
        logger.error(f"""
        Settings error:
        User: fdygg
        Error: {str(e)}
        Time: 2025-05-28 15:35:49 UTC
        """)
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/settings", response_model=DashboardSettings)
async def update_dashboard_settings(
    settings: DashboardSettings,
    current_user: str = Depends(get_current_user),
    bot=Depends(get_bot)
):
    """Update user's dashboard settings"""
    try:
        await bot.db.dashboard_settings.update_one(
            {"user_id": "fdygg"},
            {"$set": settings.dict()},
            upsert=True
        )
        return settings
    except Exception as e:
        logger.error(f"""
        Update settings error:
        User: fdygg
        Settings: {settings.dict()}
        Error: {str(e)}
        Time: 2025-05-28 15:35:49 UTC
        """)
        raise HTTPException(status_code=500, detail=str(e))

# Helper functions
async def get_system_status(bot) -> SystemStatus:
    """Get current system status"""
    return SystemStatus(
        name=bot.user.name,
        id=str(bot.user.id),
        uptime=str(datetime.now(UTC) - bot.startup_time).split('.')[0],
        guilds=len(bot.guilds),
        last_updated=datetime.strptime("2025-05-28 15:35:49", "%Y-%m-%d %H:%M:%S"),
        version="1.0.0"
    )

async def get_user_stats(bot, username: str) -> UserStats:
    """Get user statistics"""
    return UserStats(
        total_transactions=await bot.db.transactions.count_documents({"user_id": username}),
        total_balance=await get_user_balance(bot, username),
        stock_count=await bot.db.stocks.count_documents({"user_id": username}),
        last_activity=await get_last_activity(bot, username)
    )

async def get_user_balance(bot, username: str) -> float:
    """Get user's current balance"""
    balance = await bot.db.balances.find_one({"user_id": username})
    return balance.get("amount", 0.0) if balance else 0.0

async def get_last_activity(bot, username: str) -> Optional[UserActivity]:
    """Get user's last activity"""
    activity = await bot.db.activity_log.find_one(
        {"user_id": username},
        sort=[("timestamp", -1)]
    )
    return UserActivity(**activity) if activity else None

async def get_user_transactions(bot, username: str, limit: int = 5) -> List[Dict]:
    """Get user's recent transactions"""
    return await bot.db.transactions.find(
        {"user_id": username}
    ).sort("timestamp", -1).limit(limit).to_list(None)

async def get_user_stock_alerts(bot, username: str) -> List[StockAlert]:
    """Get stock alerts for user's products"""
    alerts = await bot.db.stocks.find(
        {
            "user_id": username,
            "current_stock": {"$lt": "$min_stock"}
        }
    ).to_list(None)
    
    return [StockAlert(**alert) for alert in alerts]