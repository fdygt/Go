from typing import Dict, Union, Optional

Example conversion rates (can be dynamically fetched from database in a real scenario)

DEFAULT_CONVERSION_RATES = { "WL": 1000,  # Example: 1 WL = 1000 Rupiah "DL": 10000,  # Example: 1 DL = 10,000 Rupiah "BGL": 100000,  # Example: 1 BGL = 100,000 Rupiah }

def get_conversion_rate(currency: str, rates: Optional[Dict[str, int]] = None) -> int: """ Retrieve the conversion rate for a given currency. :param currency: The currency type (e.g., WL, DL, BGL). :param rates: Optional dictionary of rates; defaults to DEFAULT_CONVERSION_RATES. :return: Conversion rate for the currency. """ rates = rates or DEFAULT_CONVERSION_RATES return rates.get(currency.upper(), 0)

def convert_to_rupiah(amount: Union[int, float], currency: str, rates: Optional[Dict[str, int]] = None) -> int: """ Convert a given amount of currency to Rupiah. :param amount: The amount to be converted. :param currency: The currency type (e.g., WL, DL, BGL). :param rates: Optional dictionary of rates; defaults to DEFAULT_CONVERSION_RATES. :return: The equivalent amount in Rupiah. """ rate = get_conversion_rate(currency, rates) return int(amount * rate)

def validate_currency(currency: str, rates: Optional[Dict[str, int]] = None) -> bool: """ Validate if the given currency is supported. :param currency: The currency type to validate. :param rates: Optional dictionary of rates; defaults to DEFAULT_CONVERSION_RATES. :return: True if the currency is supported; False otherwise. """ rates = rates or DEFAULT_CONVERSION_RATES return currency.upper() in rates

Example usage

if name == "main": print("Conversion rates:", DEFAULT_CONVERSION_RATES) print("10 WL to Rupiah:", convert_to_rupiah(10, "WL")) print("5 DL to Rupiah:", convert_to_rupiah(5, "DL")) print("Is 'WL' a valid currency?", validate_currency("WL")) print("Is 'XYZ' a valid currency?", validate_currency("XYZ"))

