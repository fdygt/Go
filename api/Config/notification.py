from typing import Dict, List
from enum import Enum
from datetime import timedelta

class NotificationChannel(str, Enum):
    DISCORD = "discord"
    EMAIL = "email"
    IN_APP = "in_app"
    WEBHOOK = "webhook"

class NotificationPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class NotificationType(str, Enum):
    TRANSACTION = "transaction"
    SYSTEM = "system"
    SECURITY = "security"
    STOCK = "stock"
    USER = "user"

# Notification templates
NOTIFICATION_TEMPLATES = {
    NotificationType.TRANSACTION: {
        "success": {
            "title": "Transaction Successful",
            "content": "Your {transaction_type} of {amount} {currency} has been completed successfully.",
            "priority": NotificationPriority.MEDIUM
        },
        "failed": {
            "title": "Transaction Failed",
            "content": "Your {transaction_type} of {amount} {currency} has failed. Reason: {reason}",
            "priority": NotificationPriority.HIGH
        }
    },
    NotificationType.STOCK: {
        "low_stock": {
            "title": "Low Stock Alert",
            "content": "Product {product_code} is running low on stock. Current stock: {current_stock}",
            "priority": NotificationPriority.HIGH
        },
        "out_of_stock": {
            "title": "Out of Stock Alert",
            "content": "Product {product_code} is now out of stock!",
            "priority": NotificationPriority.CRITICAL
        }
    },
    NotificationType.SECURITY: {
        "login": {
            "title": "New Login Detected",
            "content": "New login detected from {ip_address} using {device}",
            "priority": NotificationPriority.HIGH
        },
        "password_change": {
            "title": "Password Changed",
            "content": "Your password was changed successfully",
            "priority": NotificationPriority.HIGH
        }
    }
}

# Channel configuration
CHANNEL_CONFIG = {
    NotificationChannel.DISCORD: {
        "webhook_url": "https://discord.com/api/webhooks/...",
        "username": "NotificationBot",
        "avatar_url": "https://example.com/bot-avatar.png",
        "enabled": True
    },
    NotificationChannel.EMAIL: {
        "smtp_host": "smtp.gmail.com",
        "smtp_port": 587,
        "smtp_user": "notifications@yourdomain.com",
        "smtp_password": "${SMTP_PASSWORD}",  # Load from environment variable
        "from_email": "notifications@yourdomain.com",
        "enabled": True
    },
    NotificationChannel.IN_APP: {
        "enabled": True,
        "max_notifications": 100,
        "retention_days": 30
    },
    NotificationChannel.WEBHOOK: {
        "enabled": True,
        "retry_attempts": 3,
        "retry_delay": 5  # seconds
    }
}

# Priority settings
PRIORITY_SETTINGS = {
    NotificationPriority.CRITICAL: {
        "channels": [
            NotificationChannel.DISCORD,
            NotificationChannel.EMAIL,
            NotificationChannel.IN_APP
        ],
        "retry_attempts": 5,
        "retry_delay": timedelta(minutes=5),
        "expires_in": timedelta(hours=24)
    },
    NotificationPriority.HIGH: {
        "channels": [
            NotificationChannel.DISCORD,
            NotificationChannel.IN_APP
        ],
        "retry_attempts": 3,
        "retry_delay": timedelta(minutes=10),
        "expires_in": timedelta(hours=12)
    },
    NotificationPriority.MEDIUM: {
        "channels": [NotificationChannel.IN_APP],
        "retry_attempts": 2,
        "retry_delay": timedelta(minutes=15),
        "expires_in": timedelta(hours=6)
    },
    NotificationPriority.LOW: {
        "channels": [NotificationChannel.IN_APP],
        "retry_attempts": 1,
        "retry_delay": timedelta(minutes=30),
        "expires_in": timedelta(hours=3)
    }
}

# Default notification settings per user role
DEFAULT_USER_NOTIFICATION_SETTINGS = {
    "admin": {
        "enabled_channels": [
            NotificationChannel.DISCORD,
            NotificationChannel.EMAIL,
            NotificationChannel.IN_APP
        ],
        "minimum_priority": NotificationPriority.LOW
    },
    "moderator": {
        "enabled_channels": [
            NotificationChannel.DISCORD,
            NotificationChannel.IN_APP
        ],
        "minimum_priority": NotificationPriority.LOW
    },
    "user": {
        "enabled_channels": [NotificationChannel.IN_APP],
        "minimum_priority": NotificationPriority.MEDIUM
    }
}