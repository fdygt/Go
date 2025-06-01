import re
import jwt
from typing import Optional
from datetime import datetime

from ..config import config

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_password(password: str) -> tuple[bool, str]:
    """
    Validate password strength
    Returns: (is_valid, message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain lowercase letter"
    if not re.search(r'[0-9]', password):
        return False, "Password must contain number"
    if not re.search(r'[!@#$%^&*]', password):
        return False, "Password must contain special character"
    return True, "Password is valid"

def validate_username(username: str) -> bool:
    """Validate username format"""
    pattern = r'^[a-zA-Z0-9_]{3,20}$'
    return bool(re.match(pattern, username))

def validate_api_key(api_key: str) -> bool:
    """Validate API key format"""
    pattern = r'^[A-Za-z0-9-_]{32,64}$'
    return bool(re.match(pattern, api_key))

def validate_jwt_token(token: str) -> Optional[dict]:
    """Validate JWT token"""
    try:
        payload = jwt.decode(
            token,
            config.JWT_SECRET_KEY,
            algorithms=[config.JWT_ALGORITHM]
        )
        
        # Check expiration
        exp = datetime.fromtimestamp(payload["exp"])
        if exp < datetime.strptime("2025-05-28 15:50:29", "%Y-%m-%d %H:%M:%S"):
            return None
            
        return payload
    except:
        return None