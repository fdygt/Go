from fastapi import Request, Response
from fastapi.responses import Response
import time
import logging
from datetime import datetime, UTC
from typing import Optional, Dict, Any
from uuid import uuid4

from ..service.metrics_service import MetricsService
from ..service.logs_service import LogService

logger = logging.getLogger(__name__)

class MetricsMiddleware:
    def __init__(self):
        self.metrics = MetricsService()
        self.logs = LogService()
        self.startup_time = datetime.now(UTC)
        logger.info(f"""
        MetricsMiddleware initialized:
        Time: 2025-05-30 14:58:22
        User: fdygg
        """)

    async def __call__(self, request: Request, call_next):
        # Generate request ID if not exists
        request_id = getattr(request.state, "request_id", str(uuid4()))
        request.state.request_id = request_id
        
        # Get request context
        method = request.method
        endpoint = request.url.path
        start_time = time.time()
        
        # Record request start
        await self.metrics.record_request_start(method, endpoint)
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate metrics
            duration = time.time() - start_time
            status_code = response.status_code
            
            # Get response size
            if hasattr(response, "body"):
                size = len(response.body)
            else:
                size = 0
                
            # Record request completion
            await self.metrics.record_request_end(
                method=method,
                endpoint=endpoint,
                status_code=status_code,
                duration=duration,
                size=size
            )
            
            # Add metric headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{duration:.3f}"
            
            # Log slow requests (> 1 second)
            if duration > 1.0:
                context = await self._get_request_context(request)
                await self.metrics.log_slow_request(
                    request_id=request_id,
                    method=method,
                    endpoint=endpoint,
                    duration=duration,
                    context=context
                )
            
            return response
            
        except Exception as e:
            # Record failed request
            duration = time.time() - start_time
            await self.metrics.record_request_end(
                method=method,
                endpoint=endpoint,
                status_code=500,
                duration=duration,
                size=0
            )
            
            # Log error
            logger.error(f"""
            Request error:
            ID: {request_id}
            Error: {str(e)}
            Time: 2025-05-30 14:58:22
            User: fdygg
            Path: {endpoint}
            Duration: {duration:.3f}s
            """)
            
            raise

    async def _get_request_context(self, request: Request) -> Dict[str, Any]:
        """Get additional context about request"""
        return {
            "user_agent": request.headers.get("user-agent"),
            "ip_address": request.client.host,
            "referer": request.headers.get("referer"),
            "user_id": getattr(request.state, "user_id", None),
            "query_params": dict(request.query_params),
            "path_params": getattr(request, "path_params", {}),
            "timestamp": datetime.now(UTC).isoformat()
        }