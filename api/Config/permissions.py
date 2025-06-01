from enum import Enum
from typing import Dict, List, Set

class UserRole(str, Enum):
    ADMIN = "admin"
    MODERATOR = "moderator"
    USER = "user"
    GUEST = "guest"

class Permission(str, Enum):
    # User Management
    CREATE_USER = "create_user"
    UPDATE_USER = "update_user"
    DELETE_USER = "delete_user"
    VIEW_USERS = "view_users"
    
    # Product Management
    CREATE_PRODUCT = "create_product"
    UPDATE_PRODUCT = "update_product"
    DELETE_PRODUCT = "delete_product"
    VIEW_PRODUCTS = "view_products"
    
    # Stock Management
    MANAGE_STOCK = "manage_stock"
    VIEW_STOCK = "view_stock"
    
    # Transaction Management
    CREATE_TRANSACTION = "create_transaction"
    VIEW_TRANSACTIONS = "view_transactions"
    CANCEL_TRANSACTION = "cancel_transaction"
    
    # System Management
    VIEW_LOGS = "view_logs"
    MANAGE_SETTINGS = "manage_settings"
    VIEW_METRICS = "view_metrics"

# Role to Permissions mapping
ROLE_PERMISSIONS: Dict[UserRole, Set[Permission]] = {
    UserRole.ADMIN: {p for p in Permission},  # Admin has all permissions
    
    UserRole.MODERATOR: {
        Permission.VIEW_USERS,
        Permission.VIEW_PRODUCTS,
        Permission.VIEW_STOCK,
        Permission.MANAGE_STOCK,
        Permission.VIEW_TRANSACTIONS,
        Permission.VIEW_LOGS,
        Permission.VIEW_METRICS
    },
    
    UserRole.USER: {
        Permission.VIEW_PRODUCTS,
        Permission.VIEW_STOCK,
        Permission.CREATE_TRANSACTION
    },
    
    UserRole.GUEST: {
        Permission.VIEW_PRODUCTS
    }
}

# Endpoint to required permissions mapping
ENDPOINT_PERMISSIONS: Dict[str, List[Permission]] = {
    # User endpoints
    "POST /users": [Permission.CREATE_USER],
    "GET /users": [Permission.VIEW_USERS],
    "PUT /users/{id}": [Permission.UPDATE_USER],
    "DELETE /users/{id}": [Permission.DELETE_USER],
    
    # Product endpoints
    "POST /products": [Permission.CREATE_PRODUCT],
    "GET /products": [Permission.VIEW_PRODUCTS],
    "PUT /products/{id}": [Permission.UPDATE_PRODUCT],
    "DELETE /products/{id}": [Permission.DELETE_PRODUCT],
    
    # Stock endpoints
    "GET /stock": [Permission.VIEW_STOCK],
    "POST /stock/add": [Permission.MANAGE_STOCK],
    "POST /stock/reduce": [Permission.MANAGE_STOCK],
    
    # Transaction endpoints
    "POST /transactions": [Permission.CREATE_TRANSACTION],
    "GET /transactions": [Permission.VIEW_TRANSACTIONS],
    "POST /transactions/{id}/cancel": [Permission.CANCEL_TRANSACTION]
}

# Special admin users with full access
SUPER_ADMINS = ["fdygt"]

# Rate limiting configuration per role
ROLE_RATE_LIMITS: Dict[UserRole, Dict[str, int]] = {
    UserRole.ADMIN: {
        "requests_per_minute": 100,
        "requests_per_hour": 5000
    },
    UserRole.MODERATOR: {
        "requests_per_minute": 60,
        "requests_per_hour": 3000
    },
    UserRole.USER: {
        "requests_per_minute": 30,
        "requests_per_hour": 1000
    },
    UserRole.GUEST: {
        "requests_per_minute": 10,
        "requests_per_hour": 100
    }
}