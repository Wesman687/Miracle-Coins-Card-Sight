from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime, timezone

# Mock the schemas for now to get it running
from pydantic import BaseModel
from decimal import Decimal

class SpotPriceResponse(BaseModel):
    price: Decimal
    currency: str
    source: str
    timestamp: datetime
    confidence: float

class MarketDataResponse(BaseModel):
    avg_price: Decimal
    min_price: Decimal
    max_price: Decimal
    sample_size: int
    source: str
    timestamp: datetime
    confidence: float

class ScamDetectionResponse(BaseModel):
    is_scam: bool
    probability: float
    reasons: List[str]
    method: str
    confidence: float
    z_score: Optional[float] = None
    price_deviation: Optional[float] = None

class PricingResultResponse(BaseModel):
    final_price: Decimal
    melt_value: Decimal
    markup_factor: Decimal
    confidence_score: float
    scam_detected: bool
    sources_used: List[str]
    calculation_method: str
    timestamp: datetime

from app.services.spot_price_service import spot_price_service
from app.services.market_scraper_service import market_scraper_service
from app.services.scam_detection_service import scam_detection_service
from app.services.pricing_engine_service import pricing_engine_service, PricingInput
from app.services.shopify_pricing_service import shopify_pricing_service

logger = logging.getLogger(__name__)
router = APIRouter()

# Mock functions for now (replace with actual auth)
def get_db():
    return None

def verify_admin_token():
    return {"user_id": "admin", "isAdmin": True}

# Spot Price Endpoints
@router.get("/spot-price", response_model=SpotPriceResponse)
async def get_spot_price(
    source: Optional[str] = None,
    current_user: dict = Depends(verify_admin_token)
):
    """Get current silver spot price"""
    try:
        spot_data = await spot_price_service.fetch_spot_price(source)
        if not spot_data:
            raise HTTPException(
                status_code=503,
                detail="Unable to fetch spot price from any source"
            )
        
        return SpotPriceResponse(
            price=spot_data.price,
            currency=spot_data.currency,
            source=spot_data.source,
            timestamp=spot_data.timestamp,
            confidence=spot_data.confidence
        )
    except Exception as e:
        logger.error(f"Failed to get spot price: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch spot price")

# Market Data Endpoints
@router.get("/market-data", response_model=MarketDataResponse)
async def get_market_data(
    coin_type: str,
    source: Optional[str] = None,
    current_user: dict = Depends(verify_admin_token)
):
    """Get market data for a specific coin type"""
    try:
        market_data = await market_scraper_service.scrape_market_data(coin_type, source)
        if not market_data:
            raise HTTPException(
                status_code=404,
                detail=f"No market data available for {coin_type}"
            )
        
        return MarketDataResponse(
            avg_price=market_data.avg_price,
            min_price=market_data.min_price,
            max_price=market_data.max_price,
            sample_size=market_data.sample_size,
            source=market_data.source,
            timestamp=market_data.timestamp,
            confidence=market_data.confidence
        )
    except Exception as e:
        logger.error(f"Failed to get market data: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch market data")

# Scam Detection Endpoints
@router.post("/scam-detection", response_model=ScamDetectionResponse)
async def detect_scam_price(
    price: Decimal,
    coin_type: str,
    current_user: dict = Depends(verify_admin_token)
):
    """Detect if a price is likely a scam"""
    try:
        scam_result = await scam_detection_service.detect_scam_price(
            price=price,
            coin_type=coin_type
        )
        
        return ScamDetectionResponse(
            is_scam=scam_result.is_scam,
            probability=scam_result.probability,
            reasons=scam_result.reasons,
            method=scam_result.method,
            confidence=scam_result.confidence,
            z_score=scam_result.z_score,
            price_deviation=scam_result.price_deviation
        )
    except Exception as e:
        logger.error(f"Failed to detect scam price: {e}")
        raise HTTPException(status_code=500, detail="Failed to detect scam price")

# Pricing Engine Endpoints
@router.post("/calculate-price", response_model=PricingResultResponse)
async def calculate_price(
    coin_id: int,
    coin_type: str,
    weight_oz: Decimal,
    purity: Decimal,
    override_price: Optional[Decimal] = None,
    force_update: bool = False,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_admin_token)
):
    """Calculate price for a specific coin"""
    try:
        pricing_input = PricingInput(
            coin_id=coin_id,
            coin_type=coin_type,
            weight_oz=weight_oz,
            purity=purity,
            override_price=override_price,
            force_update=force_update
        )
        
        result = await pricing_engine_service.calculate_price(pricing_input, db)
        
        return PricingResultResponse(
            final_price=result.final_price,
            melt_value=result.melt_value,
            markup_factor=result.markup_factor,
            confidence_score=result.confidence_score,
            scam_detected=result.scam_detected,
            sources_used=result.sources_used,
            calculation_method=result.calculation_method,
            timestamp=result.timestamp
        )
    except Exception as e:
        logger.error(f"Failed to calculate price: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate price")

@router.post("/shopify/create-test-product")
async def create_test_product(
    current_user: dict = Depends(verify_admin_token)
):
    """Create a test product in Shopify"""
    try:
        result = await shopify_pricing_service.create_test_product()
        
        if result["success"]:
            return {
                "message": "Test product created successfully",
                "product_id": result["product"]["id"],
                "product_title": result["product"]["title"],
                "product_price": result["product"]["variants"][0]["price"],
                "product_sku": result["product"]["variants"][0]["sku"]
            }
        else:
            raise HTTPException(status_code=500, detail=result["message"])
            
    except Exception as e:
        logger.error(f"Failed to create test product: {e}")
        raise HTTPException(status_code=500, detail="Failed to create test product")

@router.get("/shopify/orders")
async def get_shopify_orders(
    current_user: dict = Depends(verify_admin_token)
):
    """Get recent orders from Shopify"""
    try:
        # This would fetch orders from Shopify
        # For now, return mock data
        return {
            "orders": [],
            "message": "No orders found - store may be empty or orders endpoint not implemented",
            "note": "This would connect to Shopify Orders API to get sales data"
        }
    except Exception as e:
        logger.error(f"Failed to get Shopify orders: {e}")
        raise HTTPException(status_code=500, detail="Failed to get Shopify orders")

# Shopify Integration Endpoints
@router.get("/shopify/products")
async def get_shopify_products(
    current_user: dict = Depends(verify_admin_token)
):
    """Get list of Shopify products"""
    try:
        products = await shopify_pricing_service.get_products_needing_updates()
        return {"products": products}
    except Exception as e:
        logger.error(f"Failed to get Shopify products: {e}")
        raise HTTPException(status_code=500, detail="Failed to get Shopify products")

@router.post("/shopify/update-price")
async def update_shopify_price(
    product_id: str,
    new_price: Decimal,
    current_user: dict = Depends(verify_admin_token)
):
    """Update a specific product's price in Shopify"""
    try:
        result = await shopify_pricing_service.update_product_price(product_id, new_price)
        return result
    except Exception as e:
        logger.error(f"Failed to update Shopify price: {e}")
        raise HTTPException(status_code=500, detail="Failed to update Shopify price")

# Health Check Endpoint
@router.get("/health")
async def pricing_health_check():
    """Health check for pricing services"""
    try:
        # Check if services are responsive
        spot_price = await spot_price_service.fetch_spot_price()
        
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "services": {
                "spot_price_service": "healthy" if spot_price else "degraded",
                "market_scraper_service": "healthy",
                "scam_detection_service": "healthy",
                "pricing_engine_service": "healthy",
                "shopify_pricing_service": "healthy"
            }
        }
        
        return health_status
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e)
        }
