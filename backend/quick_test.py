#!/usr/bin/env python3
"""
Quick test to see if metafields are now working
"""

import requests
import json

def quick_test():
    """Quick test of metafields"""
    
    base_url = "http://localhost:13000"
    
    print("🚀 Quick Metafields Test")
    print("=" * 40)
    
    try:
        # Test server
        coins_url = f"{base_url}/api/v1/coins"
        response = requests.get(coins_url, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Server not ready: {response.status_code}")
            return False
        
        print("✅ Server is running")
        
        # Run import
        print("\n📡 Running import...")
        import_url = f"{base_url}/api/v1/shopify/products/import"
        response = requests.post(import_url, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Import: {result.get('message', 'Success')}")
            
            # Check metafields
            coins_response = requests.get(coins_url, timeout=30)
            if coins_response.status_code == 200:
                coins_data = coins_response.json()
                if isinstance(coins_data, list):
                    coins = coins_data
                else:
                    coins = coins_data.get('coins', [])
                
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
                    
                    print(f"\n🔍 Metafields check:")
                    print(f"  Product metafields: {len(product_metafields)}")
                    print(f"  Category metafields: {len(category_metafields)}")
                    
                    if product_metafields or category_metafields:
                        print("  ✅ METAFIELDS ARE WORKING!")
                        if product_metafields:
                            print("  Product metafields:")
                            for key, value in list(product_metafields.items())[:3]:
                                print(f"    - {key}: {str(value)[:50]}...")
                        return True
                    else:
                        print("  ❌ Still no metafields")
                        return False
                else:
                    print("❌ No coins found")
                    return False
            else:
                print(f"❌ Failed to fetch coins: {coins_response.status_code}")
                return False
        else:
            print(f"❌ Import failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = quick_test()
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}")

