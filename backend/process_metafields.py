#!/usr/bin/env python3
"""
Process existing metafields data in the database to convert them to product_metafields and category_metafields
"""

import requests
import json

def process_existing_metafields():
    """Process existing metafields in the database"""
    
    base_url = "http://localhost:13000"
    
    print("🔧 Processing Existing Metafields")
    print("=" * 50)
    
    try:
        # Get all coins
        coins_url = f"{base_url}/api/v1/coins"
        response = requests.get(coins_url, timeout=30)
        
        if response.status_code == 200:
            coins_data = response.json()
            if isinstance(coins_data, list):
                coins = coins_data
            else:
                coins = coins_data.get('coins', [])
            
            print(f"📋 Found {len(coins)} coins to process")
            
            processed_count = 0
            
            for coin in coins:
                coin_id = coin.get('id')
                title = coin.get('title', 'No title')
                
                shopify_metadata = coin.get('shopify_metadata', {})
                if isinstance(shopify_metadata, str):
                    try:
                        shopify_metadata = json.loads(shopify_metadata)
                    except:
                        continue
                
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
                    
                    # Update the coin with processed metafields
                    shopify_metadata['product_metafields'] = new_product_metafields
                    shopify_metadata['category_metafields'] = new_category_metafields
                    
                    # Update the coin via API
                    update_url = f"{base_url}/api/v1/coins/{coin_id}"
                    update_data = {
                        'shopify_metadata': json.dumps(shopify_metadata)
                    }
                    
                    update_response = requests.put(update_url, json=update_data, timeout=30)
                    
                    if update_response.status_code == 200:
                        print(f"  ✅ Updated coin {coin_id} with {len(new_product_metafields)} product metafields and {len(new_category_metafields)} category metafields")
                        processed_count += 1
                    else:
                        print(f"  ❌ Failed to update coin {coin_id}: {update_response.status_code}")
            
            print(f"\n✅ Processed {processed_count} coins")
            return processed_count > 0
            
        else:
            print(f"❌ Failed to fetch coins: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = process_existing_metafields()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ SUCCESS: Metafields have been processed!")
        print("💡 You can now see coin details in the frontend")
    else:
        print("❌ FAILED: Could not process metafields")

