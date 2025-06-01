import re
import string
import random
from typing import Optional
import phonenumbers

def format_currency(amount: float, currency: str = "USD") -> str:
    """Format amount as currency"""
    return f"{currency} {amount:,.2f}"

def sanitize_string(text: str) -> str:
    """Remove special characters and sanitize string"""
    return re.sub(r'[^a-zA-Z0-9\s]', '', text)

def generate_random_string(length: int = 16) -> str:
    """Generate random string for various purposes"""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def mask_sensitive_data(data: str, mask_char: str = "*") -> str:
    """Mask sensitive data like email or phone"""
    if not data:
        return ""
    return mask_char * (len(data) - 4) + data[-4:]

def validate_phone_number(phone: str, region: str = "US") -> Optional[str]:
    """Validate and format phone number"""
    try:
        number = phonenumbers.parse(phone, region)
        if phonenumbers.is_valid_number(number):
            return phonenumbers.format_number(
                number,
                phonenumbers.PhoneNumberFormat.E164
            )
        return None
    except:
        return None