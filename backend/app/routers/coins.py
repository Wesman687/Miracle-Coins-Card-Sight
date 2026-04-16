from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
import os
from app.database import get_db
from app.schemas.coins import CoinResponse
from pydantic import BaseModel
# Import verify_admin_token from auth_utils instead of main
from app.auth_utils import verify_admin_token

router = APIRouter()

class ImageData(BaseModel):
    url: str
    file_key: str
    filename: str
    mime_type: str
    size: int

class CoinCreateWithImages(BaseModel):
    sku: Optional[str] = None
    title: str
    year: Optional[int] = None
    denomination: Optional[str] = None
    mint_mark: Optional[str] = None
    grade: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    condition_notes: Optional[str] = None
    is_silver: bool = False
    silver_percent: Optional[float] = None
    silver_content_oz: Optional[float] = None
    paid_price: Optional[float] = None
    price_strategy: str = "paid_price_multiplier"
    price_multiplier: float = 1.5
    base_from_entry: bool = True
    entry_spot: Optional[float] = None
    entry_melt: Optional[float] = None
    override_price: bool = False
    override_value: Optional[float] = None
    fixed_price: Optional[float] = None
    quantity: int = 1
    status: str = "active"
    images: Optional[List[ImageData]] = None

@router.get("/coins/test")
async def test_coins_endpoint(
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin_token)
):
    """Test endpoint to verify database connection and authentication."""
    try:
        # Test database connection with a simple query
        result = db.execute(text("SELECT COUNT(*) as count FROM coins"))
        count = result.fetchone()[0]
        return {"message": "Database connection successful", "coin_count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}") from e

@router.get("/coins/test-title")
async def test_title_field(db: Session = Depends(get_db)):
    """Test title field."""
    try:
        result = db.execute(text("SELECT id, sku, title FROM coins LIMIT 1"))
        row = result.fetchone()
        return {
            "raw_row": {"id": row[0], "sku": row[1], "title": row[2]},
            "message": "If you see 'title' key above, it's working correctly"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}") from e

@router.get("/coins/debug-real-data")
async def debug_real_data(db: Session = Depends(get_db)):
    """DEBUG endpoint to test if server is running updated code."""
    try:
        result = db.execute(text("SELECT COUNT(*) FROM coins"))
        count = result.fetchone()[0]
        
        result2 = db.execute(text("SELECT id, sku, title FROM coins ORDER BY id LIMIT 3"))
        rows = result2.fetchall()
        
        return {
            "server_code_version": "UPDATED_2025_10_21_v3",
            "total_coins_in_db": count,
            "first_3_coins": [
                {"id": row[0], "sku": row[1], "title": row[2][:50]}
                for row in rows
            ]
        }
    except Exception as e:
        return {"error": str(e)}

