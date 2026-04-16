from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date, timedelta

from app.database import get_db
from app.models.inventory import Location, InventoryItem, InventoryMovement, DeadStockAnalysis, InventoryMetrics
from app.models import Coin
from app.schemas.inventory import (
    LocationCreate, LocationResponse, InventoryMetricsResponse,
    InventoryMovementCreate, DeadStockAnalysisResponse,
    TurnoverAnalysisResponse, InventoryAlertRuleCreate, InventoryAlertRule
)
from app.services.inventory_service import InventoryService
from app.auth import get_current_admin_user

router = APIRouter(prefix="/inventory", tags=["inventory"])

@router.get("/metrics", response_model=InventoryMetricsResponse)
async def get_inventory_metrics(
    location: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Get comprehensive inventory metrics"""
    
    inventory_service = InventoryService(db)
    
    metrics = await inventory_service.get_inventory_metrics(
        location_filter=location,
        category_filter=category
    )
    
    return metrics

@router.get("/dead-stock", response_model=List[DeadStockAnalysisResponse])
async def get_dead_stock(
    category: Optional[str] = Query("dead_stock"),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Get dead stock analysis"""
    
    inventory_service = InventoryService(db)
    
    dead_stock = await inventory_service.get_dead_stock_analysis(
        category=category,
        limit=limit
    )
    
    return dead_stock

@router.get("/profit-margins")
async def get_profit_margin_analysis(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Analyze profit margins by category"""
    
    inventory_service = InventoryService(db)
    
    margin_analysis = await inventory_service._get_profit_margin_analysis()
    
    return margin_analysis

@router.get("/turnover-analysis")
async def get_turnover_analysis(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Get inventory turnover analysis"""
    
    inventory_service = InventoryService(db)
    
    turnover_data = await inventory_service.get_turnover_analysis()
    
    return turnover_data

@router.get("/locations", response_model=List[LocationResponse])
async def get_locations(
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Get all locations"""
    
    query = db.query(Location)
    if active_only:
        query = query.filter(Location.active == True)
    
    locations = query.all()
    return locations

@router.post("/locations", response_model=LocationResponse)
async def create_location(
    location_data: LocationCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Create a new location"""
    
    # Check if location name already exists
    existing = db.query(Location).filter(
        Location.name == location_data.name
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Location name already exists")
    
    location = Location(
        name=location_data.name,
        address=location_data.address,
        location_type=location_data.location_type,
        settings=location_data.settings
    )
    
    db.add(location)
    db.commit()
    db.refresh(location)
    
    return location

@router.put("/locations/{location_id}", response_model=LocationResponse)
async def update_location(
    location_id: int,
    location_data: LocationCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Update a location"""
    
    location = db.query(Location).filter(Location.id == location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    # Check if new name conflicts with existing location
    if location_data.name != location.name:
        existing = db.query(Location).filter(
            Location.name == location_data.name,
            Location.id != location_id
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="Location name already exists")
    
    # Update location
    location.name = location_data.name
    location.address = location_data.address
    location.location_type = location_data.location_type
    location.settings = location_data.settings
    location.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(location)
    
    return location

@router.delete("/locations/{location_id}")
async def delete_location(
    location_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Delete a location (soft delete by deactivating)"""
    
    location = db.query(Location).filter(Location.id == location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    # Check if location has inventory
    inventory_count = db.query(InventoryItem).filter(
        InventoryItem.location_id == location_id
    ).count()
    
    if inventory_count > 0:
        # Soft delete by deactivating
        location.active = False
        location.updated_at = datetime.utcnow()
        db.commit()
        return {"message": "Location deactivated (has existing inventory)"}
    
    # Hard delete if no inventory
    db.delete(location)
    db.commit()
    
    return {"message": "Location deleted successfully"}

@router.post("/movements")
async def create_inventory_movement(
    movement_data: InventoryMovementCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Create an inventory movement"""
    
    inventory_service = InventoryService(db)
    
    # Validate coin exists
    coin = db.query(Coin).filter(Coin.id == movement_data.coin_id).first()
    if not coin:
        raise HTTPException(status_code=404, detail="Coin not found")
    
    # Validate locations exist
    if movement_data.from_location_id:
        from_location = db.query(Location).filter(Location.id == movement_data.from_location_id).first()
        if not from_location:
            raise HTTPException(status_code=404, detail="Source location not found")
    
    to_location = db.query(Location).filter(Location.id == movement_data.to_location_id).first()
    if not to_location:
        raise HTTPException(status_code=404, detail="Destination location not found")
    
    movement = await inventory_service.create_inventory_movement(
        coin_id=movement_data.coin_id,
        from_location_id=movement_data.from_location_id,
        to_location_id=movement_data.to_location_id,
        quantity=movement_data.quantity,
        movement_type=movement_data.movement_type,
        reason=movement_data.reason,
        reference_id=movement_data.reference_id,
        moved_by=current_user.get("username", "admin")
    )
    
    return movement

@router.post("/transfer")
async def transfer_inventory(
    coin_id: int,
    from_location_id: int,
    to_location_id: int,
    quantity: int,
    reason: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Transfer inventory between locations"""
    
    inventory_service = InventoryService(db)
    
    try:
        movement = await inventory_service.transfer_inventory(
            coin_id=coin_id,
            from_location_id=from_location_id,
            to_location_id=to_location_id,
            quantity=quantity,
            reason=reason,
            moved_by=current_user.get("username", "admin")
        )
        
        return movement
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/movements")
async def get_inventory_movements(
    coin_id: Optional[int] = Query(None),
    location_id: Optional[int] = Query(None),
    movement_type: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Get inventory movements"""
    
    query = db.query(InventoryMovement)
    
    if coin_id:
        query = query.filter(InventoryMovement.coin_id == coin_id)
    
    if location_id:
        query = query.filter(
            or_(
                InventoryMovement.from_location_id == location_id,
                InventoryMovement.to_location_id == location_id
            )
        )
    
    if movement_type:
        query = query.filter(InventoryMovement.movement_type == movement_type)
    
    movements = query.order_by(InventoryMovement.moved_at.desc()).limit(limit).all()
    
    return movements

@router.get("/items")
async def get_inventory_items(
    location_id: Optional[int] = Query(None),
    coin_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Get inventory items"""
    
    query = db.query(InventoryItem)
    
    if location_id:
        query = query.filter(InventoryItem.location_id == location_id)
    
    if coin_id:
        query = query.filter(InventoryItem.coin_id == coin_id)
    
    items = query.all()
    
    # Add coin and location details
    result = []
    for item in items:
        coin = db.query(Coin).filter(Coin.id == item.coin_id).first()
        location = db.query(Location).filter(Location.id == item.location_id).first()
        
        result.append({
            "id": item.id,
            "coin_id": item.coin_id,
            "coin_title": coin.title if coin else "Unknown",
            "location_id": item.location_id,
            "location_name": location.name if location else "Unknown",
            "quantity": item.quantity,
            "reserved_quantity": item.reserved_quantity,
            "available_quantity": item.available_quantity,
            "last_counted": item.last_counted,
            "last_moved": item.last_moved,
            "notes": item.notes,
            "created_at": item.created_at,
            "updated_at": item.updated_at
        })
    
    return result

@router.post("/items", response_model=dict)
async def create_inventory_item(
    coin_id: int,
    location_id: int,
    quantity: int,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Create an inventory item"""
    
    # Validate coin exists
    coin = db.query(Coin).filter(Coin.id == coin_id).first()
    if not coin:
        raise HTTPException(status_code=404, detail="Coin not found")
    
    # Validate location exists
    location = db.query(Location).filter(Location.id == location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    # Check if inventory item already exists
    existing_item = db.query(InventoryItem).filter(
        and_(
            InventoryItem.coin_id == coin_id,
            InventoryItem.location_id == location_id
        )
    ).first()
    
    if existing_item:
        # Update existing item
        existing_item.quantity += quantity
        existing_item.available_quantity += quantity
        existing_item.updated_at = datetime.utcnow()
        if notes:
            existing_item.notes = notes
        
        db.commit()
        db.refresh(existing_item)
        
        return {"message": "Inventory item updated", "item": existing_item}
    
    # Create new inventory item
    item = InventoryItem(
        coin_id=coin_id,
        location_id=location_id,
        quantity=quantity,
        available_quantity=quantity,
        notes=notes
    )
    
    db.add(item)
    db.commit()
    db.refresh(item)
    
    return {"message": "Inventory item created", "item": item}

@router.put("/items/{item_id}")
async def update_inventory_item(
    item_id: int,
    quantity: Optional[int] = None,
    reserved_quantity: Optional[int] = None,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Update an inventory item"""
    
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    
    # Update fields
    if quantity is not None:
        item.quantity = quantity
        item.available_quantity = quantity - (item.reserved_quantity or 0)
    
    if reserved_quantity is not None:
        item.reserved_quantity = reserved_quantity
        item.available_quantity = item.quantity - reserved_quantity
    
    if notes is not None:
        item.notes = notes
    
    item.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(item)
    
    return {"message": "Inventory item updated", "item": item}


