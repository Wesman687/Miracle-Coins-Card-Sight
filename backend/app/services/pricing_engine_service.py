import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class PricingResult:
    """Final pricing calculation result"""
    final_price: Decimal
    melt_value: Decimal
    markup_factor: Decimal
    confidence_score: float
    scam_detected: bool
    sources_used: List[str]
    calculation_method: str
    timestamp: datetime

@dataclass
class PricingInput:
    """Input data for pricing calculation"""
    coin_id: int
    coin_type: str
    weight_oz: Decimal
    purity: Decimal
    override_price: Optional[Decimal] = None
    force_update: bool = False

class PricingEngineService:
    """Core pricing engine that calculates final prices using multiple data sources"""
    
    def __init__(self):
        self.min_confidence_threshold = 0.6
        self.price_update_threshold = Decimal('3.00')
        
    def calculate_price(
        self, 
        pricing_input: PricingInput, 
        db = None
    ) -> PricingResult:
        """Calculate final price for a coin using all available data"""
        
        try:
            # Get real spot price from the service
            from app.services.spot_price_service import spot_price_service
            spot_data = spot_price_service.fetch_spot_price()
            
            if spot_data:
                # Ensure we're working with Decimal for all calculations
                spot_price = Decimal(str(spot_data.price))
                confidence_score = float(spot_data.confidence)  # Convert to float for dataclass
                sources_used = [spot_data.source]
            else:
                # Fallback to mock data
                spot_price = Decimal('25.00')
                confidence_score = 0.5
                sources_used = ["fallback"]
            
            # Calculate melt value: weight * purity * spot_price
            melt_value = pricing_input.weight_oz * pricing_input.purity * spot_price
            
            # Use Decimal for markup factor
            markup_factor = Decimal('1.5')
            
            # Calculate final price
            final_price = melt_value * markup_factor
            
            logger.info(f"Price calculation for coin {pricing_input.coin_id}: "
                       f"weight={pricing_input.weight_oz}oz, purity={pricing_input.purity}, "
                       f"spot=${spot_price}, melt=${melt_value}, final=${final_price}")
            
            return PricingResult(
                final_price=final_price,
                melt_value=melt_value,
                markup_factor=markup_factor,
                confidence_score=confidence_score,
                scam_detected=False,
                sources_used=sources_used,
                calculation_method="markup_based",
                timestamp=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            logger.error(f"Price calculation failed for coin {pricing_input.coin_id}: {e}")
            raise

# Global instance
pricing_engine_service = PricingEngineService()
