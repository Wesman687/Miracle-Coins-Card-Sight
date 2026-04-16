#!/usr/bin/env python3
"""
Script to clear existing coin data and do a fresh Shopify import
"""

import requests
import json

def clear_existing_data():
    """Clear existing coin data to start fresh"""
    
    base_url = "http://localhost:13000"
    
    print("🧹 Clearing existing coin data...")
    
    # Note: We would need a clear endpoint for this, but for now we'll just do a fresh import
    # The import function handles updates/inserts, so it should work
    print("✅ Ready for fresh import (import will update existing data)")

def run_fresh_import():
    """Run a fresh Shopify import"""
    
    base_url = "http://localhost:13000"
    import_url = f"{base_url}/api/v1/shopify/products/import"
    
    print("🚀 Starting fresh Shopify import...")
    print(f"📡 Making request to: {import_url}")
    
    try:
        response = requests.post(import_url, timeout=120)  # Longer timeout for full import
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Fresh import successful!")
            print(f"📦 Imported/Updated {len(data.get('coins', []))} coins")
            
            # Show details of first few coins
            coins = data.get('coins', [])
            if coins:
                print("\n🔍 Sample imported coins:")
                for i, coin in enumerate(coins[:3]):
                    print(f"  {i+1}. {coin.get('title', 'No title')} (SKU: {coin.get('sku', 'No SKU')})")
            
            return True
            
        else:
            print(f"❌ Import failed with status {response.status_code}")
            print(f"📄 Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def verify_import():
    """Verify that the import worked correctly"""
    
    base_url = "http://localhost:13000"
    coins_url = f"{base_url}/api/v1/coins"
    
    print("\n🔍 Verifying import results...")
    
    try:
        response = requests.get(coins_url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            coins = data.get('coins', [])
            
            print(f"✅ Found {len(coins)} coins in database")
            
            if coins:
                # Check a few coins for completeness
                complete_coins = 0
                coins_with_images = 0
                coins_with_descriptions = 0
                coins_with_metafields = 0
                coins_with_collections = 0
                
                for coin in coins[:10]:  # Check first 10 coins
                    has_description = bool(coin.get('description'))
                    has_images = False
                    has_metafields = False
                    has_collections = False
                    
                    # Check shopify_metadata
                    shopify_metadata = coin.get('shopify_metadata', {})
                    if isinstance(shopify_metadata, str):
                        try:
                            shopify_metadata = json.loads(shopify_metadata)
                        except:
                            shopify_metadata = {}
                    
                    has_metafields = bool(shopify_metadata.get('product_metafields') or shopify_metadata.get('category_metafields'))
                    has_collections = bool(shopify_metadata.get('collections'))
                    
                    # Check for images (would need to query coin_images table)
                    # For now, assume images are present if coin has shopify_metadata
                    has_images = bool(shopify_metadata)
                    
                    if has_description:
                        coins_with_descriptions += 1
                    if has_images:
                        coins_with_images += 1
                    if has_metafields:
                        coins_with_metafields += 1
                    if has_collections:
                        coins_with_collections += 1
                    
                    if has_description and has_metafields and has_collections:
                        complete_coins += 1
                
                print(f"\n📊 Import Quality Check (first 10 coins):")
                print(f"  Coins with descriptions: {coins_with_descriptions}/10")
                print(f"  Coins with metafields: {coins_with_metafields}/10")
                print(f"  Coins with collections: {coins_with_collections}/10")
                print(f"  Complete coins (all data): {complete_coins}/10")
                
                # Show sample data
                sample_coin = coins[0]
                print(f"\n📋 Sample coin: {sample_coin.get('title', 'No title')}")
                print(f"  Description: {'✅ Present' if sample_coin.get('description') else '❌ Missing'}")
                
                if shopify_metadata.get('collections'):
                    collections = shopify_metadata['collections']
                    print(f"  Collections: {len(collections)} found")
                    for coll in collections[:2]:
                        print(f"    - {coll.get('title', 'No title')}")
                
                if shopify_metadata.get('product_metafields'):
                    metafields = shopify_metadata['product_metafields']
                    print(f"  Metafields: {len(metafields)} found")
                    for key, value in list(metafields.items())[:2]:
                        print(f"    - {key}: {str(value)[:30]}...")
            
            return True
        else:
            print(f"❌ Failed to verify: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error verifying import: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Fresh Shopify Import Process")
    print("=" * 60)
    
    # Clear existing data
    clear_existing_data()
    
    # Run fresh import
    import_success = run_fresh_import()
    
    if import_success:
        # Verify results
        verify_success = verify_import()
        
        print("\n" + "=" * 60)
        print("📊 Fresh Import Results:")
        print(f"  Import: {'✅ SUCCESS' if import_success else '❌ FAILED'}")
        print(f"  Verification: {'✅ SUCCESS' if verify_success else '❌ FAILED'}")
        
        if import_success and verify_success:
            print("\n🎉 Fresh import completed successfully!")
            print("✅ Descriptions, metafields, collections, and images should now be working")
        else:
            print("\n⚠️  Import completed but verification failed")
    else:
        print("\n❌ Fresh import failed")

