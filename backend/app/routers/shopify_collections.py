from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from typing import List, Optional, Dict, Any
import requests
import logging
import os
import json
from datetime import datetime
from dotenv import load_dotenv
from app.database import get_db
from app.auth import get_current_admin_user

# Load environment variables from parent directory
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/collections")
async def get_shopify_collections(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Fetch collections from Shopify"""
    try:
        # Use the Shopify domain from memory state
        shop_domain = "b99ycv-3e.myshopify.com"
        
        # Get Shopify access token from environment
        access_token = os.getenv("SHOPIFY_API_KEY") 
        
        if not access_token:
            raise HTTPException(
                status_code=400, 
                detail="Shopify access token not configured. Please set SHOPIFY_API_KEY environment variable."
            )
        
        # Get collections from Shopify (custom collections and smart collections)
        headers = {
            "X-Shopify-Access-Token": access_token,
            "Content-Type": "application/json"
        }
        
        all_collections = []
        
        # Get custom collections
        try:
            custom_collections_url = f"https://{shop_domain}/admin/api/2023-07/custom_collections.json"
            response = requests.get(custom_collections_url, headers=headers, timeout=30)
            if response.status_code == 200:
                data = response.json()
                custom_collections = data.get("custom_collections", [])
                all_collections.extend(custom_collections)
                logger.info(f"Found {len(custom_collections)} custom collections")
        except requests.exceptions.RequestException as e:
            logger.warning(f"Failed to fetch custom collections: {e}")
        
        # Get smart collections
        try:
            smart_collections_url = f"https://{shop_domain}/admin/api/2023-07/smart_collections.json"
            response = requests.get(smart_collections_url, headers=headers, timeout=30)
            if response.status_code == 200:
                data = response.json()
                smart_collections = data.get("smart_collections", [])
                all_collections.extend(smart_collections)
                logger.info(f"Found {len(smart_collections)} smart collections")
        except requests.exceptions.RequestException as e:
            logger.warning(f"Failed to fetch smart collections: {e}")
        
        if all_collections:
            # Transform Shopify collections data to our format
            formatted_collections = []
            for collection in all_collections:
                formatted_collections.append({
                    "id": collection.get("id"),
                    "title": collection.get("title"),
                    "handle": collection.get("handle"),
                    "description": collection.get("body_html", ""),
                    "updated_at": collection.get("updated_at"),
                    "product_count": collection.get("products_count", 0)
                })
            
            logger.info(f"Successfully fetched {len(formatted_collections)} collections from Shopify")
            return {"collections": formatted_collections}
        
        # If no collections found, create collections based on product types
        products_url = f"https://{shop_domain}/admin/api/2023-07/products.json"
        response = requests.get(products_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        products_data = response.json()
        products = products_data.get("products", [])
        
        # Extract unique product types and create collections
        product_types = {}
        for product in products:
            product_type = product.get("product_type", "Uncategorized")
            if product_type not in product_types:
                product_types[product_type] = {
                    "count": 0,
                    "products": []
                }
            product_types[product_type]["count"] += 1
            product_types[product_type]["products"].append(product.get("title", ""))
        
        # Transform product types to collections format
        formatted_collections = []
        for i, (product_type, data) in enumerate(product_types.items(), 1):
            formatted_collections.append({
                "id": f"product_type_{i}",
                "title": product_type,
                "handle": product_type.lower().replace(" ", "-").replace("%", "percent"),
                "description": f"Collection of {product_type} products",
                "updated_at": "2024-01-01T00:00:00Z",
                "product_count": data["count"]
            })
        
        logger.info(f"Created {len(formatted_collections)} collections from product types")
        return {"collections": formatted_collections}
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Shopify API error: {str(e)}")
        raise HTTPException(status_code=502, detail=f"Failed to connect to Shopify: {str(e)}")
    except Exception as e:
        logger.error(f"Error fetching Shopify collections: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch Shopify collections: {str(e)}")

@router.post("/collections/import")
async def import_shopify_collections(
    collection_ids: Optional[List[str]] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Import Shopify collections into local collections table"""
    try:
        from app.models.collections import Collection
        
        # Get collections from Shopify
        shopify_response = await get_shopify_collections(db, current_user)
        shopify_collections = shopify_response["collections"]
        
        # Filter by collection_ids if provided
        if collection_ids:
            shopify_collections = [
                c for c in shopify_collections 
                if c["id"] in collection_ids
            ]
        
        imported_collections = []
        
        for shopify_collection in shopify_collections:
            # Convert ID to string to match database schema
            collection_id_str = str(shopify_collection["id"])
            
            # Check if collection already exists
            existing = db.query(Collection).filter(
                Collection.shopify_collection_id == collection_id_str
            ).first()
            
            if existing:
                # Update existing collection
                existing.name = shopify_collection["title"]
                existing.description = shopify_collection.get("description", "")
                existing.updated_at = datetime.utcnow()
                imported_collections.append(existing)
            else:
                # Create new collection
                new_collection = Collection(
                    name=shopify_collection["title"],
                    description=shopify_collection.get("description", ""),
                    shopify_collection_id=collection_id_str,
                    color="#3b82f6",  # Default blue color
                    default_markup=1.3  # Default markup
                )
                db.add(new_collection)
                imported_collections.append(new_collection)
        
        db.commit()
        
        return {
            "message": f"Successfully imported {len(imported_collections)} collections",
            "collections": [
                {
                    "id": c.id,
                    "name": c.name,
                    "description": c.description,
                    "shopify_collection_id": c.shopify_collection_id
                } for c in imported_collections
            ]
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error importing Shopify collections: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to import collections: {str(e)}")

@router.get("/products")
async def get_shopify_products(
    limit: int = Query(250, ge=1, le=250, description="Number of products to fetch per page"),
    page_info: Optional[str] = Query(None, description="Pagination cursor for next page"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Fetch products from Shopify"""
    try:
        # Use the Shopify domain from memory state
        shop_domain = "b99ycv-3e.myshopify.com"
        
        # Get Shopify access token from environment
        access_token = os.getenv("SHOPIFY_API_KEY") 
        
        if not access_token:
            raise HTTPException(
                status_code=400, 
                detail="Shopify access token not configured. Please set SHOPIFY_API_KEY environment variable."
            )
        
        # Get products from Shopify
        headers = {
            "X-Shopify-Access-Token": access_token,
            "Content-Type": "application/json"
        }
        
        # Build URL with pagination
        url = f"https://{shop_domain}/admin/api/2023-10/products.json"
        params = {"limit": limit}
        if page_info:
            params["page_info"] = page_info
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        products = data.get("products", [])
        
        # Get pagination info
        pagination_info = {}
        if "Link" in response.headers:
            link_header = response.headers["Link"]
            if "rel=\"next\"" in link_header:
                # Extract page_info from Link header
                next_url = link_header.split("rel=\"next\"")[0].strip().replace("<", "").replace(">", "")
                if "page_info=" in next_url:
                    pagination_info["next_page_info"] = next_url.split("page_info=")[1].split("&")[0]
        
        return {
            "products": products,
            "count": len(products),
            "pagination": pagination_info
        }
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Shopify API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch Shopify products: {str(e)}")
    except Exception as e:
        logger.error(f"Error fetching Shopify products: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch Shopify products: {str(e)}")

@router.post("/products/import")
async def import_shopify_products(
    product_ids: Optional[List[str]] = None,
    collection_mapping: Optional[Dict[str, str]] = None,
    db: Session = Depends(get_db)
    # Temporarily removed authentication for testing
    # current_user = Depends(get_current_admin_user)
):
    """Import Shopify products into local coins table"""
    try:
        from app.models.collections import Collection
        
        # Shopify configuration
        SHOPIFY_DOMAIN = "b99ycv-3e.myshopify.com"
        SHOPIFY_ACCESS_TOKEN = os.getenv("SHOPIFY_API_KEY") 
        
        headers = {
            'X-Shopify-Access-Token': SHOPIFY_ACCESS_TOKEN,
            'Content-Type': 'application/json'
        }
        
        # Use GraphQL to get products with complete structure including description, metafields, and collections
        graphql_url = f"https://{SHOPIFY_DOMAIN}/admin/api/2023-10/graphql.json"
        
        # Complete GraphQL query to get products with everything
        query = """
        query getProducts($first: Int!) {
          products(first: $first) {
            edges {
              node {
                id
                title
                description
                descriptionHtml
                handle
                status
                productType
                vendor
                tags
                category {
                  id
                  name
                  fullName
                }
                priceRangeV2 {
                  minVariantPrice {
                    amount
                    currencyCode
                  }
                }
                totalInventory
                collections(first: 20) {
                  edges {
                    node {
                      id
                      title
                      handle
                    }
                  }
                }
                metafields(first: 50) {
                  edges {
                    node {
                      namespace
                      key
                      value
                      type
                      definition {
                        name
                        description
                      }
                    }
                  }
                }
                variants(first: 10) {
                  edges {
                    node {
                      id
                      title
                      sku
                      price
                      inventoryQuantity
                    }
                  }
                }
                images(first: 10) {
                  edges {
                    node {
                      id
                      url
                      altText
                      width
                      height
                    }
                  }
                }
              }
            }
            pageInfo {
              hasNextPage
              endCursor
            }
          }
        }
        """
        
        variables = {"first": 250}
        graphql_response = requests.post(graphql_url, headers=headers, json={"query": query, "variables": variables})
        
        if graphql_response.status_code != 200:
            logger.error(f"GraphQL request failed: {graphql_response.text}")
            raise HTTPException(status_code=500, detail="Failed to fetch products from Shopify GraphQL API")
        
        graphql_data = graphql_response.json()
        
        if "errors" in graphql_data:
            logger.error(f"GraphQL errors: {graphql_data['errors']}")
            raise HTTPException(status_code=500, detail=f"GraphQL errors: {graphql_data['errors']}")
        
        # Extract products from GraphQL response
        products_edges = graphql_data.get("data", {}).get("products", {}).get("edges", [])
        shopify_products = []
        
        for edge in products_edges:
            shopify_products.append(edge["node"])
        
        # Filter by product_ids if provided
        if product_ids:
            shopify_products = [
                p for p in shopify_products 
                if str(p["id"]) in product_ids
            ]
        
        imported_coins = []
        
        for shopify_product in shopify_products:
            # Extract product ID from GraphQL GID format
            product_gid = shopify_product['id']
            product_id = product_gid.split('/')[-1]  # Extract ID from gid://shopify/Product/12345
            
            # Debug: Log the Shopify product data to see what we're getting
            logger.info(f"Processing product {product_id}: {shopify_product.get('title', 'No title')}")
            logger.info(f"Description: {shopify_product.get('description', 'No description')}")
            logger.info(f"DescriptionHtml: {shopify_product.get('descriptionHtml', 'No descriptionHtml')}")
            logger.info(f"Metafields count: {len(shopify_product.get('metafields', {}).get('edges', []))}")
            logger.info(f"Collections count: {len(shopify_product.get('collections', {}).get('edges', []))}")
            
            # Get quantity and price from GraphQL structure
            quantity = shopify_product.get('totalInventory', 1)
            shopify_price = None
            
            # Extract price from priceRangeV2
            price_range = shopify_product.get('priceRangeV2', {})
            min_price = price_range.get('minVariantPrice', {})
            if min_price.get('amount'):
                shopify_price = float(min_price['amount'])
            
            # Fallback: get from variants if priceRangeV2 is not available
            if not shopify_price and shopify_product.get('variants'):
                variants_edges = shopify_product['variants'].get('edges', [])
                if variants_edges:
                    first_variant = variants_edges[0]['node']
                    if first_variant.get('price'):
                        shopify_price = float(first_variant['price'])
            
            # Ensure quantity is at least 1
            if quantity is None or quantity < 1:
                quantity = 1
            
            # Convert Shopify product to coin
            coin_data = {
                "sku": f"SHOP-{product_id}",  # Generate SKU from extracted product ID
                "title": shopify_product["title"],
                "description": shopify_product.get("descriptionHtml", shopify_product.get("description", "")),
                "category": shopify_product.get("category", {}).get("name", "imported") if shopify_product.get("category") else "imported",
                "is_silver": False,  # Default to non-silver, can be updated later
                "paid_price": None,  # Cost to be added manually
                "price_strategy": "fixed_price",
                "computed_price": shopify_price,
                "fixed_price": shopify_price,  # Shopify price becomes List Price
                "quantity": quantity,  # Use actual quantity from Shopify
                "status": "active",
                "created_by": "shopify_import",
                # Add Shopify metadata
                "tags": shopify_product.get("tags", []) if isinstance(shopify_product.get("tags"), list) else [],
                "shopify_metadata": {
                    "product_type": shopify_product.get("productType", ""),
                    "vendor": shopify_product.get("vendor", ""),
                    "handle": shopify_product.get("handle", ""),
                    "shopify_id": product_id,
                    "created_at": shopify_product.get("created_at", ""),
                    "updated_at": shopify_product.get("updated_at", ""),
                    "metafields": shopify_product.get("metafields", {}),
                    "status": shopify_product.get("status", ""),
                    "published_at": shopify_product.get("published_at", ""),
                    "template_suffix": shopify_product.get("template_suffix", ""),
                    "tags": shopify_product.get("tags", ""),
                    "admin_graphql_api_id": shopify_product.get("admin_graphql_api_id", ""),
                    "category": {
                        "id": shopify_product.get("category", {}).get("id") if shopify_product.get("category") else None,
                        "name": shopify_product.get("category", {}).get("name") if shopify_product.get("category") else None,
                        "full_name": shopify_product.get("category", {}).get("full_name") if shopify_product.get("category") else None
                    },
                    "variants": [
                        {
                            "id": variant.get("id"),
                            "title": variant.get("title"),
                            "price": variant.get("price"),
                            "sku": variant.get("sku"),
                            "inventoryQuantity": variant.get("inventoryQuantity")
                        } for variant in [edge["node"] for edge in shopify_product.get("variants", {}).get("edges", [])]
                    ],
                }
            }
            
            # Try to determine if it's silver based on title/description
            title_desc = f"{shopify_product['title']} {shopify_product.get('description', '')}".lower()
            silver_keywords = ['silver', 'ag', '999', 'sterling', 'morgan', 'peace', 'kennedy', 'roosevelt', 'mercury', 'barber', 'walking liberty']
            if any(keyword in title_desc for keyword in silver_keywords):
                coin_data["is_silver"] = True
                # Try to determine silver content based on denomination
                if 'quarter' in title_desc:
                    coin_data["silver_content_oz"] = 0.1808
                elif 'dime' in title_desc:
                    coin_data["silver_content_oz"] = 0.0723
                elif 'half' in title_desc:
                    coin_data["silver_content_oz"] = 0.3617
                else:
                    coin_data["silver_content_oz"] = 0.7734  # Default for silver dollars
            
            # Extract year from title if possible
            import re
            coin_data["year"] = None  # Default to None
            year_match = re.search(r'\b(19|20)\d{2}\b', shopify_product["title"])
            if year_match:
                coin_data["year"] = int(year_match.group())
            
            # Extract denomination
            denomination_patterns = [
                r'\b(dollar|half dollar|quarter|dime|nickel|penny|cent)\b',
                r'\b(\$1|\$0\.50|\$0\.25|\$0\.10|\$0\.05|\$0\.01)\b'
            ]
            coin_data["denomination"] = None  # Default to None
            for pattern in denomination_patterns:
                match = re.search(pattern, shopify_product["title"], re.IGNORECASE)
                if match:
                    coin_data["denomination"] = match.group().upper()
                    break
            
            # Extract grade
            grade_patterns = [
                r'\b(MS\d+|AU\d+|XF\d+|VF\d+|F\d+|VG\d+|G\d+|AG\d+|FA\d+|PR\d+|SP\d+)\b',
                r'\b(Mint State|About Uncirculated|Extremely Fine|Very Fine|Fine|Very Good|Good|About Good|Fair|Proof|Specimen)\b'
            ]
            coin_data["grade"] = None  # Default to None
            for pattern in grade_patterns:
                match = re.search(pattern, shopify_product["title"], re.IGNORECASE)
                if match:
                    coin_data["grade"] = match.group().upper()
                    break
            
            # Serialize JSON fields for database storage BEFORE query execution
            import json
            coin_data["tags"] = json.dumps(coin_data.get("tags", []))
            # Don't serialize shopify_metadata yet - we'll add more data to it
            
            # Ensure all required fields have values
            if coin_data.get("year") is None:
                coin_data["year"] = None
            if coin_data.get("denomination") is None:
                coin_data["denomination"] = None
            if coin_data.get("grade") is None:
                coin_data["grade"] = None
            if coin_data.get("silver_content_oz") is None:
                coin_data["silver_content_oz"] = None
            
            # Ensure quantity is an integer
            coin_data["quantity"] = int(coin_data["quantity"])
            
            # Check for existing coin with same Shopify ID to prevent duplicates
            from sqlalchemy import text
            
            # First check if a coin with this Shopify ID already exists
            existing_coin_query = text("""
                SELECT id FROM coins 
                WHERE shopify_metadata->>'shopify_id' = :shopify_id
            """)
            
            existing_result = db.execute(existing_coin_query, {"shopify_id": str(product_id)})
            existing_coin = existing_result.fetchone()
            
            if existing_coin:
                # Update existing coin instead of creating duplicate
                update_query = text("""
                    UPDATE coins SET
                        title = :title,
                        year = :year,
                        denomination = :denomination,
                        grade = :grade,
                        category = :category,
                        description = :description,
                        is_silver = :is_silver,
                        silver_content_oz = :silver_content_oz,
                        paid_price = :paid_price,
                        price_strategy = :price_strategy,
                        computed_price = :computed_price,
                        fixed_price = :fixed_price,
                        quantity = :quantity,
                        tags = :tags,
                        shopify_metadata = :shopify_metadata,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = :coin_id
                    RETURNING id
                """)
                
                result = db.execute(update_query, {
                    "coin_id": existing_coin[0],
                    "title": coin_data["title"],
                    "year": coin_data["year"],
                    "denomination": coin_data["denomination"],
                    "grade": coin_data["grade"],
                    "category": coin_data["category"],
                    "description": coin_data["description"],
                    "is_silver": coin_data["is_silver"],
                    "silver_content_oz": coin_data["silver_content_oz"],
                    "paid_price": coin_data["paid_price"],
                    "price_strategy": coin_data["price_strategy"],
                    "computed_price": coin_data["computed_price"],
                    "fixed_price": coin_data["fixed_price"],
                    "quantity": coin_data["quantity"],
                    "tags": coin_data["tags"],
                    "shopify_metadata": coin_data["shopify_metadata"]
                })
                coin_id = existing_coin[0]
            else:
                # Insert new coin
                coin_query = text("""
                    INSERT INTO coins (
                        sku, title, year, denomination, grade, category, description,
                        is_silver, silver_content_oz, paid_price, price_strategy, 
                        computed_price, fixed_price, quantity, status, created_by, tags, shopify_metadata
                    ) VALUES (
                        :sku, :title, :year, :denomination, :grade, :category, :description,
                        :is_silver, :silver_content_oz, :paid_price, :price_strategy,
                        :computed_price, :fixed_price, :quantity, :status, :created_by, :tags, :shopify_metadata
                    ) 
                    ON CONFLICT (sku) DO UPDATE SET
                        title = EXCLUDED.title,
                        year = EXCLUDED.year,
                        denomination = EXCLUDED.denomination,
                        grade = EXCLUDED.grade,
                        category = EXCLUDED.category,
                        description = EXCLUDED.description,
                        is_silver = EXCLUDED.is_silver,
                        silver_content_oz = EXCLUDED.silver_content_oz,
                        paid_price = EXCLUDED.paid_price,
                        price_strategy = EXCLUDED.price_strategy,
                        computed_price = EXCLUDED.computed_price,
                        fixed_price = EXCLUDED.fixed_price,
                        quantity = EXCLUDED.quantity,
                        tags = EXCLUDED.tags,
                        shopify_metadata = EXCLUDED.shopify_metadata,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING id
                """)
                
                result = db.execute(coin_query, coin_data)
                coin_id = result.fetchone()[0]
            
            # Handle collection associations - extract from GraphQL collections field
            collection_ids = []
            collections_info = []
            
            # Extract collections from GraphQL structure
            collections_edges = shopify_product.get('collections', {}).get('edges', [])
            
            for collection_edge in collections_edges:
                collection_node = collection_edge['node']
                collection_gid = collection_node['id']
                collection_id = collection_gid.split('/')[-1]  # Extract ID from gid://shopify/Collection/12345
                collection_ids.append(collection_id)
                collections_info.append({
                    'id': collection_id,
                    'title': collection_node.get('title', ''),
                    'handle': collection_node.get('handle', '')
                })
            
            # Update shopify_metadata with collections info (convert back to dict first)
            if collections_info:
                shopify_metadata_dict = json.loads(coin_data['shopify_metadata'])
                shopify_metadata_dict['collections'] = collections_info
                coin_data['shopify_metadata'] = json.dumps(shopify_metadata_dict)
                
            logger.info(f"Found {len(collections_info)} collections for product {product_id}: {[c['title'] for c in collections_info]}")
            
            # Insert collection associations into coin_collections table
            if collection_ids:
                for shopify_collection_id in collection_ids:
                    if shopify_collection_id:  # Make sure collection_id is not None
                        # Find the local collection ID by Shopify collection ID
                        local_collection_query = text("""
                            SELECT id FROM collections WHERE shopify_collection_id = :shopify_collection_id
                        """)
                        local_collection_result = db.execute(local_collection_query, {
                            "shopify_collection_id": str(shopify_collection_id)
                        })
                        local_collection_row = local_collection_result.fetchone()
                        
                        if local_collection_row:
                            local_collection_id = local_collection_row[0]
                            collection_insert_query = text("""
                                INSERT INTO coin_collections (coin_id, collection_id)
                                VALUES (:coin_id, :collection_id)
                                ON CONFLICT (coin_id, collection_id) DO NOTHING
                            """)
                            db.execute(collection_insert_query, {
                                "coin_id": coin_id,
                                "collection_id": local_collection_id
                            })
            
            # Ensure all required fields have values (JSON already serialized above)
            if coin_data.get("year") is None:
                coin_data["year"] = None
            if coin_data.get("denomination") is None:
                coin_data["denomination"] = None
            if coin_data.get("grade") is None:
                coin_data["grade"] = None
            if coin_data.get("silver_content_oz") is None:
                coin_data["silver_content_oz"] = None
            
            # Ensure quantity is an integer
            coin_data["quantity"] = int(coin_data["quantity"])
            
            # Process metafields from GraphQL response
            metafields_edges = shopify_product.get('metafields', {}).get('edges', [])
            product_metafields = {}
            category_metafields = {}
            
            logger.info(f"Processing {len(metafields_edges)} metafields for product {product_id}")
            
            for metafield_edge in metafields_edges:
                metafield = metafield_edge['node']
                namespace = metafield.get('namespace', '')
                key = metafield.get('key', '')
                value = metafield.get('value', '')
                metafield_type = metafield.get('type', '')
                
                logger.info(f"  Metafield: {namespace}.{key} = {str(value)[:50]}... (type: {metafield_type})")
                
                # Categorize metafields
                if namespace == 'custom':
                    category_metafields[f"{namespace}.{key}"] = {
                        'value': value,
                        'type': metafield_type,
                        'definition': metafield.get('definition', {})
                    }
                else:
                    product_metafields[f"{namespace}.{key}"] = {
                        'value': value,
                        'type': metafield_type,
                        'definition': metafield.get('definition', {})
                    }
            
            # Update shopify_metadata with metafields (it's already a dict)
            shopify_metadata_dict = coin_data['shopify_metadata']
            shopify_metadata_dict['category_metafields'] = category_metafields
            shopify_metadata_dict['product_metafields'] = product_metafields
            shopify_metadata_dict['description'] = coin_data['description']
            shopify_metadata_dict['description_html'] = coin_data['description']
            
            # Update the coin_data with the enhanced metadata (convert to JSON for database)
            coin_data['shopify_metadata'] = json.dumps(shopify_metadata_dict)
            
            logger.info(f"Found {len(product_metafields)} product metafields and {len(category_metafields)} category metafields for product {product_id}")

            # Import images from Shopify product (only if coin doesn't already have images)
            if shopify_product.get('images'):
                # Check if coin already has images
                existing_images_query = text("SELECT COUNT(*) FROM coin_images WHERE coin_id = :coin_id")
                existing_images_result = db.execute(existing_images_query, {"coin_id": coin_id})
                existing_images_count = existing_images_result.fetchone()[0]
                
                if existing_images_count == 0:
                    # Only add images if coin doesn't have any
                    images_edges = shopify_product.get('images', {}).get('edges', [])
                    for image_edge in images_edges:
                        image = image_edge['node']
                        image_query = text("""
                            INSERT INTO coin_images (
                                coin_id, url, alt, sort_order
                            ) VALUES (:coin_id, :url, :alt, :sort_order)
                        """)
                        
                        image_params = {
                            "coin_id": coin_id,
                            "url": image.get('url', ''),
                            "alt": image.get('altText') or f"{coin_data['title']} image",
                            "sort_order": 0  # Default sort order
                        }
                        
                        db.execute(image_query, image_params)
            
            imported_coins.append({
                "id": coin_id,
                "sku": coin_data["sku"],
                "title": coin_data["title"],
                "shopify_id": shopify_product["id"]
            })
        
        db.commit()
        
        return {
            "message": f"Successfully imported {len(imported_coins)} products as coins",
            "coins": imported_coins
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error importing Shopify products: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to import products: {str(e)}")

@router.post("/products/{product_id}/metafields")
async def update_product_metafields(
    product_id: str,
    metafields: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Update product metafields in Shopify"""
    try:
        # Shopify configuration
        SHOPIFY_DOMAIN = "b99ycv-3e.myshopify.com"
        SHOPIFY_ACCESS_TOKEN = os.getenv("SHOPIFY_API_KEY") 
        
        headers = {
            'X-Shopify-Access-Token': SHOPIFY_ACCESS_TOKEN,
            'Content-Type': 'application/json'
        }
        
        # Convert our metafields format to Shopify format
        shopify_metafields = []
        
        for key, value in metafields.items():
            if not value:  # Skip empty values
                continue
                
            namespace, metafield_key = key.split('.', 1) if '.' in key else ('custom', key)
            
            # Determine metafield type based on the field
            metafield_type = "single_line_text_field"  # Default
            
            if metafield_key in ['silver_content']:
                metafield_type = "number_decimal"
            elif metafield_key in ['composition', 'mint_mark', 'grade']:
                metafield_type = "list.single_line_text_field"
            elif metafield_key in ['condition_notes', 'obverse_design', 'reverse_design']:
                metafield_type = "multi_line_text_field"
            
            shopify_metafields.append({
                "namespace": namespace,
                "key": metafield_key,
                "value": str(value),
                "type": metafield_type
            })
        
        # Update metafields in Shopify
        metafields_url = f"https://{SHOPIFY_DOMAIN}/admin/api/2023-10/products/{product_id}/metafields.json"
        
        for metafield in shopify_metafields:
            response = requests.post(metafields_url, headers=headers, json={"metafield": metafield})
            
            if response.status_code not in [200, 201]:
                logger.warning(f"Failed to update metafield {metafield['key']}: {response.text}")
        
        # Also update the local database
        coin_query = text("SELECT id FROM coins WHERE shopify_id = :shopify_id")
        coin_result = db.execute(coin_query, {"shopify_id": product_id})
        coin_row = coin_result.fetchone()
        
        if coin_row:
            coin_id = coin_row[0]
            
            # Get current shopify_metadata
            metadata_query = text("SELECT shopify_metadata FROM coins WHERE id = :coin_id")
            metadata_result = db.execute(metadata_query, {"coin_id": coin_id})
            metadata_row = metadata_result.fetchone()
            
            if metadata_row and metadata_row[0]:
                shopify_metadata = json.loads(metadata_row[0])
                
                # Update product_metafields
                if 'product_metafields' not in shopify_metadata:
                    shopify_metadata['product_metafields'] = {}
                
                for key, value in metafields.items():
                    shopify_metadata['product_metafields'][key] = value
                
                # Update database
                update_query = text("UPDATE coins SET shopify_metadata = :metadata WHERE id = :coin_id")
                db.execute(update_query, {
                    "metadata": json.dumps(shopify_metadata),
                    "coin_id": coin_id
                })
                db.commit()
        
        return {"message": "Metafields updated successfully", "updated_fields": len(shopify_metafields)}
        
    except Exception as e:
        logger.error(f"Error updating metafields: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update metafields: {str(e)}")

@router.post("/products/{product_id}/category")
async def update_product_category(
    product_id: str,
    category_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Update product category in Shopify"""
    try:
        # Shopify configuration
        SHOPIFY_DOMAIN = "b99ycv-3e.myshopify.com"
        SHOPIFY_ACCESS_TOKEN = os.getenv("SHOPIFY_API_KEY") 
        
        headers = {
            'X-Shopify-Access-Token': SHOPIFY_ACCESS_TOKEN,
            'Content-Type': 'application/json'
        }
        
        # Update category in Shopify using GraphQL
        graphql_url = f"https://{SHOPIFY_DOMAIN}/admin/api/2023-10/graphql.json"
        
        mutation = f"""
        mutation {{
            productUpdate(input: {{
                id: "gid://shopify/Product/{product_id}"
                category: "{category_id}"
            }}) {{
                product {{
                    id
                    category {{
                        id
                        name
                        fullName
                    }}
                }}
                userErrors {{
                    field
                    message
                }}
            }}
        }}
        """
        
        response = requests.post(graphql_url, headers=headers, json={"query": mutation})
        
        if response.status_code == 200:
            data = response.json()
            if data.get('data', {}).get('productUpdate', {}).get('userErrors'):
                errors = data['data']['productUpdate']['userErrors']
                raise HTTPException(status_code=400, detail=f"GraphQL errors: {errors}")
            
            # Update local database
            coin_query = text("SELECT id FROM coins WHERE shopify_id = :shopify_id")
            coin_result = db.execute(coin_query, {"shopify_id": product_id})
            coin_row = coin_result.fetchone()
            
            if coin_row:
                coin_id = coin_row[0]
                
                # Get current shopify_metadata
                metadata_query = text("SELECT shopify_metadata FROM coins WHERE id = :coin_id")
                metadata_result = db.execute(metadata_query, {"coin_id": coin_id})
                metadata_row = metadata_result.fetchone()
                
                if metadata_row and metadata_row[0]:
                    shopify_metadata = json.loads(metadata_row[0])
                    
                    # Update category
                    shopify_metadata['category'] = {
                        "id": category_id,
                        "name": data.get('data', {}).get('productUpdate', {}).get('product', {}).get('category', {}).get('name'),
                        "full_name": data.get('data', {}).get('productUpdate', {}).get('product', {}).get('category', {}).get('fullName')
                    }
                    
                    # Update database
                    update_query = text("UPDATE coins SET shopify_metadata = :metadata WHERE id = :coin_id")
                    db.execute(update_query, {
                        "metadata": json.dumps(shopify_metadata),
                        "coin_id": coin_id
                    })
                    db.commit()
            
            return {"message": "Category updated successfully", "category_id": category_id}
        else:
            raise HTTPException(status_code=response.status_code, detail=f"Failed to update category: {response.text}")
        
    except Exception as e:
        logger.error(f"Error updating category: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update category: {str(e)}")
