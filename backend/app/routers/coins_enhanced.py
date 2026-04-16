from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.services.coin_service import CoinService
from app.schemas.coin_metadata import (
    CoinCreateWithMetadata, CoinUpdateWithMetadata, CoinWithMetadata,
    CoinMetadataCreate, CoinMetadataUpdate, CoinListResponse,
    CategoryMetadataTemplate
)

router = APIRouter(prefix="/api/v1/coins", tags=["coins-enhanced"])

# Coin Management with Metadata
@router.post("/", response_model=CoinWithMetadata, status_code=201)
async def create_coin_with_metadata(
    coin_data: CoinCreateWithMetadata,
    db: Session = Depends(get_db)
):
    """Create a new coin with category metadata fields"""
    service = CoinService(db)
    return service.create_coin_with_metadata(coin_data)

@router.get("/", response_model=CoinListResponse)
async def list_coins_with_metadata(
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    search: Optional[str] = Query(None, description="Search in title, sku, or description"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """List coins with metadata, filtering and pagination"""
    service = CoinService(db)
    coins, total = service.list_coins_with_metadata(
        category_id=category_id,
        search=search,
        page=page,
        per_page=per_page
    )
    
    total_pages = (total + per_page - 1) // per_page
    
    return CoinListResponse(
        coins=coins,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )

@router.get("/{coin_id}", response_model=CoinWithMetadata)
async def get_coin_with_metadata(
    coin_id: int = Path(..., description="Coin ID"),
    db: Session = Depends(get_db)
):
    """Get a specific coin with all its metadata"""
    service = CoinService(db)
    coin = service.get_coin_with_metadata(coin_id)
    if not coin:
        raise HTTPException(status_code=404, detail="Coin not found")
    return coin

@router.put("/{coin_id}", response_model=CoinWithMetadata)
async def update_coin_with_metadata(
    coin_id: int = Path(..., description="Coin ID"),
    coin_data: CoinUpdateWithMetadata = None,
    db: Session = Depends(get_db)
):
    """Update a coin and its metadata"""
    service = CoinService(db)
    coin = service.update_coin_with_metadata(coin_id, coin_data)
    if not coin:
        raise HTTPException(status_code=404, detail="Coin not found")
    return coin

@router.delete("/{coin_id}", status_code=204)
async def delete_coin(
    coin_id: int = Path(..., description="Coin ID"),
    db: Session = Depends(get_db)
):
    """Delete a coin and all its metadata"""
    service = CoinService(db)
    success = service.delete_coin(coin_id)
    if not success:
        raise HTTPException(status_code=404, detail="Coin not found")

# Metadata Management
@router.get("/{coin_id}/metadata", response_model=List[dict])
async def get_coin_metadata(
    coin_id: int = Path(..., description="Coin ID"),
    db: Session = Depends(get_db)
):
    """Get all metadata for a specific coin"""
    service = CoinService(db)
    coin = service.get_coin_with_metadata(coin_id)
    if not coin:
        raise HTTPException(status_code=404, detail="Coin not found")
    
    return coin.metadata

@router.put("/{coin_id}/metadata", response_model=CoinWithMetadata)
async def update_coin_metadata(
    coin_id: int = Path(..., description="Coin ID"),
    metadata: dict = Body(..., description="Metadata field name to value mapping"),
    db: Session = Depends(get_db)
):
    """Update metadata for a specific coin"""
    service = CoinService(db)
    
    # Check if coin exists
    coin = service.get_coin_with_metadata(coin_id)
    if not coin:
        raise HTTPException(status_code=404, detail="Coin not found")
    
    # Update metadata
    service._update_coin_metadata(coin_id, metadata)
    db.commit()
    
    # Return updated coin
    updated_coin = service.get_coin_with_metadata(coin_id)
    return updated_coin

@router.post("/bulk-metadata", response_model=dict)
async def bulk_update_coin_metadata(
    updates: List[dict] = Body(..., description="List of coin_id and metadata updates"),
    db: Session = Depends(get_db)
):
    """Bulk update metadata for multiple coins"""
    service = CoinService(db)
    result = service.bulk_update_coin_metadata(updates)
    return result

# Category Metadata Templates
@router.get("/metadata-templates/{category_id}", response_model=List[CategoryMetadataTemplate])
async def get_category_metadata_templates(
    category_id: int = Path(..., description="Category ID"),
    db: Session = Depends(get_db)
):
    """Get metadata field templates for a category"""
    service = CoinService(db)
    templates = service.get_coin_metadata_templates(category_id)
    return templates

# Category Management (Enhanced)
@router.get("/categories/{category_id}/coins", response_model=CoinListResponse)
async def get_coins_by_category(
    category_id: int = Path(..., description="Category ID"),
    search: Optional[str] = Query(None, description="Search in title, sku, or description"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """Get all coins in a specific category with metadata"""
    service = CoinService(db)
    coins, total = service.list_coins_with_metadata(
        category_id=category_id,
        search=search,
        page=page,
        per_page=per_page
    )
    
    total_pages = (total + per_page - 1) // per_page
    
    return CoinListResponse(
        coins=coins,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )

# Search and Filter
@router.get("/search/advanced", response_model=CoinListResponse)
async def advanced_coin_search(
    search: Optional[str] = Query(None, description="Search term"),
    category_id: Optional[int] = Query(None, description="Filter by category"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """Advanced search with metadata filtering"""
    service = CoinService(db)
    
    # For now, use basic search - advanced metadata filtering can be added later
    coins, total = service.list_coins_with_metadata(
        category_id=category_id,
        search=search,
        page=page,
        per_page=per_page
    )
    
    total_pages = (total + per_page - 1) // per_pages
    
    return CoinListResponse(
        coins=coins,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )
