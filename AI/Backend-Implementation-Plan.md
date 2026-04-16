# 🔧 Backend Implementation Plan
## Miracle Coins CoinSync Pro - Detailed Backend Development

---

## 📋 **Backend Architecture Overview**

### **Technology Stack:**
- **Framework**: FastAPI with async/await
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Background Tasks**: Celery with Redis
- **Caching**: Redis for frequently accessed data
- **Authentication**: JWT with Stream-Line integration
- **API Documentation**: OpenAPI/Swagger
- **Monitoring**: Structured logging with performance metrics

### **Database Design:**
- **Normalized Schema**: Proper relationships and constraints
- **Audit Logging**: Track all changes
- **Performance**: Indexed queries, optimized for 5-10k coins
- **Scalability**: Designed for future growth

---

## 🎯 **Phase 1: Sales & Revenue Forecasting Backend (Weeks 1-2)**

### **1.1 Sales Management Models**

#### **File: `app/models/sales.py`**
```python
from sqlalchemy import Column, Integer, String, DateTime, Decimal, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base
import uuid
from datetime import datetime
from decimal import Decimal

class SalesChannel(Base):
    __tablename__ = "sales_channels"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    channel_type = Column(String(50), nullable=False)  # shopify, in_store, auction, direct
    active = Column(Boolean, default=True)
    settings = Column(JSON)  # Channel-specific settings
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Sale(Base):
    __tablename__ = "sales"
    
    id = Column(Integer, primary_key=True, index=True)
    coin_id = Column(Integer, ForeignKey("coins.id"), nullable=False)
    channel_id = Column(Integer, ForeignKey("sales_channels.id"), nullable=False)
    
    # Sale details
    sale_price = Column(Decimal(10, 2), nullable=False)
    profit = Column(Decimal(10, 2), nullable=False)
    quantity_sold = Column(Integer, default=1)
    
    # Customer information
    customer_info = Column(JSON)  # Name, email, phone, etc.
    transaction_id = Column(String(100))  # External transaction ID
    
    # Timestamps
    sold_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    coin = relationship("Coin", back_populates="sales")
    channel = relationship("SalesChannel")

class SalesForecast(Base):
    __tablename__ = "sales_forecasts"
    
    id = Column(Integer, primary_key=True, index=True)
    forecast_type = Column(String(20), nullable=False)  # daily, weekly, monthly, etc.
    forecast_horizon = Column(Integer, nullable=False)  # Number of periods ahead
    confidence_level = Column(Integer, nullable=False)  # 50-95%
    
    # Forecast data
    forecast_data = Column(JSON)  # Array of forecast periods
    factors_used = Column(JSON)  # Factors considered in forecast
    accuracy_score = Column(Decimal(5, 2))  # Historical accuracy
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    valid_until = Column(DateTime)
    
    # Settings used
    include_seasonality = Column(Boolean, default=True)
    include_trends = Column(Boolean, default=True)
    include_external_factors = Column(Boolean, default=False)
```

### **1.2 Sales API Endpoints**

