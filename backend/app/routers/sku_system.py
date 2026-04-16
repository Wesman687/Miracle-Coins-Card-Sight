"""
Two-Part SKU System API Router
Format: [PREFIX]-[SEQUENCE] (e.g., ASE-001, MOR-002)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.auth_utils import verify_admin_token
from app.services.sku_service import SKUService
from app.schemas.sku_system import (
    SKUPrefixCreate, SKUPrefixUpdate, SKUPrefixResponse,
    SKUSequenceResponse, SKUGenerationRequest, SKUGenerationResponse,
    SKUBulkOperationRequest, SKUBulkOperationResponse, SKUStatsResponse
)

router = APIRouter(
    prefix="/sku",
    tags=["sku-management"],
    dependencies=[Depends(verify_admin_token)]
)

@router.post("/prefixes", response_model=SKUPrefixResponse, status_code=status.HTTP_201_CREATED)
async def create_prefix(
    prefix_data: SKUPrefixCreate,
    db: Session = Depends(get_db)
):
    """Create a new SKU prefix"""
    service = SKUService(db)
    try:
        return service.create_prefix(prefix_data)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/prefixes", response_model=List[SKUPrefixResponse])
async def list_prefixes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """List all SKU prefixes"""
    service = SKUService(db)
    return service.list_prefixes(skip=skip, limit=limit)

@router.get("/prefixes/{prefix_id}", response_model=SKUPrefixResponse)
async def get_prefix(
    prefix_id: int,
    db: Session = Depends(get_db)
):
    """Get SKU prefix by ID"""
    service = SKUService(db)
    prefix = service.get_prefix(prefix_id)
    if not prefix:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prefix not found")
    return prefix

@router.put("/prefixes/{prefix_id}", response_model=SKUPrefixResponse)
async def update_prefix(
    prefix_id: int,
    prefix_data: SKUPrefixUpdate,
    db: Session = Depends(get_db)
):
    """Update SKU prefix"""
    service = SKUService(db)
    prefix = service.update_prefix(prefix_id, prefix_data)
    if not prefix:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prefix not found")
    return prefix

@router.delete("/prefixes/{prefix_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prefix(
    prefix_id: int,
    db: Session = Depends(get_db)
):
    """Delete SKU prefix"""
    service = SKUService(db)
    try:
        success = service.delete_prefix(prefix_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prefix not found")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/generate", response_model=SKUGenerationResponse)
async def generate_sku(
    request: SKUGenerationRequest,
    db: Session = Depends(get_db)
):
    """Generate next SKU(s) for a prefix"""
    service = SKUService(db)
    try:
        if request.count == 1:
            # Single SKU generation
            sku = service.generate_next_sku(request.prefix)
            return SKUGenerationResponse(
                prefix=request.prefix,
                start_sequence=int(sku.split('-')[1]),
                end_sequence=int(sku.split('-')[1]),
                skus=[sku],
                total_generated=1
            )
        else:
            # Bulk SKU generation
            start_seq, end_seq = service.generate_sku_range(request.prefix, request.count)
            skus = [f"{request.prefix}-{i:03d}" for i in range(start_seq, end_seq + 1)]
            return SKUGenerationResponse(
                prefix=request.prefix,
                start_sequence=start_seq,
                end_sequence=end_seq,
                skus=skus,
                total_generated=len(skus)
            )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/stats", response_model=SKUStatsResponse)
async def get_sku_stats(
    db: Session = Depends(get_db)
):
    """Get SKU system statistics"""
    service = SKUService(db)
    try:
        return service.get_sku_stats()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/migrate", status_code=status.HTTP_200_OK)
async def migrate_existing_skus(
    db: Session = Depends(get_db)
):
    """Migrate existing SKUs to new two-part format"""
    service = SKUService(db)
    try:
        result = service.migrate_existing_skus()
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
