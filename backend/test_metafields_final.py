#!/usr/bin/env python3
"""
Clear all coins and test the fixed import with metafields
"""

import requests
import json
import time

def clear_and_test():
    """Clear all coins and test the fixed import"""
    
    base_url = "http://localhost:13000"
    
    print("🚀 Testing Fixed Import with Metafields")
    print("=" * 60)
    
    try:
        # Clear all coins first
        print("🧹 Clearing all coins...")
        clear_url = f"{base_url}/api/v1/coins/clear"
        clear_response = requests.delete(clear_url, timeout=30)
        
        if clear_response.status_code == 200:
            print("✅ All coins cleared")
        else:
            print(f"⚠️ Clear failed: {clear_response.status_code}, continuing anyway...")
        
        # Run import (should handle duplicates by updating existing coins)
        print("\n📡 Running Shopify import...")
        import_url = f"{base_url}/api/v1/shopify/products/import"
        response = requests.post(import_url, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Import successful!")
            print(f"📊 Result: {result.get('message', 'No message')}")
            
            # Check metafields
            print("\n🔍 Checking metafields...")
            coins_url = f"{base_url}/api/v1/coins"
            coins_response = requests.get(coins_url, timeout=30)
            
            if coins_response.status_code == 200:
                coins_data = coins_response.json()
                if isinstance(coins_data, list):
                    coins = coins_data
                else:
                    coins = coins_data.get('coins', [])
                
                print(f"📋 Found {len(coins)} coins after import")
                
                if coins:
                    sample_coin = coins[0]
                    print(f"\n📋 Sample coin: {sample_coin.get('title', 'No title')}")
                    
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
                        print("  ✅ Product metafields found:")
                        for key, value in list(product_metafields.items())[:5]:  # Show first 5
                            print(f"    - {key}: {str(value)[:50]}...")
                    
                    if category_metafields:
                        print("  ✅ Category metafields found:")
                        for key, value in list(category_metafields.items())[:5]:  # Show first 5
                            print(f"    - {key}: {str(value)[:50]}...")
                    
                    if not product_metafields and not category_metafields:
                        print("  ❌ Still no metafields found!")
                        print("  💡 Check server logs for metafields processing")
                        return False
                    else:
                        print("  ✅ Metafields are now working!")
                        return True
                else:
                    print("❌ No coins found after import")
                    return False
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
    success = clear_and_test()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ SUCCESS: Metafields are now working!")
        print("💡 You can now click 'Sync Shopify' to get all the coin details")
    else:
        print("❌ FAILED: Metafields still not working")
        print("💡 Check server logs for more details")

