from typing import Optional, List, Dict, Any
from decimal import Decimal
from sqlalchemy.orm import Session
from app.models import Coin, CoinImage, Listing, Order, SpotPrice, AuditLog
from app.types import (
    CoinCreate, CoinUpdate, CoinImageCreate, ListingCreate, OrderCreate,
    SpotPriceCreate, AuditLogCreate, CoinStatus, ListingStatus, MarketplaceChannel
)
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class CoinRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, coin_data: CoinCreate, created_by: str) -> Coin:
        """Create a new coin with type safety"""
        try:
            db_coin = Coin(**coin_data.dict(), created_by=created_by)
            self.db.add(db_coin)
            self.db.commit()
            self.db.refresh(db_coin)
            logger.info(f"Created coin {db_coin.id}: {db_coin.title}")
            return db_coin
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating coin: {e}")
            raise
    
    def get_by_id(self, coin_id: int) -> Optional[Coin]:
        """Get coin by ID with type safety"""
        return self.db.query(Coin).filter(Coin.id == coin_id).first()
    
    def get_by_sku(self, sku: str) -> Optional[Coin]:
        """Get coin by SKU with type safety"""
        return self.db.query(Coin).filter(Coin.sku == sku).first()
    
    def get_all(self, skip: int = 0, limit: int = 100, status: Optional[CoinStatus] = None) -> List[Coin]:
        """Get all coins with pagination and filtering"""
        query = self.db.query(Coin)
        if status:
            query = query.filter(Coin.status == status.value)
        return query.offset(skip).limit(limit).all()
    
    def update(self, coin_id: int, coin_data: CoinUpdate) -> Optional[Coin]:
        """Update coin with type safety"""
        try:
            db_coin = self.get_by_id(coin_id)
            if not db_coin:
                return None
            
            update_data = coin_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_coin, field, value)
            
            db_coin.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(db_coin)
            logger.info(f"Updated coin {coin_id}")
            return db_coin
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating coin {coin_id}: {e}")
            raise
    
    def delete(self, coin_id: int) -> bool:
        """Delete coin with type safety"""
        try:
            db_coin = self.get_by_id(coin_id)
            if not db_coin:
                return False
            
            self.db.delete(db_coin)
            self.db.commit()
            logger.info(f"Deleted coin {coin_id}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting coin {coin_id}: {e}")
            raise
    
    def search(self, query: str, skip: int = 0, limit: int = 100) -> List[Coin]:
        """Search coins with type safety"""
        search_filter = f"%{query}%"
        return self.db.query(Coin).filter(
            (Coin.title.ilike(search_filter)) |
            (Coin.sku.ilike(search_filter)) |
            (Coin.description.ilike(search_filter)) |
            (Coin.category.ilike(search_filter))
        ).offset(skip).limit(limit).all()
    
    def get_by_status(self, status: CoinStatus) -> List[Coin]:
        """Get coins by status"""
        return self.db.query(Coin).filter(Coin.status == status.value).all()
    
    def get_silver_coins(self) -> List[Coin]:
        """Get all silver coins"""
        return self.db.query(Coin).filter(Coin.is_silver == True).all()

class CoinImageRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, image_data: CoinImageCreate) -> CoinImage:
        """Create coin image with type safety"""
        try:
            db_image = CoinImage(**image_data.dict())
            self.db.add(db_image)
            self.db.commit()
            self.db.refresh(db_image)
            logger.info(f"Created image {db_image.id} for coin {image_data.coin_id}")
            return db_image
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating image: {e}")
            raise
    
    def get_by_id(self, image_id: int) -> Optional[CoinImage]:
        """Get image by ID"""
        return self.db.query(CoinImage).filter(CoinImage.id == image_id).first()
    
    def get_by_coin_id(self, coin_id: int) -> List[CoinImage]:
        """Get all images for a coin"""
        return self.db.query(CoinImage).filter(
            CoinImage.coin_id == coin_id
        ).order_by(CoinImage.sort_order).all()
    
    def update_sort_order(self, image_id: int, sort_order: int) -> bool:
        """Update image sort order"""
        try:
            db_image = self.get_by_id(image_id)
            if not db_image:
                return False
            
            db_image.sort_order = sort_order
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating image sort order: {e}")
            raise
    
    def delete(self, image_id: int) -> bool:
        """Delete coin image with type safety"""
        try:
            db_image = self.get_by_id(image_id)
            if not db_image:
                return False
            
            self.db.delete(db_image)
            self.db.commit()
            logger.info(f"Deleted image {image_id}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting image {image_id}: {e}")
            raise

class ListingRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, listing_data: ListingCreate) -> Listing:
        """Create listing with type safety"""
        try:
            db_listing = Listing(**listing_data.dict())
            self.db.add(db_listing)
            self.db.commit()
            self.db.refresh(db_listing)
            logger.info(f"Created listing {db_listing.id} for coin {listing_data.coin_id}")
            return db_listing
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating listing: {e}")
            raise
    
    def get_by_id(self, listing_id: int) -> Optional[Listing]:
        """Get listing by ID"""
        return self.db.query(Listing).filter(Listing.id == listing_id).first()
    
    def get_by_coin_id(self, coin_id: int) -> List[Listing]:
        """Get all listings for a coin"""
        return self.db.query(Listing).filter(Listing.coin_id == coin_id).all()
    
    def get_by_channel(self, channel: MarketplaceChannel) -> List[Listing]:
        """Get all listings for a channel"""
        return self.db.query(Listing).filter(Listing.channel == channel.value).all()
    
    def get_by_status(self, status: ListingStatus) -> List[Listing]:
        """Get listings by status"""
        return self.db.query(Listing).filter(Listing.status == status.value).all()
    
    def update_status(self, listing_id: int, status: ListingStatus, error: Optional[str] = None) -> bool:
        """Update listing status with type safety"""
        try:
            db_listing = self.get_by_id(listing_id)
            if not db_listing:
                return False
            
            db_listing.status = status.value
            if error:
                db_listing.last_error = error
            db_listing.updated_at = datetime.utcnow()
            
            self.db.commit()
            logger.info(f"Updated listing {listing_id} status to {status.value}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating listing status: {e}")
            raise
    
    def delete(self, listing_id: int) -> bool:
        """Delete listing with type safety"""
        try:
            db_listing = self.get_by_id(listing_id)
            if not db_listing:
                return False
            
            self.db.delete(db_listing)
            self.db.commit()
            logger.info(f"Deleted listing {listing_id}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting listing {listing_id}: {e}")
            raise

class OrderRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, order_data: OrderCreate) -> Order:
        """Create order with type safety"""
        try:
            db_order = Order(**order_data.dict())
            self.db.add(db_order)
            self.db.commit()
            self.db.refresh(db_order)
            logger.info(f"Created order {db_order.id} for coin {order_data.coin_id}")
            return db_order
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating order: {e}")
            raise
    
    def get_by_id(self, order_id: int) -> Optional[Order]:
        """Get order by ID"""
        return self.db.query(Order).filter(Order.id == order_id).first()
    
    def get_by_coin_id(self, coin_id: int) -> List[Order]:
        """Get all orders for a coin"""
        return self.db.query(Order).filter(Order.coin_id == coin_id).all()
    
    def get_by_channel(self, channel: MarketplaceChannel) -> List[Order]:
        """Get all orders for a channel"""
        return self.db.query(Order).filter(Order.channel == channel.value).all()
    
    def get_recent_orders(self, days: int = 30) -> List[Order]:
        """Get recent orders"""
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return self.db.query(Order).filter(Order.created_at >= cutoff_date).all()

class SpotPriceRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_latest(self, metal: str = "silver") -> Optional[SpotPrice]:
        """Get latest spot price for metal"""
        return self.db.query(SpotPrice).filter(
            SpotPrice.metal == metal
        ).order_by(SpotPrice.fetched_at.desc()).first()
    
    def create(self, metal: str, price: Decimal, source: str = "api") -> SpotPrice:
        """Create new spot price entry with type safety"""
        try:
            db_spot = SpotPrice(metal=metal, price=price, source=source)
            self.db.add(db_spot)
            self.db.commit()
            self.db.refresh(db_spot)
            logger.info(f"Created spot price for {metal}: ${price}")
            return db_spot
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating spot price: {e}")
            raise
    
    def get_price_history(self, metal: str, days: int = 30) -> List[SpotPrice]:
        """Get price history for metal"""
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return self.db.query(SpotPrice).filter(
            SpotPrice.metal == metal,
            SpotPrice.fetched_at >= cutoff_date
        ).order_by(SpotPrice.fetched_at.desc()).all()

class AuditLogRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, actor: str, action: str, entity: str, entity_id: Optional[str] = None, payload: Optional[Dict[str, Any]] = None) -> AuditLog:
        """Create audit log entry with type safety"""
        try:
            db_log = AuditLog(
                actor=actor,
                action=action,
                entity=entity,
                entity_id=entity_id,
                payload=str(payload) if payload else None
            )
            self.db.add(db_log)
            self.db.commit()
            self.db.refresh(db_log)
            logger.info(f"Created audit log: {action} on {entity}")
            return db_log
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating audit log: {e}")
            raise
    
    def get_by_entity(self, entity: str, entity_id: str) -> List[AuditLog]:
        """Get audit logs for specific entity"""
        return self.db.query(AuditLog).filter(
            AuditLog.entity == entity,
            AuditLog.entity_id == entity_id
        ).order_by(AuditLog.created_at.desc()).all()
    
    def get_recent_activity(self, limit: int = 100) -> List[AuditLog]:
        """Get recent audit activity"""
        return self.db.query(AuditLog).order_by(
            AuditLog.created_at.desc()
        ).limit(limit).all()




