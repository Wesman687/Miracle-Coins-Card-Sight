from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from decimal import Decimal

from app.database import get_db
from app.models import Coin
from app.schemas.search import (
    SearchRequest, SearchResponse, BulkOperationRequest, BulkOperationResult,
    SearchSuggestionResponse, BulkOperationPreview, AdvancedSearchFilters
)
from app.services.search_service import SearchService
from app.auth import get_current_admin_user

router = APIRouter(prefix="/search", tags=["search"])

@router.post("/advanced", response_model=SearchResponse)
async def advanced_search(
    search_request: SearchRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Advanced search with multiple criteria"""
    
    search_service = SearchService(db)
    
    result = await search_service.advanced_search(
        query=search_request.query,
        year=search_request.year,
        denomination=search_request.denomination,
        grade=search_request.grade,
        category=search_request.category,
        min_price=search_request.min_price,
        max_price=search_request.max_price,
        min_paid_price=search_request.min_paid_price,
        max_paid_price=search_request.max_paid_price,
        is_silver=search_request.is_silver,
        status=search_request.status,
        mint_mark=search_request.mint_mark,
        silver_percent_min=search_request.silver_percent_min,
        silver_percent_max=search_request.silver_percent_max,
        silver_content_min=search_request.silver_content_min,
        silver_content_max=search_request.silver_content_max,
        created_after=search_request.created_after,
        created_before=search_request.created_before,
        sort_by=search_request.sort_by,
        sort_order=search_request.sort_order,
        limit=search_request.limit,
        offset=search_request.offset
    )
    
    return result

@router.get("/suggestions")
async def get_search_suggestions(
    q: str = Query(..., min_length=2),
    limit: int = Query(10, le=50),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Get search suggestions based on query"""
    
    search_service = SearchService(db)
    
    suggestions = await search_service.get_search_suggestions(
        query=q,
        limit=limit
    )
    
    return SearchSuggestionResponse(
        suggestions=suggestions,
        query=q
    )

@router.post("/bulk/preview")
async def preview_bulk_operation(
    operation_request: BulkOperationRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Preview bulk operation before execution"""
    
    search_service = SearchService(db)
    
    preview = await search_service.get_bulk_operation_preview(
        coin_ids=operation_request.selected_coins,
        operation_type=operation_request.operation_type,
        operation_data=operation_request.operation_data
    )
    
    return preview

@router.post("/bulk/price-update")
async def bulk_price_update(
    coin_ids: List[int],
    strategy: str = Query(..., pattern="^(fixed|multiplier|profit_margin)$"),
    price: Optional[Decimal] = Query(None, ge=0),
    multiplier: Optional[Decimal] = Query(None, ge=0.1, le=10),
    profit_margin: Optional[Decimal] = Query(None, ge=0, le=5),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Bulk price update with individual tracking"""
    
    search_service = SearchService(db)
    
    result = await search_service.bulk_price_update(
        coin_ids=coin_ids,
        price_strategy=strategy,
        price_value=price,
        multiplier=multiplier,
        updated_by=current_user.get("username", "admin")
    )
    
    return result

@router.post("/bulk/category-update")
async def bulk_category_update(
    coin_ids: List[int],
    category: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Bulk category update with individual tracking"""
    
    search_service = SearchService(db)
    
    result = await search_service.bulk_category_update(
        coin_ids=coin_ids,
        category=category,
        updated_by=current_user.get("username", "admin")
    )
    
    return result

@router.post("/bulk/status-update")
async def bulk_status_update(
    coin_ids: List[int],
    status: str = Query(..., pattern="^(active|inactive|sold|reserved)$"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Bulk status update with individual tracking"""
    
    search_service = SearchService(db)
    
    result = await search_service.bulk_status_update(
        coin_ids=coin_ids,
        status=status,
        updated_by=current_user.get("username", "admin")
    )
    
    return result

@router.post("/bulk/execute")
async def execute_bulk_operation(
    operation_request: BulkOperationRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Execute bulk operation"""
    
    search_service = SearchService(db)
    
    if operation_request.operation_type == "price_update":
        operation_data = operation_request.operation_data
        result = await search_service.bulk_price_update(
            coin_ids=operation_request.selected_coins,
            price_strategy=operation_data.get("strategy", "fixed"),
            price_value=operation_data.get("price"),
            multiplier=operation_data.get("multiplier"),
            updated_by=current_user.get("username", "admin")
        )
    
    elif operation_request.operation_type == "category_change":
        result = await search_service.bulk_category_update(
            coin_ids=operation_request.selected_coins,
            category=operation_request.operation_data.get("category", ""),
            updated_by=current_user.get("username", "admin")
        )
    
    elif operation_request.operation_type == "status_change":
        result = await search_service.bulk_status_update(
            coin_ids=operation_request.selected_coins,
            status=operation_request.operation_data.get("status", "active"),
            updated_by=current_user.get("username", "admin")
        )
    
    else:
        raise HTTPException(status_code=400, detail="Unsupported operation type")
    
    return result

@router.get("/facets")
async def get_search_facets(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Get search facets for filtering"""
    
    search_service = SearchService(db)
    
    facets = await search_service._calculate_facets()
    
    return facets

@router.get("/quick-filters")
async def get_quick_filters(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Get predefined quick filters"""
    
    quick_filters = [
        {
            "name": "silver_coins",
            "label": "Silver Coins",
            "criteria": {"is_silver": True},
            "count": 0  # Would be calculated from database
        },
        {
            "name": "high_value",
            "label": "High Value (>$100)",
            "criteria": {"min_price": 100},
            "count": 0
        },
        {
            "name": "recent_additions",
            "label": "Recent Additions",
            "criteria": {"created_after": "2024-01-01"},
            "count": 0
        },
        {
            "name": "premium_grade",
            "label": "Premium Grade (MS65+)",
            "criteria": {"grade": "MS65"},
            "count": 0
        },
        {
            "name": "bullion",
            "label": "Bullion Coins",
            "criteria": {"category": "bullion"},
            "count": 0
        }
    ]
    
    return quick_filters

@router.get("/stats")
async def get_search_stats(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Get search statistics"""
    
    from sqlalchemy import func
    
    # Total coins
    total_coins = db.query(func.count()).select_from(Coin).scalar()
    
    # Active coins
    active_coins = db.query(func.count()).select_from(Coin).filter(Coin.status == "active").scalar()
    
    # Sold coins
    sold_coins = db.query(func.count()).select_from(Coin).filter(Coin.status == "sold").scalar()
    
    # Total value
    total_value = db.query(func.sum(Coin.computed_price * Coin.quantity)).scalar() or Decimal('0')
    
    # Average price
    avg_price = db.query(func.avg(Coin.computed_price)).scalar() or Decimal('0')
    
    # Price range
    min_price = db.query(func.min(Coin.computed_price)).scalar() or Decimal('0')
    max_price = db.query(func.max(Coin.computed_price)).scalar() or Decimal('0')
    
    # Category breakdown
    category_breakdown = db.query(
        Coin.category,
        func.count(Coin.id).label('count')
    ).group_by(Coin.category).all()
    
    # Year range
    min_year = db.query(func.min(Coin.year)).scalar()
    max_year = db.query(func.max(Coin.year)).scalar()
    
    return {
        "total_coins": total_coins,
        "active_coins": active_coins,
        "sold_coins": sold_coins,
        "total_value": float(total_value),
        "average_price": float(avg_price),
        "price_range": {
            "min": float(min_price),
            "max": float(max_price)
        },
        "category_breakdown": {
            row.category or "uncategorized": row.count
            for row in category_breakdown
        },
        "year_range": {
            "min": min_year,
            "max": max_year
        }
    }

@router.get("/history")
async def get_search_history(
    limit: int = Query(10, le=50),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Get search history (placeholder - would be implemented with user tracking)"""
    
    # This would typically be stored in a separate table tracking user searches
    return {
        "recent_searches": [],
        "saved_searches": []
    }

@router.post("/save-search")
async def save_search(
    name: str,
    filters: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Save a search for later use (placeholder)"""
    
    # This would typically save to a user_saved_searches table
    return {"message": "Search saved successfully", "name": name}
