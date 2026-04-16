import os
from typing import List, Dict, Any
from pydantic import BaseSettings, Field
from decimal import Decimal

class PricingConfig(BaseSettings):
    """Configuration for pricing agent services"""
    
    # Database Configuration
    DATABASE_URL: str = Field(
        default="postgresql://user:password@localhost/miracle_coins",
        description="Database connection URL"
    )
    
    # Redis Configuration
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL for Celery"
    )
    
    # API Keys for Spot Price Sources
    METALS_API_KEY: str = Field(
        default="",
        description="Metals-API.com API key"
    )
    
    GOLDAPI_KEY: str = Field(
        default="",
        description="GoldAPI.io API key"
    )
    
    ALPHA_VANTAGE_KEY: str = Field(
        default="",
        description="Alpha Vantage API key"
    )
    
    FIXER_API_KEY: str = Field(
        default="",
        description="Fixer.io API key"
    )
    
    # Shopify Configuration
    SHOPIFY_DOMAIN: str = Field(
        default="",
        description="Shopify store domain"
    )
    
    SHOPIFY_ACCESS_TOKEN: str = Field(
        default="",
        description="Shopify API access token"
    )
    
    # Pricing Configuration
    DEFAULT_MARKUP_FACTOR: Decimal = Field(
        default=Decimal('1.500'),
        description="Default markup factor for pricing"
    )
    
    MIN_MARKUP_FACTOR: Decimal = Field(
        default=Decimal('1.200'),
        description="Minimum markup factor"
    )
    
    MAX_MARKUP_FACTOR: Decimal = Field(
        default=Decimal('2.000'),
        description="Maximum markup factor"
    )
    
    PRICE_UPDATE_THRESHOLD: Decimal = Field(
        default=Decimal('3.00'),
        description="Price update threshold percentage"
    )
    
    # Scam Detection Configuration
    SCAM_DETECTION_ENABLED: bool = Field(
        default=True,
        description="Enable scam detection"
    )
    
    SCAM_THRESHOLD: Decimal = Field(
        default=Decimal('0.300'),
        description="Scam detection threshold"
    )
    
    CONFIDENCE_THRESHOLD: Decimal = Field(
        default=Decimal('0.70'),
        description="Minimum confidence threshold"
    )
    
    # Market Scraping Configuration
    SCRAPING_ENABLED: bool = Field(
        default=True,
        description="Enable market data scraping"
    )
    
    SCRAPING_DELAY: int = Field(
        default=2,
        description="Delay between scraping requests (seconds)"
    )
    
    MAX_SCRAPING_RETRIES: int = Field(
        default=3,
        description="Maximum retries for scraping"
    )
    
    # Rate Limiting Configuration
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = Field(
        default=60,
        description="Rate limit for API requests per minute"
    )
    
    RATE_LIMIT_BURST: int = Field(
        default=10,
        description="Burst rate limit"
    )
    
    # Background Task Configuration
    CELERY_TASK_TIME_LIMIT: int = Field(
        default=300,
        description="Celery task time limit in seconds"
    )
    
    CELERY_TASK_SOFT_TIME_LIMIT: int = Field(
        default=240,
        description="Celery task soft time limit in seconds"
    )
    
    # Logging Configuration
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level"
    )
    
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string"
    )
    
    # Performance Configuration
    BATCH_SIZE: int = Field(
        default=10,
        description="Batch size for processing"
    )
    
    MAX_CONCURRENT_REQUESTS: int = Field(
        default=5,
        description="Maximum concurrent requests"
    )
    
    # Cache Configuration
    CACHE_TTL: int = Field(
        default=3600,
        description="Cache TTL in seconds"
    )
    
    ENABLE_CACHING: bool = Field(
        default=True,
        description="Enable caching"
    )
    
    # Security Configuration
    ALLOWED_HOSTS: List[str] = Field(
        default=["localhost", "127.0.0.1"],
        description="Allowed hosts for CORS"
    )
    
    SECRET_KEY: str = Field(
        default="your-secret-key-here",
        description="Secret key for JWT tokens"
    )
    
    # Monitoring Configuration
    ENABLE_METRICS: bool = Field(
        default=True,
        description="Enable metrics collection"
    )
    
    METRICS_PORT: int = Field(
        default=9090,
        description="Metrics server port"
    )
    
    # Development Configuration
    DEBUG: bool = Field(
        default=False,
        description="Enable debug mode"
    )
    
    TESTING: bool = Field(
        default=False,
        description="Enable testing mode"
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Global configuration instance
pricing_config = PricingConfig()

# Service-specific configurations
class SpotPriceServiceConfig:
    """Configuration for spot price service"""
    
    SOURCES = [
        {
            "name": "metals-api",
            "url": "https://metals-api.com/api/latest",
            "headers": {"apikey": pricing_config.METALS_API_KEY},
            "price_key": "rates.XAG",
            "currency_key": "base",
            "timeout": 10,
            "retry_count": 3
        },
        {
            "name": "goldapi",
            "url": "https://www.goldapi.io/api/XAG/USD",
            "headers": {"x-access-token": pricing_config.GOLDAPI_KEY},
            "price_key": "price",
            "currency_key": "currency",
            "timeout": 15,
            "retry_count": 3
        },
        {
            "name": "alpha-vantage",
            "url": "https://www.alphavantage.co/query",
            "headers": {},
            "price_key": "Realtime Currency Exchange Rate.5. Exchange Rate",
            "currency_key": "Realtime Currency Exchange Rate.3. To_Currency Code",
            "timeout": 20,
            "retry_count": 2
        }
    ]
    
    FALLBACK_SOURCES = ["metals-api", "goldapi"]
    CONFIDENCE_THRESHOLD = 0.7

class MarketScraperConfig:
    """Configuration for market scraper service"""
    
    SCRAPERS = {
        "ebay": {
            "base_url": "https://www.ebay.com/sch/i.html",
            "params": {
                "_sop": "13",
                "LH_Complete": "1",
                "LH_Sold": "1"
            },
            "timeout": 30,
            "retry_count": 2
        },
        "apmex": {
            "base_url": "https://www.apmex.com",
            "timeout": 30,
            "retry_count": 2
        },
        "jm_bullion": {
            "base_url": "https://www.jmbullion.com",
            "timeout": 30,
            "retry_count": 2
        },
        "sd_bullion": {
            "base_url": "https://sdbullion.com",
            "timeout": 30,
            "retry_count": 2
        }
    }
    
    COIN_TYPE_MAPPINGS = {
        "silver_eagle": "silver eagle 1oz",
        "silver_round": "silver round 1oz",
        "silver_bar": "silver bar 1oz",
        "gold_coin": "gold coin 1oz",
        "platinum_coin": "platinum coin 1oz"
    }
    
    MAX_RESULTS_PER_SOURCE = 20
    SCRAPING_DELAY = pricing_config.SCRAPING_DELAY

class ScamDetectionConfig:
    """Configuration for scam detection service"""
    
    DETECTION_METHODS = [
        "statistical_analysis",
        "price_deviation",
        "pattern_recognition",
        "market_consistency"
    ]
    
    STATISTICAL_THRESHOLDS = {
        "z_score_threshold": 3.0,
        "iqr_multiplier": 1.5,
        "outlier_threshold": 0.05
    }
    
    PRICE_DEVIATION_THRESHOLD = pricing_config.SCAM_THRESHOLD
    
    PATTERN_DETECTION = {
        "round_number_check": True,
        "sequential_pattern_check": True,
        "repeated_digit_check": True
    }
    
    CONFIDENCE_WEIGHTS = {
        "statistical_analysis": 0.3,
        "price_deviation": 0.3,
        "pattern_recognition": 0.2,
        "market_consistency": 0.2
    }

class PricingEngineConfig:
    """Configuration for pricing engine"""
    
    CALCULATION_METHODS = [
        "override",
        "markup_based",
        "market_based",
        "min_markup_constraint",
        "max_markup_constraint"
    ]
    
    MARKUP_RANGES = {
        "silver_eagle": {"min": 1.3, "max": 1.8, "default": 1.55},
        "silver_round": {"min": 1.2, "max": 1.6, "default": 1.4},
        "silver_bar": {"min": 1.15, "max": 1.5, "default": 1.35},
        "gold_coin": {"min": 1.4, "max": 2.0, "default": 1.7},
        "platinum_coin": {"min": 1.35, "max": 1.9, "default": 1.65},
        "generic_silver": {"min": 1.2, "max": 1.7, "default": 1.45}
    }
    
    CONFIDENCE_FACTORS = {
        "spot_price": 0.3,
        "market_data": 0.3,
        "scam_detection": 0.2,
        "configuration": 0.2
    }
    
    PRICE_UPDATE_THRESHOLD = pricing_config.PRICE_UPDATE_THRESHOLD

class ShopifyConfig:
    """Configuration for Shopify integration"""
    
    API_VERSION = "2023-10"
    BATCH_SIZE = pricing_config.BATCH_SIZE
    RATE_LIMIT = 2  # requests per second
    
    PRODUCT_UPDATE_FIELDS = [
        "price",
        "compare_at_price",
        "inventory_quantity"
    ]
    
    WEBHOOK_EVENTS = [
        "orders/create",
        "orders/updated",
        "orders/paid",
        "orders/cancelled"
    ]

class CeleryConfig:
    """Configuration for Celery tasks"""
    
    TASK_SCHEDULES = {
        "update_spot_prices": "0 * * * *",  # Every hour
        "scrape_market_data": "0 2 * * *",   # Daily at 2 AM
        "calculate_all_prices": "30 * * * *", # Every hour at 30 minutes
        "sync_shopify_prices": "45 * * * *", # Every hour at 45 minutes
        "detect_scam_prices": "0 3 * * *",   # Daily at 3 AM
        "cleanup_old_data": "0 4 * * 1"      # Weekly on Monday at 4 AM
    }
    
    TASK_RETRY_CONFIG = {
        "max_retries": 3,
        "countdown": 60,
        "max_countdown": 3600
    }
    
    TASK_TIME_LIMITS = {
        "update_spot_prices": 300,
        "scrape_market_data": 600,
        "calculate_all_prices": 900,
        "sync_shopify_prices": 300,
        "detect_scam_prices": 600,
        "cleanup_old_data": 3600
    }

# Environment-specific configurations
class DevelopmentConfig(PricingConfig):
    """Development environment configuration"""
    DEBUG = True
    LOG_LEVEL = "DEBUG"
    TESTING = False

class ProductionConfig(PricingConfig):
    """Production environment configuration"""
    DEBUG = False
    LOG_LEVEL = "INFO"
    TESTING = False

class TestingConfig(PricingConfig):
    """Testing environment configuration"""
    DEBUG = True
    LOG_LEVEL = "DEBUG"
    TESTING = True
    DATABASE_URL = "sqlite:///test.db"

# Configuration factory
def get_config() -> PricingConfig:
    """Get configuration based on environment"""
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return ProductionConfig()
    elif env == "testing":
        return TestingConfig()
    else:
        return DevelopmentConfig()

# Export the active configuration
config = get_config()




