from celery_app import celery_app
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from app.repositories import SpotPriceRepository
import os
from dotenv import load_dotenv
import logging
import httpx

load_dotenv()

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/miracle-coins")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

logger = logging.getLogger(__name__)

@celery_app.task
def refresh_spot_prices():
    """Refresh spot prices from external API"""
    try:
        db = SessionLocal()
        spot_repo = SpotPriceRepository(db)
        
        # TODO: Replace with actual silver price API
        # For now, using a mock price
        silver_price = 25.50  # Mock price
        
        # Create new spot price entry
        spot_repo.create("silver", silver_price, "api")
        
        logger.info(f"Updated silver spot price to ${silver_price}")
        
        db.close()
        return {"status": "success", "price": silver_price}
        
    except Exception as e:
        logger.error(f"Error refreshing spot prices: {e}")
        return {"status": "error", "message": str(e)}

@celery_app.task
def bulk_reprice_task(coin_ids=None, new_multiplier=None):
    """Bulk reprice coins task"""
    try:
        db = SessionLocal()
        from app.services.pricing_service import PricingService
        
        pricing_service = PricingService(db)
        updated_count = pricing_service.bulk_reprice_coins(coin_ids, new_multiplier)
        
        logger.info(f"Bulk repriced {updated_count} coins")
        
        db.close()
        return {"status": "success", "updated_count": updated_count}
        
    except Exception as e:
        logger.error(f"Error in bulk reprice task: {e}")
        return {"status": "error", "message": str(e)}

@celery_app.task
def sync_shopify_listing(coin_id):
    """Sync coin to Shopify"""
    try:
        db = SessionLocal()
        from app.repositories import CoinRepository, ListingRepository
        
        coin_repo = CoinRepository(db)
        listing_repo = ListingRepository(db)
        
        coin = coin_repo.get_by_id(coin_id)
        if not coin:
            return {"status": "error", "message": "Coin not found"}
        
        # TODO: Implement actual Shopify API integration
        # For now, just create a mock listing
        
        listing_data = {
            "coin_id": coin_id,
            "channel": "shopify",
            "external_id": f"shopify_{coin_id}",
            "url": f"https://shopify-store.com/products/{coin.sku}",
            "status": "listed"
        }
        
        listing = listing_repo.create(listing_data)
        
        logger.info(f"Synced coin {coin_id} to Shopify")
        
        db.close()
        return {"status": "success", "listing_id": listing.id}
        
    except Exception as e:
        logger.error(f"Error syncing to Shopify: {e}")
        return {"status": "error", "message": str(e)}