#### **File: `app/routers/sales.py`**
```python
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date, timedelta
from decimal import Decimal

from app.database import get_db
from app.models.sales import Sale, SalesChannel, SalesForecast
from app.models.coins import Coin
from app.schemas.sales import (
    SaleCreate, SaleResponse, SalesChannelCreate, SalesChannelResponse,
    SalesForecastRequest, SalesForecastResponse, SalesDashboardResponse
)
from app.services.sales_service import SalesService
from app.services.forecast_service import ForecastService
from app.auth import get_current_admin_user

router = APIRouter(prefix="/sales", tags=["sales"])

@router.get("/dashboard", response_model=SalesDashboardResponse)
async def get_sales_dashboard(
    period: str = Query("daily", regex="^(daily|weekly|monthly)$"),
    channel: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Get comprehensive sales dashboard metrics"""
    
    sales_service = SalesService(db)
    
    # Calculate date range based on period
    end_date = datetime.utcnow()
    if period == "daily":
        start_date = end_date - timedelta(days=1)
    elif period == "weekly":
        start_date = end_date - timedelta(weeks=1)
    else:  # monthly
        start_date = end_date - timedelta(days=30)
    
    dashboard_data = await sales_service.get_dashboard_metrics(
        start_date=start_date,
        end_date=end_date,
        channel=channel
    )
    
    return dashboard_data

@router.post("/forecast", response_model=SalesForecastResponse)
async def generate_revenue_forecast(
    forecast_request: SalesForecastRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Generate revenue forecast based on historical data"""
    
    forecast_service = ForecastService(db)
    
    forecast_data = await forecast_service.generate_forecast(
        time_period=forecast_request.time_period,
        horizon=forecast_request.forecast_horizon,
        confidence_level=forecast_request.confidence_level,
        include_seasonality=forecast_request.include_seasonality,
        include_trends=forecast_request.include_trends
    )
    
    return forecast_data

@router.get("/by-channel", response_model=List[dict])
async def get_sales_by_channel(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Get sales breakdown by channel"""
    
    sales_service = SalesService(db)
    
    if not start_date:
        start_date = date.today() - timedelta(days=30)
    if not end_date:
        end_date = date.today()
    
    channel_sales = await sales_service.get_sales_by_channel(
        start_date=start_date,
        end_date=end_date
    )
    
    return channel_sales

@router.post("/", response_model=SaleResponse)
async def create_sale(
    sale_data: SaleCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Record a new sale"""
    
    sales_service = SalesService(db)
    
    # Validate coin exists and is available
    coin = db.query(Coin).filter(Coin.id == sale_data.coin_id).first()
    if not coin:
        raise HTTPException(status_code=404, detail="Coin not found")
    
    if coin.status != "active":
        raise HTTPException(status_code=400, detail="Coin is not available for sale")
    
    # Calculate profit
    profit = sale_data.sale_price - (coin.paid_price or Decimal('0'))
    
    sale = await sales_service.create_sale(
        coin_id=sale_data.coin_id,
        channel_id=sale_data.channel_id,
        sale_price=sale_data.sale_price,
        profit=profit,
        quantity_sold=sale_data.quantity_sold,
        customer_info=sale_data.customer_info,
        transaction_id=sale_data.transaction_id
    )
    
    # Update coin status
    coin.status = "sold"
    coin.quantity -= sale_data.quantity_sold
    db.commit()
    
    return sale

@router.get("/channels", response_model=List[SalesChannelResponse])
async def get_sales_channels(
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Get all sales channels"""
    
    query = db.query(SalesChannel)
    if active_only:
        query = query.filter(SalesChannel.active == True)
    
    channels = query.all()
    return channels

@router.post("/channels", response_model=SalesChannelResponse)
async def create_sales_channel(
    channel_data: SalesChannelCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Create a new sales channel"""
    
    # Check if channel name already exists
    existing = db.query(SalesChannel).filter(
        SalesChannel.name == channel_data.name
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Channel name already exists")
    
    channel = SalesChannel(
        name=channel_data.name,
        channel_type=channel_data.channel_type,
        settings=channel_data.settings
    )
    
    db.add(channel)
    db.commit()
    db.refresh(channel)
    
    return channel
```

### **1.3 Sales Service Layer**

#### **File: `app/services/sales_service.py`**
```python
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from decimal import Decimal

from app.models.sales import Sale, SalesChannel
from app.models.coins import Coin
from app.schemas.sales import SalesDashboardResponse

class SalesService:
    def __init__(self, db: Session):
        self.db = db
    
    async def get_dashboard_metrics(
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
        
        # Sales by channel
        channel_sales = await self._get_sales_by_channel(start_date, end_date)
        
        # Top selling coins
        top_coins = await self._get_top_selling_coins(start_date, end_date)
        
        # Period comparison
        comparison = await self._get_period_comparison(start_date, end_date)
        
        return SalesDashboardResponse(
            total_sales=total_sales,
            sales_by_channel=channel_sales,
            top_selling_coins=top_coins,
            profit_per_coin=profit_per_coin,
            sales_velocity=sales_velocity,
            period_comparison=comparison
        )
    
    async def _get_sales_by_channel(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
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
            {
                "channel": row.name,
                "sales_count": row.sales_count,
                "revenue": row.revenue,
                "profit": row.profit,
                "percentage": (row.revenue / total_revenue * 100) if total_revenue > 0 else 0
            }
            for row in result
        ]
    
    async def _get_top_selling_coins(
        self,
        start_date: datetime,
        end_date: datetime,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
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
            {
                "id": row.id,
                "title": row.title,
                "sales_count": row.sales_count,
                "total_sales": row.total_sales
            }
            for row in result
        ]
    
    async def _get_period_comparison(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
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
            change_percentage = ((current_sales - previous_sales) / previous_sales) * 100
        else:
            change_percentage = 0
        
        trend = "up" if change_percentage > 0 else "down" if change_percentage < 0 else "stable"
        
        return {
            "current_period": float(current_sales),
            "previous_period": float(previous_sales),
            "change_percentage": float(change_percentage),
            "trend": trend
        }
    
    async def create_sale(
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
```

---

## 🎯 **Phase 2: Inventory Management Backend (Weeks 3-4)**

### **2.1 Inventory Models**

