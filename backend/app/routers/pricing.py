from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.auth import get_current_admin_user
from app.database import get_db
from app.services.spot_price_service import SpotPriceService
from app.services.market_scraper_service import MarketScraperService
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize services
spot_price_service = SpotPriceService()
market_scraper_service = MarketScraperService()

@router.get("/pricing")
async def get_pricing():
    return {"message": "Pricing endpoint - not implemented yet"}

@router.post("/calculate")
async def calculate_pricing():
    return {"message": "Calculate pricing endpoint - not implemented yet"}

@router.get("/test-updated-code")
async def test_updated_code():
    """Test if updated code is being loaded."""
    return {"message": "UPDATED CODE IS LOADING!", "timestamp": "2025-10-21-22:55"}

@router.get("/test-metals-prices")
async def test_metals_prices():
    """Test metals prices fetching"""
    try:
        # Test silver
        silver_data = spot_price_service.fetch_spot_price("goldapi", "silver")
        
        # Test gold
        gold_data = spot_price_service.fetch_spot_price("goldapi", "gold")
        
        metals_prices = {}
        
        if silver_data:
            metals_prices["silver"] = {
                "price": float(silver_data.price),
                "currency": silver_data.currency,
                "source": silver_data.source,
                "timestamp": silver_data.timestamp.isoformat() if silver_data.timestamp else None,
                "confidence": silver_data.confidence
            }
        else:
            metals_prices["silver"] = {
                "price": None,
                "currency": "USD",
                "source": "unavailable",
                "timestamp": None,
                "confidence": 0.0
            }
        
        if gold_data:
            metals_prices["gold"] = {
                "price": float(gold_data.price),
                "currency": gold_data.currency,
                "source": gold_data.source,
                "timestamp": gold_data.timestamp.isoformat() if gold_data.timestamp else None,
                "confidence": gold_data.confidence
            }
        else:
            metals_prices["gold"] = {
                "price": None,
                "currency": "USD",
                "source": "unavailable",
                "timestamp": None,
                "confidence": 0.0
            }
        
        return {
            "status": "success",
            "metals_prices": metals_prices
        }
        
    except Exception as e:
        logger.error(f"Error testing metals prices: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

@router.get("/metals-rate-limit")
async def get_metals_rate_limit(
    _: dict = Depends(get_current_admin_user)
):
    """Get current metals API rate limit status"""
    try:
        rate_limit_status = spot_price_service.cache.get_rate_limit_status()
        return {
            "status": "success",
            "rate_limit": rate_limit_status
        }
    except Exception as e:
        logger.error("Error getting rate limit status: %s", e)
        return {
            "status": "error",
            "message": str(e)
        }

@router.get("/dashboard-kpis")
async def get_dashboard_kpis(
    _: dict = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get dashboard KPIs for pricing overview including metals prices."""
    try:
        # Get total active coins
        total_coins_result = db.execute(text("""
            SELECT COUNT(*) FROM coins WHERE status = 'active'
        """))
        total_coins = total_coins_result.fetchone()[0]
        
        # Get total active listings (same as active coins for now)
        active_listings = total_coins
        
        # Get sold coins this month
        sold_this_month_result = db.execute(text("""
            SELECT COUNT(*) FROM coins 
            WHERE status = 'sold' 
            AND updated_at >= date_trunc('month', CURRENT_DATE)
        """))
        sold_this_month = sold_this_month_result.fetchone()[0]
        
        # Calculate inventory values
        inventory_values_result = db.execute(text("""
            SELECT 
                SUM(CASE WHEN paid_price IS NOT NULL THEN paid_price * quantity ELSE 0 END) as total_paid,
                SUM(CASE WHEN computed_price IS NOT NULL THEN computed_price * quantity ELSE 0 END) as total_list
            FROM coins 
            WHERE status = 'active'
        """))
        values_row = inventory_values_result.fetchone()
        inventory_melt_value = float(values_row[0] or 0)
        inventory_list_value = float(values_row[1] or 0)
        gross_profit = inventory_list_value - inventory_melt_value
        melt_vs_list_ratio = round(inventory_list_value / inventory_melt_value, 2) if inventory_melt_value > 0 else 0
        
        # Get metals prices
        metals_prices = {}
        
        # Get silver spot price
        try:
            silver_data = spot_price_service.fetch_spot_price("goldapi", "silver")
            if silver_data:
                metals_prices["silver"] = {
                    "price": float(silver_data.price),
                    "currency": silver_data.currency,
                    "source": silver_data.source,
                    "timestamp": silver_data.timestamp.isoformat() if silver_data.timestamp else None,
                    "confidence": silver_data.confidence
                }
            else:
                metals_prices["silver"] = {
                    "price": None,
                    "currency": "USD",
                    "source": "unavailable",
                    "timestamp": None,
                    "confidence": 0.0
                }
        except Exception as e:
            logger.error("Failed to fetch silver price: %s", e)
            metals_prices["silver"] = {
                "price": None,
                "currency": "USD", 
                "source": "error",
                "timestamp": None,
                "confidence": 0.0
            }
        
        # Get gold spot price
        try:
            gold_data = spot_price_service.fetch_spot_price("goldapi", "gold")
            if gold_data:
                metals_prices["gold"] = {
                    "price": float(gold_data.price),
                    "currency": gold_data.currency,
                    "source": gold_data.source,
                    "timestamp": gold_data.timestamp.isoformat() if gold_data.timestamp else None,
                    "confidence": gold_data.confidence
                }
            else:
                metals_prices["gold"] = {
                    "price": None,
                    "currency": "USD",
                    "source": "unavailable", 
                    "timestamp": None,
                    "confidence": 0.0
                }
        except Exception as e:
            logger.error("Failed to fetch gold price: %s", e)
            metals_prices["gold"] = {
                "price": None,
                "currency": "USD",
                "source": "error",
                "timestamp": None,
                "confidence": 0.0
            }
        
        return {
            "inventory_melt_value": inventory_melt_value,
            "inventory_list_value": inventory_list_value,
            "gross_profit": gross_profit,
            "melt_vs_list_ratio": melt_vs_list_ratio,
            "total_coins": total_coins,
            "active_listings": active_listings,
            "sold_this_month": sold_this_month,
            "metals_prices": metals_prices
        }
    except Exception as e:
        logger.error("Error in dashboard KPIs: %s", e)
        # Fallback to zeros if there's an error
        return {
            "inventory_melt_value": 0.0,
            "inventory_list_value": 0.0,
            "gross_profit": 0.0,
            "melt_vs_list_ratio": 0.0,
            "total_coins": 0,
            "active_listings": 0,
            "sold_this_month": 0,
            "metals_prices": {
                "silver": {"price": None, "currency": "USD", "source": "error", "timestamp": None, "confidence": 0.0},
                "gold": {"price": None, "currency": "USD", "source": "error", "timestamp": None, "confidence": 0.0}
            }
        }