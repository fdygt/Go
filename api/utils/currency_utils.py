from typing import Union, Tuple, Dict
from ..models.balance import CurrencyType
from datetime import datetime, UTC

class CurrencyUtils:
    @staticmethod
    def validate_currency_amount(amount: int, currency_type: CurrencyType) -> bool:
        """Validasi jumlah currency berdasarkan tipe"""
        min_amounts = {
            CurrencyType.WL: 1,
            CurrencyType.DL: 1,
            CurrencyType.BGL: 1,
            CurrencyType.RUPIAH: 1000  # Minimum 1000 Rupiah
        }
        return amount >= min_amounts.get(currency_type, 0)

    @staticmethod
    def format_game_currency(amount: int, currency_type: CurrencyType) -> str:
        """Format jumlah currency game (WL/DL/BGL)"""
        currency_names = {
            CurrencyType.WL: "World Lock",
            CurrencyType.DL: "Diamond Lock",
            CurrencyType.BGL: "Blue Gem Lock"
        }
        return f"{amount:,} {currency_names.get(currency_type, '')}"

    @staticmethod
    def format_rupiah(amount: int) -> str:
        """Format jumlah Rupiah"""
        return f"Rp {amount:,}"

    @staticmethod
    def convert_game_currency(amount: int, from_type: CurrencyType, to_type: CurrencyType) -> int:
        """Konversi antar currency game"""
        rates = {
            "WL_TO_DL": 100,
            "DL_TO_BGL": 100
        }
        # Implementasi konversi
        pass

    @staticmethod
    def validate_conversion_rules(user_type: str, from_currency: CurrencyType, to_currency: CurrencyType) -> bool:
        """Validasi aturan konversi berdasarkan tipe user"""
        if user_type != "discord":
            return False
        if from_currency == CurrencyType.RUPIAH:
            return False
        if to_currency != CurrencyType.RUPIAH:
            return False
        return True