#### **File: `app/models/inventory.py`**
```python
from sqlalchemy import Column, Integer, String, DateTime, Decimal, ForeignKey, JSON, Boolean, Text
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
from decimal import Decimal

class Location(Base):
    __tablename__ = "locations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    address = Column(Text)
    location_type = Column(String(50), default="store")  # store, warehouse, vault
    active = Column(Boolean, default=True)
    settings = Column(JSON)  # Location-specific settings
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    inventory_items = relationship("InventoryItem", back_populates="location")

class InventoryItem(Base):
    __tablename__ = "inventory_items"
    
    id = Column(Integer, primary_key=True, index=True)
    coin_id = Column(Integer, ForeignKey("coins.id"), nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    
    # Inventory details
    quantity = Column(Integer, nullable=False, default=1)
    reserved_quantity = Column(Integer, default=0)  # Reserved for pending sales
    available_quantity = Column(Integer, nullable=False)  # Calculated field
    
    # Tracking
    last_counted = Column(DateTime)
    last_moved = Column(DateTime)
    notes = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    coin = relationship("Coin", back_populates="inventory_items")
    location = relationship("Location", back_populates="inventory_items")

class InventoryMovement(Base):
    __tablename__ = "inventory_movements"
    
    id = Column(Integer, primary_key=True, index=True)
    coin_id = Column(Integer, ForeignKey("coins.id"), nullable=False)
    from_location_id = Column(Integer, ForeignKey("locations.id"))
    to_location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    
    # Movement details
    quantity = Column(Integer, nullable=False)
    movement_type = Column(String(50), nullable=False)  # transfer, sale, adjustment, count
    reason = Column(String(200))
    reference_id = Column(String(100))  # Reference to sale, order, etc.
    
    # User tracking
    moved_by = Column(String(100))  # User who performed the movement
    
    # Timestamps
    moved_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    coin = relationship("Coin")
    from_location = relationship("Location", foreign_keys=[from_location_id])
    to_location = relationship("Location", foreign_keys=[to_location_id])

class DeadStockAnalysis(Base):
    __tablename__ = "dead_stock_analysis"
    
    id = Column(Integer, primary_key=True, index=True)
    coin_id = Column(Integer, ForeignKey("coins.id"), nullable=False)
    
    # Analysis criteria
    days_since_last_sale = Column(Integer)
    days_since_added = Column(Integer)
    profit_margin = Column(Decimal(5, 2))
    category = Column(String(50))  # slow_moving, dead_stock, fast_moving
    
    # Analysis metadata
    analysis_date = Column(DateTime, default=datetime.utcnow)
    criteria_used = Column(JSON)  # Criteria used for classification
    
    # Relationships
    coin = relationship("Coin")
```

### **2.2 Inventory API Endpoints**

#### **File: `app/routers/inventory.py`**
```python
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date, timedelta

from app.database import get_db
from app.models.inventory import Location, InventoryItem, InventoryMovement, DeadStockAnalysis
from app.models.coins import Coin
from app.schemas.inventory import (
    LocationCreate, LocationResponse, InventoryMetricsResponse,
    InventoryMovementCreate, DeadStockResponse
)
from app.services.inventory_service import InventoryService
from app.auth import get_current_admin_user

router = APIRouter(prefix="/inventory", tags=["inventory"])

@router.get("/metrics", response_model=InventoryMetricsResponse)
async def get_inventory_metrics(
    location: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Get comprehensive inventory metrics"""
    
    inventory_service = InventoryService(db)
    
    metrics = await inventory_service.get_inventory_metrics(
        location_filter=location,
        category_filter=category
    )
    
    return metrics

@router.get("/dead-stock", response_model=List[DeadStockResponse])
async def get_dead_stock(
    category: Optional[str] = Query("dead_stock"),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Get dead stock analysis"""
    
    inventory_service = InventoryService(db)
    
    dead_stock = await inventory_service.get_dead_stock_analysis(
        category=category,
        limit=limit
    )
    
    return dead_stock

@router.get("/profit-margins")
async def get_profit_margin_analysis(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Analyze profit margins by category"""
    
    inventory_service = InventoryService(db)
    
    margin_analysis = await inventory_service.get_profit_margin_analysis()
    
    return margin_analysis

@router.get("/locations", response_model=List[LocationResponse])
async def get_locations(
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Get all locations"""
    
    query = db.query(Location)
    if active_only:
        query = query.filter(Location.active == True)
    
    locations = query.all()
    return locations

@router.post("/locations", response_model=LocationResponse)
async def create_location(
    location_data: LocationCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Create a new location"""
    
    # Check if location name already exists
    existing = db.query(Location).filter(
        Location.name == location_data.name
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Location name already exists")
    
    location = Location(
        name=location_data.name,
        address=location_data.address,
        location_type=location_data.location_type,
        settings=location_data.settings
    )
    
    db.add(location)
    db.commit()
    db.refresh(location)
    
    return location

@router.post("/movements")
async def create_inventory_movement(
    movement_data: InventoryMovementCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Create an inventory movement"""
    
    inventory_service = InventoryService(db)
    
    movement = await inventory_service.create_movement(
        coin_id=movement_data.coin_id,
        from_location_id=movement_data.from_location_id,
        to_location_id=movement_data.to_location_id,
        quantity=movement_data.quantity,
        movement_type=movement_data.movement_type,
        reason=movement_data.reason,
        reference_id=movement_data.reference_id,
        moved_by=current_user.username
    )
    
    return movement

@router.get("/turnover-analysis")
async def get_turnover_analysis(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Get inventory turnover analysis"""
    
    inventory_service = InventoryService(db)
    
    turnover_data = await inventory_service.get_turnover_analysis()
    
    return turnover_data
```

