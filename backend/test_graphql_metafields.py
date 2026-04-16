#!/usr/bin/env python3
"""
Test GraphQL query directly to see if metafields are being returned
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_graphql_metafields():
    """Test GraphQL query directly"""
    
    # Use the same hardcoded values as the server
    SHOPIFY_DOMAIN = "b99ycv-3e.myshopify.com"
    SHOPIFY_ACCESS_TOKEN = os.getenv("SHOPIFY_API_KEY") or "shpat_your_token_here"
    
    print(f"🔑 Using Shopify domain: {SHOPIFY_DOMAIN}")
    print(f"🔑 Using access token: {SHOPIFY_ACCESS_TOKEN[:20]}...")
    
    print("🚀 Testing GraphQL Metafields Query")
    print("=" * 50)
    
    # GraphQL query to get products with metafields
    query = """
    query getProducts($first: Int!) {
      products(first: $first) {
        edges {
          node {
            id
            title
            metafields(first: 10) {
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
          }
        }
      }
    }
    """
    
    variables = {"first": 3}  # Just get 3 products for testing
    
    headers = {
        "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN,
        "Content-Type": "application/json"
    }
    
    graphql_url = f"https://{SHOPIFY_DOMAIN}/admin/api/2023-10/graphql.json"
    
    try:
        print("📡 Making GraphQL request...")
        response = requests.post(
            graphql_url,
            json={"query": query, "variables": variables},
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if "errors" in data:
                print(f"❌ GraphQL errors: {data['errors']}")
                return False
            
            products = data.get("data", {}).get("products", {}).get("edges", [])
            print(f"✅ Got {len(products)} products")
            
            for i, product_edge in enumerate(products):
                product = product_edge["node"]
                product_id = product["id"]
                title = product["title"]
                
                metafields_edges = product.get("metafields", {}).get("edges", [])
                print(f"\n📋 Product {i+1}: {title}")
                print(f"  ID: {product_id}")
                print(f"  Metafields: {len(metafields_edges)}")
                
                if metafields_edges:
                    print("  ✅ Metafields found:")
                    for metafield_edge in metafields_edges[:3]:  # Show first 3
                        metafield = metafield_edge["node"]
                        namespace = metafield.get("namespace", "")
                        key = metafield.get("key", "")
                        value = metafield.get("value", "")
                        print(f"    - {namespace}.{key}: {str(value)[:50]}...")
                else:
                    print("  ❌ No metafields found")
            
            return len(products) > 0
            
        else:
            print(f"❌ GraphQL request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_graphql_metafields()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ GraphQL query is working")
        print("💡 If no metafields found, they might not exist in Shopify")
    else:
        print("❌ GraphQL query failed")
        print("💡 Check Shopify credentials and API access")
