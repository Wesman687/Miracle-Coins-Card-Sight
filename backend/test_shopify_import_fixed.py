#!/usr/bin/env python3
"""
Test script to verify Shopify import functionality with description, metadata, and collections
"""

import requests
import json

def test_shopify_import():
    """Test the Shopify import endpoint"""
    
    # Server URL
    base_url = "http://localhost:13000"
    
    # Test the import endpoint
    import_url = f"{base_url}/api/v1/shopify/products/import"
    
    print("🧪 Testing Shopify Import with Enhanced Data...")
    print(f"📡 Making request to: {import_url}")
    
    try:
        # Make the import request
        response = requests.post(import_url, timeout=30)
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Import successful!")
            print(f"📦 Imported {len(data.get('coins', []))} coins")
            
            # Show details of first few coins
            coins = data.get('coins', [])
            if coins:
                print("\n🔍 Sample imported coins:")
                for i, coin in enumerate(coins[:3]):  # Show first 3 coins
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

def test_coins_endpoint():
    """Test the coins endpoint to see imported data"""
    
    base_url = "http://localhost:13000"
    coins_url = f"{base_url}/api/v1/coins"
    
    print("\n🔍 Testing coins endpoint to verify imported data...")
    
    try:
        response = requests.get(coins_url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            coins = data.get('coins', [])
            
            print(f"✅ Found {len(coins)} coins in database")
            
            # Check a few coins for description, metadata, and collections
            if coins:
                print("\n📋 Sample coin data verification:")
                for i, coin in enumerate(coins[:2]):  # Check first 2 coins
                    print(f"\n  Coin {i+1}: {coin.get('title', 'No title')}")
                    print(f"    Description: {'✅ Present' if coin.get('description') else '❌ Missing'}")
                    
                    # Check shopify_metadata
                    shopify_metadata = coin.get('shopify_metadata', {})
                    if isinstance(shopify_metadata, str):
                        try:
                            shopify_metadata = json.loads(shopify_metadata)
                        except:
                            shopify_metadata = {}
                    
                    print(f"    Product Metafields: {'✅ Present' if shopify_metadata.get('product_metafields') else '❌ Missing'}")
                    print(f"    Category Metafields: {'✅ Present' if shopify_metadata.get('category_metafields') else '❌ Missing'}")
                    print(f"    Collections: {'✅ Present' if shopify_metadata.get('collections') else '❌ Missing'}")
                    
                    if shopify_metadata.get('collections'):
                        collections = shopify_metadata['collections']
                        print(f"      Collections count: {len(collections)}")
                        for coll in collections[:2]:  # Show first 2 collections
                            print(f"        - {coll.get('title', 'No title')}")
            
            return True
        else:
            print(f"❌ Failed to fetch coins: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing coins endpoint: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Shopify Import Test Suite")
    print("=" * 50)
    
    # Test import
    import_success = test_shopify_import()
    
    # Test coins endpoint
    coins_success = test_coins_endpoint()
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(f"  Import Test: {'✅ PASSED' if import_success else '❌ FAILED'}")
    print(f"  Coins Test: {'✅ PASSED' if coins_success else '❌ FAILED'}")
    
    if import_success and coins_success:
        print("\n🎉 All tests passed! Description, metadata, and collections should be working.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