---

## 🎯 **Phase 3: Financial Management Backend (Weeks 5-6)**

### **3.1 Financial Models**

#### **File: `app/models/financial.py`**
```python
from sqlalchemy import Column, Integer, String, DateTime, Decimal, ForeignKey, JSON, Boolean, Text
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime, date
from decimal import Decimal

class FinancialPeriod(Base):
    __tablename__ = "financial_periods"
    
    id = Column(Integer, primary_key=True, index=True)
    period_type = Column(String(20), nullable=False)  # daily, weekly, monthly, quarterly, yearly
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    
    # Revenue breakdown
    total_revenue = Column(Decimal(12, 2), default=Decimal('0'))
    sales_revenue = Column(Decimal(12, 2), default=Decimal('0'))
    other_revenue = Column(Decimal(12, 2), default=Decimal('0'))
    
    # Cost breakdown
    cost_of_goods = Column(Decimal(12, 2), default=Decimal('0'))
    operating_expenses = Column(Decimal(12, 2), default=Decimal('0'))
    other_expenses = Column(Decimal(12, 2), default=Decimal('0'))
    
    # Calculated fields
    gross_profit = Column(Decimal(12, 2), default=Decimal('0'))
    net_profit = Column(Decimal(12, 2), default=Decimal('0'))
    profit_margin = Column(Decimal(5, 2), default=Decimal('0'))
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Additional data
    notes = Column(Text)
    adjustments = Column(JSON)  # Manual adjustments

class CashFlow(Base):
    __tablename__ = "cash_flow"
    
    id = Column(Integer, primary_key=True, index=True)
    period_id = Column(Integer, ForeignKey("financial_periods.id"))
    
    # Cash flow categories
    operating_cash_flow = Column(Decimal(12, 2), default=Decimal('0'))
    investing_cash_flow = Column(Decimal(12, 2), default=Decimal('0'))
    financing_cash_flow = Column(Decimal(12, 2), default=Decimal('0'))
    
    # Calculated fields
    net_cash_flow = Column(Decimal(12, 2), default=Decimal('0'))
    beginning_cash = Column(Decimal(12, 2), default=Decimal('0'))
    ending_cash = Column(Decimal(12, 2), default=Decimal('0'))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    period = relationship("FinancialPeriod")

class PricingStrategy(Base):
    __tablename__ = "pricing_strategies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    strategy_type = Column(String(50), nullable=False)  # spot_plus_percentage, profit_margin_target, competitive
    
    # Strategy parameters
    base_multiplier = Column(Decimal(5, 2))  # e.g., 1.30 for 30% over spot
    min_profit_margin = Column(Decimal(5, 2))  # e.g., 0.20 for 20% minimum
    max_profit_margin = Column(Decimal(5, 2))  # e.g., 0.60 for 60% maximum
    
    # Category overrides
    category_overrides = Column(JSON)  # Different strategies per category
    
    # Active status
    active = Column(Boolean, default=True)
    applied_at = Column(DateTime)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))
    
    # Relationships
    pricing_updates = relationship("PricingUpdate", back_populates="strategy")

class PricingUpdate(Base):
    __tablename__ = "pricing_updates"
    
    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("pricing_strategies.id"))
    coin_id = Column(Integer, ForeignKey("coins.id"))
    
    # Price changes
    old_price = Column(Decimal(10, 2))
    new_price = Column(Decimal(10, 2))
    price_change = Column(Decimal(10, 2))
    change_percentage = Column(Decimal(5, 2))
    
    # Update metadata
    update_reason = Column(String(200))
    applied_at = Column(DateTime, default=datetime.utcnow)
    applied_by = Column(String(100))
    
    # Relationships
    strategy = relationship("PricingStrategy", back_populates="pricing_updates")
    coin = relationship("Coin")
```

### **3.2 Financial API Endpoints**

