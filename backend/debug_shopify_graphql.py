#!/usr/bin/env python3
"""
Debug script to test GraphQL query and see what data we're getting
"""

import requests
import json

def test_graphql_query():
    """Test the GraphQL query directly to see what data structure we get"""
    
    # Shopify configuration
    SHOPIFY_DOMAIN = "b99ycv-3e.myshopify.com"
    SHOPIFY_ACCESS_TOKEN = "shpat_your_token_here"
    
    headers = {
        'X-Shopify-Access-Token': SHOPIFY_ACCESS_TOKEN,
        'Content-Type': 'application/json'
    }
    
    # Test GraphQL query
    graphql_url = f"https://{SHOPIFY_DOMAIN}/admin/api/2023-10/graphql.json"
    
    query = """
    query getProducts($first: Int!) {
      products(first: $first) {
        edges {
          node {
            id
            title
            description
            descriptionHtml
            handle
            status
            productType
            vendor
            tags
            category {
              id
              name
              fullName
            }
            priceRangeV2 {
              minVariantPrice {
                amount
                currencyCode
              }
            }
            totalInventory
            collections(first: 20) {
              edges {
                node {
                  id
                  title
                  handle
                }
              }
            }
            metafields(first: 50) {
              edges {
                node {
                  namespace
                  key
                  value
                  type
                  definition {
                    name
                    description
                  }
                }
              }
            }
            variants(first: 10) {
              edges {
                node {
                  id
                  title
                  sku
                  price
                  inventoryQuantity
                }
              }
            }
          }
        }
        pageInfo {
          hasNextPage
          endCursor
        }
      }
    }
    """
    
    variables = {"first": 5}  # Just get 5 products for testing
    
    print("🧪 Testing GraphQL Query...")
    print(f"📡 Making request to: {graphql_url}")
    
    try:
        response = requests.post(graphql_url, headers=headers, json={"query": query, "variables": variables}, timeout=30)
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if "errors" in data:
                print(f"❌ GraphQL Errors: {data['errors']}")
                return False
            
            products_edges = data.get("data", {}).get("products", {}).get("edges", [])
            print(f"✅ Found {len(products_edges)} products")
            
            if products_edges:
                # Analyze first product
                first_product = products_edges[0]["node"]
                product_id = first_product['id'].split('/')[-1]
                
                print(f"\n🔍 Analyzing first product (ID: {product_id}):")
                print(f"  Title: {first_product.get('title', 'No title')}")
                print(f"  Description: {'✅ Present' if first_product.get('description') else '❌ Missing'}")
                print(f"  DescriptionHtml: {'✅ Present' if first_product.get('descriptionHtml') else '❌ Missing'}")
                
                # Check metafields
                metafields_edges = first_product.get('metafields', {}).get('edges', [])
                print(f"  Metafields: {len(metafields_edges)} found")
                if metafields_edges:
                    print("    Sample metafields:")
                    for i, metafield_edge in enumerate(metafields_edges[:3]):
                        metafield = metafield_edge['node']
                        print(f"      {i+1}. {metafield.get('namespace', '')}.{metafield.get('key', '')} = {metafield.get('value', '')[:50]}...")
                
                # Check collections
                collections_edges = first_product.get('collections', {}).get('edges', [])
                print(f"  Collections: {len(collections_edges)} found")
                if collections_edges:
                    print("    Collections:")
                    for collection_edge in collections_edges:
                        collection = collection_edge['node']
                        print(f"      - {collection.get('title', 'No title')} (ID: {collection.get('id', 'No ID')})")
                
                # Check category
                category = first_product.get('category')
                if category:
                    print(f"  Category: {category.get('name', 'No name')} (ID: {category.get('id', 'No ID')})")
                else:
                    print("  Category: ❌ Missing")
                
                return True
            else:
                print("❌ No products found")
                return False
                
        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"📄 Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_import_endpoint():
    """Test the import endpoint to see what's happening"""
    
    base_url = "http://localhost:13000"
    import_url = f"{base_url}/api/v1/shopify/products/import"
    
    print("\n🧪 Testing Import Endpoint...")
    print(f"📡 Making request to: {import_url}")
    
    try:
        response = requests.post(import_url, timeout=60)
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Import successful!")
            print(f"📦 Imported {len(data.get('coins', []))} coins")
            
            # Check first coin for data
            coins = data.get('coins', [])
            if coins:
                first_coin = coins[0]
                print(f"\n🔍 First imported coin:")
                print(f"  Title: {first_coin.get('title', 'No title')}")
                print(f"  SKU: {first_coin.get('sku', 'No SKU')}")
                
                # Check if we can get more details from the coins endpoint
                coins_url = f"{base_url}/api/v1/coins"
                coins_response = requests.get(coins_url, timeout=10)
                
                if coins_response.status_code == 200:
                    coins_data = coins_response.json()
                    all_coins = coins_data.get('coins', [])
                    
                    if all_coins:
                        sample_coin = all_coins[0]
                        print(f"\n📋 Sample coin from database:")
                        print(f"  Title: {sample_coin.get('title', 'No title')}")
                        print(f"  Description: {'✅ Present' if sample_coin.get('description') else '❌ Missing'}")
                        
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
                            for coll in collections[:2]:
                                print(f"      - {coll.get('title', 'No title')}")
            
            return True
        else:
            print(f"❌ Import failed with status {response.status_code}")
            print(f"📄 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing import: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Shopify Debug Suite")
    print("=" * 50)
    
    # Test GraphQL query
    graphql_success = test_graphql_query()
    
    # Test import endpoint
    import_success = test_import_endpoint()
    
    print("\n" + "=" * 50)
    print("📊 Debug Results Summary:")
    print(f"  GraphQL Query: {'✅ WORKING' if graphql_success else '❌ FAILED'}")
    print(f"  Import Endpoint: {'✅ WORKING' if import_success else '❌ FAILED'}")
    
    if not graphql_success:
        print("\n⚠️  GraphQL query is failing - check Shopify credentials and API access")
    elif not import_success:
        print("\n⚠️  GraphQL works but import is failing - check server logs")
    else:
        print("\n🎉 Both GraphQL and import are working!")