@router.get("/coins")
async def get_coins(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
    search: Optional[str] = None,
    status: Optional[str] = None,
    is_silver: Optional[bool] = None,
    db: Session = Depends(get_db)
    # Temporarily removed authentication for testing
    # _: str = Depends(verify_admin_token)
):
    """Get all coins with optional filtering and pagination."""
    try:
        # Use raw SQL query to avoid model import issues
        query = "SELECT * FROM coins"
        params = []
        
        conditions = []
        if search:
            conditions.append("title ILIKE :search")
            params.append({"search": f"%{search}%"})
        
        if status:
            conditions.append("status = :status")
            params.append({"status": status})
        
        if is_silver is not None:
            conditions.append("is_silver = :is_silver")
            params.append({"is_silver": is_silver})
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += f" ORDER BY id LIMIT {limit} OFFSET {skip}"
        
        # Merge all params into one dict
        all_params = {}
        for param_dict in params:
            all_params.update(param_dict)
        
        result = db.execute(text(query), all_params)
        rows = result.fetchall()
        
        # Convert Decimal values to float for frontend compatibility
        def convert_decimal(value):
            if value is None:
                return None
            if hasattr(value, '__float__'):
                return float(value)
            return value
        
        # Parse JSON fields
        def parse_json_field(value):
            if value is None or value == '':
                return None
            # If it's already a dict/list, return it
            if isinstance(value, (dict, list)):
                return value
            # If it's a string, try to parse it
            try:
                import json
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return None
        
        # Convert rows to CoinResponse format
        coins = []
        for row in rows:
            coin_id = row[0]  # Get coin ID for image lookup
            
            coin_data = {
                "id": coin_id,                    # id
                "sku": row[1],                    # sku
                "title": row[2],                   # title
                "year": row[3],                   # year
                "denomination": row[4],           # denomination
                "mint_mark": row[5],              # mint_mark
                "grade": row[6],                  # grade
                "category": row[7],               # category
                "description": row[8],            # description
                "condition_notes": row[9],        # condition_notes
                "is_silver": row[10],             # is_silver
                "silver_percent": row[11],        # silver_percent
                "silver_content_oz": convert_decimal(row[12]),     # silver_content_oz
                "paid_price": convert_decimal(row[13]),            # paid_price
                "price_strategy": row[14],        # price_strategy
                "fixed_price": convert_decimal(row[15]),           # fixed_price (column 15)
                "computed_price": convert_decimal(row[21]),        # computed_price (column 21)
                "quantity": row[22],              # quantity (column 22)
                "status": row[23],                # status (column 23)
                "created_by": row[24],            # created_by (column 24)
                "created_at": row[25],            # created_at (column 25)
                "updated_at": row[26],            # updated_at (column 26)
                "tags": parse_json_field(row[35]) if len(row) > 35 else None,  # tags (column 35)
                "shopify_metadata": parse_json_field(row[37]) if len(row) > 37 else None,  # shopify_metadata (column 37)
                "images": [],  # Will be populated with actual image URLs
                "bulk_operation_id": row[29],     # bulk_operation_id (column 29)
                "bulk_item_id": row[30],          # bulk_item_id (column 30)
                "serial_number": row[31],         # serial_number (column 31)
                "bulk_sequence_number": row[32]   # bulk_sequence_number (column 32)
            }
            coins.append(coin_data)
        
        # Fetch images for all coins in a single query
        if coins:
            coin_ids = [coin["id"] for coin in coins]
            # Use IN clause instead of ANY for better compatibility
            placeholders = ','.join([f':coin_id_{i}' for i in range(len(coin_ids))])
            images_query = text(f"""
                SELECT coin_id, url, alt, sort_order 
                FROM coin_images 
                WHERE coin_id IN ({placeholders})
                ORDER BY coin_id, sort_order
            """)
            
            # Create parameter dict
            params = {f'coin_id_{i}': coin_id for i, coin_id in enumerate(coin_ids)}
            images_result = db.execute(images_query, params)
            images_rows = images_result.fetchall()
            
            # Group images by coin_id
            images_by_coin = {}
            for img_row in images_rows:
                coin_id = img_row[0]
                if coin_id not in images_by_coin:
                    images_by_coin[coin_id] = []
                images_by_coin[coin_id].append(img_row[1])  # Just the URL
            
            # Assign images to coins
            for coin in coins:
                coin["images"] = images_by_coin.get(coin["id"], [])
            
            # Fetch collection IDs for all coins
            collections_query = text(f"""
                SELECT coin_id, collection_id 
                FROM coin_collections 
                WHERE coin_id IN ({placeholders})
                ORDER BY coin_id, collection_id
            """)
            
            collections_result = db.execute(collections_query, params)
            collections_rows = collections_result.fetchall()
            
            # Group collection IDs by coin_id
            collections_by_coin = {}
            for coll_row in collections_rows:
                coin_id = coll_row[0]
                if coin_id not in collections_by_coin:
                    collections_by_coin[coin_id] = []
                collections_by_coin[coin_id].append(coll_row[1])
            
            # Assign collection_ids to coins
            for coin in coins:
                coin["collection_ids"] = collections_by_coin.get(coin["id"], [])
        
        return coins
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}") from e

