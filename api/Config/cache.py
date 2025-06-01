from datetime import timedelta
from typing import Dict, Any

# Cache backend configuration
CACHE_CONFIG = {
    "backend": "redis",  # Options: redis, memcached, in-memory
    "url": "redis://localhost:6379/0",
    "password": "${REDIS_PASSWORD}",  # Load from environment variable
    "timeout": 5,  # seconds
    "retry_attempts": 3,
    "retry_delay": 1  # seconds
}

# TTL (Time To Live) settings for different types of data
CACHE_TTL = {
    "user": {
        "profile": timedelta(minutes=15),
        "preferences": timedelta(hours=1),
        "permissions": timedelta(minutes=5)
    },
    "product": {
        "details": timedelta(minutes=5),
        "list": timedelta(minutes=2),
        "stock": timedelta(seconds=30)
    },
    "transaction": {
        "details": timedelta(minutes=30),
        "history": timedelta(minutes=15)
    },
    "auth": {
        "token": timedelta(minutes=15),
        "session": timedelta(hours=24)
    }
}

# Cache key patterns
CACHE_KEY_PATTERNS = {
    "user_profile": "user:profile:{user_id}",
    "user_preferences": "user:preferences:{user_id}",
    "user_permissions": "user:permissions:{user_id}",
    "product_details": "product:details:{product_id}",
    "product_list": "product:list:{page}:{limit}:{filters}",
    "product_stock": "product:stock:{product_id}",
    "transaction": "transaction:{transaction_id}",
    "auth_token": "auth:token:{user_id}",
    "rate_limit": "rate_limit:{user_id}:{endpoint}"
}

# Cache invalidation rules
CACHE_INVALIDATION_RULES = {
    "user_update": [
        "user:profile:{user_id}",
        "user:preferences:{user_id}",
        "user:permissions:{user_id}"
    ],
    "product_update": [
        "product:details:{product_id}",
        "product:list:*",
        "product:stock:{product_id}"
    ],
    "transaction_complete": [
        "product:stock:{product_id}",
        "transaction:{transaction_id}",
        "user:profile:{user_id}"
    ]
}

# Cache warming configuration
CACHE_WARMING = {
    "enabled": True,
    "schedule": {
        "product_list": "*/5 * * * *",  # every 5 minutes
        "stock_levels": "* * * * *"      # every minute
    },
    "preload_patterns": [
        "product:list:1:10:*",
        "product:stock:*"
    ]
}

# Cache monitoring settings
CACHE_MONITORING = {
    "enabled": True,
    "metrics": [
        "hits",
        "misses",
        "hit_ratio",
        "memory_usage",
        "evictions"
    ],
    "alert_thresholds": {
        "hit_ratio_min": 0.8,
        "memory_usage_max": 0.9,
        "evictions_per_minute_max": 100
    }
}

# Circuitbreaker settings for cache operations
CACHE_CIRCUIT_BREAKER = {
    "failure_threshold": 5,
    "recovery_timeout": 30,  # seconds
    "fallback_strategy": "local_memory"  # Options: local_memory, no_cache, error
}