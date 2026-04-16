#!/usr/bin/env python3
"""
Test the fixed import with metafields processing
"""

import requests
import json

def test_fixed_import():
    """Test the fixed import"""
    
    base_url = "http://localhost:13000"
    
    print("🧪 Testing Fixed Import with Metafields")
    print("=" * 50)
    
    try:
        # Clear existing coins first
        print("🗑️ Clearing existing coins...")
        clear_url = f"{base_url}/api/v1/coins/clear"
        clear_response = requests.delete(clear_url, timeout=30)
        
        if clear_response.status_code == 200:
            print("✅ Coins cleared successfully")
        else:
            print(f"⚠️ Clear failed: {clear_response.status_code}")
        
        # Run import
        print("\n📡 Running import...")
        import_url = f"{base_url}/api/v1/shopify/products/import"
        response = requests.post(import_url, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Import: {result.get('message', 'Success')}")
            
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
                
                print(f"📋 Found {len(coins)} coins")
                
                metafields_found = 0
                
                for coin in coins[:3]:  # Check first 3 coins
                    coin_id = coin.get('id')
                    title = coin.get('title', 'No title')
                    
                    shopify_metadata = coin.get('shopify_metadata', {})
                    if isinstance(shopify_metadata, str):
                        try:
                            shopify_metadata = json.loads(shopify_metadata)
                        except:
                            continue
                    
                    product_metafields = shopify_metadata.get('product_metafields', {})
                    category_metafields = shopify_metadata.get('category_metafields', {})
                    
                    print(f"\n🔍 Coin {coin_id}: {title}")
                    print(f"  Product metafields: {len(product_metafields)}")
                    print(f"  Category metafields: {len(category_metafields)}")
                    
                    if product_metafields or category_metafields:
                        metafields_found += 1
                        print(f"  ✅ Metafields found!")
                        
                        # Show sample metafields
                        if category_metafields:
                            print(f"  Category metafields:")
                            for key, value in list(category_metafields.items())[:2]:
                                print(f"    - {key}: {str(value.get('value', ''))[:50]}...")
                    
                    if not product_metafields and not category_metafields:
                        print(f"  ❌ No metafields found")
                
                print(f"\n📊 Summary:")
                print(f"  Total coins: {len(coins)}")
                print(f"  Coins with metafields: {metafields_found}")
                
                if metafields_found > 0:
                    print("  ✅ SUCCESS: Metafields are being processed!")
                    return True
                else:
                    print("  ❌ FAILED: No metafields found")
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
    success = test_fixed_import()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ SUCCESS: Metafields processing is working!")
        print("💡 You can now see coin details in the frontend")
    else:
        print("❌ FAILED: Metafields processing is not working")