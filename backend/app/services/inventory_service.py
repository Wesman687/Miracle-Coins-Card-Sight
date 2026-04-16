from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from decimal import Decimal
import logging

from app.models.inventory import (
    Location, InventoryItem, InventoryMovement, DeadStockAnalysis, 
    InventoryMetrics, TurnoverAnalysis
)
from app.models import Coin
from app.models.sales import Sale
from app.schemas.inventory import (
    InventoryMetricsResponse, LocationInventory, MarginAnalysis,
    DeadStockAnalysisResponse, TurnoverAnalysisResponse
)

logger = logging.getLogger(__name__)

class InventoryService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_inventory_metrics(
        self,
        location_filter: Optional[str] = None,
        category_filter: Optional[str] = None
    ) -> InventoryMetricsResponse:
        """Get comprehensive inventory metrics"""
        
        # Base query for coins
        query = self.db.query(Coin)
        
        if category_filter and category_filter != 'all':
            query = query.filter(Coin.category == category_filter)
        
        coins = query.all()
        
        # Calculate metrics
        total_coins = sum(coin.quantity for coin in coins)
        total_value = sum(coin.computed_price * coin.quantity for coin in coins if coin.computed_price)
        
        # Dead stock analysis
        dead_stock_data = self._analyze_dead_stock()
        dead_stock_count = len(dead_stock_data)
        dead_stock_value = sum(item['coin_value'] for item in dead_stock_data)
        
        # Turnover analysis
        turnover_rate = self._calculate_turnover_rate()
        
        # Location breakdown
        location_breakdown = self._get_location_breakdown(location_filter)
        
        # Category breakdown
        category_breakdown = self._get_category_breakdown()
        
        # Profit margin analysis
        profit_margin_analysis = self._get_profit_margin_analysis()
        
        # Calculated metrics
        average_value_per_coin = total_value / total_coins if total_coins > 0 else Decimal('0')
        dead_stock_percentage = (dead_stock_count / total_coins * 100) if total_coins > 0 else Decimal('0')
        
        return InventoryMetricsResponse(
            period_type="current",
            period_start=datetime.utcnow(),
            period_end=datetime.utcnow(),
            total_coins=total_coins,
            total_value=total_value,
            dead_stock_count=dead_stock_count,
            dead_stock_value=dead_stock_value,
            turnover_rate=turnover_rate,
            location_breakdown=location_breakdown,
            category_breakdown=category_breakdown,
            profit_margin_analysis=profit_margin_analysis,
            average_value_per_coin=average_value_per_coin,
            dead_stock_percentage=dead_stock_percentage,
            calculated_at=datetime.utcnow()
        )
    
    def _analyze_dead_stock(self) -> List[Dict[str, Any]]:
        """Analyze dead stock items"""
        
        # Get coins with no recent sales
        cutoff_date = datetime.utcnow() - timedelta(days=90)  # 90 days threshold
        
        dead_stock_coins = self.db.query(Coin).outerjoin(Sale).filter(
            or_(
                Sale.id.is_(None),  # No sales at all
                Sale.sold_at < cutoff_date  # Last sale was more than 90 days ago
            )
        ).all()
        
        dead_stock_data = []
        for coin in dead_stock_coins:
            # Get last sale date
            last_sale = self.db.query(Sale).filter(
                Sale.coin_id == coin.id
            ).order_by(Sale.sold_at.desc()).first()
            
            days_since_last_sale = None
            if last_sale:
                days_since_last_sale = (datetime.utcnow() - last_sale.sold_at).days
            
            # Calculate profit margin
            profit_margin = None
            if coin.paid_price and coin.computed_price:
                profit = coin.computed_price - coin.paid_price
                profit_margin = (profit / coin.paid_price) * 100
            
            dead_stock_data.append({
                'coin_id': coin.id,
                'coin_title': coin.title,
                'coin_value': coin.computed_price or Decimal('0'),
                'coin_category': coin.category or 'uncategorized',
                'days_since_last_sale': days_since_last_sale,
                'days_since_added': (datetime.utcnow() - coin.created_at).days,
                'profit_margin': profit_margin,
                'category': 'dead_stock'
            })
        
        return dead_stock_data
    
    def _calculate_turnover_rate(self) -> Decimal:
        """Calculate inventory turnover rate"""
        
        # Get total inventory value
        total_inventory_value = self.db.query(
            func.sum(Coin.computed_price * Coin.quantity)
        ).scalar() or Decimal('0')
        
        # Get sales for the last 12 months
        twelve_months_ago = datetime.utcnow() - timedelta(days=365)
        total_sales = self.db.query(
            func.sum(Sale.sale_price)
        ).filter(Sale.sold_at >= twelve_months_ago).scalar() or Decimal('0')
        
        # Calculate turnover rate (sales / average inventory)
        if total_inventory_value > 0:
            turnover_rate = total_sales / total_inventory_value
        else:
            turnover_rate = Decimal('0')
        
        return turnover_rate
    
    def _get_location_breakdown(self, location_filter: Optional[str] = None) -> List[LocationInventory]:
        """Get inventory breakdown by location"""
        
        query = self.db.query(Location)
        if location_filter and location_filter != 'all':
            query = query.filter(Location.name == location_filter)
        
        locations = query.all()
        location_data = []
        
        for location in locations:
            # Get inventory items for this location
            inventory_items = self.db.query(InventoryItem).filter(
                InventoryItem.location_id == location.id
            ).all()
            
            coin_count = sum(item.quantity for item in inventory_items)
            total_value = Decimal('0')
            total_profit = Decimal('0')
            
            for item in inventory_items:
                coin = self.db.query(Coin).filter(Coin.id == item.coin_id).first()
                if coin and coin.computed_price:
                    total_value += coin.computed_price * item.quantity
                    if coin.paid_price:
                        profit = (coin.computed_price - coin.paid_price) * item.quantity
                        total_profit += profit
            
            profit_margin = (total_profit / total_value * 100) if total_value > 0 else Decimal('0')
            
            location_data.append(LocationInventory(
                location_id=location.id,
                location_name=location.name,
                coin_count=coin_count,
                total_value=total_value,
                profit_margin=profit_margin,
                last_updated=datetime.utcnow()
            ))
        
        return location_data
    
    def _get_category_breakdown(self) -> List[Dict[str, Any]]:
        """Get inventory breakdown by category"""
        
        result = self.db.query(
            Coin.category,
            func.sum(Coin.quantity).label('coin_count'),
            func.sum(Coin.computed_price * Coin.quantity).label('total_value')
        ).group_by(Coin.category).all()
        
        return [
            {
                "category": row.category or "uncategorized",
                "coin_count": row.coin_count,
                "total_value": float(row.total_value)
            }
            for row in result
        ]
    
    def _get_profit_margin_analysis(self) -> List[MarginAnalysis]:
        """Analyze profit margins by category"""
        
        result = self.db.query(
            Coin.category,
            func.count(Coin.id).label('coin_count'),
            func.sum(Coin.computed_price * Coin.quantity).label('total_value'),
            func.avg(
                (Coin.computed_price - Coin.paid_price) / Coin.paid_price * 100
            ).label('avg_margin'),
            func.min(
                (Coin.computed_price - Coin.paid_price) / Coin.paid_price * 100
            ).label('min_margin'),
            func.max(
                (Coin.computed_price - Coin.paid_price) / Coin.paid_price * 100
            ).label('max_margin')
        ).filter(
            Coin.paid_price.isnot(None),
            Coin.computed_price.isnot(None),
            Coin.paid_price > 0
        ).group_by(Coin.category).all()
        
        return [
            MarginAnalysis(
                category=row.category or "uncategorized",
                average_margin=Decimal(str(row.avg_margin or 0)),
                min_margin=Decimal(str(row.min_margin or 0)),
                max_margin=Decimal(str(row.max_margin or 0)),
                coin_count=row.coin_count,
                total_value=Decimal(str(row.total_value or 0))
            )
            for row in result
        ]
    
    def get_dead_stock_analysis(
        self,
        category: str = "dead_stock",
        limit: int = 50
    ) -> List[DeadStockAnalysisResponse]:
        """Get dead stock analysis"""
        
        dead_stock_data = self._analyze_dead_stock()
        
        # Filter by category
        if category != "all":
            dead_stock_data = [item for item in dead_stock_data if item['category'] == category]
        
        # Limit results
        dead_stock_data = dead_stock_data[:limit]
        
        return [
            DeadStockAnalysisResponse(
                id=item['coin_id'],
                coin_id=item['coin_id'],
                days_since_last_sale=item['days_since_last_sale'],
                days_since_added=item['days_since_added'],
                profit_margin=item['profit_margin'],
                category=item['category'],
                analysis_date=datetime.utcnow(),
                criteria_used={"threshold_days": 90},
                coin_title=item['coin_title'],
                coin_value=item['coin_value'],
                coin_category=item['coin_category']
            )
            for item in dead_stock_data
        ]
    
    def get_turnover_analysis(self) -> Dict[str, List[TurnoverAnalysisResponse]]:
        """Get turnover analysis for all coins"""
        
        # Get all coins with sales data
        coins_with_sales = self.db.query(Coin).join(Sale).distinct().all()
        
        turnover_data = {
            "fast_moving": [],
            "slow_moving": [],
            "dead_stock": []
        }
        
        for coin in coins_with_sales:
            # Get sales data for this coin
            sales = self.db.query(Sale).filter(Sale.coin_id == coin.id).all()
            
            if not sales:
                continue
            
            # Calculate metrics
            total_revenue = sum(sale.sale_price for sale in sales)
            sales_count = len(sales)
            
            # Get last sale date
            last_sale = max(sale.sold_at for sale in sales)
            days_since_last_sale = (datetime.utcnow() - last_sale).days
            
            # Calculate sales velocity (sales per day)
            first_sale = min(sale.sold_at for sale in sales)
            total_days = (last_sale - first_sale).days or 1
            sales_velocity = Decimal(sales_count) / total_days
            
            # Calculate profit margin
            profit_margin = Decimal('0')
            if coin.paid_price and coin.computed_price:
                profit = coin.computed_price - coin.paid_price
                profit_margin = (profit / coin.paid_price) * 100
            
            # Categorize based on sales velocity
            if sales_velocity >= Decimal('0.1'):  # More than 1 sale per 10 days
                category = "fast_moving"
            elif sales_velocity >= Decimal('0.01'):  # More than 1 sale per 100 days
                category = "slow_moving"
            else:
                category = "dead_stock"
            
            turnover_item = TurnoverAnalysisResponse(
                id=coin.id,
                coin_id=coin.id,
                analysis_period_start=first_sale,
                analysis_period_end=last_sale,
                days_since_last_sale=days_since_last_sale,
                days_since_added=(datetime.utcnow() - coin.created_at).days,
                sales_count=sales_count,
                total_revenue=total_revenue,
                turnover_category=category,
                sales_velocity=sales_velocity,
                profit_margin=profit_margin,
                analysis_date=datetime.utcnow(),
                coin_title=coin.title,
                coin_value=coin.computed_price or Decimal('0')
            )
            
            turnover_data[category].append(turnover_item)
        
        return turnover_data
    
    def create_inventory_movement(
        self,
        coin_id: int,
        from_location_id: Optional[int],
        to_location_id: int,
        quantity: int,
        movement_type: str,
        reason: Optional[str] = None,
        reference_id: Optional[str] = None,
        moved_by: str = "system"
    ) -> InventoryMovement:
        """Create an inventory movement record"""
        
        movement = InventoryMovement(
            coin_id=coin_id,
            from_location_id=from_location_id,
            to_location_id=to_location_id,
            quantity=quantity,
            movement_type=movement_type,
            reason=reason,
            reference_id=reference_id,
            moved_by=moved_by
        )
        
        self.db.add(movement)
        self.db.commit()
        self.db.refresh(movement)
        
        return movement
    
    def transfer_inventory(
        self,
        coin_id: int,
        from_location_id: int,
        to_location_id: int,
        quantity: int,
        reason: Optional[str] = None,
        moved_by: str = "system"
    ) -> InventoryMovement:
        """Transfer inventory between locations"""
        
        # Validate inventory exists at source location
        source_item = self.db.query(InventoryItem).filter(
            and_(
                InventoryItem.coin_id == coin_id,
                InventoryItem.location_id == from_location_id
            )
        ).first()
        
        if not source_item or source_item.available_quantity < quantity:
            raise ValueError("Insufficient inventory at source location")
        
        # Update source location
        source_item.quantity -= quantity
        source_item.available_quantity -= quantity
        source_item.last_moved = datetime.utcnow()
        
        # Update or create destination location
        dest_item = self.db.query(InventoryItem).filter(
            and_(
                InventoryItem.coin_id == coin_id,
                InventoryItem.location_id == to_location_id
            )
        ).first()
        
        if dest_item:
            dest_item.quantity += quantity
            dest_item.available_quantity += quantity
            dest_item.last_moved = datetime.utcnow()
        else:
            dest_item = InventoryItem(
                coin_id=coin_id,
                location_id=to_location_id,
                quantity=quantity,
                available_quantity=quantity,
                last_moved=datetime.utcnow()
            )
            self.db.add(dest_item)
        
        # Create movement record
        movement = self.create_inventory_movement(
            coin_id=coin_id,
            from_location_id=from_location_id,
            to_location_id=to_location_id,
            quantity=quantity,
            movement_type="transfer",
            reason=reason,
            moved_by=moved_by
        )
        
        self.db.commit()
        
        return movement


