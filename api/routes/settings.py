from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
import logging

from ..models.settings import AppSettings
from ..service.settings_service import SettingsService
from ..dependencies import get_bot, verify_admin

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/", response_model=AppSettings)
async def get_settings(
    bot=Depends(get_bot),
    current_user: str = Depends(verify_admin)
):
    """Get application settings (admin only)"""
    try:
        service = SettingsService(bot)
        return await service.get_settings()
    except Exception as e:
        logger.error(f"""
        Get settings error:
        Admin: {current_user}
        Error: {str(e)}
        """)
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/")
async def update_settings(
    settings: AppSettings,
    bot=Depends(get_bot),
    current_user: str = Depends(verify_admin)
):
    """Update application settings (admin only)"""
    try:
        service = SettingsService(bot)
        updated = await service.update_settings(settings.dict())
        return updated
    except Exception as e:
        logger.error(f"""
        Update settings error:
        Admin: {current_user}
        Settings: {settings.dict()}
        Error: {str(e)}
        """)
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/reset")
async def reset_settings(
    bot=Depends(get_bot),
    current_user: str = Depends(verify_admin)
):
    """Reset settings to defaults (admin only)"""
    try:
        service = SettingsService(bot)
        await service.reset_settings()
        return {"status": "success"}
    except Exception as e:
        logger.error(f"""
        Reset settings error:
        Admin: {current_user}
        Error: {str(e)}
        """)
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/cache/clear")
async def clear_cache(
    key_pattern: Optional[str] = None,
    bot=Depends(get_bot),
    current_user: str = Depends(verify_admin)
):
    """Clear application cache (admin only)"""
    try:
        service = SettingsService(bot)
        count = await service.clear_cache(key_pattern)
        return {
            "status": "success",
            "cleared_keys": count
        }
    except Exception as e:
        logger.error(f"""
        Clear cache error:
        Admin: {current_user}
        Pattern: {key_pattern}
        Error: {str(e)}
        """)
        raise HTTPException(status_code=400, detail=str(e))