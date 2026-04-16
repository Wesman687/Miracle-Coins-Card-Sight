# Import Base from database to avoid circular imports
from app.database import Base

# Import individual model files directly
from .sales import Sale, SalesChannel, SalesForecast, ForecastPeriod, SalesMetrics
from .financial import FinancialPeriod, CashFlow, PricingStrategy, PricingUpdate, FinancialMetrics, ExpenseCategory, Expense
from .inventory import Location, InventoryItem, InventoryMovement, DeadStockAnalysis, InventoryMetrics, TurnoverAnalysis
from .alerts import AlertRule, Alert, ShopifyIntegration, ShopifySyncLog, ShopifyProduct, ShopifyOrder, ShopifyOrderItem, NotificationTemplate, NotificationLog
from .pricing_models import (
    MarketPrice, PricingConfig, ScamDetectionResult, PriceHistory,
    SpotPriceData, MarketData, ScamDetectionData, PricingResult
)
from .sku_system import SKUPrefix, SKUSequence
from .bulk_operations import BulkOperation, BulkOperationItem
from .audit_system import AuditLog, AuditEvent, ComplianceReport, DataIntegrityCheck, UserActivityLog
from .sync_system import SyncChannel, SyncLog, SyncConflict, SyncQueue, SyncStatus
from .consistency_system import ConsistencyRule, ConsistencyCheck, ConsistencyViolation, ConsistencyReport, ConsistencyRepairLog
from .collections import Collection
from .collection_metadata import CollectionMetadata
from .collection_images import CollectionImage

# Import from main models file directly to avoid circular imports
# Import these after other models to avoid circular dependencies
try:
    from ..models import Coin, CoinImage, Listing, Order, SpotPrice, AuditLog
except ImportError:
    # If circular import, set to None and import directly where needed
    Coin = None
    CoinImage = None
    Listing = None
    Order = None
    SpotPrice = None
    AuditLog = None

__all__ = [
    "Base",
    "Coin", 
    "CoinImage",
    "Listing",
    "Order",
    "SpotPrice",
    "AuditLog",
    "Sale",
    "SalesChannel", 
    "SalesForecast",
    "ForecastPeriod",
    "SalesMetrics",
    "FinancialPeriod",
    "CashFlow",
    "PricingStrategy", 
    "PricingUpdate",
    "FinancialMetrics",
    "ExpenseCategory",
    "Expense",
    "Location",
    "InventoryItem",
    "InventoryMovement", 
    "DeadStockAnalysis",
    "InventoryMetrics",
    "TurnoverAnalysis",
    "AlertRule",
    "Alert",
    "ShopifyIntegration",
    "ShopifySyncLog", 
    "ShopifyProduct",
    "ShopifyOrder",
    "ShopifyOrderItem",
    "NotificationTemplate",
    "NotificationLog",
    "MarketPrice",
    "PricingConfig",
    "ScamDetectionResult",
    "PriceHistory",
    "SpotPriceData",
    "MarketData", 
    "ScamDetectionData",
    "PricingResult",
    "SKUPrefix",
    "SKUSequence",
    "BulkOperation",
    "BulkOperationItem",
    "AuditLog",
    "AuditEvent",
    "ComplianceReport",
    "DataIntegrityCheck",
    "UserActivityLog",
    "SyncChannel",
    "SyncLog",
    "SyncConflict",
    "SyncQueue",
    "SyncStatus",
    "ConsistencyRule",
    "ConsistencyCheck",
    "ConsistencyViolation",
    "ConsistencyReport",
    "ConsistencyRepairLog",
    "Collection",
    "CollectionMetadata",
    "CollectionImage"
]
