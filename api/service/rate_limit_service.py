from datetime import datetime, UTC
from typing import Dict, Optional, Tuple
import logging
from .database_service import DatabaseService

logger = logging.getLogger(__name__)

class RateLimitService:
    def __init__(self):
        self.db = DatabaseService()
        self.startup_time = datetime.now(UTC)
        logger.info(f"""
        RateLimitService initialized:
        Time: 2025-05-30 14:39:23
        User: fdygg
        """)
        
        # Default limits
        self.DEFAULT_RATE_LIMIT = {
            "requests": 100,  # requests
            "window": 60      # seconds
        }
        
        # Special limits for specific endpoints
        self.ENDPOINT_LIMITS = {
            "/api/auth/login": {
                "requests": 5,
                "window": 60
            },
            "/api/users": {
                "requests": 50,
                "window": 60
            }
        }
        
        # Role-based limits
        self.ROLE_LIMITS = {
            "admin": {
                "requests": 1000,
                "window": 60
            },
            "moderator": {
                "requests": 500,
                "window": 60
            },
            "discord_user": {
                "requests": 100,
                "window": 60
            },
            "web_user": {
                "requests": 200,
                "window": 60
            }
        }

    async def get_rate_limit(self, user_id: str, endpoint: str) -> Dict:
        """Get rate limit for user and endpoint"""
        # Get user role from auth service
        user_query = "SELECT role FROM users WHERE id = ?"
        user_result = await self.db.execute_query(user_query, (user_id,))
        user_role = user_result[0]["role"] if user_result else "web_user"
        
        # Get endpoint specific limit
        if endpoint in self.ENDPOINT_LIMITS:
            return self.ENDPOINT_LIMITS[endpoint]
            
        # Get role based limit
        if user_role in self.ROLE_LIMITS:
            return self.ROLE_LIMITS[user_role]
            
        # Return default limit
        return self.DEFAULT_RATE_LIMIT

    async def check_rate_limit(
        self,
        user_id: str,
        endpoint: str,
        ip_address: str
    ) -> Tuple[bool, Dict]:
        """Check if request is within rate limit"""
        try:
            # Get rate limit rules
            limit = await self.get_rate_limit(user_id, endpoint)
            window = limit["window"]
            max_requests = limit["requests"]
            
            # Calculate window start
            now = datetime.now(UTC)
            window_start = now.timestamp() - window
            
            # Count requests in window
            query = """
            SELECT COUNT(*) as request_count 
            FROM rate_limit_logs
            WHERE (user_id = ? OR ip_address = ?)
            AND endpoint = ?
            AND timestamp > ?
            """
            
            result = await self.db.execute_query(
                query,
                (user_id, ip_address, endpoint, window_start)
            )
            
            request_count = result[0]["request_count"]
            
            # Check if within limit
            remaining = max_requests - request_count
            reset_time = datetime.fromtimestamp(window_start + window, UTC)
            
            return remaining > 0, {
                "limit": max_requests,
                "remaining": remaining,
                "reset": reset_time.isoformat(),
                "window": window
            }
            
        except Exception as e:
            logger.error(f"Rate limit check error: {str(e)}")
            return True, self.DEFAULT_RATE_LIMIT

    async def log_request(
        self,
        user_id: str,
        endpoint: str,
        ip_address: str
    ) -> bool:
        """Log rate limited request"""
        try:
            query = """
            INSERT INTO rate_limit_logs (
                user_id, endpoint, ip_address, timestamp
            ) VALUES (?, ?, ?, ?)
            """
            
            await self.db.execute_query(
                query,
                (user_id, endpoint, ip_address, datetime.now(UTC).timestamp()),
                fetch=False
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Rate limit log error: {str(e)}")
            return False