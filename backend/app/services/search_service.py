from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, asc
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal
import logging

from app.models import Coin
import app.schemas as schemas_module
CoinResponse = schemas_module.Coin if hasattr(schemas_module, 'Coin') else None
logger = logging.getLogger(__name__)

class SearchService:
    def __init__(self, db: Session):
        self.db = db
    
    def advanced_search(
        self,
        query: Optional[str] = None,
        year: Optional[int] = None,
        denomination: Optional[str] = None,
        grade: Optional[str] = None,
        category: Optional[str] = None,
        min_price: Optional[Decimal] = None,
        max_price: Optional[Decimal] = None,
        min_paid_price: Optional[Decimal] = None,
        max_paid_price: Optional[Decimal] = None,
        is_silver: Optional[bool] = None,
        status: Optional[str] = None,
        mint_mark: Optional[str] = None,
        silver_percent_min: Optional[Decimal] = None,
        silver_percent_max: Optional[Decimal] = None,
        silver_content_min: Optional[Decimal] = None,
        silver_content_max: Optional[Decimal] = None,
        created_after: Optional[date] = None,
        created_before: Optional[date] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Advanced search with multiple criteria"""
        
        # Build base query
        query_obj = self.db.query(Coin)
        
        # Apply filters
        if query:
            query_obj = query_obj.filter(
                or_(
                    Coin.title.ilike(f"%{query}%"),
                    Coin.description.ilike(f"%{query}%"),
                    Coin.condition_notes.ilike(f"%{query}%")
                )
            )
        
        if year:
            query_obj = query_obj.filter(Coin.year == year)
        
        if denomination:
            query_obj = query_obj.filter(Coin.denomination.ilike(f"%{denomination}%"))
        
        if grade:
            query_obj = query_obj.filter(Coin.grade.ilike(f"%{grade}%"))
        
        if category:
            query_obj = query_obj.filter(Coin.category == category)
        
        if min_price:
            query_obj = query_obj.filter(Coin.computed_price >= min_price)
        
        if max_price:
            query_obj = query_obj.filter(Coin.computed_price <= max_price)
        
        if min_paid_price:
            query_obj = query_obj.filter(Coin.paid_price >= min_paid_price)
        
        if max_paid_price:
            query_obj = query_obj.filter(Coin.paid_price <= max_paid_price)
        
        if is_silver is not None:
            query_obj = query_obj.filter(Coin.is_silver == is_silver)
        
        if status:
            query_obj = query_obj.filter(Coin.status == status)
        
        if mint_mark:
            query_obj = query_obj.filter(Coin.mint_mark.ilike(f"%{mint_mark}%"))
        
        if silver_percent_min:
            query_obj = query_obj.filter(Coin.silver_percent >= silver_percent_min)
        
        if silver_percent_max:
            query_obj = query_obj.filter(Coin.silver_percent <= silver_percent_max)
        
        if silver_content_min:
            query_obj = query_obj.filter(Coin.silver_content_oz >= silver_content_min)
        
        if silver_content_max:
            query_obj = query_obj.filter(Coin.silver_content_oz <= silver_content_max)
        
        if created_after:
            query_obj = query_obj.filter(Coin.created_at >= created_after)
        
        if created_before:
            query_obj = query_obj.filter(Coin.created_at <= created_before)
        
        # Apply sorting
        sort_column = getattr(Coin, sort_by, Coin.created_at)
        if sort_order.lower() == "desc":
            query_obj = query_obj.order_by(desc(sort_column))
        else:
            query_obj = query_obj.order_by(asc(sort_column))
        
        # Get total count before pagination
        total_count = query_obj.count()
        
        # Apply pagination
        coins = query_obj.offset(offset).limit(limit).all()
        
        # Calculate facets for filtering
        facets = self._calculate_facets()
        
        return {
            "coins": coins,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "facets": facets,
            "search_criteria": {
                "query": query,
                "year": year,
                "denomination": denomination,
                "grade": grade,
                "category": category,
                "min_price": float(min_price) if min_price else None,
                "max_price": float(max_price) if max_price else None,
                "min_paid_price": float(min_paid_price) if min_paid_price else None,
                "max_paid_price": float(max_paid_price) if max_paid_price else None,
                "is_silver": is_silver,
                "status": status,
                "mint_mark": mint_mark,
                "silver_percent_min": float(silver_percent_min) if silver_percent_min else None,
                "silver_percent_max": float(silver_percent_max) if silver_percent_max else None,
                "silver_content_min": float(silver_content_min) if silver_content_min else None,
                "silver_content_max": float(silver_content_max) if silver_content_max else None,
                "created_after": created_after.isoformat() if created_after else None,
                "created_before": created_before.isoformat() if created_before else None,
                "sort_by": sort_by,
                "sort_order": sort_order
            }
        }
    
    def _calculate_facets(self) -> Dict[str, List[Dict[str, Any]]]:
        """Calculate facets for filtering"""
        
        # Years facet
        years_result = self.db.query(
            Coin.year,
            func.count(Coin.id).label('count')
        ).filter(
            Coin.year.isnot(None)
        ).group_by(Coin.year).order_by(desc(Coin.year)).limit(20).all()
        
        years_facet = [
            {"value": str(row.year), "count": row.count}
            for row in years_result
        ]
        
        # Denominations facet
        denominations_result = self.db.query(
            Coin.denomination,
            func.count(Coin.id).label('count')
        ).filter(
            Coin.denomination.isnot(None)
        ).group_by(Coin.denomination).order_by(desc('count')).limit(20).all()
        
        denominations_facet = [
            {"value": row.denomination, "count": row.count}
            for row in denominations_result
        ]
        
        # Grades facet
        grades_result = self.db.query(
            Coin.grade,
            func.count(Coin.id).label('count')
        ).filter(
            Coin.grade.isnot(None)
        ).group_by(Coin.grade).order_by(desc('count')).limit(20).all()
        
        grades_facet = [
            {"value": row.grade, "count": row.count}
            for row in grades_result
        ]
        
        # Categories facet
        categories_result = self.db.query(
            Coin.category,
            func.count(Coin.id).label('count')
        ).filter(
            Coin.category.isnot(None)
        ).group_by(Coin.category).order_by(desc('count')).limit(20).all()
        
        categories_facet = [
            {"value": row.category, "count": row.count}
            for row in categories_result
        ]
        
        # Mint marks facet
        mint_marks_result = self.db.query(
            Coin.mint_mark,
            func.count(Coin.id).label('count')
        ).filter(
            Coin.mint_mark.isnot(None)
        ).group_by(Coin.mint_mark).order_by(desc('count')).limit(20).all()
        
        mint_marks_facet = [
            {"value": row.mint_mark, "count": row.count}
            for row in mint_marks_result
        ]
        
        # Status facet
        status_result = self.db.query(
            Coin.status,
            func.count(Coin.id).label('count')
        ).group_by(Coin.status).order_by(desc('count')).all()
        
        status_facet = [
            {"value": row.status, "count": row.count}
            for row in status_result
        ]
        
        return {
            "years": years_facet,
            "denominations": denominations_facet,
            "grades": grades_facet,
            "categories": categories_facet,
            "mint_marks": mint_marks_facet,
            "status": status_facet
        }
    
    def get_search_suggestions(
        self,
        query: str,
        limit: int = 10
    ) -> List[str]:
        """Get search suggestions based on query"""
        
        if len(query) < 2:
            return []
        
        # Get suggestions from titles
        title_suggestions = self.db.query(Coin.title).filter(
            Coin.title.ilike(f"%{query}%")
        ).distinct().limit(limit).all()
        
        suggestions = [row.title for row in title_suggestions]
        
        # Get suggestions from denominations if we have space
        if len(suggestions) < limit:
            denomination_suggestions = self.db.query(Coin.denomination).filter(
                and_(
                    Coin.denomination.ilike(f"%{query}%"),
                    Coin.denomination.notin_(suggestions)
                )
            ).distinct().limit(limit - len(suggestions)).all()
            
            suggestions.extend([row.denomination for row in denomination_suggestions])
        
        return suggestions[:limit]
    
    def bulk_update_coins(
        self,
        coin_ids: List[int],
        updates: Dict[str, Any],
        updated_by: str = "system"
    ) -> Dict[str, Any]:
        """Bulk update coins with individual tracking"""
        
        if not coin_ids:
            return {"updated": 0, "errors": ["No coins selected"]}
        
        updated_count = 0
        errors = []
        
        for coin_id in coin_ids:
            try:
                coin = self.db.query(Coin).filter(Coin.id == coin_id).first()
                if not coin:
                    errors.append(f"Coin {coin_id} not found")
                    continue
                
                # Apply updates
                for field, value in updates.items():
                    if hasattr(coin, field):
                        setattr(coin, field, value)
                
                coin.updated_at = datetime.utcnow()
                updated_count += 1
                
            except Exception as e:
                errors.append(f"Error updating coin {coin_id}: {str(e)}")
        
        self.db.commit()
        
        return {
            "updated": updated_count,
            "total_selected": len(coin_ids),
            "errors": errors
        }
    
    def bulk_price_update(
        self,
        coin_ids: List[int],
        price_strategy: str,
        price_value: Optional[Decimal] = None,
        multiplier: Optional[Decimal] = None,
        updated_by: str = "system"
    ) -> Dict[str, Any]:
        """Bulk price update with individual tracking"""
        
        if not coin_ids:
            return {"updated": 0, "errors": ["No coins selected"]}
        
        updated_count = 0
        errors = []
        price_changes = []
        
        for coin_id in coin_ids:
            try:
                coin = self.db.query(Coin).filter(Coin.id == coin_id).first()
                if not coin:
                    errors.append(f"Coin {coin_id} not found")
                    continue
                
                old_price = coin.computed_price
                new_price = None
                
                if price_strategy == "fixed":
                    new_price = price_value
                elif price_strategy == "multiplier" and multiplier:
                    if coin.entry_melt:
                        new_price = coin.entry_melt * multiplier
                    elif coin.paid_price:
                        new_price = coin.paid_price * multiplier
                elif price_strategy == "profit_margin" and price_value:
                    if coin.paid_price:
                        new_price = coin.paid_price * (1 + price_value)
                
                if new_price is not None:
                    coin.computed_price = new_price
                    coin.updated_at = datetime.utcnow()
                    
                    price_changes.append({
                        "coin_id": coin_id,
                        "coin_title": coin.title,
                        "old_price": float(old_price) if old_price else 0,
                        "new_price": float(new_price),
                        "change": float(new_price - (old_price or 0)),
                        "change_percentage": float(((new_price - (old_price or 0)) / (old_price or 1)) * 100) if old_price else 0
                    })
                    
                    updated_count += 1
                
            except Exception as e:
                errors.append(f"Error updating coin {coin_id}: {str(e)}")
        
        self.db.commit()
        
        return {
            "updated": updated_count,
            "total_selected": len(coin_ids),
            "price_changes": price_changes,
            "errors": errors
        }
    
    def bulk_category_update(
        self,
        coin_ids: List[int],
        category: str,
        updated_by: str = "system"
    ) -> Dict[str, Any]:
        """Bulk category update with individual tracking"""
        
        return self.bulk_update_coins(
            coin_ids=coin_ids,
            updates={"category": category},
            updated_by=updated_by
        )
    
    def bulk_status_update(
        self,
        coin_ids: List[int],
        status: str,
        updated_by: str = "system"
    ) -> Dict[str, Any]:
        """Bulk status update with individual tracking"""
        
        return self.bulk_update_coins(
            coin_ids=coin_ids,
            updates={"status": status},
            updated_by=updated_by
        )
    
    def get_bulk_operation_preview(
        self,
        coin_ids: List[int],
        operation_type: str,
        operation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get preview of bulk operation before execution"""
        
        if not coin_ids:
            return {"coins": [], "total_count": 0, "preview": []}
        
        coins = self.db.query(Coin).filter(Coin.id.in_(coin_ids)).all()
        
        preview = []
        
        for coin in coins:
            preview_item = {
                "coin_id": coin.id,
                "coin_title": coin.title,
                "current_value": None,
                "new_value": None,
                "change_description": ""
            }
            
            if operation_type == "price_update":
                if operation_data.get("strategy") == "fixed":
                    preview_item["current_value"] = float(coin.computed_price) if coin.computed_price else 0
                    preview_item["new_value"] = float(operation_data.get("price", 0))
                    preview_item["change_description"] = f"Price: ${preview_item['current_value']:.2f} → ${preview_item['new_value']:.2f}"
                
                elif operation_data.get("strategy") == "multiplier":
                    multiplier = operation_data.get("multiplier", 1)
                    base_price = coin.entry_melt or coin.paid_price or 0
                    preview_item["current_value"] = float(coin.computed_price) if coin.computed_price else 0
                    preview_item["new_value"] = float(base_price * multiplier)
                    preview_item["change_description"] = f"Price: ${preview_item['current_value']:.2f} → ${preview_item['new_value']:.2f} (×{multiplier})"
            
            elif operation_type == "category_change":
                preview_item["current_value"] = coin.category or "uncategorized"
                preview_item["new_value"] = operation_data.get("category", "")
                preview_item["change_description"] = f"Category: {preview_item['current_value']} → {preview_item['new_value']}"
            
            elif operation_type == "status_change":
                preview_item["current_value"] = coin.status
                preview_item["new_value"] = operation_data.get("status", "")
                preview_item["change_description"] = f"Status: {preview_item['current_value']} → {preview_item['new_value']}"
            
            preview.append(preview_item)
        
        return {
            "coins": coins,
            "total_count": len(coins),
            "preview": preview,
            "operation_type": operation_type,
            "operation_data": operation_data
        }


