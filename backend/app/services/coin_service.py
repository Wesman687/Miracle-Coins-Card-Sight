from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func, desc
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from decimal import Decimal
import logging

from app.models import Coin
from app.models.coin_metadata import CoinMetadata
# from app.models.categories import CoinCategory, CategoryMetadata as CategoryMetadataModel  # Temporarily disabled
from app.schemas.coin_metadata import (
    CoinCreateWithMetadata, CoinUpdateWithMetadata, CoinWithMetadata,
    CoinMetadataCreate, CoinMetadataUpdate, CoinListResponse,
    CategoryMetadataTemplate
)
from app.utils.sku_generator import generate_complete_sku

logger = logging.getLogger(__name__)

class CoinService:
    def __init__(self, db: Session):
        self.db = db

    def create_coin_with_metadata(self, coin_data: CoinCreateWithMetadata) -> CoinWithMetadata:
        """Create a new coin with category metadata fields"""
        # Auto-generate SKU if not provided
        if not coin_data.sku:
            category_name = None
            if coin_data.category_id:
                # category = self.db.query(CoinCategory).filter(CoinCategory.id == coin_data.category_id).first()  # Temporarily disabled
                category = None
                if category:
                    category_name = category.name
            
            coin_data.sku = generate_complete_sku(
                db_session=self.db,
                title=coin_data.title,
                year=coin_data.year,
                denomination=coin_data.denomination,
                mint_mark=coin_data.mint_mark,
                grade=coin_data.grade,
                category_name=category_name
            )
        
        # Create the coin
        coin = Coin(
            sku=coin_data.sku,
            title=coin_data.title,
            year=coin_data.year,
            denomination=coin_data.denomination,
            mint_mark=coin_data.mint_mark,
            grade=coin_data.grade,
            category=coin_data.category,
            description=coin_data.description,
            condition_notes=coin_data.condition_notes,
            is_silver=coin_data.is_silver,
            silver_percent=coin_data.silver_percent,
            silver_content_oz=coin_data.silver_content_oz,
            paid_price=coin_data.paid_price,
            price_strategy=coin_data.price_strategy,
            price_multiplier=coin_data.price_multiplier,
            base_from_entry=coin_data.base_from_entry,
            entry_spot=coin_data.entry_spot,
            entry_melt=coin_data.entry_melt,
            override_price=coin_data.override_price,
            override_value=coin_data.override_value,
            computed_price=coin_data.computed_price,
            quantity=coin_data.quantity,
            status=coin_data.status,
            created_by=coin_data.created_by,
            category_id=coin_data.category_id
        )
        
        self.db.add(coin)
        self.db.flush()  # Get the ID
        
        # Create metadata fields based on category
        if coin_data.category_id:
            metadata_fields = self._get_category_metadata_fields(coin_data.category_id)
            self._create_coin_metadata(coin.id, metadata_fields, coin_data.metadata or {})
        
        self.db.commit()
        self.db.refresh(coin)
        
        logger.info("Created coin with metadata: %s (ID: %s)", coin.title, coin.id)
        return self._coin_to_coin_with_metadata(coin)

    def update_coin_with_metadata(self, coin_id: int, coin_data: CoinUpdateWithMetadata) -> Optional[CoinWithMetadata]:
        """Update a coin and its metadata"""
        coin = self.db.query(Coin).filter(Coin.id == coin_id).first()
        if not coin:
            return None
        
        # Check if SKU-generating fields have changed
        sku_fields = ['title', 'year', 'denomination', 'mint_mark', 'grade', 'category_id']
        sku_changed = any(field in coin_data.dict(exclude_unset=True) for field in sku_fields)
        
        # Auto-regenerate SKU if key fields changed
        if sku_changed and not coin_data.sku:
            category_name = None
            category_id = coin_data.category_id if 'category_id' in coin_data.dict(exclude_unset=True) else coin.category_id
            if category_id:
                # category = self.db.query(CoinCategory).filter(CoinCategory.id == category_id).first()  # Temporarily disabled
                category = None
                if category:
                    category_name = category.name
            
            coin_data.sku = generate_complete_sku(
                db_session=self.db,
                title=coin_data.title if 'title' in coin_data.dict(exclude_unset=True) else coin.title,
                year=coin_data.year if 'year' in coin_data.dict(exclude_unset=True) else coin.year,
                denomination=coin_data.denomination if 'denomination' in coin_data.dict(exclude_unset=True) else coin.denomination,
                mint_mark=coin_data.mint_mark if 'mint_mark' in coin_data.dict(exclude_unset=True) else coin.mint_mark,
                grade=coin_data.grade if 'grade' in coin_data.dict(exclude_unset=True) else coin.grade,
                category_name=category_name
            )
        
        # Update basic coin fields
        update_data = coin_data.dict(exclude_unset=True, exclude={'metadata'})
        for field, value in update_data.items():
            setattr(coin, field, value)
        
        coin.updated_at = datetime.utcnow()
        
        # Handle category change
        if 'category_id' in update_data:
            old_category_id = coin.category_id
            new_category_id = update_data['category_id']
            
            # If category changed, update metadata fields
            if old_category_id != new_category_id:
                # Remove old metadata
                self.db.query(CoinMetadata).filter(CoinMetadata.coin_id == coin_id).delete()
                
                # Create new metadata fields if new category exists
                if new_category_id:
                    metadata_fields = self._get_category_metadata_fields(new_category_id)
                    self._create_coin_metadata(coin.id, metadata_fields, coin_data.metadata or {})
        
        # Update metadata if provided
        if coin_data.metadata is not None:
            self._update_coin_metadata(coin_id, coin_data.metadata)
        
        self.db.commit()
        self.db.refresh(coin)
        
        logger.info("Updated coin with metadata: %s (ID: %s)", coin.title, coin.id)
        return self._coin_to_coin_with_metadata(coin)

    def get_coin_with_metadata(self, coin_id: int) -> Optional[CoinWithMetadata]:
        """Get a coin with all its metadata"""
        coin = self.db.query(Coin)\
            .options(
                joinedload(Coin.metadata),
                joinedload(Coin.coin_category)
            )\
            .filter(Coin.id == coin_id)\
            .first()
        
        if not coin:
            return None
            
        return self._coin_to_coin_with_metadata(coin)

    def list_coins_with_metadata(
        self,
        category_id: Optional[int] = None,
        search: Optional[str] = None,
        page: int = 1,
        per_page: int = 50
    ) -> Tuple[List[CoinWithMetadata], int]:
        """List coins with metadata, filtering and pagination"""
        query = self.db.query(Coin)\
            .options(
                joinedload(Coin.metadata),
                joinedload(Coin.coin_category)
            )
        
        if category_id:
            query = query.filter(Coin.category_id == category_id)
            
        if search:
            search_filter = or_(
                Coin.title.ilike(f"%{search}%"),
                Coin.sku.ilike(f"%{search}%"),
                Coin.description.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
            
        total = query.count()
        
        coins = query\
            .order_by(desc(Coin.created_at))\
            .offset((page - 1) * per_page)\
            .limit(per_page)\
            .all()
        
        coin_with_metadata = [self._coin_to_coin_with_metadata(coin) for coin in coins]
        return coin_with_metadata, total

    def delete_coin(self, coin_id: int) -> bool:
        """Delete a coin and all its metadata"""
        coin = self.db.query(Coin).filter(Coin.id == coin_id).first()
        if not coin:
            return False
        
        # Metadata will be deleted automatically due to CASCADE
        self.db.delete(coin)
        self.db.commit()
        
        logger.info("Deleted coin: %s (ID: %s)", coin.title, coin.id)
        return True

    def get_coin_metadata_templates(self, category_id: int) -> List[CategoryMetadataTemplate]:  # Temporarily disabled
        """Get metadata field templates for a category"""
        # Temporarily disabled - category metadata functionality
        return []

    def _get_category_metadata_fields(self, category_id: int) -> List:  # Temporarily disabled
        """Get all metadata field definitions for a category"""
        # return self.db.query(CategoryMetadataModel)\
        #     .filter(CategoryMetadataModel.category_id == category_id)\
        #     .order_by(CategoryMetadataModel.sort_order, CategoryMetadataModel.field_name)\
        #     .all()
        return []  # Temporarily return empty list

    def _create_coin_metadata(self, coin_id: int, metadata_fields: List, provided_metadata: Dict[str, Any]):  # Temporarily disabled
        """Create metadata entries for a coin based on category fields"""
        # Temporarily disabled - category metadata functionality
        pass
        # for field in metadata_fields:
        #     # Get value from provided metadata or use default
        #     value = provided_metadata.get(field.field_name, field.default_value)
        #     
        #     # Convert value to string for storage
        #     if value is not None:
        #         if field.field_type == "boolean":
        #             value = str(bool(value)).lower()
        #         elif field.field_type in ["number", "date"]:
        #             value = str(value)
        #         elif field.field_type == "select":
        #             # Validate select option
        #             if field.select_options and value not in field.select_options:
        #                 value = field.default_value
        #         
        #         metadata = CoinMetadata(
        #             coin_id=coin_id,
        #             field_name=field.field_name,
        #             field_value=value,
        #             field_type=field.field_type
        #         )
        #         self.db.add(metadata)

    def _update_coin_metadata(self, coin_id: int, metadata_updates: Dict[str, Any]):  # Temporarily disabled
        """Update metadata values for a coin"""
        # Temporarily disabled - category metadata functionality
        pass

    def _coin_to_coin_with_metadata(self, coin: Coin) -> CoinWithMetadata:
        """Convert a Coin model to CoinWithMetadata schema"""
        # Convert metadata to dict
        metadata_dict = {m.field_name: m.field_value for m in coin.metadata}
        
        # Get category info
        category_info = None
        if coin.coin_category:
            category_info = {
                "id": coin.coin_category.id,
                "name": coin.coin_category.name,
                "display_name": coin.coin_category.display_name,
                "category_type": coin.coin_category.category_type.value if hasattr(coin.coin_category.category_type, 'value') else str(coin.coin_category.category_type)
            }
        
        return CoinWithMetadata(
            id=coin.id,
            sku=coin.sku,
            title=coin.title,
            year=coin.year,
            denomination=coin.denomination,
            mint_mark=coin.mint_mark,
            grade=coin.grade,
            category=coin.category,
            description=coin.description,
            condition_notes=coin.condition_notes,
            is_silver=coin.is_silver,
            silver_percent=coin.silver_percent,
            silver_content_oz=coin.silver_content_oz,
            paid_price=coin.paid_price,
            price_strategy=coin.price_strategy,
            price_multiplier=coin.price_multiplier,
            base_from_entry=coin.base_from_entry,
            entry_spot=coin.entry_spot,
            entry_melt=coin.entry_melt,
            override_price=coin.override_price,
            override_value=coin.override_value,
            computed_price=coin.computed_price,
            quantity=coin.quantity,
            status=coin.status,
            created_by=coin.created_by,
            category_id=coin.category_id,
            created_at=coin.created_at,
            updated_at=coin.updated_at,
            metadata=[CoinMetadata(
                id=m.id,
                coin_id=m.coin_id,
                field_name=m.field_name,
                field_value=m.field_value,
                field_type=m.field_type,
                created_at=m.created_at,
                updated_at=m.updated_at
            ) for m in coin.metadata],
            category_info=category_info
        )

    def bulk_update_coin_metadata(self, updates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Bulk update metadata for multiple coins"""
        successful = 0
        failed = 0
        errors = []
        
        for update in updates:
            try:
                coin_id = update.get("coin_id")
                metadata = update.get("metadata", {})
                
                if not coin_id:
                    errors.append("Missing coin_id in update")
                    failed += 1
                    continue
                
                self._update_coin_metadata(coin_id, metadata)
                successful += 1
                
            except Exception as e:
                logger.error("Failed to update coin metadata: %s", e)
                errors.append(f"Coin {update.get('coin_id', 'unknown')}: {str(e)}")
                failed += 1
        
        self.db.commit()
        
        return {
            "successful": successful,
            "failed": failed,
            "total": len(updates),
            "errors": errors
        }
