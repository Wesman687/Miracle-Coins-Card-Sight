from decimal import Decimal
from sqlalchemy.orm import Session
from app.models import Coin, SpotPrice
from app.repositories import SpotPriceRepository
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class PricingService:
    def __init__(self, db: Session):
        self.db = db
        self.spot_repo = SpotPriceRepository(db)
    
    def calculate_coin_price(self, coin_id: int) -> Optional[Decimal]:
        """Calculate computed price for a coin"""
        try:
            coin = self.db.query(Coin).filter(Coin.id == coin_id).first()
            if not coin:
                return None
            
            # If override price is set, use that
            if coin.override_price and coin.override_value:
                coin.computed_price = coin.override_value
                self.db.commit()
                return coin.computed_price
            
            # Calculate based on pricing strategy
            if coin.price_strategy == 'spot_multiplier':
                computed_price = self._calculate_spot_multiplier_price(coin)
            else:
                # Default to spot multiplier
                computed_price = self._calculate_spot_multiplier_price(coin)
            
            coin.computed_price = computed_price
            self.db.commit()
            
            return computed_price
        except Exception as e:
            logger.error(f"Error calculating price for coin {coin_id}: {e}")
            return None
    
    def _calculate_spot_multiplier_price(self, coin: Coin) -> Decimal:
        """Calculate price using spot multiplier strategy"""
        if not coin.is_silver or not coin.silver_content_oz:
            return coin.paid_price or Decimal('0.00')
        
        # Get current spot price
        spot_price = self.spot_repo.get_latest("silver")
        if not spot_price:
            logger.warning("No spot price available, using entry spot")
            current_spot = coin.entry_spot or Decimal('0.00')
        else:
            current_spot = spot_price.price
        
        # Calculate melt value
        if coin.base_from_entry and coin.entry_melt:
            # Use entry melt as base
            melt_value = coin.entry_melt
        else:
            # Calculate from current spot
            melt_value = coin.silver_content_oz * current_spot
        
        # Apply multiplier
        computed_price = melt_value * coin.price_multiplier
        
        return computed_price
    
    def bulk_reprice_coins(self, coin_ids: Optional[list] = None, new_multiplier: Optional[Decimal] = None) -> int:
        """Bulk reprice coins"""
        try:
            query = self.db.query(Coin)
            if coin_ids:
                query = query.filter(Coin.id.in_(coin_ids))
            
            coins = query.all()
            updated_count = 0
            
            for coin in coins:
                if new_multiplier:
                    coin.price_multiplier = new_multiplier
                
                self.calculate_coin_price(coin.id)
                updated_count += 1
            
            self.db.commit()
            return updated_count
        except Exception as e:
            logger.error(f"Error in bulk reprice: {e}")
            self.db.rollback()
            return 0
    
    def get_dashboard_kpis(self) -> dict:
        """Calculate dashboard KPIs"""
        try:
            coins = self.db.query(Coin).filter(Coin.status == 'active').all()
            
            inventory_melt_value = Decimal('0.00')
            inventory_list_value = Decimal('0.00')
            total_coins = len(coins)
            
            for coin in coins:
                if coin.is_silver and coin.silver_content_oz:
                    # Calculate melt value
                    spot_price = self.spot_repo.get_latest("silver")
                    if spot_price:
                        melt_value = coin.silver_content_oz * spot_price.price
                    else:
                        melt_value = coin.entry_melt or Decimal('0.00')
                    
                    inventory_melt_value += melt_value * coin.quantity
                
                # Add computed price to list value
                if coin.computed_price:
                    inventory_list_value += coin.computed_price * coin.quantity
            
            # Calculate gross profit
            gross_profit = inventory_list_value - inventory_melt_value
            
            # Calculate ratio
            melt_vs_list_ratio = Decimal('0.00')
            if inventory_melt_value > 0:
                melt_vs_list_ratio = inventory_list_value / inventory_melt_value
            
            return {
                "inventory_melt_value": inventory_melt_value,
                "inventory_list_value": inventory_list_value,
                "gross_profit": gross_profit,
                "melt_vs_list_ratio": melt_vs_list_ratio,
                "total_coins": total_coins
            }
        except Exception as e:
            logger.error(f"Error calculating dashboard KPIs: {e}")
            return {
                "inventory_melt_value": Decimal('0.00'),
                "inventory_list_value": Decimal('0.00'),
                "gross_profit": Decimal('0.00'),
                "melt_vs_list_ratio": Decimal('0.00'),
                "total_coins": 0
            }

