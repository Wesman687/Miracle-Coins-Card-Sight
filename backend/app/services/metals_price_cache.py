import os
import json
import logging
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class CachedMetalsPrice:
    """Cached metals price data"""
    price: Decimal
    currency: str
    source: str
    timestamp: datetime
    confidence: float
    cached_at: datetime

class MetalsPriceCache:
    """Service for caching metals prices with rate limit protection"""
    
    def __init__(self):
        self.cache_file = Path("metals_prices_cache.json")
        self.cache_duration = timedelta(minutes=10)  # Cache for 10 minutes
        self.rate_limit_window = timedelta(hours=1)  # Rate limit window
        self.max_requests_per_hour = 8  # Leave buffer under 10/hour limit
        
    def _load_cache(self) -> Dict[str, Any]:
        """Load cache from file"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r') as f:
                    data = json.load(f)
                    # Convert datetime strings back to datetime objects
                    for metal in ['silver', 'gold']:
                        if metal in data and 'cached_at' in data[metal]:
                            if isinstance(data[metal]['cached_at'], str):
                                data[metal]['cached_at'] = datetime.fromisoformat(data[metal]['cached_at'])
                        if metal in data and 'timestamp' in data[metal]:
                            if isinstance(data[metal]['timestamp'], str):
                                data[metal]['timestamp'] = datetime.fromisoformat(data[metal]['timestamp'])
                    return data
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}")
        return {}
    
    def _save_cache(self, data: Dict[str, Any]):
        """Save cache to file"""
        try:
            # Convert datetime objects to strings for JSON serialization
            cache_data = {}
            for metal in ['silver', 'gold']:
                if metal in data:
                    cache_data[metal] = data[metal].copy()
                    if 'cached_at' in cache_data[metal]:
                        if hasattr(cache_data[metal]['cached_at'], 'isoformat'):
                            cache_data[metal]['cached_at'] = cache_data[metal]['cached_at'].isoformat()
                    if 'timestamp' in cache_data[metal]:
                        if hasattr(cache_data[metal]['timestamp'], 'isoformat'):
                            cache_data[metal]['timestamp'] = cache_data[metal]['timestamp'].isoformat()
            
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
    
    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits"""
        cache = self._load_cache()
        
        # Check if we have rate limit tracking
        if 'rate_limit' not in cache:
            return True
        
        rate_limit_data = cache['rate_limit']
        last_request_time = datetime.fromisoformat(rate_limit_data['last_request'])
        request_count = rate_limit_data['count']
        
        # Reset count if we're in a new hour
        if datetime.now(timezone.utc) - last_request_time > self.rate_limit_window:
            return True
        
        # Check if we're under the limit
        return request_count < self.max_requests_per_hour
    
    def _update_rate_limit(self):
        """Update rate limit tracking"""
        cache = self._load_cache()
        now = datetime.now(timezone.utc)
        
        if 'rate_limit' not in cache:
            cache['rate_limit'] = {
                'last_request': now.isoformat(),
                'count': 1
            }
        else:
            rate_limit_data = cache['rate_limit']
            last_request_time = datetime.fromisoformat(rate_limit_data['last_request'])
            
            # Reset count if we're in a new hour
            if now - last_request_time > self.rate_limit_window:
                rate_limit_data['count'] = 1
            else:
                rate_limit_data['count'] += 1
            
            rate_limit_data['last_request'] = now.isoformat()
        
        self._save_cache(cache)
    
    def get_cached_price(self, metal: str) -> Optional[CachedMetalsPrice]:
        """Get cached price if still valid"""
        cache = self._load_cache()
        
        if metal not in cache:
            return None
        
        cached_data = cache[metal]
        cached_at = cached_data['cached_at']
        
        # Check if cache is still valid
        if datetime.now(timezone.utc) - cached_at < self.cache_duration:
            return CachedMetalsPrice(
                price=Decimal(str(cached_data['price'])),
                currency=cached_data['currency'],
                source=cached_data['source'],
                timestamp=cached_data['timestamp'],
                confidence=cached_data['confidence'],
                cached_at=cached_at
            )
        
        return None
    
    def cache_price(self, metal: str, price_data: Dict[str, Any]):
        """Cache a price with timestamp"""
        cache = self._load_cache()
        
        cache[metal] = {
            'price': float(price_data['price']),
            'currency': price_data['currency'],
            'source': price_data['source'],
            'timestamp': price_data['timestamp'].isoformat() if price_data['timestamp'] and hasattr(price_data['timestamp'], 'isoformat') else str(price_data['timestamp']) if price_data['timestamp'] else None,
            'confidence': price_data['confidence'],
            'cached_at': datetime.now(timezone.utc).isoformat()
        }
        
        self._save_cache(cache)
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limit status"""
        cache = self._load_cache()
        
        if 'rate_limit' not in cache:
            return {
                'within_limit': True,
                'requests_remaining': self.max_requests_per_hour,
                'reset_time': None,
                'last_request': None
            }
        
        rate_limit_data = cache['rate_limit']
        last_request_time = datetime.fromisoformat(rate_limit_data['last_request'])
        request_count = rate_limit_data['count']
        
        # Calculate reset time
        reset_time = last_request_time + self.rate_limit_window
        
        return {
            'within_limit': request_count < self.max_requests_per_hour,
            'requests_remaining': max(0, self.max_requests_per_hour - request_count),
            'reset_time': reset_time.isoformat(),
            'last_request': last_request_time.isoformat(),
            'current_count': request_count
        }
