from sqlalchemy.orm import Session
from app.models import Coin, CoinImage, Listing, Order, SpotPrice, AuditLog
from app.schemas import CoinCreate, CoinUpdate, CoinImageCreate, ListingCreate, OrderCreate
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

class CoinRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, coin_data: CoinCreate, created_by: str) -> Coin:
        """Create a new coin"""
        db_coin = Coin(**coin_data.dict(), created_by=created_by)
        self.db.add(db_coin)
        self.db.commit()
        self.db.refresh(db_coin)
        return db_coin
    
    def get_by_id(self, coin_id: int) -> Optional[Coin]:
        """Get coin by ID"""
        return self.db.query(Coin).filter(Coin.id == coin_id).first()
    
    def get_by_sku(self, sku: str) -> Optional[Coin]:
        """Get coin by SKU"""
        return self.db.query(Coin).filter(Coin.sku == sku).first()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[Coin]:
        """Get all coins with pagination"""
        return self.db.query(Coin).offset(skip).limit(limit).all()
    
    def update(self, coin_id: int, coin_data: CoinUpdate) -> Optional[Coin]:
        """Update coin"""
        db_coin = self.get_by_id(coin_id)
        if not db_coin:
            return None
        
        update_data = coin_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_coin, field, value)
        
        self.db.commit()
        self.db.refresh(db_coin)
        return db_coin
    
    def delete(self, coin_id: int) -> bool:
        """Delete coin"""
        db_coin = self.get_by_id(coin_id)
        if not db_coin:
            return False
        
        self.db.delete(db_coin)
        self.db.commit()
        return True
    
    def search(self, query: str, skip: int = 0, limit: int = 100) -> List[Coin]:
        """Search coins by title, SKU, or description"""
        search_filter = f"%{query}%"
        return self.db.query(Coin).filter(
            (Coin.title.ilike(search_filter)) |
            (Coin.sku.ilike(search_filter)) |
            (Coin.description.ilike(search_filter))
        ).offset(skip).limit(limit).all()

class CoinImageRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, image_data: CoinImageCreate) -> CoinImage:
        """Create a new coin image"""
        db_image = CoinImage(**image_data.dict())
        self.db.add(db_image)
        self.db.commit()
        self.db.refresh(db_image)
        return db_image
    
    def get_by_coin_id(self, coin_id: int) -> List[CoinImage]:
        """Get all images for a coin"""
        return self.db.query(CoinImage).filter(
            CoinImage.coin_id == coin_id
        ).order_by(CoinImage.sort_order).all()
    
    def delete(self, image_id: int) -> bool:
        """Delete coin image"""
        db_image = self.db.query(CoinImage).filter(CoinImage.id == image_id).first()
        if not db_image:
            return False
        
        self.db.delete(db_image)
        self.db.commit()
        return True

class ListingRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, listing_data: ListingCreate) -> Listing:
        """Create a new listing"""
        db_listing = Listing(**listing_data.dict())
        self.db.add(db_listing)
        self.db.commit()
        self.db.refresh(db_listing)
        return db_listing
    
    def get_by_coin_id(self, coin_id: int) -> List[Listing]:
        """Get all listings for a coin"""
        return self.db.query(Listing).filter(Listing.coin_id == coin_id).all()
    
    def get_by_channel(self, channel: str) -> List[Listing]:
        """Get all listings for a channel"""
        return self.db.query(Listing).filter(Listing.channel == channel).all()
    
    def update_status(self, listing_id: int, status: str, error: str = None) -> bool:
        """Update listing status"""
        db_listing = self.db.query(Listing).filter(Listing.id == listing_id).first()
        if not db_listing:
            return False
        
        db_listing.status = status
        if error:
            db_listing.last_error = error
        
        self.db.commit()
        return True

class OrderRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, order_data: OrderCreate) -> Order:
        """Create a new order"""
        db_order = Order(**order_data.dict())
        self.db.add(db_order)
        self.db.commit()
        self.db.refresh(db_order)
        return db_order
    
    def get_by_coin_id(self, coin_id: int) -> List[Order]:
        """Get all orders for a coin"""
        return self.db.query(Order).filter(Order.coin_id == coin_id).all()
    
    def get_by_channel(self, channel: str) -> List[Order]:
        """Get all orders for a channel"""
        return self.db.query(Order).filter(Order.channel == channel).all()

class SpotPriceRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_latest(self, metal: str = "silver") -> Optional[SpotPrice]:
        """Get latest spot price for metal"""
        return self.db.query(SpotPrice).filter(
            SpotPrice.metal == metal
        ).order_by(SpotPrice.fetched_at.desc()).first()
    
    def create(self, metal: str, price: float, source: str = "api") -> SpotPrice:
        """Create new spot price entry"""
        db_spot = SpotPrice(metal=metal, price=price, source=source)
        self.db.add(db_spot)
        self.db.commit()
        self.db.refresh(db_spot)
        return db_spot

class AuditLogRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, actor: str, action: str, entity: str, entity_id: str = None, payload: str = None) -> AuditLog:
        """Create audit log entry"""
        db_log = AuditLog(
            actor=actor,
            action=action,
            entity=entity,
            entity_id=entity_id,
            payload=payload
        )
        self.db.add(db_log)
        self.db.commit()
        self.db.refresh(db_log)
        return db_log