#### **File: `app/routers/financial.py`**
```python
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date, timedelta
from decimal import Decimal

from app.database import get_db
from app.models.financial import FinancialPeriod, CashFlow, PricingStrategy, PricingUpdate
from app.schemas.financial import (
    FinancialPeriodCreate, FinancialPeriodResponse, CashFlowResponse,
    PricingStrategyCreate, PricingStrategyResponse, PLStatementResponse
)
from app.services.financial_service import FinancialService
from app.services.pricing_service import PricingService
from app.auth import get_current_admin_user

router = APIRouter(prefix="/financial", tags=["financial"])

@router.get("/p-l", response_model=PLStatementResponse)
async def get_p_l_statement(
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Generate P&L statement for period"""
    
    financial_service = FinancialService(db)
    
    pl_statement = await financial_service.generate_p_l_statement(
        start_date=start_date,
        end_date=end_date
    )
    
    return pl_statement

@router.get("/cash-flow", response_model=List[CashFlowResponse])
async def get_cash_flow_analysis(
    period_type: str = Query("monthly", regex="^(daily|weekly|monthly|quarterly|yearly)$"),
    months: int = Query(12, le=24),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Get cash flow analysis"""
    
    financial_service = FinancialService(db)
    
    end_date = date.today()
    start_date = end_date - timedelta(days=months * 30)
    
    cash_flow_data = await financial_service.get_cash_flow_analysis(
        start_date=start_date,
        end_date=end_date,
        period_type=period_type
    )
    
    return cash_flow_data

@router.post("/pricing/strategy", response_model=PricingStrategyResponse)
async def create_pricing_strategy(
    strategy_data: PricingStrategyCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Create a new pricing strategy"""
    
    pricing_service = PricingService(db)
    
    strategy = await pricing_service.create_strategy(
        name=strategy_data.name,
        strategy_type=strategy_data.strategy_type,
        base_multiplier=strategy_data.base_multiplier,
        min_profit_margin=strategy_data.min_profit_margin,
        max_profit_margin=strategy_data.max_profit_margin,
        category_overrides=strategy_data.category_overrides,
        created_by=current_user.username
    )
    
    return strategy

@router.post("/pricing/apply-strategy")
async def apply_pricing_strategy(
    strategy_id: int,
    coin_ids: Optional[List[int]] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Apply pricing strategy to coins"""
    
    pricing_service = PricingService(db)
    
    result = await pricing_service.apply_strategy(
        strategy_id=strategy_id,
        coin_ids=coin_ids,
        applied_by=current_user.username
    )
    
    return result

@router.get("/pricing/strategies", response_model=List[PricingStrategyResponse])
async def get_pricing_strategies(
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Get all pricing strategies"""
    
    query = db.query(PricingStrategy)
    if active_only:
        query = query.filter(PricingStrategy.active == True)
    
    strategies = query.all()
    return strategies

@router.get("/periods", response_model=List[FinancialPeriodResponse])
async def get_financial_periods(
    period_type: Optional[str] = Query(None),
    limit: int = Query(12, le=50),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Get financial periods"""
    
    query = db.query(FinancialPeriod)
    
    if period_type:
        query = query.filter(FinancialPeriod.period_type == period_type)
    
    periods = query.order_by(FinancialPeriod.end_date.desc()).limit(limit).all()
    return periods

@router.post("/periods", response_model=FinancialPeriodResponse)
async def create_financial_period(
    period_data: FinancialPeriodCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Create a financial period"""
    
    financial_service = FinancialService(db)
    
    period = await financial_service.create_period(
        period_type=period_data.period_type,
        start_date=period_data.start_date,
        end_date=period_data.end_date,
        notes=period_data.notes
    )
    
    return period
```

---

## 🎯 **Phase 4: Alert System Backend (Weeks 7-8)**

### **4.1 Alert Models**

#### **File: `app/models/alerts.py`**
```python
from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime

class AlertRule(Base):
    __tablename__ = "alert_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    alert_type = Column(String(50), nullable=False)  # low_inventory, price_change, system_issue, sales_milestone
    
    # Rule conditions
    conditions = Column(JSON, nullable=False)  # Array of condition objects
    product_specific = Column(Boolean, default=False)
    product_id = Column(Integer, ForeignKey("coins.id"))
    
    # Alert actions
    actions = Column(JSON, nullable=False)  # Array of action objects
    
    # Rule status
    enabled = Column(Boolean, default=True)
    last_triggered = Column(DateTime)
    trigger_count = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    alerts = relationship("Alert", back_populates="rule")
    product = relationship("Coin")

class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, ForeignKey("alert_rules.id"), nullable=False)
    
    # Alert details
    message = Column(Text, nullable=False)
    severity = Column(String(20), default="medium")  # low, medium, high, critical
    alert_data = Column(JSON)  # Additional data about the alert
    
    # Status tracking
    status = Column(String(20), default="active")  # active, acknowledged, resolved
    acknowledged_at = Column(DateTime)
    acknowledged_by = Column(String(100))
    resolved_at = Column(DateTime)
    resolved_by = Column(String(100))
    
    # Timestamps
    triggered_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    rule = relationship("AlertRule", back_populates="alerts")

class AlertAction(Base):
    __tablename__ = "alert_actions"
    
    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("alerts.id"), nullable=False)
    
    # Action details
    action_type = Column(String(50), nullable=False)  # notification, email, webhook, sms
    target = Column(String(200), nullable=False)  # Email, phone, webhook URL
    message_template = Column(Text)
    
    # Execution tracking
    status = Column(String(20), default="pending")  # pending, sent, failed, retrying
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    last_attempt = Column(DateTime)
    error_message = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # Relationships
    alert = relationship("Alert")
```

### **4.2 Alert Service**

