import logging
import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Dict, Any, Tuple
import httpx
import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

@dataclass
class ShopifyProduct:
    """Shopify product data"""
    id: str
    title: str
    sku: str
    price: Decimal
    compare_at_price: Optional[Decimal] = None
    inventory_quantity: int = 0
    status: str = "active"

@dataclass
class ShopifyUpdateResult:
    """Result of Shopify price update"""
    product_id: str
    success: bool
    old_price: Optional[Decimal]
    new_price: Decimal
    error_message: Optional[str] = None
    updated_at: datetime = None

class ShopifyPricingService:
    """Service for updating Shopify product prices based on pricing engine results"""
    
    def __init__(self):
        self.shopify_domain = os.getenv("SHOPIFY_SHOP_DOMAIN", "b99ycv-3e.myshopify.com")
        self.access_token = os.getenv("SHOPIFY_API_KEY", "")
        self.api_version = "2023-10"
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "X-Shopify-Access-Token": self.access_token,
                "Content-Type": "application/json"
            }
        )
        self.price_update_threshold = Decimal('3.00')
        
    def update_product_price(
        self, 
        product_id: str, 
        new_price: Decimal,
        reason: str = "pricing_engine_update"
    ) -> ShopifyUpdateResult:
        """Update a single product's price in Shopify"""
        
        try:
            # Get current product data
            current_product = self._get_product(product_id)
            if not current_product:
                return ShopifyUpdateResult(
                    product_id=product_id,
                    success=False,
                    old_price=None,
                    new_price=new_price,
                    error_message="Product not found"
                )
            
            old_price = current_product.price
            
            # Check if update is needed
            if not self._should_update_price(old_price, new_price):
                return ShopifyUpdateResult(
                    product_id=product_id,
                    success=True,
                    old_price=old_price,
                    new_price=new_price,
                    error_message="Price change below threshold"
                )
            
            # Update the product
            success = self._update_product_in_shopify(product_id, new_price)
            
            if success:
                logger.info(f"Updated Shopify product {product_id}: ${old_price} -> ${new_price}")
                return ShopifyUpdateResult(
                    product_id=product_id,
                    success=True,
                    old_price=old_price,
                    new_price=new_price,
                    updated_at=datetime.now(timezone.utc)
                )
            else:
                return ShopifyUpdateResult(
                    product_id=product_id,
                    success=False,
                    old_price=old_price,
                    new_price=new_price,
                    error_message="Failed to update product in Shopify"
                )
                
        except Exception as e:
            logger.error(f"Failed to update Shopify product {product_id}: {e}")
            return ShopifyUpdateResult(
                product_id=product_id,
                success=False,
                old_price=None,
                new_price=new_price,
                error_message=str(e)
            )
    
    def _get_product(self, product_id: str) -> Optional[ShopifyProduct]:
        """Get product data from Shopify"""
        try:
            url = f"https://{self.shopify_domain}/admin/api/{self.api_version}/products/{product_id}.json"
            
            response = self.client.get(url)
            response.raise_for_status()
            
            data = response.json()
            product_data = data["product"]
            
            return ShopifyProduct(
                id=product_data["id"],
                title=product_data["title"],
                sku=product_data.get("variants", [{}])[0].get("sku", ""),
                price=Decimal(str(product_data.get("variants", [{}])[0].get("price", "0"))),
                compare_at_price=Decimal(str(product_data.get("variants", [{}])[0].get("compare_at_price", "0"))) if product_data.get("variants", [{}])[0].get("compare_at_price") else None,
                inventory_quantity=product_data.get("variants", [{}])[0].get("inventory_quantity", 0),
                status=product_data.get("status", "active")
            )
            
        except Exception as e:
            logger.error(f"Failed to get Shopify product {product_id}: {e}")
            return None
    
    def _update_product_in_shopify(self, product_id: str, new_price: Decimal) -> bool:
        """Update product price in Shopify"""
        try:
            url = f"https://{self.shopify_domain}/admin/api/{self.api_version}/products/{product_id}.json"
            
            # Get current product to preserve other data
            current_product = self._get_product(product_id)
            if not current_product:
                return False
            
            # Prepare update data
            update_data = {
                "product": {
                    "id": product_id,
                    "variants": [
                        {
                            "id": product_id,  # Assuming variant ID same as product ID
                            "price": str(new_price)
                        }
                    ]
                }
            }
            
            response = self.client.put(url, json=update_data)
            response.raise_for_status()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update Shopify product {product_id}: {e}")
            return False
    
    def _should_update_price(self, old_price: Decimal, new_price: Decimal) -> bool:
        """Determine if price should be updated based on change threshold"""
        if old_price == 0:
            return True
        
        change_percent = abs(new_price - old_price) / old_price * 100
        return change_percent >= float(self.price_update_threshold)
    
    def get_products_needing_updates(self, db = None) -> List[Dict[str, Any]]:
        """Get list of products that need price updates"""
        try:
            # Get products from Shopify with better error handling
            url = f"https://{self.shopify_domain}/admin/api/{self.api_version}/products.json"
            
            response = self.client.get(url)
            response.raise_for_status()
            
            data = response.json()
            products = data.get("products", [])
            
            logger.info(f"Found {len(products)} products in Shopify store")
            
            # Filter products that might need updates
            products_needing_updates = []
            for product in products:
                if product.get("status") == "active":
                    variant = product.get("variants", [{}])[0] if product.get("variants") else {}
                    products_needing_updates.append({
                        "product_id": product["id"],
                        "title": product["title"],
                        "sku": variant.get("sku", ""),
                        "current_price": float(variant.get("price", 0)),
                        "status": product.get("status"),
                        "vendor": product.get("vendor", ""),
                        "product_type": product.get("product_type", "")
                    })
            
            return products_needing_updates
            
        except Exception as e:
            logger.error(f"Failed to get products needing updates: {e}")
            return []
    
    def create_test_product(self) -> Dict[str, Any]:
        """Create a test product in Shopify"""
        try:
            # Create a test silver coin product
            test_product_data = {
                "product": {
                    "title": "Test Silver Eagle 1oz - AI Pricing Test",
                    "body_html": "<p>Test product created by Miracle Coins AI Pricing System</p><p>This product is used to test the pricing integration.</p>",
                    "vendor": "Miracle Coins",
                    "product_type": "Silver Coins",
                    "tags": "test,ai-pricing,silver",
                    "variants": [
                        {
                            "price": "77.97",
                            "sku": "TEST-SILVER-EAGLE-AI-001",
                            "inventory_quantity": 5,
                            "weight": 1.0,
                            "weight_unit": "oz",
                            "requires_shipping": True,
                            "taxable": True
                        }
                    ],
                    "status": "active",
                    "published": True
                }
            }
            
            url = f"https://{self.shopify_domain}/admin/api/{self.api_version}/products.json"
            
            response = self.client.post(url, json=test_product_data)
            response.raise_for_status()
            
            created_product = response.json()
            logger.info(f"Successfully created test product: {created_product['product']['title']}")
            
            return {
                "success": True,
                "product": created_product["product"],
                "message": "Test product created successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to create test product: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to create test product"
            }
    
    def close(self):
        """Close the HTTP client"""
        self.client.close()

# Global instance
shopify_pricing_service = ShopifyPricingService()
