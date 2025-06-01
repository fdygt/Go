from typing import Dict, Optional
import logging
from datetime import datetime, UTC
from .database_service import DatabaseService

logger = logging.getLogger(__name__)

class SettingsService:
    def __init__(self):
        self.db = DatabaseService()
        self.startup_time = datetime.now(UTC)
        logger.info(f"""
        SettingsService initialized:
        Time: 2025-05-30 14:53:16
        User: fdygg
        """)

    async def get_compression_settings(self) -> Dict:
        """Get compression settings from database"""
        try:
            query = "SELECT * FROM compression_settings WHERE is_active = 1"
            results = await self.db.execute_query(query)
            
            if not results:
                return {}
                
            settings = results[0]
            return {
                "gzip": {
                    "enabled": settings["gzip_enabled"],
                    "level": settings["gzip_level"],
                    "min_size": settings["min_size"],
                    "types": settings["content_types"].split(",")
                },
                "brotli": {
                    "enabled": settings["brotli_enabled"],
                    "quality": settings["brotli_quality"],
                    "min_size": settings["min_size"],
                    "types": settings["content_types"].split(",")
                },
                "deflate": {
                    "enabled": settings["deflate_enabled"],
                    "level": settings["deflate_level"],
                    "min_size": settings["min_size"],
                    "types": settings["content_types"].split(",")
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting compression settings: {str(e)}")
            return {}

    async def update_compression_settings(
        self,
        settings: Dict,
        user_id: str
    ) -> bool:
        """Update compression settings"""
        try:
            # Validate settings
            if not self._validate_compression_settings(settings):
                return False
                
            # Deactivate current settings
            await self.db.execute_query(
                "UPDATE compression_settings SET is_active = 0",
                fetch=False
            )
            
            # Insert new settings
            query = """
            INSERT INTO compression_settings (
                gzip_enabled, gzip_level,
                brotli_enabled, brotli_quality,
                deflate_enabled, deflate_level,
                min_size, content_types,
                is_active, created_by,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
            """
            
            values = (
                settings["gzip"]["enabled"],
                settings["gzip"]["level"],
                settings["brotli"]["enabled"],
                settings["brotli"]["quality"],
                settings["deflate"]["enabled"],
                settings["deflate"]["level"],
                settings["gzip"]["min_size"],  # Use same min_size for all
                ",".join(settings["gzip"]["types"]),  # Use same types for all
                user_id,
                datetime.now(UTC)
            )
            
            await self.db.execute_query(query, values, fetch=False)
            return True
            
        except Exception as e:
            logger.error(f"Error updating compression settings: {str(e)}")
            return False

    def _validate_compression_settings(self, settings: Dict) -> bool:
        """Validate compression settings"""
        try:
            # Check required algorithms
            for algo in ["gzip", "brotli", "deflate"]:
                if algo not in settings:
                    return False
                    
                # Check required fields
                if algo in ["gzip", "deflate"]:
                    if not 1 <= settings[algo]["level"] <= 9:
                        return False
                elif algo == "brotli":
                    if not 0 <= settings[algo]["quality"] <= 11:
                        return False
                        
                # Check other fields
                if "enabled" not in settings[algo] or \
                   "min_size" not in settings[algo] or \
                   "types" not in settings[algo]:
                    return False
                    
                # Validate min_size
                if settings[algo]["min_size"] < 0:
                    return False
                    
                # Validate content types
                if not isinstance(settings[algo]["types"], list):
                    return False
                    
            return True
            
        except Exception as e:
            logger.error(f"Settings validation error: {str(e)}")
            return False