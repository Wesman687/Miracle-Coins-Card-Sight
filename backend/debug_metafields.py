#!/usr/bin/env python3
"""
Test to see what's actually happening with metafields processing
"""

import requests
import json

def debug_metafields():
    """Debug metafields processing"""
    
    base_url = "http://localhost:13000"
    
    print("🔍 Debugging Metafields Processing")
    print("=" * 50)
    
    try:
        # Run import and capture any errors
        print("📡 Running import...")
        import_url = f"{base_url}/api/v1/shopify/products/import"
        response = requests.post(import_url, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Import successful: {result.get('message', 'Success')}")
            
            # Check a few coins to see their metafields
            coins_url = f"{base_url}/api/v1/coins"
            coins_response = requests.get(coins_url, timeout=30)
            
            if coins_response.status_code == 200:
                coins_data = coins_response.json()
                if isinstance(coins_data, list):
                    coins = coins_data
                else:
                    coins = coins_data.get('coins', [])
                
                print(f"\n📋 Checking {min(3, len(coins))} coins for metafields:")
                
                for i, coin in enumerate(coins[:3]):
                    print(f"\n🔍 Coin {i+1}: {coin.get('title', 'No title')}")
                    print(f"  ID: {coin.get('id')}")
                    print(f"  Shopify ID: {coin.get('shopify_id')}")
                    
                    shopify_metadata = coin.get('shopify_metadata', {})
                    if isinstance(shopify_metadata, str):
                        try:
                            shopify_metadata = json.loads(shopify_metadata)
                            print(f"  ✅ shopify_metadata parsed successfully")
                        except Exception as e:
                            print(f"  ❌ Failed to parse shopify_metadata: {e}")
                            shopify_metadata = {}
                    
                    print(f"  shopify_metadata keys: {list(shopify_metadata.keys())}")
                    
                    product_metafields = shopify_metadata.get('product_metafields', {})
                    category_metafields = shopify_metadata.get('category_metafields', {})
                    
                    print(f"  Product metafields: {len(product_metafields)}")
                    print(f"  Category metafields: {len(category_metafields)}")
                    
                    if product_metafields:
                        print(f"  ✅ Product metafields found:")
                        for key, value in list(product_metafields.items())[:2]:
                            print(f"    - {key}: {str(value)[:50]}...")
                    
                    if category_metafields:
                        print(f"  ✅ Category metafields found:")
                        for key, value in list(category_metafields.items())[:2]:
                            print(f"    - {key}: {str(value)[:50]}...")
                    
                    if not product_metafields and not category_metafields:
                        print(f"  ❌ No metafields found")
                        # Show what's actually in shopify_metadata
                        print(f"  Full shopify_metadata: {shopify_metadata}")
                
                return len(coins) > 0
            else:
                print(f"❌ Failed to fetch coins: {coins_response.status_code}")
                return False
        else:
            print(f"❌ Import failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = debug_metafields()
    print(f"\n{'✅ Debug complete' if success else '❌ Debug failed'}")

