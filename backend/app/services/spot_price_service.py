import asyncio
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Dict, Any
import requests
import os
from dataclasses import dataclass
from .metals_price_cache import MetalsPriceCache, CachedMetalsPrice

logger = logging.getLogger(__name__)

@dataclass
class SpotPriceData:
    """Spot price data from external APIs"""
    price: Decimal
    currency: str
    source: str
    timestamp: datetime
    confidence: float = 1.0

class SpotPriceService:
    """Service for fetching live silver spot prices from multiple sources"""
    
    def __init__(self):
        # Load environment variables explicitly
        from dotenv import load_dotenv
        load_dotenv()
        
        self.goldapi_key = os.getenv("SILVER_PRICE_API_KEY", "")
        self.silver_symbol = "XAG"  # Fixed: Use correct symbol for silver
        self.gold_symbol = "XAU"    # Fixed: Use correct symbol for gold
        self.api_base_url = "https://www.goldapi.io/api"  # Fixed: Use correct base URL
        # Don't use session to avoid authentication issues
        self.client = None
        self.cache = MetalsPriceCache()
        
        # Debug logging
        logger.info(f"SpotPriceService initialized with API key length: {len(self.goldapi_key)}")
    
    def fetch_spot_price(self, source: Optional[str] = None, metal: str = "silver") -> Optional[SpotPriceData]:
        """Fetch spot price from a specific source or try all sources with caching"""
        
        # First, check if we have a valid cached price
        cached_price = self.cache.get_cached_price(metal)
        if cached_price:
            logger.info(f"Using cached {metal} price: ${cached_price.price}")
            return SpotPriceData(
                price=cached_price.price,
                currency=cached_price.currency,
                source=f"{cached_price.source} (cached)",
                timestamp=cached_price.timestamp,
                confidence=cached_price.confidence
            )
        
        # Check rate limits before making API call
        if not self.cache._check_rate_limit():
            logger.warning(f"Rate limit exceeded for {metal}, using fallback data")
            return self._get_fallback_price(metal)
        
        # Try GoldAPI first (configured in .env)
        if not source or source == "goldapi":
            try:
                if metal == "silver":
                    result = self._fetch_from_goldapi()  # This fetches silver
                elif metal == "gold":
                    result = self._fetch_gold_from_goldapi()
                else:
                    result = self._fetch_from_goldapi()  # Default to silver
                    
                if result:
                    # Cache the successful result
                    self.cache.cache_price(metal, {
                        'price': result.price,
                        'currency': result.currency,
                        'source': result.source,
                        'timestamp': result.timestamp,
                        'confidence': result.confidence
                    })
                    
                    # Update rate limit tracking
                    self.cache._update_rate_limit()
                    
                    logger.info(f"Successfully fetched and cached {metal} price: ${result.price}")
                    return result
            except Exception as e:
                logger.warning(f"GoldAPI failed: {e}")
        
        # Fallback to mock data if APIs fail
        logger.warning("All API sources failed, using fallback data")
        return self._get_fallback_price(metal)
    
    def _get_fallback_price(self, metal: str) -> SpotPriceData:
        """Get fallback price data - return None to show loading state"""
        return None
    
    def _fetch_from_goldapi(self) -> Optional[SpotPriceData]:
        """Fetch silver price from GoldAPI.io"""
        try:
            url = f"{self.api_base_url}/{self.silver_symbol}/USD"
            headers = {
                "x-access-token": self.goldapi_key,
                "Content-Type": "application/json"
            }
            
            logger.info(f"Fetching silver price from GoldAPI: {url}")
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                logger.error(f"GoldAPI failed with status {response.status_code}: {response.text}")
                return None
                
            data = response.json()
            price_value = data.get("price", 0)
            
            if not price_value or price_value <= 0:
                logger.error(f"Invalid price from GoldAPI: {price_value}")
                return None
            
            price = Decimal(str(price_value))
            timestamp_value = data.get("timestamp", 0)
            
            if timestamp_value:
                timestamp = datetime.fromtimestamp(timestamp_value, tz=timezone.utc)
            else:
                timestamp = datetime.now(timezone.utc)
            
            logger.info(f"Successfully fetched silver price: ${price} USD from GoldAPI")
            return SpotPriceData(
                price=price,
                currency="USD",
                source="goldapi",
                timestamp=timestamp,
                confidence=0.95
            )
            
        except Exception as e:
            logger.error(f"GoldAPI fetch failed: {e}")
            return None

    def _fetch_gold_from_goldapi(self) -> Optional[SpotPriceData]:
        """Fetch gold price from GoldAPI.io"""
        try:
            url = f"{self.api_base_url}/{self.gold_symbol}/USD"
            headers = {
                "x-access-token": self.goldapi_key,
                "Content-Type": "application/json"
            }
            
            logger.info(f"Fetching gold price from GoldAPI: {url}")
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                logger.error(f"GoldAPI failed with status {response.status_code}: {response.text}")
                return None
                
            data = response.json()
            price_value = data.get("price", 0)
            
            if not price_value or price_value <= 0:
                logger.error(f"Invalid price from GoldAPI: {price_value}")
                return None
            
            price = Decimal(str(price_value))
            timestamp_value = data.get("timestamp", 0)
            
            if timestamp_value:
                timestamp = datetime.fromtimestamp(timestamp_value, tz=timezone.utc)
            else:
                timestamp = datetime.now(timezone.utc)
            
            logger.info(f"Successfully fetched gold price: ${price} USD from GoldAPI")
            return SpotPriceData(
                price=price,
                currency="USD",
                source="goldapi",
                timestamp=timestamp,
                confidence=0.95
            )
            
        except Exception as e:
            logger.error(f"GoldAPI fetch failed: {e}")
            return None
    
    def validate_price(self, price: Decimal) -> bool:
        """Validate if a price is within reasonable bounds"""
        # Get current market price for comparison
        current_price = self.fetch_spot_price()
        if not current_price:
            return True  # Can't validate without current price
        
        # Check if price is within 50% of current market price
        min_price = current_price.price * Decimal('0.5')
        max_price = current_price.price * Decimal('1.5')
        
        return min_price <= price <= max_price
    
    def close(self):
        """Close the HTTP client"""
        self.client.close()

# Global instance
spot_price_service = SpotPriceService()
