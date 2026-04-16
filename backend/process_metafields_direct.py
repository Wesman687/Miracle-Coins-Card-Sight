#!/usr/bin/env python3
"""
Process existing metafields in database directly
"""

import os
import sys
import json
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def process_metafields_directly():
    """Process metafields directly in the database"""
    
    print("🔧 Processing Metafields Directly in Database")
    print("=" * 60)
    
    # Database connection
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://Miracle-Coins:password@localhost:5432/miracle-coins")
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    try:
        db = SessionLocal()
        
        # Get all coins with metafields
        query = text("""
            SELECT id, title, shopify_metadata 
            FROM coins 
            WHERE shopify_metadata IS NOT NULL 
            AND shopify_metadata != '{}'
            ORDER BY id
        """)
        
        result = db.execute(query)
        coins = result.fetchall()
        
        print(f"📋 Found {len(coins)} coins with metafields to process")
        
        processed_count = 0
        
        for coin in coins:
            coin_id, title, shopify_metadata_json = coin
            
            try:
                # Parse shopify_metadata
                if isinstance(shopify_metadata_json, str):
                    shopify_metadata = json.loads(shopify_metadata_json)
                else:
                    shopify_metadata = shopify_metadata_json
                
                # Check if metafields exist but product_metafields/category_metafields don't
                raw_metafields = shopify_metadata.get('metafields', {})
                product_metafields = shopify_metadata.get('product_metafields', {})
                category_metafields = shopify_metadata.get('category_metafields', {})
                
                if raw_metafields.get('edges') and not product_metafields and not category_metafields:
                    print(f"\n🔧 Processing coin {coin_id}: {title}")
                    
                    # Process the raw metafields
                    metafields_edges = raw_metafields.get('edges', [])
                    new_product_metafields = {}
                    new_category_metafields = {}
                    
                    print(f"  Found {len(metafields_edges)} raw metafields")
                    
                    for metafield_edge in metafields_edges:
                        metafield = metafield_edge.get('node', {})
                        namespace = metafield.get('namespace', '')
                        key = metafield.get('key', '')
                        value = metafield.get('value', '')
                        metafield_type = metafield.get('type', '')
                        
                        print(f"    - {namespace}.{key}: {str(value)[:50]}...")
                        
                        # Categorize metafields
                        if namespace == 'custom':
                            new_category_metafields[f"{namespace}.{key}"] = {
                                'value': value,
                                'type': metafield_type,
                                'definition': metafield.get('definition', {})
                            }
                        else:
                            new_product_metafields[f"{namespace}.{key}"] = {
                                'value': value,
                                'type': metafield_type,
                                'definition': metafield.get('definition', {})
                            }
                    
                    # Update the shopify_metadata with processed metafields
                    shopify_metadata['product_metafields'] = new_product_metafields
                    shopify_metadata['category_metafields'] = new_category_metafields
                    
                    # Update the coin in the database
                    update_query = text("""
                        UPDATE coins 
                        SET shopify_metadata = :shopify_metadata 
                        WHERE id = :coin_id
                    """)
                    
                    db.execute(update_query, {
                        "shopify_metadata": json.dumps(shopify_metadata),
                        "coin_id": coin_id
                    })
                    
                    print(f"  ✅ Updated coin {coin_id} with {len(new_product_metafields)} product metafields and {len(new_category_metafields)} category metafields")
                    processed_count += 1
                
            except Exception as e:
                print(f"  ❌ Error processing coin {coin_id}: {e}")
                continue
        
        # Commit all changes
        db.commit()
        print(f"\n✅ Successfully processed {processed_count} coins")
        
        # Verify the results
        print("\n🔍 Verifying results...")
        verify_query = text("""
            SELECT id, title, 
                   jsonb_array_length(shopify_metadata->'product_metafields') as product_count,
                   jsonb_array_length(shopify_metadata->'category_metafields') as category_count
            FROM coins 
            WHERE shopify_metadata->'product_metafields' IS NOT NULL 
            OR shopify_metadata->'category_metafields' IS NOT NULL
            ORDER BY id
            LIMIT 5
        """)
        
        verify_result = db.execute(verify_query)
        verify_coins = verify_result.fetchall()
        
        for coin in verify_coins:
            coin_id, title, product_count, category_count = coin
            print(f"  Coin {coin_id}: {title} - {product_count} product metafields, {category_count} category metafields")
        
        return processed_count > 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = process_metafields_directly()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ SUCCESS: Metafields have been processed!")
        print("💡 You can now see coin details in the frontend")
    else:
        print("❌ FAILED: Could not process metafields")

