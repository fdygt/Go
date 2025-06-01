from typing import Any, Optional
from functools import wraps
from api.Config.cache import CACHE_CONFIG, CACHE_TTL, CACHE_KEY_PATTERNS
from .redis import redis_client
from .logger import logger
import json
import time

class CacheManager:
    def __init__(self):
        self.client = redis_client
        self.config = CACHE_CONFIG
        self.ttl = CACHE_TTL
        self.key_patterns = CACHE_KEY_PATTERNS
        
    async def get(self, key: str) -> Optional[Any]:
        try:
            data = self.client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Cache get error: {str(e)}")
            return None
            
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        try:
            data = json.dumps(value)
            return self.client.set(key, data, ex=ttl)
        except Exception as e:
            logger.error(f"Cache set error: {str(e)}")
            return False
            
    async def delete(self, key: str) -> bool:
        try:
            return bool(self.client.delete(key))
        except Exception as e:
            logger.error(f"Cache delete error: {str(e)}")
            return False
            
    async def clear_pattern(self, pattern: str) -> bool:
        try:
            keys = self.client.keys(pattern)
            if keys:
                return bool(self.client.delete(*keys))
            return True
        except Exception as e:
            logger.error(f"Cache clear pattern error: {str(e)}")
            return False

# Cache decorator
def cached(key_pattern: str, ttl: Optional[int] = None):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_manager = CacheManager()
            
            # Generate cache key
            try:
                cache_key = key_pattern.format(**kwargs)
            except KeyError:
                return await func(*args, **kwargs)
                
            # Try to get from cache
            cached_data = await cache_manager.get(cache_key)
            if cached_data is not None:
                return cached_data
                
            # If not in cache, execute function
            result = await func(*args, **kwargs)
            
            # Store in cache
            if result is not None:
                await cache_manager.set(
                    cache_key,
                    result,
                    ttl=ttl
                )
                
            return result
        return wrapper
    return decorator

cache_manager = CacheManager()