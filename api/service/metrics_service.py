from typing import Dict, Optional, List, Any
from datetime import datetime, UTC, timedelta
import logging
import psutil
import time
from prometheus_client import (
    Counter, Histogram, Gauge,
    CollectorRegistry, generate_latest
)

from .logs_service import LogService
from .database_service import DatabaseService

logger = logging.getLogger(__name__)

class MetricsService:
    def __init__(self):
        self.logs = LogService()
        self.db = DatabaseService()
        self.startup_time = datetime.now(UTC)
        self.registry = CollectorRegistry()
        
        # Initialize Prometheus metrics
        self.request_count = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status'],
            registry=self.registry
        )
        
        self.request_latency = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'endpoint'],
            registry=self.registry
        )
        
        self.response_size = Histogram(
            'http_response_size_bytes',
            'HTTP response size in bytes',
            ['method', 'endpoint'],
            registry=self.registry
        )
        
        self.active_requests = Gauge(
            'http_active_requests',
            'Number of active HTTP requests',
            ['method'],
            registry=self.registry
        )
        
        self.system_memory = Gauge(
            'system_memory_usage_bytes',
            'System memory usage in bytes',
            registry=self.registry
        )
        
        self.system_cpu = Gauge(
            'system_cpu_usage_percent',
            'System CPU usage percentage',
            registry=self.registry
        )
        
        logger.info(f"""
        MetricsService initialized:
        Time: 2025-05-30 14:58:22
        User: fdygg
        """)

    async def record_request_start(
        self,
        method: str,
        endpoint: str
    ) -> None:
        """Record the start of a request"""
        self.active_requests.labels(method=method).inc()

    async def record_request_end(
        self,
        method: str,
        endpoint: str,
        status_code: int,
        duration: float,
        size: int
    ) -> None:
        """Record the end of a request"""
        self.active_requests.labels(method=method).dec()
        self.request_count.labels(
            method=method,
            endpoint=endpoint,
            status=status_code
        ).inc()
        self.request_latency.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
        self.response_size.labels(
            method=method,
            endpoint=endpoint
        ).observe(size)

    async def update_system_metrics(self) -> None:
        """Update system metrics"""
        try:
            # Memory metrics
            memory = psutil.virtual_memory()
            self.system_memory.set(memory.used)
            
            # CPU metrics
            self.system_cpu.set(psutil.cpu_percent())
            
        except Exception as e:
            logger.error(f"Error updating system metrics: {str(e)}")

    async def get_metrics(self) -> bytes:
        """Get Prometheus metrics"""
        try:
            await self.update_system_metrics()
            return generate_latest(self.registry)
        except Exception as e:
            logger.error(f"Error generating metrics: {str(e)}")
            return b""

    async def get_metrics_summary(
        self,
        interval: timedelta = timedelta(minutes=5)
    ) -> Dict[str, Any]:
        """Get metrics summary for monitoring dashboard"""
        try:
            end_time = datetime.now(UTC)
            start_time = end_time - interval
            
            # Query metrics from database
            query = """
            SELECT 
                COUNT(*) as total_requests,
                AVG(duration) as avg_duration,
                MAX(duration) as max_duration,
                COUNT(CASE WHEN status_code >= 500 THEN 1 END) as error_count,
                COUNT(CASE WHEN duration > 1.0 THEN 1 END) as slow_requests
            FROM request_metrics
            WHERE timestamp BETWEEN ? AND ?
            """
            
            results = await self.db.execute_query(
                query,
                (start_time, end_time)
            )
            
            if not results:
                return {}
                
            metrics = results[0]
            
            # Add system metrics
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=1)
            
            return {
                "requests": {
                    "total": metrics["total_requests"],
                    "errors": metrics["error_count"],
                    "slow": metrics["slow_requests"]
                },
                "performance": {
                    "avg_duration": round(metrics["avg_duration"], 3),
                    "max_duration": round(metrics["max_duration"], 3)
                },
                "system": {
                    "cpu_percent": cpu_percent,
                    "memory_used": memory.used,
                    "memory_total": memory.total,
                    "memory_percent": memory.percent
                },
                "timestamp": end_time.isoformat(),
                "interval": str(interval)
            }
            
        except Exception as e:
            logger.error(f"Error getting metrics summary: {str(e)}")
            return {}

    async def log_slow_request(
        self,
        request_id: str,
        method: str,
        endpoint: str,
        duration: float,
        context: Dict[str, Any]
    ) -> None:
        """Log slow requests for investigation"""
        try:
            await self.logs.create_log(
                Log(
                    level=LogLevel.WARNING,
                    category=LogCategory.PERFORMANCE,
                    message=f"Slow request detected: {duration:.3f}s for {method} {endpoint}",
                    source="MetricsService",
                    metadata={
                        "request_id": request_id,
                        "method": method,
                        "endpoint": endpoint,
                        "duration": duration,
                        **context
                    }
                )
            )
        except Exception as e:
            logger.error(f"Error logging slow request: {str(e)}")