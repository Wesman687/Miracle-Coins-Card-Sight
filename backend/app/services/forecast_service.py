from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from decimal import Decimal
import logging
import statistics

from app.models.sales import Sale, SalesForecast, ForecastPeriod
from app.schemas.sales import (
    SalesForecastRequest, SalesForecastResponse, 
    ForecastPeriodData, ForecastFactor
)

logger = logging.getLogger(__name__)

class ForecastService:
    def __init__(self, db: Session):
        self.db = db
    
    def generate_forecast(
        self,
        time_period: str,
        horizon: int,
        confidence_level: int,
        include_seasonality: bool = True,
        include_trends: bool = True,
        include_external_factors: bool = False
    ) -> SalesForecastResponse:
        """Generate revenue forecast based on historical data"""
        
        # Get historical data
        historical_data = self._get_historical_data(time_period)
        
        if not historical_data:
            raise ValueError("Insufficient historical data for forecasting")
        
        # Calculate forecast periods
        forecast_periods = self._calculate_forecast_periods(
            historical_data, time_period, horizon, confidence_level,
            include_seasonality, include_trends, include_external_factors
        )
        
        # Calculate accuracy score based on historical performance
        accuracy_score = self._calculate_accuracy_score(historical_data, time_period)
        
        # Create forecast record
        forecast = SalesForecast(
            forecast_type=time_period,
            forecast_horizon=horizon,
            confidence_level=confidence_level,
            forecast_data=[fp.dict() for fp in forecast_periods],
            factors_used=self._get_factors_used(include_seasonality, include_trends, include_external_factors),
            accuracy_score=accuracy_score,
            include_seasonality=include_seasonality,
            include_trends=include_trends,
            include_external_factors=include_external_factors,
            valid_until=datetime.utcnow() + timedelta(days=7)  # Forecast valid for 7 days
        )
        
        self.db.add(forecast)
        self.db.commit()
        self.db.refresh(forecast)
        
        return SalesForecastResponse(
            forecast_type=forecast.forecast_type,
            forecast_horizon=forecast.forecast_horizon,
            confidence_level=forecast.confidence_level,
            forecast_data=forecast_periods,
            accuracy_score=forecast.accuracy_score,
            created_at=forecast.created_at,
            valid_until=forecast.valid_until
        )
    
    def _get_historical_data(self, time_period: str) -> List[Dict[str, Any]]:
        """Get historical sales data for the specified time period"""
        
        # Determine lookback period based on forecast type
        lookback_days = {
            "daily": 90,      # 3 months
            "weekly": 365,    # 1 year
            "monthly": 1095,  # 3 years
            "quarterly": 1825, # 5 years
            "yearly": 3650    # 10 years
        }
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=lookback_days.get(time_period, 365))
        
        # Group sales by time period
        if time_period == "daily":
            group_by = func.date(Sale.sold_at)
        elif time_period == "weekly":
            group_by = func.date_trunc('week', Sale.sold_at)
        elif time_period == "monthly":
            group_by = func.date_trunc('month', Sale.sold_at)
        elif time_period == "quarterly":
            group_by = func.date_trunc('quarter', Sale.sold_at)
        else:  # yearly
            group_by = func.date_trunc('year', Sale.sold_at)
        
        result = self.db.query(
            group_by.label('period'),
            func.sum(Sale.sale_price).label('revenue'),
            func.count(Sale.id).label('sales_count'),
            func.sum(Sale.profit).label('profit')
        ).filter(
            and_(
                Sale.sold_at >= start_date,
                Sale.sold_at <= end_date
            )
        ).group_by(group_by).order_by(group_by).all()
        
        return [
            {
                "period": row.period,
                "revenue": float(row.revenue),
                "sales_count": row.sales_count,
                "profit": float(row.profit)
            }
            for row in result
        ]
    
    def _calculate_forecast_periods(
        self,
        historical_data: List[Dict[str, Any]],
        time_period: str,
        horizon: int,
        confidence_level: int,
        include_seasonality: bool,
        include_trends: bool,
        include_external_factors: bool
    ) -> List[ForecastPeriodData]:
        """Calculate forecast periods using multiple algorithms"""
        
        if not historical_data:
            return []
        
        # Extract revenue values
        revenues = [data["revenue"] for data in historical_data]
        
        # Calculate base forecast using simple moving average
        base_forecast = self._calculate_moving_average_forecast(revenues, horizon)
        
        # Apply trend adjustment if enabled
        if include_trends:
            base_forecast = self._apply_trend_adjustment(base_forecast, revenues)
        
        # Apply seasonality adjustment if enabled
        if include_seasonality:
            base_forecast = self._apply_seasonality_adjustment(base_forecast, historical_data, time_period)
        
        # Calculate confidence intervals
        confidence_intervals = self._calculate_confidence_intervals(
            revenues, base_forecast, confidence_level
        )
        
        # Generate forecast periods
        forecast_periods = []
        current_date = datetime.utcnow()
        
        for i in range(horizon):
            # Calculate period dates
            if time_period == "daily":
                period_start = current_date + timedelta(days=i)
                period_end = period_start + timedelta(days=1)
                period_name = period_start.strftime("%Y-%m-%d")
            elif time_period == "weekly":
                period_start = current_date + timedelta(weeks=i)
                period_end = period_start + timedelta(weeks=1)
                period_name = f"Week {i+1}"
            elif time_period == "monthly":
                period_start = current_date + timedelta(days=30*i)
                period_end = period_start + timedelta(days=30)
                period_name = period_start.strftime("%B %Y")
            elif time_period == "quarterly":
                period_start = current_date + timedelta(days=90*i)
                period_end = period_start + timedelta(days=90)
                period_name = f"Q{i+1} {period_start.year}"
            else:  # yearly
                period_start = current_date + timedelta(days=365*i)
                period_end = period_start + timedelta(days=365)
                period_name = str(period_start.year)
            
            # Get forecast value
            predicted_revenue = Decimal(str(base_forecast[i])) if i < len(base_forecast) else Decimal('0')
            
            # Get confidence range
            confidence_range = confidence_intervals[i] if i < len(confidence_intervals) else {
                "min": predicted_revenue * Decimal('0.8'),
                "max": predicted_revenue * Decimal('1.2')
            }
            
            # Generate factors
            factors = self._generate_forecast_factors(
                predicted_revenue, include_seasonality, include_trends, include_external_factors
            )
            
            forecast_periods.append(ForecastPeriodData(
                period=period_name,
                predicted_revenue=predicted_revenue,
                confidence_range=confidence_range,
                factors=factors,
                accuracy_score=Decimal('85.0')  # Default accuracy score
            ))
        
        return forecast_periods
    
    def _calculate_moving_average_forecast(
        self, 
        revenues: List[float], 
        horizon: int
    ) -> List[float]:
        """Calculate forecast using moving average"""
        
        if len(revenues) < 3:
            # If insufficient data, use simple average
            avg_revenue = sum(revenues) / len(revenues) if revenues else 0
            return [avg_revenue] * horizon
        
        # Use last 3 periods for moving average
        window_size = min(3, len(revenues))
        recent_avg = sum(revenues[-window_size:]) / window_size
        
        # Apply slight growth trend based on recent performance
        if len(revenues) >= 2:
            recent_trend = (revenues[-1] - revenues[-2]) / revenues[-2] if revenues[-2] > 0 else 0
            growth_factor = 1 + (recent_trend * 0.1)  # Dampen the trend
        else:
            growth_factor = 1.0
        
        forecast = []
        for i in range(horizon):
            forecast_value = recent_avg * (growth_factor ** i)
            forecast.append(max(0, forecast_value))  # Ensure non-negative
        
        return forecast
    
    def _apply_trend_adjustment(
        self, 
        base_forecast: List[float], 
        revenues: List[float]
    ) -> List[float]:
        """Apply trend adjustment to forecast"""
        
        if len(revenues) < 2:
            return base_forecast
        
        # Calculate trend from recent data
        recent_data = revenues[-min(10, len(revenues)):]  # Use last 10 periods
        trend = statistics.mean([
            (recent_data[i] - recent_data[i-1]) / recent_data[i-1] 
            for i in range(1, len(recent_data)) 
            if recent_data[i-1] > 0
        ]) if len(recent_data) > 1 else 0
        
        # Apply trend adjustment
        adjusted_forecast = []
        for i, value in enumerate(base_forecast):
            trend_adjustment = 1 + (trend * (i + 1) * 0.1)  # Gradual trend application
            adjusted_forecast.append(value * trend_adjustment)
        
        return adjusted_forecast
    
    def _apply_seasonality_adjustment(
        self, 
        base_forecast: List[float], 
        historical_data: List[Dict[str, Any]], 
        time_period: str
    ) -> List[float]:
        """Apply seasonality adjustment to forecast"""
        
        if time_period not in ["monthly", "quarterly"]:
            return base_forecast  # Seasonality mainly applies to longer periods
        
        # Calculate seasonal patterns
        seasonal_factors = self._calculate_seasonal_factors(historical_data, time_period)
        
        # Apply seasonal adjustment
        adjusted_forecast = []
        for i, value in enumerate(base_forecast):
            seasonal_factor = seasonal_factors.get(i % len(seasonal_factors), 1.0)
            adjusted_forecast.append(value * seasonal_factor)
        
        return adjusted_forecast
    
    def _calculate_seasonal_factors(
        self, 
        historical_data: List[Dict[str, Any]], 
        time_period: str
    ) -> Dict[int, float]:
        """Calculate seasonal factors from historical data"""
        
        if time_period == "monthly":
            # Group by month
            monthly_data = {}
            for data in historical_data:
                month = data["period"].month
                if month not in monthly_data:
                    monthly_data[month] = []
                monthly_data[month].append(data["revenue"])
            
            # Calculate average for each month
            monthly_avg = {}
            overall_avg = sum(data["revenue"] for data in historical_data) / len(historical_data)
            
            for month in range(1, 13):
                if month in monthly_data:
                    monthly_avg[month] = sum(monthly_data[month]) / len(monthly_data[month])
                else:
                    monthly_avg[month] = overall_avg
            
            # Calculate seasonal factors
            seasonal_factors = {}
            for month in range(1, 13):
                seasonal_factors[month-1] = monthly_avg[month] / overall_avg if overall_avg > 0 else 1.0
            
            return seasonal_factors
        
        elif time_period == "quarterly":
            # Group by quarter
            quarterly_data = {}
            for data in historical_data:
                quarter = (data["period"].month - 1) // 3 + 1
                if quarter not in quarterly_data:
                    quarterly_data[quarter] = []
                quarterly_data[quarter].append(data["revenue"])
            
            # Calculate average for each quarter
            quarterly_avg = {}
            overall_avg = sum(data["revenue"] for data in historical_data) / len(historical_data)
            
            for quarter in range(1, 5):
                if quarter in quarterly_data:
                    quarterly_avg[quarter] = sum(quarterly_data[quarter]) / len(quarterly_data[quarter])
                else:
                    quarterly_avg[quarter] = overall_avg
            
            # Calculate seasonal factors
            seasonal_factors = {}
            for quarter in range(1, 5):
                seasonal_factors[quarter-1] = quarterly_avg[quarter] / overall_avg if overall_avg > 0 else 1.0
            
            return seasonal_factors
        
        return {}
    
    def _calculate_confidence_intervals(
        self, 
        revenues: List[float], 
        forecast: List[float], 
        confidence_level: int
    ) -> List[Dict[str, Decimal]]:
        """Calculate confidence intervals for forecast"""
        
        if not revenues:
            return []
        
        # Calculate historical volatility
        if len(revenues) > 1:
            returns = [(revenues[i] - revenues[i-1]) / revenues[i-1] 
                      for i in range(1, len(revenues)) if revenues[i-1] > 0]
            volatility = statistics.stdev(returns) if len(returns) > 1 else 0.1
        else:
            volatility = 0.1
        
        # Calculate confidence multiplier based on confidence level
        confidence_multipliers = {
            50: 0.67,
            60: 0.84,
            70: 1.04,
            80: 1.28,
            90: 1.64,
            95: 1.96
        }
        
        multiplier = confidence_multipliers.get(confidence_level, 1.28)
        
        intervals = []
        for value in forecast:
            margin = Decimal(str(value)) * Decimal(str(volatility)) * Decimal(str(multiplier))
            intervals.append({
                "min": Decimal(str(value)) - margin,
                "max": Decimal(str(value)) + margin
            })
        
        return intervals
    
    def _generate_forecast_factors(
        self, 
        predicted_revenue: Decimal, 
        include_seasonality: bool, 
        include_trends: bool, 
        include_external_factors: bool
    ) -> List[ForecastFactor]:
        """Generate factors that influenced the forecast"""
        
        factors = []
        
        if include_trends:
            factors.append(ForecastFactor(
                name="Historical Trend",
                impact="positive",
                weight=0.3,
                description="Based on recent sales trend analysis"
            ))
        
        if include_seasonality:
            factors.append(ForecastFactor(
                name="Seasonal Patterns",
                impact="neutral",
                weight=0.2,
                description="Historical seasonal variations"
            ))
        
        if include_external_factors:
            factors.append(ForecastFactor(
                name="Market Conditions",
                impact="neutral",
                weight=0.1,
                description="External market factors"
            ))
        
        factors.append(ForecastFactor(
            name="Historical Average",
            impact="positive",
            weight=0.4,
            description="Based on historical sales performance"
        ))
        
        return factors
    
    def _calculate_accuracy_score(
        self, 
        historical_data: List[Dict[str, Any]], 
        time_period: str
    ) -> Decimal:
        """Calculate accuracy score based on historical forecast performance"""
        
        # This is a simplified accuracy calculation
        # In a real implementation, you would compare previous forecasts with actual results
        
        if len(historical_data) < 10:
            return Decimal('70.0')  # Lower confidence with less data
        
        # Calculate coefficient of variation
        revenues = [data["revenue"] for data in historical_data]
        if len(revenues) > 1:
            mean_revenue = statistics.mean(revenues)
            std_revenue = statistics.stdev(revenues)
            cv = std_revenue / mean_revenue if mean_revenue > 0 else 1.0
            
            # Convert CV to accuracy score (lower CV = higher accuracy)
            accuracy = max(50, min(95, 100 - (cv * 50)))
            return Decimal(str(accuracy))
        
        return Decimal('75.0')
    
    def _get_factors_used(
        self, 
        include_seasonality: bool, 
        include_trends: bool, 
        include_external_factors: bool
    ) -> Dict[str, Any]:
        """Get list of factors used in the forecast"""
        
        factors = {
            "historical_average": True,
            "seasonality": include_seasonality,
            "trends": include_trends,
            "external_factors": include_external_factors
        }
        
        return factors


