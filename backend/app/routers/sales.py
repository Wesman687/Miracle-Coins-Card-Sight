from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date, timedelta
from decimal import Decimal

from app.database import get_db
from app.models.sales import Sale, SalesChannel, SalesForecast
from app.models import Coin
from app.schemas.sales import (
    SaleCreate, SaleResponse, SalesChannelCreate, SalesChannelResponse,
    SalesForecastRequest, SalesForecastResponse, SalesDashboardResponse,
    SalesMetricsRequest, SalesMetricsResponse
)
from app.services.sales_service import SalesService
from app.services.forecast_service import ForecastService
from app.auth import get_current_admin_user

router = APIRouter(prefix="/sales", tags=["sales"])

@router.get("/dashboard", response_model=SalesDashboardResponse)
async def get_sales_dashboard(
    period: str = Query("daily", pattern="^(daily|weekly|monthly)$"),
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
    
    try:
        forecast_data = await forecast_service.generate_forecast(
            time_period=forecast_request.time_period,
            horizon=forecast_request.forecast_horizon,
            confidence_level=forecast_request.confidence_level,
            include_seasonality=forecast_request.include_seasonality,
            include_trends=forecast_request.include_trends,
            include_external_factors=forecast_request.include_external_factors
        )
        
        return forecast_data
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to generate forecast")

@router.get("/by-channel")
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
    
    # Validate channel exists
    channel = db.query(SalesChannel).filter(SalesChannel.id == sale_data.channel_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Sales channel not found")
    
    if not channel.active:
        raise HTTPException(status_code=400, detail="Sales channel is not active")
    
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
    
    # Update coin status and quantity
    coin.quantity -= sale_data.quantity_sold
    if coin.quantity <= 0:
        coin.status = "sold"
    
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

@router.put("/channels/{channel_id}", response_model=SalesChannelResponse)
async def update_sales_channel(
    channel_id: int,
    channel_data: SalesChannelCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Update a sales channel"""
    
    channel = db.query(SalesChannel).filter(SalesChannel.id == channel_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    # Check if new name conflicts with existing channel
    if channel_data.name != channel.name:
        existing = db.query(SalesChannel).filter(
            SalesChannel.name == channel_data.name,
            SalesChannel.id != channel_id
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="Channel name already exists")
    
    # Update channel
    channel.name = channel_data.name
    channel.channel_type = channel_data.channel_type
    channel.settings = channel_data.settings
    channel.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(channel)
    
    return channel

@router.delete("/channels/{channel_id}")
async def delete_sales_channel(
    channel_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Delete a sales channel (soft delete by deactivating)"""
    
    channel = db.query(SalesChannel).filter(SalesChannel.id == channel_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    # Check if channel has sales
    sales_count = db.query(Sale).filter(Sale.channel_id == channel_id).count()
    if sales_count > 0:
        # Soft delete by deactivating
        channel.active = False
        channel.updated_at = datetime.utcnow()
        db.commit()
        return {"message": "Channel deactivated (has existing sales)"}
    
    # Hard delete if no sales
    db.delete(channel)
    db.commit()
    
    return {"message": "Channel deleted successfully"}

@router.get("/metrics", response_model=List[SalesMetricsResponse])
async def get_sales_metrics(
    period_type: str = Query("daily", pattern="^(daily|weekly|monthly)$"),
    limit: int = Query(30, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Get historical sales metrics"""
    
    from app.models.sales import SalesMetrics
    
    metrics = db.query(SalesMetrics).filter(
        SalesMetrics.period_type == period_type
    ).order_by(SalesMetrics.period_end.desc()).limit(limit).all()
    
    return metrics

@router.post("/metrics/calculate")
async def calculate_sales_metrics(
    metrics_request: SalesMetricsRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Calculate and store sales metrics for a specific period"""
    
    sales_service = SalesService(db)
    
    metrics = await sales_service.calculate_sales_metrics(
        start_date=metrics_request.start_date,
        end_date=metrics_request.end_date,
        period_type=metrics_request.period_type
    )
    
    return metrics

@router.get("/forecasts", response_model=List[SalesForecastResponse])
async def get_sales_forecasts(
    forecast_type: Optional[str] = Query(None, regex="^(daily|weekly|monthly|quarterly|yearly)$"),
    limit: int = Query(10, le=50),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Get recent sales forecasts"""
    
    query = db.query(SalesForecast)
    
    if forecast_type:
        query = query.filter(SalesForecast.forecast_type == forecast_type)
    
    forecasts = query.order_by(SalesForecast.created_at.desc()).limit(limit).all()
    
    return forecasts

@router.get("/forecasts/{forecast_id}", response_model=SalesForecastResponse)
async def get_sales_forecast(
    forecast_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Get a specific sales forecast"""
    
    forecast = db.query(SalesForecast).filter(SalesForecast.id == forecast_id).first()
    if not forecast:
        raise HTTPException(status_code=404, detail="Forecast not found")
    
    return forecast


