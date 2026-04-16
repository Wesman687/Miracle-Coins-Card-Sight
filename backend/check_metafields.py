#!/usr/bin/env python3
"""
Quick test to see what metafields are being imported from Shopify
"""

import requests
import json

def check_metafields():
    """Check what metafields are actually in the database"""
    
    base_url = "http://localhost:13000"
    coins_url = f"{base_url}/api/v1/coins"
    
    print("🔍 Checking metafields in database...")
    
    try:
        response = requests.get(coins_url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            # Handle both list and dict responses
            if isinstance(data, list):
                coins = data
            else:
                coins = data.get('coins', [])
            
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
                
                print(f"\n📊 Metafields found:")
                print(f"  Product metafields: {len(product_metafields)}")
                print(f"  Category metafields: {len(category_metafields)}")
                
                if product_metafields:
                    print(f"\n🔍 Product metafields:")
                    for key, value in product_metafields.items():
                        print(f"  - {key}: {str(value)[:100]}...")
                
                if category_metafields:
                    print(f"\n🔍 Category metafields:")
                    for key, value in category_metafields.items():
                        print(f"  - {key}: {str(value)[:100]}...")
                
                # Check for specific coin detail fields
                coin_detail_fields = [
                    'silver_content', 'year', 'weight', 'diameter', 'composition',
                    'mintage', 'estimated_value', 'rarity', 'grade', 'condition',
                    'obverse_design', 'reverse_design', 'origin_country', 'variety'
                ]
                
                print(f"\n🎯 Looking for coin detail fields:")
                found_fields = []
                for field in coin_detail_fields:
                    for metafield_key in product_metafields.keys():
                        if field.lower() in metafield_key.lower():
                            found_fields.append(field)
                            print(f"  ✅ Found: {metafield_key}")
                
                if not found_fields:
                    print("  ❌ No coin detail fields found in metafields")
                    print("  This suggests metafields aren't being imported properly")
                else:
                    print(f"  ✅ Found {len(found_fields)} coin detail fields")
                
                return len(product_metafields) > 0
            else:
                print("❌ No coins found")
                return False
        else:
            print(f"❌ Failed to fetch coins: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Checking Metafields Import")
    print("=" * 50)
    
    success = check_metafields()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ Metafields are being imported")
        print("💡 If coin details aren't showing in frontend, check frontend code")
    else:
        print("❌ Metafields are NOT being imported")
        print("💡 Need to fix the Shopify import to get metafields")