#### **File: `app/services/alert_service.py`**
```python
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
import logging

from app.models.alerts import AlertRule, Alert, AlertAction
from app.models.coins import Coin
from app.models.sales import Sale
from app.models.inventory import InventoryItem

logger = logging.getLogger(__name__)

class AlertService:
    def __init__(self, db: Session):
        self.db = db
    
    async def check_all_rules(self):
        """Check all enabled alert rules"""
        
        rules = self.db.query(AlertRule).filter(AlertRule.enabled == True).all()
        
        for rule in rules:
            try:
                await self._check_rule(rule)
            except Exception as e:
                logger.error(f"Error checking rule {rule.id}: {str(e)}")
    
    async def _check_rule(self, rule: AlertRule):
        """Check a specific alert rule"""
        
        if rule.alert_type == "low_inventory":
            await self._check_low_inventory_rule(rule)
        elif rule.alert_type == "price_change":
            await self._check_price_change_rule(rule)
        elif rule.alert_type == "system_issue":
            await self._check_system_issue_rule(rule)
        elif rule.alert_type == "sales_milestone":
            await self._check_sales_milestone_rule(rule)
    
    async def _check_low_inventory_rule(self, rule: AlertRule):
        """Check low inventory alert rule"""
        
        conditions = rule.conditions
        
        for condition in conditions:
            field = condition.get("field")
            operator = condition.get("operator")
            value = condition.get("value")
            
            if field == "quantity":
                query = self.db.query(Coin).join(InventoryItem)
                
                if rule.product_specific and rule.product_id:
                    query = query.filter(Coin.id == rule.product_id)
                
                if operator == "lt":
                    coins = query.filter(InventoryItem.available_quantity < value).all()
                elif operator == "lte":
                    coins = query.filter(InventoryItem.available_quantity <= value).all()
                
                if coins:
                    await self._trigger_alert(rule, {
                        "message": f"Low inventory alert: {len(coins)} items below threshold",
                        "affected_items": [{"id": coin.id, "title": coin.title, "quantity": coin.inventory_items[0].available_quantity} for coin in coins],
                        "threshold": value
                    })
    
    async def _check_price_change_rule(self, rule: AlertRule):
        """Check price change alert rule"""
        
        # This would check for significant price changes
        # Implementation depends on how price changes are tracked
        pass
    
    async def _check_system_issue_rule(self, rule: AlertRule):
        """Check system issue alert rule"""
        
        # This would check for system health issues
        # Implementation depends on system monitoring setup
        pass
    
    async def _check_sales_milestone_rule(self, rule: AlertRule):
        """Check sales milestone alert rule"""
        
        conditions = rule.conditions
        
        for condition in conditions:
            field = condition.get("field")
            operator = condition.get("operator")
            value = condition.get("value")
            
            if field == "daily_sales":
                today = datetime.utcnow().date()
                sales_today = self.db.query(Sale).filter(
                    Sale.sold_at >= today
                ).count()
                
                if operator == "gte" and sales_today >= value:
                    await self._trigger_alert(rule, {
                        "message": f"Sales milestone reached: ${sales_today} in sales today",
                        "milestone": value,
                        "actual_sales": sales_today
                    })
    
    async def _trigger_alert(self, rule: AlertRule, alert_data: Dict[str, Any]):
        """Trigger an alert for a rule"""
        
        # Create alert record
        alert = Alert(
            rule_id=rule.id,
            message=alert_data.get("message", "Alert triggered"),
            alert_data=alert_data,
            severity=alert_data.get("severity", "medium")
        )
        
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)
        
        # Execute alert actions
        await self._execute_alert_actions(alert, rule.actions)
        
        # Update rule statistics
        rule.last_triggered = datetime.utcnow()
        rule.trigger_count += 1
        self.db.commit()
    
    async def _execute_alert_actions(self, alert: Alert, actions: List[Dict[str, Any]]):
        """Execute alert actions"""
        
        for action_config in actions:
            action = AlertAction(
                alert_id=alert.id,
                action_type=action_config.get("type"),
                target=action_config.get("target"),
                message_template=action_config.get("message_template")
            )
            
            self.db.add(action)
            self.db.commit()
            
            # Execute the action (this would be handled by a background task)
            # For now, just mark as pending
            action.status = "pending"
            self.db.commit()
    
    async def get_active_alerts(self, limit: int = 50) -> List[Alert]:
        """Get active alerts"""
        
        return self.db.query(Alert).filter(
            Alert.status == "active"
        ).order_by(Alert.triggered_at.desc()).limit(limit).all()
    
    async def acknowledge_alert(self, alert_id: int, acknowledged_by: str):
        """Acknowledge an alert"""
        
        alert = self.db.query(Alert).filter(Alert.id == alert_id).first()
        if alert:
            alert.status = "acknowledged"
            alert.acknowledged_at = datetime.utcnow()
            alert.acknowledged_by = acknowledged_by
            self.db.commit()
    
    async def resolve_alert(self, alert_id: int, resolved_by: str):
        """Resolve an alert"""
        
        alert = self.db.query(Alert).filter(Alert.id == alert_id).first()
        if alert:
            alert.status = "resolved"
            alert.resolved_at = datetime.utcnow()
            alert.resolved_by = resolved_by
            self.db.commit()
```

