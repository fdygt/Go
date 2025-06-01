from fastapi import Request, Response
from fastapi.responses import JSONResponse, StreamingResponse
import logging
from typing import Optional, Dict, List, Any, Set
from datetime import datetime, UTC, timedelta
import json
import hashlib
from urllib.parse import urlparse, parse_qs

from ..service.database_service import DatabaseService

logger = logging.getLogger(__name__)

class CacheMiddleware:
    def __init__(self):
        self.db = DatabaseService()
        self.startup_time = datetime.now(UTC)
        
        # Cache settings
        self.DEFAULT_TTL = 3600  # 1 hour
        self.MAX_TTL = 86400  # 24 hours
        self.MIN_TTL = 60  # 1 minute
        self.CACHE_SIZE_LIMIT = 1024 * 1024 * 100  # 100MB
        
        # Cache control
        self.NO_CACHE_PATHS = {
            r"^/auth/",
            r"^/admin/",
            r"^/user/profile"
        }
        self.CACHE_METHODS = {"GET", "HEAD"}
        self.CACHEABLE_STATUS = {200, 301, 302, 304}
        
        # Custom cache rules
        self.cache_rules = [
            {
                "path": r"^/products",
                "ttl": 1800,  # 30 minutes
                "vary": ["Authorization"]
            },
            {
                "path": r"^/categories",
                "ttl": 3600,  # 1 hour
                "vary": []
            }
        ]
        
        logger.info(f"""
        CacheMiddleware initialized:
        Time: 2025-05-30 15:09:00
        User: fdygg
        """)

    def _should_cache_response(
        self,
        request: Request,
        response: Response
    ) -> bool:
        """Check if response should be cached"""
        # Check request method
        if request.method not in self.CACHE_METHODS:
            return False
            
        # Check response code
        if response.status_code not in self.CACHEABLE_STATUS:
            return False
            
        # Check no-cache paths
        path = request.url.path
        if any(path.startswith(p.strip("^")) for p in self.NO_CACHE_PATHS):
            return False
            
        # Check cache-control headers
        if "no-store" in response.headers.get("Cache-Control", "").lower():
            return False
            
        return True

    async def _get_cache_key(
        self,
        request: Request,
        vary_headers: List[str] = None
    ) -> str:
        """Generate cache key from request"""
        # Start with URL path
        key_parts = [request.url.path]
        
        # Add query params
        if request.url.query:
            # Sort query params for consistent keys
            parsed = parse_qs(request.url.query)
            sorted_query = "&".join(
                f"{k}={sorted(v)[0]}"
                for k, v in sorted(parsed.items())
            )
            key_parts.append(sorted_query)
            
        # Add vary headers
        if vary_headers:
            for header in vary_headers:
                value = request.headers.get(header)
                if value:
                    key_parts.append(f"{header}:{value}")
                    
        # Generate key
        key = ":".join(key_parts)
        return f"cache:{hashlib.md5(key.encode()).hexdigest()}"

    async def _get_cache_ttl(
        self,
        request: Request
    ) -> int:
        """Get TTL for request"""
        path = request.url.path
        
        # Check custom rules
        for rule in self.cache_rules:
            if path.startswith(rule["path"].strip("^")):
                return rule["ttl"]
                
        return self.DEFAULT_TTL

    async def _get_vary_headers(
        self,
        request: Request
    ) -> List[str]:
        """Get vary headers for request"""
        path = request.url.path
        
        # Check custom rules
        for rule in self.cache_rules:
            if path.startswith(rule["path"].strip("^")):
                return rule["vary"]
                
        return []

    async def _serialize_response(
        self,
        response: Response
    ) -> Dict:
        """Serialize response for caching"""
        return {
            "content": response.body.decode() if isinstance(response.body, bytes) else response.body,
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "media_type": response.media_type
        }

    async def _deserialize_response(
        self,
        data: Dict
    ) -> Response:
        """Deserialize cached response"""
        return Response(
            content=data["content"],
            status_code=data["status_code"],
            headers=data["headers"],
            media_type=data["media_type"]
        )

    async def __call__(self, request: Request, call_next):
        # Skip caching for streaming responses
        if "text/event-stream" in request.headers.get("Accept", ""):
            return await call_next(request)

        try:
            # Get cache key and TTL
            vary_headers = await self._get_vary_headers(request)
            cache_key = await self._get_cache_key(request, vary_headers)
            cache_ttl = await self._get_cache_ttl(request)

            # Try to get from cache
            cached_data = await self.db.cache_get(cache_key)
            if cached_data:
                response = await self._deserialize_response(cached_data)
                response.headers["X-Cache"] = "HIT"
                return response

            # Get fresh response
            response = await call_next(request)
            
            # Cache if appropriate
            if self._should_cache_response(request, response):
                try:
                    # Serialize and cache response
                    serialized = await self._serialize_response(response)
                    await self.db.cache_set(
                        cache_key,
                        serialized,
                        cache_ttl
                    )
                    
                    # Add cache headers
                    response.headers["Cache-Control"] = f"public, max-age={cache_ttl}"
                    response.headers["X-Cache"] = "MISS"
                    if vary_headers:
                        response.headers["Vary"] = ", ".join(vary_headers)
                        
                except Exception as e:
                    logger.error(f"Caching error: {str(e)}")
                    
            return response

        except Exception as e:
            logger.error(f"""
            Cache middleware error:
            Error: {str(e)}
            Time: 2025-05-30 15:09:00
            User: fdygg
            Path: {request.url.path}
            """)
            return await call_next(request)

    async def clear_cache(
        self,
        pattern: str = "*"
    ) -> bool:
        """Clear cache entries matching pattern"""
        try:
            return await self.db.cache_clear(f"cache:{pattern}")
        except Exception as e:
            logger.error(f"Cache clear error: {str(e)}")
            return False

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            redis = self.db.get_redis()
            info = redis.info()
            
            return {
                "hits": info["keyspace_hits"],
                "misses": info["keyspace_misses"],
                "memory_used": info["used_memory"],
                "keys": len(redis.keys("cache:*")),
                "uptime": info["uptime_in_seconds"]
            }
        except Exception as e:
            logger.error(f"Cache stats error: {str(e)}")
            return {}