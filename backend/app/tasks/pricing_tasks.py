import logging
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any
from celery import Celery
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

from app.services.spot_price_service import spot_price_service
from app.services.market_scraper_service import market_scraper_service
from app.services.pricing_engine_service import pricing_engine_service, PricingInput
from app.services.shopify_pricing_service import shopify_pricing_service
from app.models.pricing_models import MarketPrice, PricingConfig, Coin

# Configure logging
logger = logging.getLogger(__name__)

# Celery app configuration
celery_app = Celery('pricing_tasks')
celery_app.conf.update(
    broker_url=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    result_backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes
)

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost/miracle_coins')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@celery_app.task(bind=True, name='pricing.update_spot_prices')
def update_spot_prices(self):
    """Update spot prices from all sources"""
    try:
        logger.info("Starting spot price update task")
        
        # Get database session
        db = SessionLocal()
        
        try:
            # Fetch spot prices from all sources
            spot_prices = []
            
            # This would be implemented to fetch from multiple sources
            # and store the results in the database
            
            logger.info(f"Updated spot prices from {len(spot_prices)} sources")
            
            return {
                "status": "success",
                "sources_updated": len(spot_prices),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Spot price update task failed: {e}")
        raise self.retry(exc=e, countdown=60, max_retries=3)

@celery_app.task(bind=True, name='pricing.scrape_market_data')
def scrape_market_data(self, coin_types: Optional[List[str]] = None):
    """Scrape market data for all coin types"""
    try:
        logger.info("Starting market data scraping task")
        
        # Get database session
        db = SessionLocal()
        
        try:
            if not coin_types:
                # Get all active coin types from configuration
                configs = db.query(PricingConfig).filter(PricingConfig.is_active == True).all()
                coin_types = [config.coin_type for config in configs]
            
            scraped_count = 0
            
            for coin_type in coin_types:
                try:
                    # Scrape market data
                    market_data = await market_scraper_service.scrape_market_data(coin_type)
                    
                    if market_data:
                        # Store market data (this would be implemented)
                        scraped_count += 1
                        logger.info(f"Scraped market data for {coin_type}")
                    
                except Exception as e:
                    logger.error(f"Failed to scrape market data for {coin_type}: {e}")
                    continue
            
            logger.info(f"Scraped market data for {scraped_count} coin types")
            
            return {
                "status": "success",
                "coin_types_scraped": scraped_count,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Market data scraping task failed: {e}")
        raise self.retry(exc=e, countdown=120, max_retries=2)

@celery_app.task(bind=True, name='pricing.calculate_all_prices')
def calculate_all_prices(self):
    """Calculate prices for all coins using pricing engine"""
    try:
        logger.info("Starting price calculation task")
        
        # Get database session
        db = SessionLocal()
        
        try:
            # Get all coins that need price updates
            coins = db.query(Coin).filter(Coin.status == 'available').all()
            
            pricing_inputs = []
            for coin in coins:
                pricing_inputs.append(PricingInput(
                    coin_id=coin.id,
                    coin_type=coin.metal_type or 'generic_silver',
                    weight_oz=coin.weight_oz or Decimal('1.0'),
                    purity=coin.purity or Decimal('0.999'),
                    override_price=coin.override_price
                ))
            
            # Calculate prices in batches
            results = await pricing_engine_service.batch_calculate_prices(pricing_inputs, db)
            
            successful_updates = sum(1 for result in results if result.final_price > 0)
            
            logger.info(f"Calculated prices for {successful_updates} coins")
            
            return {
                "status": "success",
                "coins_updated": successful_updates,
                "total_coins": len(coins),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Price calculation task failed: {e}")
        raise self.retry(exc=e, countdown=180, max_retries=2)

@celery_app.task(bind=True, name='pricing.sync_shopify_prices')
def sync_shopify_prices(self):
    """Sync price changes to Shopify"""
    try:
        logger.info("Starting Shopify price sync task")
        
        # Get database session
        db = SessionLocal()
        
        try:
            # Get recent price changes that need syncing
            recent_changes = db.query(MarketPrice).filter(
                MarketPrice.last_updated_at >= datetime.now(timezone.utc) - timedelta(hours=1)
            ).all()
            
            if not recent_changes:
                logger.info("No recent price changes to sync")
                return {
                    "status": "success",
                    "products_updated": 0,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            
            # Convert to pricing results for sync
            pricing_results = []
            for change in recent_changes:
                pricing_results.append(PricingResult(
                    final_price=change.final_price,
                    melt_value=change.melt_value,
                    markup_factor=change.markup_factor,
                    confidence_score=float(change.confidence_score),
                    scam_detected=change.scam_detected,
                    sources_used=[change.source],
                    calculation_method="background_update",
                    timestamp=change.last_updated_at
                ))
            
            # Sync to Shopify
            sync_results = await shopify_pricing_service.sync_pricing_changes(pricing_results, db)
            
            successful_syncs = sum(1 for result in sync_results if result.success)
            
            logger.info(f"Synced {successful_syncs} price changes to Shopify")
            
            return {
                "status": "success",
                "products_updated": successful_syncs,
                "total_changes": len(recent_changes),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Shopify price sync task failed: {e}")
        raise self.retry(exc=e, countdown=300, max_retries=2)

@celery_app.task(bind=True, name='pricing.detect_scam_prices')
def detect_scam_prices(self):
    """Run scam detection on all recent prices"""
    try:
        logger.info("Starting scam detection task")
        
        # Get database session
        db = SessionLocal()
        
        try:
            # Get recent prices that haven't been checked for scams
            recent_prices = db.query(MarketPrice).filter(
                MarketPrice.created_at >= datetime.now(timezone.utc) - timedelta(hours=24),
                MarketPrice.scam_detected == False
            ).all()
            
            scam_detections = 0
            
            for price in recent_prices:
                try:
                    # Get coin data
                    coin = db.query(Coin).filter(Coin.id == price.coin_id).first()
                    if not coin:
                        continue
                    
                    # Run scam detection
                    scam_result = await scam_detection_service.detect_scam_price(
                        price=price.final_price,
                        coin_type=coin.metal_type or 'generic_silver',
                        market_data={
                            "avg_price": price.market_avg,
                            "min_price": price.market_min,
                            "max_price": price.market_max,
                            "spot_price": price.spot_price
                        }
                    )
                    
                    # Update scam detection status
                    if scam_result.is_scam:
                        price.scam_detected = True
                        price.scam_reason = scam_result.reasons[0] if scam_result.reasons else "AI detected scam"
                        scam_detections += 1
                    
                    db.commit()
                    
                except Exception as e:
                    logger.error(f"Scam detection failed for price {price.id}: {e}")
                    continue
            
            logger.info(f"Detected {scam_detections} potential scams")
            
            return {
                "status": "success",
                "scams_detected": scam_detections,
                "prices_checked": len(recent_prices),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Scam detection task failed: {e}")
        raise self.retry(exc=e, countdown=240, max_retries=2)

@celery_app.task(bind=True, name='pricing.full_pricing_update')
def full_pricing_update(self):
    """Run complete pricing update cycle"""
    try:
        logger.info("Starting full pricing update cycle")
        
        # Step 1: Update spot prices
        spot_result = update_spot_prices.delay()
        spot_result.get(timeout=300)
        
        # Step 2: Scrape market data
        market_result = scrape_market_data.delay()
        market_result.get(timeout=600)
        
        # Step 3: Calculate all prices
        calc_result = calculate_all_prices.delay()
        calc_result.get(timeout=900)
        
        # Step 4: Detect scams
        scam_result = detect_scam_prices.delay()
        scam_result.get(timeout=600)
        
        # Step 5: Sync to Shopify
        sync_result = sync_shopify_prices.delay()
        sync_result.get(timeout=300)
        
        logger.info("Full pricing update cycle completed")
        
        return {
            "status": "success",
            "spot_update": spot_result.result,
            "market_scrape": market_result.result,
            "price_calculation": calc_result.result,
            "scam_detection": scam_result.result,
            "shopify_sync": sync_result.result,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Full pricing update cycle failed: {e}")
        raise self.retry(exc=e, countdown=600, max_retries=1)

@celery_app.task(bind=True, name='pricing.cleanup_old_data')
def cleanup_old_data(self):
    """Clean up old pricing data to keep database size manageable"""
    try:
        logger.info("Starting data cleanup task")
        
        # Get database session
        db = SessionLocal()
        
        try:
            # Delete old market prices (keep last 30 days)
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
            
            old_prices = db.query(MarketPrice).filter(
                MarketPrice.created_at < cutoff_date
            ).all()
            
            deleted_count = len(old_prices)
            
            for price in old_prices:
                db.delete(price)
            
            db.commit()
            
            logger.info(f"Cleaned up {deleted_count} old pricing records")
            
            return {
                "status": "success",
                "records_deleted": deleted_count,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Data cleanup task failed: {e}")
        raise self.retry(exc=e, countdown=3600, max_retries=1)

# Periodic task scheduling
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    'update-spot-prices-hourly': {
        'task': 'pricing.update_spot_prices',
        'schedule': crontab(minute=0),  # Every hour
    },
    'scrape-market-data-daily': {
        'task': 'pricing.scrape_market_data',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
    'calculate-prices-hourly': {
        'task': 'pricing.calculate_all_prices',
        'schedule': crontab(minute=30),  # Every hour at 30 minutes
    },
    'sync-shopify-prices-hourly': {
        'task': 'pricing.sync_shopify_prices',
        'schedule': crontab(minute=45),  # Every hour at 45 minutes
    },
    'detect-scam-prices-daily': {
        'task': 'pricing.detect_scam_prices',
        'schedule': crontab(hour=3, minute=0),  # Daily at 3 AM
    },
    'cleanup-old-data-weekly': {
        'task': 'pricing.cleanup_old_data',
        'schedule': crontab(hour=4, minute=0, day_of_week=1),  # Weekly on Monday at 4 AM
    },
}

celery_app.conf.timezone = 'UTC'




