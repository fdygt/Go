from typing import Dict, Optional
from datetime import datetime, UTC

class PlatformUtils:
    @staticmethod
    def validate_platform_access(platform: str, feature: str) -> bool:
        """Validasi akses fitur berdasarkan platform"""
        platform_features = {
            "discord": ["convert_currency", "game_currency", "rupiah"],
            "web": ["rupiah"]
        }
        return feature in platform_features.get(platform, [])

    @staticmethod
    def get_platform_limits(platform: str) -> Dict[str, int]:
        """Dapatkan batasan platform"""
        limits = {
            "discord": {
                "max_daily_conversions": 10,
                "max_transaction_amount": 1000000000
            },
            "web": {
                "max_daily_transactions": 20,
                "max_transaction_amount": 10000000
            }
        }
        return limits.get(platform, {})

    @staticmethod
    def validate_growtopia_id(growtopia_id: str) -> bool:
        """Validasi format Growtopia ID"""
        if not growtopia_id:
            return False
        # Implementasi validasi
        pass