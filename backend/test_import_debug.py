#!/usr/bin/env python3
"""
Test the Shopify import to see if metafields are being fetched
"""

import requests
import json

def test_import():
    """Test the Shopify import endpoint"""
    
    base_url = "http://localhost:13000"
    import_url = f"{base_url}/api/v1/shopify/products/import"
    
    print("🚀 Testing Shopify Import")
    print("=" * 50)
    
    try:
        print("📡 Calling import endpoint...")
        response = requests.post(import_url, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Import successful!")
            print(f"📊 Result: {result}")
            
            # Check if we got any coins
            coins_url = f"{base_url}/api/v1/coins"
            coins_response = requests.get(coins_url, timeout=30)
            
            if coins_response.status_code == 200:
                coins_data = coins_response.json()
                if isinstance(coins_data, list):
                    coins = coins_data
                else:
                    coins = coins_data.get('coins', [])
                
                print(f"\n📋 Found {len(coins)} coins after import")
                
                if coins:
                    sample_coin = coins[0]
                    shopify_metadata = sample_coin.get('shopify_metadata', {})
                    if isinstance(shopify_metadata, str):
                        try:
                            shopify_metadata = json.loads(shopify_metadata)
                        except:
                            shopify_metadata = {}
                    
                    product_metafields = shopify_metadata.get('product_metafields', {})
                    category_metafields = shopify_metadata.get('category_metafields', {})
                    
                    print(f"🔍 Sample coin metafields:")
                    print(f"  Product metafields: {len(product_metafields)}")
                    print(f"  Category metafields: {len(category_metafields)}")
                    
                    if product_metafields:
                        print("  Product metafields found:")
                        for key, value in list(product_metafields.items())[:5]:  # Show first 5
                            print(f"    - {key}: {str(value)[:50]}...")
                    
                    if category_metafields:
                        print("  Category metafields found:")
                        for key, value in list(category_metafields.items())[:5]:  # Show first 5
                            print(f"    - {key}: {str(value)[:50]}...")
                    
                    if not product_metafields and not category_metafields:
                        print("  ❌ No metafields found - this is the problem!")
                        print("  💡 Check server logs for metafields processing")
                else:
                    print("❌ No coins found after import")
            else:
                print(f"❌ Failed to fetch coins: {coins_response.status_code}")
        else:
            print(f"❌ Import failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_import()

