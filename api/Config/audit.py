from typing import Dict, List
from enum import Enum
from datetime import timedelta

class AuditLevel(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AuditCategory(str, Enum):
    AUTH = "auth"
    USER = "user"
    PRODUCT = "product"
    STOCK = "stock"
    TRANSACTION = "transaction"
    SYSTEM = "system"

# Audit configuration
AUDIT_CONFIG = {
    "enabled": True,
    "storage": {
        "type": "database",  # Options: database, file, external
        "connection": "${AUDIT_DB_URL}",  # Load from environment variable
        "table_name": "audit_logs"
    },
    "retention": {
        "database": timedelta(days=90),
        "archive": timedelta(days=365)
    }
}

# Events to audit
AUDIT_EVENTS = {
    AuditCategory.AUTH: {
        "login": {
            "level": AuditLevel.INFO,
            "fields": ["user_id", "ip_address", "user_agent", "status"]
        },
        "logout": {
            "level": AuditLevel.INFO,
            "fields": ["user_id"]
        },
        "password_change": {
            "level": AuditLevel.WARNING,
            "fields": ["user_id", "ip_address"]
        },
        "failed_login": {
            "level": AuditLevel.WARNING,
            "fields": ["username", "ip_address", "reason"]
        }
    },
    AuditCategory.USER: {
        "create": {
            "level": AuditLevel.INFO,
            "fields": ["user_id", "username", "role"]
        },
        "update": {
            "level": AuditLevel.INFO,
            "fields": ["user_id", "changed_fields"]
        },
        "delete": {
            "level": AuditLevel.WARNING,
            "fields": ["user_id", "reason"]
        }
    },
    AuditCategory.PRODUCT: {
        "create": {
            "level": AuditLevel.INFO,
            "fields": ["product_id", "code", "name", "price"]
        },
        "update": {
            "level": AuditLevel.INFO,
            "fields": ["product_id", "changed_fields"]
        },
        "delete": {
            "level": AuditLevel.WARNING,
            "fields": ["product_id", "reason"]
        }
    },
    AuditCategory.STOCK: {
        "add": {
            "level": AuditLevel.INFO,
            "fields": ["product_id", "quantity", "added_by"]
        },
        "reduce": {
            "level": AuditLevel.INFO,
            "fields": ["product_id", "quantity", "reduced_by"]
        },
        "adjustment": {
            "level": AuditLevel.WARNING,
            "fields": ["product_id", "old_quantity", "new_quantity", "reason"]
        }
    },
    AuditCategory.TRANSACTION: {
        "create": {
            "level": AuditLevel.INFO,
            "fields": ["transaction_id", "user_id", "amount", "status"]
        },
        "complete": {
            "level": AuditLevel.INFO,
            "fields": ["transaction_id", "status", "completion_time"]
        },
        "fail": {
            "level": AuditLevel.ERROR,
            "fields": ["transaction_id", "error_code", "error_message"]
        },
        "cancel": {
            "level": AuditLevel.WARNING,
            "fields": ["transaction_id", "reason", "cancelled_by"]
        }
    }
}

# Audit log format
AUDIT_LOG_FORMAT = {
    "timestamp": "",            # ISO 8601 format
    "category": "",            # AuditCategory
    "level": "",              # AuditLevel
    "event": "",              # Event name
    "user_id": "",            # ID of user performing the action
    "ip_address": "",         # IP address
    "data": {},               # Event specific data
    "metadata": {}            # Additional context
}

# Alert thresholds for audit events
AUDIT_ALERTS = {
    "failed_login_attempts": {
        "threshold": 5,
        "window": timedelta(minutes=15),
        "action": "notify_admin"
    },
    "stock_adjustments": {
        "threshold": 10,
        "window": timedelta(hours=1),
        "action": "notify_admin"
    },
    "failed_transactions": {
        "threshold": 3,
        "window": timedelta(minutes=5),
        "action": ["notify_admin", "slack_alert"]
    }
}

# Archive settings
AUDIT_ARCHIVE = {
    "enabled": True,
    "schedule": "0 0 * * *",  # Daily at midnight
    "format": "json",
    "compression": "gzip",
    "storage": {
        "type": "s3",
        "bucket": "audit-logs-archive",
        "prefix": "logs/",
        "retention_days": 365
    }
}