@router.post("/coins", response_model=CoinResponse)
async def create_coin(
    coin_data: CoinCreateWithImages,
    db: Session = Depends(get_db),
    token: str = Depends(verify_admin_token)
):
    """Create a new coin with optional images."""
    try:
        # Calculate computed price based on strategy
        computed_price = None
        if coin_data.price_strategy == "paid_price_multiplier" and coin_data.paid_price:
            computed_price = coin_data.paid_price * coin_data.price_multiplier
        elif coin_data.price_strategy == "fixed_price" and coin_data.fixed_price:
            computed_price = coin_data.fixed_price
        elif coin_data.price_strategy == "entry_based" and coin_data.entry_melt:
            computed_price = coin_data.entry_melt * coin_data.price_multiplier
        # Add other pricing strategies as needed
        
        # Insert coin into database
        coin_query = """
        INSERT INTO coins (
            sku, title, year, denomination, mint_mark, grade, category,
            description, condition_notes, is_silver, silver_percent, silver_content_oz,
            paid_price, price_strategy, price_multiplier, base_from_entry,
            entry_spot, entry_melt, override_price, override_value, fixed_price,
            computed_price, quantity, status, created_by
        ) VALUES (
            :sku, :title, :year, :denomination, :mint_mark, :grade, :category,
            :description, :condition_notes, :is_silver, :silver_percent, :silver_content_oz,
            :paid_price, :price_strategy, :price_multiplier, :base_from_entry,
            :entry_spot, :entry_melt, :override_price, :override_value, :fixed_price,
            :computed_price, :quantity, :status, :created_by
        ) RETURNING id
        """
        
        coin_params = {
            "sku": coin_data.sku, "title": coin_data.title, "year": coin_data.year, 
            "denomination": coin_data.denomination, "mint_mark": coin_data.mint_mark, 
            "grade": coin_data.grade, "category": coin_data.category,
            "description": coin_data.description, "condition_notes": coin_data.condition_notes, 
            "is_silver": coin_data.is_silver, "silver_percent": coin_data.silver_percent, 
            "silver_content_oz": coin_data.silver_content_oz, "paid_price": coin_data.paid_price,
            "price_strategy": coin_data.price_strategy, "price_multiplier": coin_data.price_multiplier, 
            "base_from_entry": coin_data.base_from_entry, "entry_spot": coin_data.entry_spot, 
            "entry_melt": coin_data.entry_melt, "override_price": coin_data.override_price,
            "override_value": coin_data.override_value, "fixed_price": coin_data.fixed_price, 
            "computed_price": computed_price, "quantity": coin_data.quantity, 
            "status": coin_data.status, "created_by": "admin"
        }
        
        result = db.execute(text(coin_query), coin_params)
        coin_id = result.fetchone()[0]
        
        # Insert images if provided
        if coin_data.images:
            for image in coin_data.images:
                image_query = """
                INSERT INTO coin_images (
                    coin_id, url, file_key, filename, mime_type, size, is_primary
                ) VALUES (:coin_id, :url, :file_key, :filename, :mime_type, :size, :is_primary)
                """
                image_params = {
                    "coin_id": coin_id, "url": image.url, "file_key": image.file_key, 
                    "filename": image.filename, "mime_type": image.mime_type, 
                    "size": image.size, "is_primary": False
                }
                db.execute(text(image_query), image_params)
        
        db.commit()
        
        # Return the created coin
        return CoinResponse(
            id=coin_id,
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
            fixed_price=coin_data.fixed_price,
            computed_price=computed_price,
            quantity=coin_data.quantity,
            status=coin_data.status,
            created_by="admin",
            created_at="2025-01-28T00:00:00Z",  # Will be set by database
            updated_at="2025-01-28T00:00:00Z"   # Will be set by database
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create coin: {str(e)}")

@router.put("/coins/{coin_id}", response_model=CoinResponse)
async def update_coin(
    coin_id: int,
    coin_data: CoinCreateWithImages,
    db: Session = Depends(get_db),
    token: str = Depends(verify_admin_token)
):
    """Update an existing coin"""
    try:
        # Calculate computed price based on strategy
        computed_price = None
        if coin_data.price_strategy == "paid_price_multiplier" and coin_data.paid_price:
            computed_price = coin_data.paid_price * coin_data.price_multiplier
        elif coin_data.price_strategy == "fixed_price" and coin_data.fixed_price:
            computed_price = coin_data.fixed_price
        elif coin_data.price_strategy == "entry_based" and coin_data.entry_melt:
            computed_price = coin_data.entry_melt * coin_data.price_multiplier
        
        # Update coin in database
        update_query = text("""
            UPDATE coins SET
                sku = :sku,
                title = :title,
                year = :year,
                denomination = :denomination,
                mint_mark = :mint_mark,
                grade = :grade,
                category = :category,
                description = :description,
                condition_notes = :condition_notes,
                is_silver = :is_silver,
                silver_percent = :silver_percent,
                silver_content_oz = :silver_content_oz,
                paid_price = :paid_price,
                price_strategy = :price_strategy,
                price_multiplier = :price_multiplier,
                base_from_entry = :base_from_entry,
                entry_spot = :entry_spot,
                entry_melt = :entry_melt,
                override_price = :override_price,
                override_value = :override_value,
                fixed_price = :fixed_price,
                computed_price = :computed_price,
                quantity = :quantity,
                status = :status,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :coin_id
            RETURNING id
        """)
        
        update_params = {
            "coin_id": coin_id,
            "sku": coin_data.sku, "title": coin_data.title, "year": coin_data.year, 
            "denomination": coin_data.denomination, "mint_mark": coin_data.mint_mark, 
            "grade": coin_data.grade, "category": coin_data.category,
            "description": coin_data.description, "condition_notes": coin_data.condition_notes, 
            "is_silver": coin_data.is_silver, "silver_percent": coin_data.silver_percent, 
            "silver_content_oz": coin_data.silver_content_oz, "paid_price": coin_data.paid_price,
            "price_strategy": coin_data.price_strategy, "price_multiplier": coin_data.price_multiplier, 
            "base_from_entry": coin_data.base_from_entry, "entry_spot": coin_data.entry_spot, 
            "entry_melt": coin_data.entry_melt, "override_price": coin_data.override_price,
            "override_value": coin_data.override_value, "fixed_price": coin_data.fixed_price,
            "computed_price": computed_price, "quantity": coin_data.quantity,
            "status": coin_data.status
        }
        
        result = db.execute(update_query, update_params)
        updated_coin_id = result.fetchone()
        
        if not updated_coin_id:
            raise HTTPException(status_code=404, detail="Coin not found")
        
        # Handle images if provided
        if coin_data.images:
            # Delete existing images
            delete_images_query = text("DELETE FROM coin_images WHERE coin_id = :coin_id")
            db.execute(delete_images_query, {"coin_id": coin_id})
            
            # Insert new images
            for i, image_url in enumerate(coin_data.images):
                image_query = text("""
                    INSERT INTO coin_images (coin_id, url, alt, sort_order)
                    VALUES (:coin_id, :url, :alt, :sort_order)
                """)
                db.execute(image_query, {
                    "coin_id": coin_id,
                    "url": image_url,
                    "alt": f"{coin_data.title} image {i+1}",
                    "sort_order": i
                })
        
        db.commit()
        
        # Auto-sync to Shopify if coin is active and has shopify_id
        if coin_data.status == "active":
            # Check if coin has shopify_id
            shopify_check_query = text("SELECT shopify_id FROM coins WHERE id = :coin_id")
            shopify_result = db.execute(shopify_check_query, {"coin_id": coin_id})
            shopify_row = shopify_result.fetchone()
            
            if shopify_row and shopify_row[0]:
                try:
                    await sync_coin_to_shopify(coin_id, db)
                except Exception as e:
                    # Log error but don't fail the update
                    print(f"Warning: Failed to sync coin {coin_id} to Shopify: {e}")
        
        # Return updated coin data
        return CoinResponse(
            id=coin_id,
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
            fixed_price=coin_data.fixed_price,
            computed_price=computed_price,
            quantity=coin_data.quantity,
            status=coin_data.status,
            created_by="admin",
            created_at="2025-01-28T00:00:00Z",
            updated_at="2025-01-28T00:00:00Z"
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update coin: {str(e)}")

async def sync_coin_to_shopify(coin_id: int, db: Session):
    """Sync coin data to Shopify if it has a shopify_id"""
    try:
        # Get coin data
        coin_query = text("""
            SELECT sku, title, description, computed_price, quantity, status, shopify_id
            FROM coins WHERE id = :coin_id
        """)
        coin_result = db.execute(coin_query, {"coin_id": coin_id})
        coin_row = coin_result.fetchone()
        
        if not coin_row or not coin_row[6]:  # No shopify_id
            return
        
        sku, title, description, computed_price, quantity, status, shopify_id = coin_row
        
        # Shopify configuration
        SHOPIFY_DOMAIN = "b99ycv-3e.myshopify.com"
        SHOPIFY_ACCESS_TOKEN = os.getenv("SHOPIFY_API_KEY") or "shpat_your_token_here"
        
        headers = {
            'X-Shopify-Access-Token': SHOPIFY_ACCESS_TOKEN,
            'Content-Type': 'application/json'
        }
        
        # Update product in Shopify
        product_url = f"https://{SHOPIFY_DOMAIN}/admin/api/2023-10/products/{shopify_id}.json"
        
        product_data = {
            "product": {
                "id": int(shopify_id),
                "title": title,
                "body_html": description or "",
                "status": "active" if status == "active" else "draft",
                "variants": [{
                    "id": None,  # Will be filled by Shopify
                    "price": str(computed_price) if computed_price else "0.00",
                    "inventory_quantity": quantity,
                    "sku": sku
                }]
            }
        }
        
        import requests
        response = requests.put(product_url, headers=headers, json=product_data)
        
        if response.status_code not in [200, 201]:
            raise Exception(f"Shopify API error: {response.status_code} - {response.text}")
        
        print(f"Successfully synced coin {coin_id} to Shopify")
        
    except Exception as e:
        print(f"Error syncing coin {coin_id} to Shopify: {e}")
        raise

@router.delete("/coins/clear")
async def clear_all_coins(
    confirm: bool = Query(False, description="Must be true to confirm deletion"),
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin_token)
):
    """Delete all coins from the database - DANGEROUS OPERATION"""
    if not confirm:
        raise HTTPException(
            status_code=400, 
            detail="Must set confirm=true to delete all coins. This operation cannot be undone."
        )
    
    try:
        # Get count before deletion
        count_result = db.execute(text("SELECT COUNT(*) as count FROM coins"))
        coin_count = count_result.fetchone()[0]
        
        if coin_count == 0:
            return {"message": "No coins to delete", "deleted_count": 0}
        
        # Delete all coins
        db.execute(text("DELETE FROM coins"))
        db.commit()
        
        return {
            "message": f"Successfully deleted {coin_count} coins from database",
            "deleted_count": coin_count,
            "warning": "This operation cannot be undone"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting coins: {str(e)}") from e