from datetime import datetime
import logging

# Constants
CURRENT_TIMESTAMP = "2025-05-30 12:56:57"
CURRENT_USER = "fdygg"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Import all services
from .admin_service import AdminService
from .auth_service import AuthService
from .balance_service import BalanceService
from .blacklist_service import BlacklistService
from .conversion_service import ConversionService
from .database_service import DatabaseService
from .logs_service import LogService
from .notifications_service import NotificationService
from .product_service import ProductService
from .settings_service import SettingsService
from .stock_service import StockService
from .transaction_service import TransactionService
from .user_service import UserService
from .audit_service import AuditService

# Service registry
class ServiceRegistry:
    """Central registry for all services"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ServiceRegistry, cls).__new__(cls)
            cls._instance._initialize_services()
        return cls._instance

    def _initialize_services(self):
        """Initialize all services"""
        self.startup_time = datetime.strptime(
            CURRENT_TIMESTAMP,
            "%Y-%m-%d %H:%M:%S"
        )
        
        # Core services (no dependencies)
        self.database = DatabaseService()
        self.logger = LogService()
        self.audit = AuditService()
        
        # Auth & User services
        self.auth = AuthService()
        self.user = UserService()
        self.admin = AdminService()
        
        # Business services
        self.product = ProductService()
        self.stock = StockService()
        self.balance = BalanceService()
        self.transaction = TransactionService()
        self.conversion = ConversionService()
        
        # Support services
        self.blacklist = BlacklistService()
        self.notifications = NotificationService()
        self.settings = SettingsService()
        
        logging.info(f"""
        ServiceRegistry initialized:
        Time: {CURRENT_TIMESTAMP}
        User: {CURRENT_USER}
        Services: {', '.join([
            'database', 'logger', 'audit',
            'auth', 'user', 'admin',
            'product', 'stock', 'balance',
            'transaction', 'conversion',
            'blacklist', 'notifications',
            'settings'
        ])}
        """)

    async def cleanup(self):
        """Cleanup all services before shutdown"""
        # Implement cleanup logic here
        pass

# Create global service registry instance
services = ServiceRegistry()

# Export all services
__all__ = [
    'services',
    'AdminService',
    'AuditService',
    'AuthService',
    'BalanceService',
    'BlacklistService',
    'ConversionService',
    'DatabaseService',
    'LogService',
    'NotificationService',
    'ProductService',
    'SettingsService',
    'StockService',
    'TransactionService',
    'UserService'
]