---

## 🎯 **Phase 5: Shopify Integration Backend (Weeks 9-10)**

### **5.1 Shopify Integration Service**

#### **File: `app/services/shopify_service.py`**
```python
import httpx
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from app.core.config import settings
from app.models.coins import Coin
from app.models.sales import Sale, SalesChannel

logger = logging.getLogger(__name__)

class ShopifyService:
    def __init__(self):
        self.shopify_url = settings.SHOPIFY_STORE_URL
        self.access_token = settings.SHOPIFY_ACCESS_TOKEN
        self.api_version = "2023-10"
        
        self.client = httpx.AsyncClient(
            base_url=f"{self.shopify_url}/admin/api/{self.api_version}",
            headers={
                "X-Shopify-Access-Token": self.access_token,
                "Content-Type": "application/json"
            },
            timeout=30.0
        )
    
    async def sync_products_to_shopify(self, coin_ids: Optional[List[int]] = None):
        """Sync coins to Shopify products"""
        
        if coin_ids:
            coins = self.db.query(Coin).filter(Coin.id.in_(coin_ids)).all()
        else:
            coins = self.db.query(Coin).filter(Coin.status == "active").all()
        
        results = {
            "created": 0,
            "updated": 0,
            "errors": []
        }
        
        for coin in coins:
            try:
                product_data = await self._create_product_data(coin)
                
                # Check if product already exists in Shopify
                existing_product = await self._find_product_by_sku(coin.sku)
                
                if existing_product:
                    # Update existing product
                    await self._update_product(existing_product["id"], product_data)
                    results["updated"] += 1
                else:
                    # Create new product
                    await self._create_product(product_data)
                    results["created"] += 1
                    
            except Exception as e:
                logger.error(f"Error syncing coin {coin.id}: {str(e)}")
                results["errors"].append({
                    "coin_id": coin.id,
                    "error": str(e)
                })
        
        return results
    
    async def _create_product_data(self, coin: Coin) -> Dict[str, Any]:
        """Create Shopify product data from coin"""
        
        # Calculate pricing
        price = coin.computed_price or coin.paid_price or 0
        
        # Create product title
        title_parts = [coin.title]
        if coin.year:
            title_parts.append(str(coin.year))
        if coin.denomination:
            title_parts.append(coin.denomination)
        if coin.grade:
            title_parts.append(f"Grade {coin.grade}")
        
        title = " ".join(title_parts)
        
        # Create description
        description_parts = [f"<p><strong>{coin.title}</strong></p>"]
        
        if coin.year:
            description_parts.append(f"<p>Year: {coin.year}</p>")
        if coin.denomination:
            description_parts.append(f"<p>Denomination: {coin.denomination}</p>")
        if coin.grade:
            description_parts.append(f"<p>Grade: {coin.grade}</p>")
        if coin.mint_mark:
            description_parts.append(f"<p>Mint Mark: {coin.mint_mark}</p>")
        if coin.is_silver and coin.silver_content_oz:
            description_parts.append(f"<p>Silver Content: {coin.silver_content_oz} oz</p>")
        
        if coin.ai_notes:
            description_parts.append(f"<p><strong>AI Analysis:</strong></p><p>{coin.ai_notes}</p>")
        
        description = "".join(description_parts)
        
        # Create tags
        tags = ["coin", "numismatics"]
        if coin.is_silver:
            tags.append("silver")
        if coin.category:
            tags.append(coin.category)
        if coin.year:
            tags.append(f"year-{coin.year}")
        
        return {
            "product": {
                "title": title,
                "body_html": description,
                "vendor": "Miracle Coins",
                "product_type": "Coins",
                "tags": ", ".join(tags),
                "variants": [{
                    "price": str(price),
                    "sku": coin.sku or f"MC-{coin.id}",
                    "inventory_quantity": coin.quantity,
                    "inventory_management": "shopify",
                    "requires_shipping": True,
                    "weight": coin.silver_content_oz or 0.1,
                    "weight_unit": "oz"
                }],
                "metafields": [
                    {
                        "namespace": "miracle_coins",
                        "key": "coin_id",
                        "value": str(coin.id),
                        "type": "single_line_text_field"
                    },
                    {
                        "namespace": "miracle_coins",
                        "key": "paid_price",
                        "value": str(coin.paid_price or 0),
                        "type": "money"
                    },
                    {
                        "namespace": "miracle_coins",
                        "key": "profit_margin",
                        "value": str(self._calculate_profit_margin(coin)),
                        "type": "number_decimal"
                    }
                ]
            }
        }
    
    async def sync_orders_from_shopify(self):
        """Sync orders from Shopify"""
        
        # Get recent orders from Shopify
        response = await self.client.get("/orders.json", params={
            "status": "any",
            "created_at_min": (datetime.utcnow() - timedelta(days=7)).isoformat(),
            "limit": 250
        })
        
        orders = response.json()["orders"]
        results = {
            "processed": 0,
            "created": 0,
            "errors": []
        }
        
        for order in orders:
            try:
                await self._process_shopify_order(order)
                results["processed"] += 1
            except Exception as e:
                logger.error(f"Error processing order {order['id']}: {str(e)}")
                results["errors"].append({
                    "order_id": order["id"],
                    "error": str(e)
                })
        
        return results
    
    async def _process_shopify_order(self, order: Dict[str, Any]):
        """Process a Shopify order"""
        
        # Get or create Shopify sales channel
        shopify_channel = self.db.query(SalesChannel).filter(
            SalesChannel.name == "shopify"
        ).first()
        
        if not shopify_channel:
            shopify_channel = SalesChannel(
                name="shopify",
                channel_type="shopify",
                settings={"webhook_url": f"{settings.API_URL}/webhooks/shopify"}
            )
            self.db.add(shopify_channel)
            self.db.commit()
        
        # Process each line item
        for line_item in order["line_items"]:
            # Find coin by SKU
            coin = self.db.query(Coin).filter(Coin.sku == line_item["sku"]).first()
            
            if coin:
                # Create sale record
                sale = Sale(
                    coin_id=coin.id,
                    channel_id=shopify_channel.id,
                    sale_price=float(line_item["price"]),
                    profit=float(line_item["price"]) - (coin.paid_price or 0),
                    quantity_sold=line_item["quantity"],
                    customer_info={
                        "email": order["customer"]["email"],
                        "name": f"{order['customer']['first_name']} {order['customer']['last_name']}",
                        "phone": order["customer"]["phone"]
                    },
                    transaction_id=str(order["id"])
                )
                
                self.db.add(sale)
                
                # Update coin status
                coin.quantity -= line_item["quantity"]
                if coin.quantity <= 0:
                    coin.status = "sold"
        
        self.db.commit()
    
    async def sync_inventory_with_shopify(self):
        """Sync inventory levels with Shopify"""
        
        # Get all products from Shopify
        response = await self.client.get("/products.json", params={"limit": 250})
        products = response.json()["products"]
        
        results = {
            "updated": 0,
            "errors": []
        }
        
        for product in products:
            try:
                # Find coin by SKU
                sku = product["variants"][0]["sku"]
                coin = self.db.query(Coin).filter(Coin.sku == sku).first()
                
                if coin:
                    # Update Shopify inventory
                    variant_id = product["variants"][0]["id"]
                    await self.client.put(f"/variants/{variant_id}.json", json={
                        "variant": {
                            "id": variant_id,
                            "inventory_quantity": coin.quantity
                        }
                    })
                    results["updated"] += 1
                    
            except Exception as e:
                logger.error(f"Error updating inventory for product {product['id']}: {str(e)}")
                results["errors"].append({
                    "product_id": product["id"],
                    "error": str(e)
                })
        
        return results
    
    async def sync_pricing_to_shopify(self):
        """Sync AI pricing to Shopify"""
        
        # Get coins with updated pricing
        coins = self.db.query(Coin).filter(
            Coin.status == "active",
            Coin.computed_price.isnot(None)
        ).all()
        
        results = {
            "updated": 0,
            "errors": []
        }
        
        for coin in coins:
            try:
                # Find Shopify product
                product = await self._find_product_by_sku(coin.sku)
                
                if product:
                    # Update price
                    variant_id = product["variants"][0]["id"]
                    await self.client.put(f"/variants/{variant_id}.json", json={
                        "variant": {
                            "id": variant_id,
                            "price": str(coin.computed_price)
                        }
                    })
                    results["updated"] += 1
                    
            except Exception as e:
                logger.error(f"Error updating price for coin {coin.id}: {str(e)}")
                results["errors"].append({
                    "coin_id": coin.id,
                    "error": str(e)
                })
        
        return results
    
    async def _find_product_by_sku(self, sku: str) -> Optional[Dict[str, Any]]:
        """Find Shopify product by SKU"""
        
        response = await self.client.get("/products.json", params={
            "fields": "id,title,variants",
            "limit": 250
        })
        
        products = response.json()["products"]
        
        for product in products:
            for variant in product["variants"]:
                if variant["sku"] == sku:
                    return product
        
        return None
    
    def _calculate_profit_margin(self, coin: Coin) -> float:
        """Calculate profit margin for coin"""
        
        if not coin.paid_price or not coin.computed_price:
            return 0.0
        
        profit = coin.computed_price - coin.paid_price
        return (profit / coin.paid_price) * 100
```

This comprehensive backend implementation plan provides all the necessary APIs, services, and database models to support your frontend requirements. Each service is designed to be scalable, maintainable, and performant for your 5-10k coin inventory.

The backend follows FastAPI best practices with proper error handling, authentication, and documentation. All endpoints are designed to work seamlessly with the frontend components we planned earlier.

Would you like me to continue with any specific part of the implementation or create additional services for specific features?


