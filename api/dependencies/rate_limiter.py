from fastapi import HTTPException
from datetime import datetime, timedelta
from typing import Optional, Tuple
from .redis import redis_client
from .logger import logger
from api.Config.rate_limit import RATE_LIMIT, RATE_LIMIT_STRATEGY

class RateLimiter:
    def __init__(self):
        self.redis = redis_client
        self.limit = int(RATE_LIMIT.split('/')[0])
        self.window = 60  # 1 minute default
        
    async def check_rate_limit(
        self,
        user_id: str,
        endpoint: str
    ) -> Tuple[bool, Optional[int]]:
        """
        Check if request is within rate limit
        Returns: (is_allowed, retry_after)
        """
        try:
            key = f"rate_limit:{user_id}:{endpoint}"
            current = datetime.utcnow()
            
            # Get current window data
            window_data = self.redis.get(key)
            if window_data:
                count, window_start = map(int, window_data.split(':'))
                window_start = datetime.fromtimestamp(window_start)
                
                # Check if window expired
                if current - window_start > timedelta(seconds=self.window):
                    # Start new window
                    self.redis.set(key, f"1:{int(current.timestamp())}", ex=self.window)
                    return True, None
                    
                # Check if limit exceeded
                if count >= self.limit:
                    retry_after = self.window - (current - window_start).seconds
                    return False, retry_after
                    
                # Increment counter
                self.redis.set(key, f"{count+1}:{int(window_start.timestamp())}", ex=self.window)
                return True, None
            else:
                # First request in window
                self.redis.set(key, f"1:{int(current.timestamp())}", ex=self.window)
                return True, None
                
        except Exception as e:
            logger.error(f"Rate limit error: {str(e)}")
            return True, None  # Allow request on error
            
    async def reset_limit(self, user_id: str, endpoint: str) -> bool:
        """Reset rate limit for user and endpoint"""
        try:
            key = f"rate_limit:{user_id}:{endpoint}"
            return bool(self.redis.delete(key))
        except Exception as e:
            logger.error(f"Reset rate limit error: {str(e)}")
            return False

rate_limiter = RateLimiter()

# Rate limit decorator
def rate_limit():
    async def dependency(user_id: str = None):
        if not user_id:
            return
            
        is_allowed, retry_after = await rate_limiter.check_rate_limit(
            user_id=user_id,
            endpoint="global"  # Use specific endpoint for more granular control
        )
        
        if not is_allowed:
            raise HTTPException(
                status_code=429,
                detail={
                    "message": "Too many requests",
                    "retry_after": retry_after
                }
            )
        
    return dependency