from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from decimal import Decimal
import logging

from app.models.sales import Sale, SalesChannel, SalesForecast, ForecastPeriod, SalesMetrics
from app.models import Coin
from app.schemas.sales import (
    SalesDashboardResponse, ChannelSales, TopSellingCoin, 
    PeriodComparison, SalesForecastRequest, SalesForecastResponse,
    ForecastPeriodData, ForecastFactor
)

logger = logging.getLogger(__name__)

class SalesService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_dashboard_metrics(
        self,
        start_date: datetime,
        end_date: datetime,
        channel: Optional[str] = None
    ) -> SalesDashboardResponse:
        """Calculate comprehensive sales dashboard metrics"""
        
        # Base query for sales in date range
        query = self.db.query(Sale).filter(
            and_(
                Sale.sold_at >= start_date,
                Sale.sold_at <= end_date
            )
        )
        
        if channel:
            query = query.join(SalesChannel).filter(SalesChannel.name == channel)
        
        sales = query.all()
        
        # Calculate metrics
        total_sales = sum(sale.sale_price for sale in sales)
        total_profit = sum(sale.profit for sale in sales)
        sales_count = len(sales)
        
        # Sales velocity (coins per day)
        days = (end_date - start_date).days or 1
        sales_velocity = sales_count / days
        
        # Profit per coin
        profit_per_coin = total_profit / sales_count if sales_count > 0 else Decimal('0')
        
        # Average sale value
        average_sale_value = total_sales / sales_count if sales_count > 0 else Decimal('0')
        
        # Profit margin percentage
        profit_margin_percentage = (total_profit / total_sales * 100) if total_sales > 0 else Decimal('0')
        
        # Unique customers
        unique_customers = len(set(
            sale.customer_info.get('email', '') for sale in sales 
            if sale.customer_info and sale.customer_info.get('email')
        ))
        
        # Sales by channel
        channel_sales = self._get_sales_by_channel(start_date, end_date)
        
        # Top selling coins
        top_coins = self._get_top_selling_coins(start_date, end_date)
        
        # Period comparison
        comparison = self._get_period_comparison(start_date, end_date)
        
        return SalesDashboardResponse(
            total_sales=total_sales,
            sales_by_channel=channel_sales,
            top_selling_coins=top_coins,
            profit_per_coin=profit_per_coin,
            sales_velocity=sales_velocity,
            period_comparison=comparison,
            total_profit=total_profit,
            sales_count=sales_count,
            unique_customers=unique_customers,
            average_sale_value=average_sale_value,
            profit_margin_percentage=profit_margin_percentage
        )
    
    def _get_sales_by_channel(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[ChannelSales]:
        """Get sales breakdown by channel"""
        
        result = self.db.query(
            SalesChannel.name,
            func.count(Sale.id).label('sales_count'),
            func.sum(Sale.sale_price).label('revenue'),
            func.sum(Sale.profit).label('profit')
        ).join(Sale).filter(
            and_(
                Sale.sold_at >= start_date,
                Sale.sold_at <= end_date
            )
        ).group_by(SalesChannel.name).all()
        
        total_revenue = sum(row.revenue for row in result)
        
        return [
            ChannelSales(
                channel=row.name,
                sales_count=row.sales_count,
                revenue=row.revenue,
                profit=row.profit,
                percentage=float(row.revenue / total_revenue * 100) if total_revenue > 0 else 0
            )
            for row in result
        ]
    
    def _get_top_selling_coins(
        self,
        start_date: datetime,
        end_date: datetime,
        limit: int = 10
    ) -> List[TopSellingCoin]:
        """Get top selling coins by revenue"""
        
        result = self.db.query(
            Coin.id,
            Coin.title,
            func.count(Sale.id).label('sales_count'),
            func.sum(Sale.sale_price).label('total_sales')
        ).join(Sale).filter(
            and_(
                Sale.sold_at >= start_date,
                Sale.sold_at <= end_date
            )
        ).group_by(Coin.id, Coin.title).order_by(
            func.sum(Sale.sale_price).desc()
        ).limit(limit).all()
        
        return [
            TopSellingCoin(
                id=row.id,
                title=row.title,
                sales_count=row.sales_count,
                total_sales=row.total_sales
            )
            for row in result
        ]
    
    def _get_period_comparison(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> PeriodComparison:
        """Compare current period with previous period"""
        
        # Current period sales
        current_sales = self.db.query(func.sum(Sale.sale_price)).filter(
            and_(
                Sale.sold_at >= start_date,
                Sale.sold_at <= end_date
            )
        ).scalar() or Decimal('0')
        
        # Previous period sales
        period_length = end_date - start_date
        prev_start = start_date - period_length
        prev_end = start_date
        
        previous_sales = self.db.query(func.sum(Sale.sale_price)).filter(
            and_(
                Sale.sold_at >= prev_start,
                Sale.sold_at <= prev_end
            )
        ).scalar() or Decimal('0')
        
        # Calculate change
        if previous_sales > 0:
            change_percentage = float((current_sales - previous_sales) / previous_sales) * 100
        else:
            change_percentage = 0
        
        trend = "up" if change_percentage > 0 else "down" if change_percentage < 0 else "stable"
        
        return PeriodComparison(
            current_period=float(current_sales),
            previous_period=float(previous_sales),
            change_percentage=change_percentage,
            trend=trend
        )
    
    def create_sale(
        self,
        coin_id: int,
        channel_id: int,
        sale_price: Decimal,
        profit: Decimal,
        quantity_sold: int = 1,
        customer_info: Optional[Dict] = None,
        transaction_id: Optional[str] = None
    ) -> Sale:
        """Create a new sale record"""
        
        sale = Sale(
            coin_id=coin_id,
            channel_id=channel_id,
            sale_price=sale_price,
            profit=profit,
            quantity_sold=quantity_sold,
            customer_info=customer_info,
            transaction_id=transaction_id
        )
        
        self.db.add(sale)
        self.db.commit()
        self.db.refresh(sale)
        
        return sale
    
    def get_sales_by_channel(
        self,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """Get sales breakdown by channel for a date range"""
        
        result = self.db.query(
            SalesChannel.name,
            SalesChannel.channel_type,
            func.count(Sale.id).label('sales_count'),
            func.sum(Sale.sale_price).label('revenue'),
            func.sum(Sale.profit).label('profit'),
            func.avg(Sale.sale_price).label('avg_sale_price')
        ).join(Sale).filter(
            and_(
                Sale.sold_at >= start_date,
                Sale.sold_at <= end_date
            )
        ).group_by(SalesChannel.name, SalesChannel.channel_type).all()
        
        return [
            {
                "channel": row.name,
                "channel_type": row.channel_type,
                "sales_count": row.sales_count,
                "revenue": float(row.revenue),
                "profit": float(row.profit),
                "avg_sale_price": float(row.avg_sale_price)
            }
            for row in result
        ]
    
    def calculate_sales_metrics(
        self,
        start_date: date,
        end_date: date,
        period_type: str = "daily"
    ) -> SalesMetrics:
        """Calculate and store sales metrics for a period"""
        
        # Get sales data
        sales = self.db.query(Sale).filter(
            and_(
                Sale.sold_at >= start_date,
                Sale.sold_at <= end_date
            )
        ).all()
        
        # Calculate metrics
        total_sales = sum(sale.sale_price for sale in sales)
        total_profit = sum(sale.profit for sale in sales)
        sales_count = len(sales)
        
        # Unique customers
        unique_customers = len(set(
            sale.customer_info.get('email', '') for sale in sales 
            if sale.customer_info and sale.customer_info.get('email')
        ))
        
        # Channel breakdown
        channel_breakdown = self._get_sales_by_channel(
            datetime.combine(start_date, datetime.min.time()),
            datetime.combine(end_date, datetime.max.time())
        )
        
        # Top items
        top_items = self._get_top_selling_coins(
            datetime.combine(start_date, datetime.min.time()),
            datetime.combine(end_date, datetime.max.time())
        )
        
        # Calculated metrics
        average_sale_value = total_sales / sales_count if sales_count > 0 else Decimal('0')
        profit_margin_percentage = (total_profit / total_sales * 100) if total_sales > 0 else Decimal('0')
        
        # Sales velocity (sales per day)
        days = (end_date - start_date).days or 1
        sales_velocity = Decimal(sales_count) / days
        
        # Create metrics record
        metrics = SalesMetrics(
            period_type=period_type,
            period_start=datetime.combine(start_date, datetime.min.time()),
            period_end=datetime.combine(end_date, datetime.max.time()),
            total_sales=total_sales,
            total_profit=total_profit,
            sales_count=sales_count,
            unique_customers=unique_customers,
            channel_breakdown=[cs.dict() for cs in channel_breakdown],
            top_items=[tsc.dict() for tsc in top_items],
            average_sale_value=average_sale_value,
            profit_margin_percentage=profit_margin_percentage,
            sales_velocity=sales_velocity
        )
        
        self.db.add(metrics)
        self.db.commit()
        self.db.refresh(metrics)
        
        return metrics


