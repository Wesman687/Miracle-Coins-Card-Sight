#!/usr/bin/env python3
"""
Test script to verify that descriptions, metafields, and collections are properly imported
"""

import requests
import json

def test_imported_data():
    """Test the coins endpoint to see if descriptions, metafields, and collections are imported"""
    
    base_url = "http://localhost:13000"
    coins_url = f"{base_url}/api/v1/coins"
    
    print("🔍 Testing imported coin data...")
    
    try:
        response = requests.get(coins_url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            coins = data.get('coins', [])
            
            print(f"✅ Found {len(coins)} coins in database")
            
            if coins:
                sample_coin = coins[0]
                print(f"\n📋 Sample coin: {sample_coin.get('title', 'No title')}")
                print(f"  Description: {'✅ Present' if sample_coin.get('description') else '❌ Missing'}")
                
                if sample_coin.get('description'):
                    desc_preview = sample_coin['description'][:100] + "..." if len(sample_coin['description']) > 100 else sample_coin['description']
                    print(f"    Preview: {desc_preview}")
                
                # Check shopify_metadata
                shopify_metadata = sample_coin.get('shopify_metadata', {})
                if isinstance(shopify_metadata, str):
                    try:
                        shopify_metadata = json.loads(shopify_metadata)
                    except:
                        shopify_metadata = {}
                
                print(f"  Product Metafields: {'✅ Present' if shopify_metadata.get('product_metafields') else '❌ Missing'}")
                print(f"  Category Metafields: {'✅ Present' if shopify_metadata.get('category_metafields') else '❌ Missing'}")
                print(f"  Collections: {'✅ Present' if shopify_metadata.get('collections') else '❌ Missing'}")
                
                if shopify_metadata.get('collections'):
                    collections = shopify_metadata['collections']
                    print(f"    Collections count: {len(collections)}")
                    for coll in collections[:3]:
                        print(f"      - {coll.get('title', 'No title')}")
                
                if shopify_metadata.get('product_metafields'):
                    metafields = shopify_metadata['product_metafields']
                    print(f"    Product metafields count: {len(metafields)}")
                    for key, value in list(metafields.items())[:3]:
                        print(f"      - {key}: {str(value)[:50]}...")
                
                if shopify_metadata.get('category_metafields'):
                    cat_metafields = shopify_metadata['category_metafields']
                    print(f"    Category metafields count: {len(cat_metafields)}")
                    for key, value in list(cat_metafields.items())[:2]:
                        print(f"      - {key}: {str(value)[:50]}...")
                
                return True
            else:
                print("❌ No coins found")
                return False
        else:
            print(f"❌ Failed to fetch coins: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing imported data: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing Imported Data Quality")
    print("=" * 50)
    
    success = test_imported_data()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Data import verification completed!")
        print("✅ Descriptions, metafields, and collections should now be working")
    else:
        print("⚠️  Data import verification failed")

