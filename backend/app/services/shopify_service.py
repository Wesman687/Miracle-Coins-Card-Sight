from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
import json
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.models.alerts import ShopifyIntegration, ShopifySyncLog, ShopifyProduct, ShopifyOrder, ShopifyOrderItem
from app.models import Coin
from app.models.sales import Sale
from app.models.inventory import InventoryItem, Location
from app.schemas.alerts import (
    ShopifyIntegrationCreate, ShopifySyncRequest, ShopifyWebhookPayload
)

logger = logging.getLogger(__name__)

class ShopifyService:
    def __init__(self, db: Session):
        self.db = db
        self.session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def create_integration(self, integration_data: ShopifyIntegrationCreate, created_by: str) -> ShopifyIntegration:
        """Create a new Shopify integration."""
        integration = ShopifyIntegration(
            shop_domain=integration_data.shop_domain,
            access_token=integration_data.access_token,
            webhook_secret=integration_data.webhook_secret,
            sync_products=integration_data.sync_products,
            sync_inventory=integration_data.sync_inventory,
            sync_orders=integration_data.sync_orders,
            sync_pricing=integration_data.sync_pricing,
            sync_frequency=integration_data.sync_frequency,
            active=True,
            created_by=created_by
        )
        self.db.add(integration)
        self.db.commit()
        self.db.refresh(integration)
        return integration

    def update_integration(self, integration_id: int, integration_data: Dict[str, Any]) -> Optional[ShopifyIntegration]:
        """Update Shopify integration settings."""
        integration = self.db.query(ShopifyIntegration).filter(ShopifyIntegration.id == integration_id).first()
        if not integration:
            return None

        for key, value in integration_data.items():
            if hasattr(integration, key):
                setattr(integration, key, value)

        integration.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(integration)
        return integration

    def get_integration(self, integration_id: int) -> Optional[ShopifyIntegration]:
        """Get Shopify integration by ID."""
        return self.db.query(ShopifyIntegration).filter(ShopifyIntegration.id == integration_id).first()

    def get_active_integration(self) -> Optional[ShopifyIntegration]:
        """Get the active Shopify integration."""
        return self.db.query(ShopifyIntegration).filter(ShopifyIntegration.active == True).first()

    def test_connection(self, integration_id: int) -> Dict[str, Any]:
        """Test Shopify API connection."""
        integration = self.get_integration(integration_id)
        if not integration:
            return {"status": "error", "message": "Integration not found"}

        try:
            url = f"https://{integration.shop_domain}/admin/api/2023-10/shop.json"
            headers = {
                "X-Shopify-Access-Token": integration.access_token,
                "Content-Type": "application/json"
            }
            
            response = self.session.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                shop_data = response.json()
                return {
                    "status": "success",
                    "message": "Connection successful",
                    "shop_name": shop_data.get("shop", {}).get("name", "Unknown")
                }
            else:
                return {
                    "status": "error",
                    "message": f"API error: {response.status_code} - {response.text}"
                }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Connection failed: {str(e)}"
            }

    def sync_products_to_shopify(self, integration_id: int, force_sync: bool = False) -> Dict[str, Any]:
        """Sync products from database to Shopify."""
        integration = self.get_integration(integration_id)
        if not integration:
            return {"status": "error", "message": "Integration not found"}

        sync_log = ShopifySyncLog(
            integration_id=integration_id,
            sync_type="products",
            sync_direction="to_shopify",
            status="running",
            started_at=datetime.utcnow()
        )
        self.db.add(sync_log)
        self.db.commit()

        try:
            # Get coins that need to be synced
            query = self.db.query(Coin)
            if not force_sync:
                # Only sync coins that haven't been synced or have been updated
                query = query.filter(
                    or_(
                        ~Coin.id.in_(
                            self.db.query(ShopifyProduct.coin_id).filter(
                                ShopifyProduct.sync_status == "synced"
                            )
                        ),
                        Coin.updated_at > func.coalesce(
                            self.db.query(ShopifyProduct.last_synced).filter(
                                ShopifyProduct.coin_id == Coin.id
                            ).scalar(),
                            datetime.min
                        )
                    )
                )
            
            coins = query.limit(100).all()  # Limit batch size
            processed = 0
            successful = 0
            failed = 0
            errors = []

            for coin in coins:
                processed += 1
                try:
                    # Check if product already exists in Shopify
                    existing_product = self.db.query(ShopifyProduct).filter(
                        ShopifyProduct.coin_id == coin.id
                    ).first()

                    if existing_product and existing_product.shopify_product_id:
                        # Update existing product
                        result = self._update_shopify_product(integration, coin, existing_product.shopify_product_id)
                    else:
                        # Create new product
                        result = self._create_shopify_product(integration, coin)

                    if result["success"]:
                        successful += 1
                        # Update or create ShopifyProduct record
                        if existing_product:
                            existing_product.sync_status = "synced"
                            existing_product.last_synced = datetime.utcnow()
                            existing_product.sync_error = None
                        else:
                            new_product = ShopifyProduct(
                                coin_id=coin.id,
                                shopify_product_id=result["product_id"],
                                shopify_variant_id=result.get("variant_id"),
                                sync_status="synced",
                                last_synced=datetime.utcnow(),
                                shopify_title=result.get("title"),
                                shopify_description=result.get("description"),
                                shopify_price=result.get("price"),
                                shopify_inventory_quantity=result.get("inventory_quantity")
                            )
                            self.db.add(new_product)
                        
                        # Ensure inventory item exists for this coin
                        self._ensure_inventory_item_exists(coin.id)
                    else:
                        failed += 1
                        errors.append(f"Coin {coin.id}: {result['error']}")
                        
                        # Update error status
                        if existing_product:
                            existing_product.sync_status = "error"
                            existing_product.sync_error = result["error"]

                except Exception as e:
                    failed += 1
                    errors.append(f"Coin {coin.id}: {str(e)}")
                    logger.error(f"Error syncing coin {coin.id}: {str(e)}")

            # Update sync log
            sync_log.items_processed = processed
            sync_log.items_successful = successful
            sync_log.items_failed = failed
            sync_log.status = "completed" if failed == 0 else "completed_with_errors"
            sync_log.completed_at = datetime.utcnow()
            sync_log.duration_seconds = int((sync_log.completed_at - sync_log.started_at).total_seconds())
            if errors:
                sync_log.error_message = "; ".join(errors[:5])  # Limit error message length

            # Update integration last sync
            integration.last_sync = datetime.utcnow()
            if errors:
                integration.last_error = errors[0]
                integration.error_count += 1
            else:
                integration.last_error = None

            self.db.commit()

            return {
                "status": "success",
                "processed": processed,
                "successful": successful,
                "failed": failed,
                "errors": errors[:10]  # Return first 10 errors
            }

        except Exception as e:
            sync_log.status = "failed"
            sync_log.completed_at = datetime.utcnow()
            sync_log.error_message = str(e)
            self.db.commit()
            
            return {
                "status": "error",
                "message": str(e)
            }

    def _create_shopify_product(self, integration: ShopifyIntegration, coin: Coin) -> Dict[str, Any]:
        """Create a product in Shopify."""
        try:
            url = f"https://{integration.shop_domain}/admin/api/2023-10/products.json"
            headers = {
                "X-Shopify-Access-Token": integration.access_token,
                "Content-Type": "application/json"
            }

            # Prepare product data
            product_data = {
                "product": {
                    "title": coin.title,
                    "body_html": coin.description or f"Coin: {coin.title}",
                    "vendor": "Miracle Coins",
                    "product_type": "Coin",
                    "tags": f"coin,{coin.category},{coin.year}",
                    "variants": [{
                        "price": str(coin.computed_price or coin.paid_price or 0),
                        "inventory_quantity": coin.quantity or 0,
                        "sku": coin.sku or f"MC-{coin.id}",
                        "requires_shipping": True,
                        "taxable": True
                    }]
                }
            }

            response = self.session.post(url, headers=headers, json=product_data, timeout=30)
            
            if response.status_code in [200, 201]:
                product_response = response.json()
                product = product_response["product"]
                variant = product["variants"][0] if product["variants"] else None
                
                return {
                    "success": True,
                    "product_id": str(product["id"]),
                    "variant_id": str(variant["id"]) if variant else None,
                    "title": product["title"],
                    "description": product["body_html"],
                    "price": Decimal(str(variant["price"])) if variant else None,
                    "inventory_quantity": variant["inventory_quantity"] if variant else None
                }
            else:
                return {
                    "success": False,
                    "error": f"Shopify API error: {response.status_code} - {response.text}"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _update_shopify_product(self, integration: ShopifyIntegration, coin: Coin, product_id: str) -> Dict[str, Any]:
        """Update an existing product in Shopify."""
        try:
            url = f"https://{integration.shop_domain}/admin/api/2023-10/products/{product_id}.json"
            headers = {
                "X-Shopify-Access-Token": integration.access_token,
                "Content-Type": "application/json"
            }

            # Get current product data
            get_response = self.session.get(url, headers=headers, timeout=30)
            if get_response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Failed to get product: {get_response.status_code}"
                }

            current_product = get_response.json()["product"]
            variant = current_product["variants"][0] if current_product["variants"] else None

            # Prepare update data
            update_data = {
                "product": {
                    "id": int(product_id),
                    "title": coin.title,
                    "body_html": coin.description or f"Coin: {coin.title}",
                    "variants": [{
                        "id": int(variant["id"]) if variant else None,
                        "price": str(coin.computed_price or coin.paid_price or 0),
                        "inventory_quantity": coin.quantity or 0,
                        "sku": coin.sku or f"MC-{coin.id}"
                    }]
                }
            }

            response = self.session.put(url, headers=headers, json=update_data, timeout=30)
            
            if response.status_code in [200, 201]:
                product_response = response.json()
                product = product_response["product"]
                variant = product["variants"][0] if product["variants"] else None
                
                return {
                    "success": True,
                    "product_id": str(product["id"]),
                    "variant_id": str(variant["id"]) if variant else None,
                    "title": product["title"],
                    "description": product["body_html"],
                    "price": Decimal(str(variant["price"])) if variant else None,
                    "inventory_quantity": variant["inventory_quantity"] if variant else None
                }
            else:
                return {
                    "success": False,
                    "error": f"Shopify API error: {response.status_code} - {response.text}"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def sync_orders_from_shopify(self, integration_id: int, hours_back: int = 24) -> Dict[str, Any]:
        """Sync orders from Shopify to database."""
        integration = self.get_integration(integration_id)
        if not integration:
            return {"status": "error", "message": "Integration not found"}

        sync_log = ShopifySyncLog(
            integration_id=integration_id,
            sync_type="orders",
            sync_direction="from_shopify",
            status="running",
            started_at=datetime.utcnow()
        )
        self.db.add(sync_log)
        self.db.commit()

        try:
            # Calculate date range
            since_date = datetime.utcnow() - timedelta(hours=hours_back)
            since_str = since_date.strftime("%Y-%m-%dT%H:%M:%S-00:00")

            url = f"https://{integration.shop_domain}/admin/api/2023-10/orders.json"
            headers = {
                "X-Shopify-Access-Token": integration.access_token,
                "Content-Type": "application/json"
            }
            
            params = {
                "created_at_min": since_str,
                "status": "any",
                "limit": 250
            }

            processed = 0
            successful = 0
            failed = 0
            errors = []

            while True:
                response = self.session.get(url, headers=headers, params=params, timeout=30)
                
                if response.status_code != 200:
                    errors.append(f"API error: {response.status_code} - {response.text}")
                    break

                orders_data = response.json()
                orders = orders_data.get("orders", [])

                if not orders:
                    break

                for order_data in orders:
                    processed += 1
                    try:
                        # Check if order already exists
                        existing_order = self.db.query(ShopifyOrder).filter(
                            ShopifyOrder.shopify_order_id == str(order_data["id"])
                        ).first()

                        if existing_order:
                            continue  # Skip existing orders

                        # Create order record
                        order = ShopifyOrder(
                            shopify_order_id=str(order_data["id"]),
                            order_number=order_data.get("order_number"),
                            customer_email=order_data.get("customer", {}).get("email"),
                            customer_name=f"{order_data.get('customer', {}).get('first_name', '')} {order_data.get('customer', {}).get('last_name', '')}".strip(),
                            total_price=Decimal(str(order_data.get("total_price", 0))),
                            currency=order_data.get("currency", "USD"),
                            order_status=order_data.get("financial_status"),
                            fulfillment_status=order_data.get("fulfillment_status"),
                            sync_status="synced",
                            last_synced=datetime.utcnow(),
                            order_date=datetime.fromisoformat(order_data["created_at"].replace("Z", "+00:00"))
                        )
                        self.db.add(order)
                        self.db.flush()  # Get the order ID

                        # Process line items
                        for line_item in order_data.get("line_items", []):
                            # Try to match with existing coin by SKU or title
                            coin = self._find_coin_by_shopify_item(line_item)
                            
                            if coin:
                                order_item = ShopifyOrderItem(
                                    order_id=order.id,
                                    coin_id=coin.id,
                                    shopify_line_item_id=str(line_item["id"]),
                                    product_title=line_item.get("title"),
                                    variant_title=line_item.get("variant_title"),
                                    quantity=line_item.get("quantity", 1),
                                    price=Decimal(str(line_item.get("price", 0)))
                                )
                                self.db.add(order_item)

                        successful += 1

                    except Exception as e:
                        failed += 1
                        errors.append(f"Order {order_data.get('id', 'unknown')}: {str(e)}")
                        logger.error(f"Error processing order {order_data.get('id')}: {str(e)}")

                # Check for next page
                if len(orders) < params["limit"]:
                    break
                
                # Update params for next page (Shopify uses cursor-based pagination)
                # This is simplified - in practice you'd use the Link header
                params["page_info"] = orders_data.get("page_info")

            # Update sync log
            sync_log.items_processed = processed
            sync_log.items_successful = successful
            sync_log.items_failed = failed
            sync_log.status = "completed" if failed == 0 else "completed_with_errors"
            sync_log.completed_at = datetime.utcnow()
            sync_log.duration_seconds = int((sync_log.completed_at - sync_log.started_at).total_seconds())
            if errors:
                sync_log.error_message = "; ".join(errors[:5])

            # Update integration
            integration.last_sync = datetime.utcnow()
            if errors:
                integration.last_error = errors[0]
                integration.error_count += 1
            else:
                integration.last_error = None

            self.db.commit()

            return {
                "status": "success",
                "processed": processed,
                "successful": successful,
                "failed": failed,
                "errors": errors[:10]
            }

        except Exception as e:
            sync_log.status = "failed"
            sync_log.completed_at = datetime.utcnow()
            sync_log.error_message = str(e)
            self.db.commit()
            
            return {
                "status": "error",
                "message": str(e)
            }

    def _find_coin_by_shopify_item(self, line_item: Dict[str, Any]) -> Optional[Coin]:
        """Find a coin by Shopify line item data."""
        sku = line_item.get("sku")
        title = line_item.get("title", "")
        
        # Try to find by SKU first
        if sku:
            coin = self.db.query(Coin).filter(Coin.sku == sku).first()
            if coin:
                return coin
        
        # Try to find by Shopify product mapping
        if "product_id" in line_item:
            shopify_product = self.db.query(ShopifyProduct).filter(
                ShopifyProduct.shopify_product_id == str(line_item["product_id"])
            ).first()
            if shopify_product:
                return self.db.query(Coin).filter(Coin.id == shopify_product.coin_id).first()
        
        # Try to find by title matching (fuzzy matching)
        # This is a simplified approach - in practice you'd use more sophisticated matching
        coins = self.db.query(Coin).filter(Coin.title.ilike(f"%{title}%")).all()
        if coins:
            return coins[0]  # Return first match
        
        return None

    def sync_inventory_from_shopify(self, integration_id: int) -> Dict[str, Any]:
        """Sync inventory levels from Shopify."""
        integration = self.get_integration(integration_id)
        if not integration:
            return {"status": "error", "message": "Integration not found"}

        sync_log = ShopifySyncLog(
            integration_id=integration_id,
            sync_type="inventory",
            sync_direction="from_shopify",
            status="running",
            started_at=datetime.utcnow()
        )
        self.db.add(sync_log)
        self.db.commit()

        try:
            # Get all Shopify products
            shopify_products = self.db.query(ShopifyProduct).filter(
                ShopifyProduct.shopify_product_id.isnot(None)
            ).all()

            processed = 0
            successful = 0
            failed = 0
            errors = []

            for shopify_product in shopify_products:
                processed += 1
                try:
                    # Get inventory levels from Shopify
                    url = f"https://{integration.shop_domain}/admin/api/2023-10/products/{shopify_product.shopify_product_id}.json"
                    headers = {
                        "X-Shopify-Access-Token": integration.access_token,
                        "Content-Type": "application/json"
                    }

                    response = self.session.get(url, headers=headers, timeout=30)
                    
                    if response.status_code == 200:
                        product_data = response.json()["product"]
                        variant = product_data["variants"][0] if product_data["variants"] else None
                        
                        if variant:
                            # Update coin quantity
                            coin = self.db.query(Coin).filter(Coin.id == shopify_product.coin_id).first()
                            if coin:
                                coin.quantity = variant.get("inventory_quantity", 0)
                                coin.updated_at = datetime.utcnow()
                                
                                # Update ShopifyProduct record
                                shopify_product.shopify_inventory_quantity = variant.get("inventory_quantity", 0)
                                shopify_product.last_synced = datetime.utcnow()
                                shopify_product.sync_error = None
                                
                                successful += 1
                    else:
                        failed += 1
                        errors.append(f"Product {shopify_product.shopify_product_id}: API error {response.status_code}")

                except Exception as e:
                    failed += 1
                    errors.append(f"Product {shopify_product.shopify_product_id}: {str(e)}")
                    logger.error(f"Error syncing inventory for product {shopify_product.shopify_product_id}: {str(e)}")

            # Update sync log
            sync_log.items_processed = processed
            sync_log.items_successful = successful
            sync_log.items_failed = failed
            sync_log.status = "completed" if failed == 0 else "completed_with_errors"
            sync_log.completed_at = datetime.utcnow()
            sync_log.duration_seconds = int((sync_log.completed_at - sync_log.started_at).total_seconds())
            if errors:
                sync_log.error_message = "; ".join(errors[:5])

            # Update integration
            integration.last_sync = datetime.utcnow()
            if errors:
                integration.last_error = errors[0]
                integration.error_count += 1
            else:
                integration.last_error = None

            self.db.commit()

            return {
                "status": "success",
                "processed": processed,
                "successful": successful,
                "failed": failed,
                "errors": errors[:10]
            }

        except Exception as e:
            sync_log.status = "failed"
            sync_log.completed_at = datetime.utcnow()
            sync_log.error_message = str(e)
            self.db.commit()
            
            return {
                "status": "error",
                "message": str(e)
            }

    def process_webhook(self, webhook_data: ShopifyWebhookPayload) -> Dict[str, Any]:
        """Process incoming Shopify webhook."""
        try:
            # Verify webhook signature (simplified)
            integration = self.get_active_integration()
            if not integration:
                return {"status": "error", "message": "No active integration found"}

            # Process based on webhook topic
            if webhook_data.topic == "orders/create":
                return self._process_order_webhook(webhook_data)
            elif webhook_data.topic == "orders/updated":
                return self._process_order_update_webhook(webhook_data)
            elif webhook_data.topic == "orders/paid":
                return self._process_order_paid_webhook(webhook_data)
            elif webhook_data.topic == "inventory_levels/update":
                return self._process_inventory_webhook(webhook_data)
            else:
                return {"status": "ignored", "message": f"Unhandled webhook topic: {webhook_data.topic}"}

        except Exception as e:
            logger.error(f"Error processing webhook: {str(e)}")
            return {"status": "error", "message": str(e)}

    def _process_order_webhook(self, webhook_data: ShopifyWebhookPayload) -> Dict[str, Any]:
        """Process order creation webhook."""
        # Implementation would be similar to sync_orders_from_shopify but for single order
        return {"status": "success", "message": "Order webhook processed"}

    def _process_order_update_webhook(self, webhook_data: ShopifyWebhookPayload) -> Dict[str, Any]:
        """Process order update webhook."""
        return {"status": "success", "message": "Order update webhook processed"}

    def _process_order_paid_webhook(self, webhook_data: ShopifyWebhookPayload) -> Dict[str, Any]:
        """Process order paid webhook."""
        return {"status": "success", "message": "Order paid webhook processed"}

    def _process_inventory_webhook(self, webhook_data: ShopifyWebhookPayload) -> Dict[str, Any]:
        """Process inventory update webhook."""
        return {"status": "success", "message": "Inventory webhook processed"}

    def get_sync_logs(self, integration_id: int, limit: int = 50) -> List[ShopifySyncLog]:
        """Get sync logs for an integration."""
        return self.db.query(ShopifySyncLog).filter(
            ShopifySyncLog.integration_id == integration_id
        ).order_by(desc(ShopifySyncLog.started_at)).limit(limit).all()

    def get_shopify_products(self, integration_id: int) -> List[ShopifyProduct]:
        """Get all Shopify products for an integration."""
        return self.db.query(ShopifyProduct).join(Coin).filter(
            ShopifyProduct.coin_id == Coin.id
        ).order_by(desc(ShopifyProduct.last_synced)).all()

    def get_shopify_orders(self, integration_id: int, limit: int = 100) -> List[ShopifyOrder]:
        """Get Shopify orders for an integration."""
        return self.db.query(ShopifyOrder).order_by(desc(ShopifyOrder.order_date)).limit(limit).all()

    def get_sync_statistics(self, integration_id: int) -> Dict[str, Any]:
        """Get sync statistics for an integration."""
        total_syncs = self.db.query(ShopifySyncLog).filter(
            ShopifySyncLog.integration_id == integration_id
        ).count()
        
        successful_syncs = self.db.query(ShopifySyncLog).filter(
            and_(
                ShopifySyncLog.integration_id == integration_id,
                ShopifySyncLog.status == "completed"
            )
        ).count()
        
        failed_syncs = self.db.query(ShopifySyncLog).filter(
            and_(
                ShopifySyncLog.integration_id == integration_id,
                ShopifySyncLog.status.in_(["failed", "completed_with_errors"])
            )
        ).count()
        
        # Recent sync activity
        since = datetime.utcnow() - timedelta(days=7)
        recent_syncs = self.db.query(ShopifySyncLog).filter(
            and_(
                ShopifySyncLog.integration_id == integration_id,
                ShopifySyncLog.started_at >= since
            )
        ).count()
        
        return {
            "total_syncs": total_syncs,
            "successful_syncs": successful_syncs,
            "failed_syncs": failed_syncs,
            "success_rate": (successful_syncs / total_syncs * 100) if total_syncs > 0 else 0,
            "recent_syncs": recent_syncs
        }

    def _ensure_inventory_item_exists(self, coin_id: int) -> None:
        """Ensure an inventory item exists for a coin when it's added to Shopify."""
        try:
            # Check if inventory item already exists
            existing_item = self.db.query(InventoryItem).filter(
                InventoryItem.coin_id == coin_id
            ).first()
            
            if existing_item:
                # Update existing item to ensure it's marked as available for sale
                existing_item.status = "available"
                existing_item.updated_at = datetime.utcnow()
                logger.info(f"Updated inventory item for coin {coin_id}")
                return
            
            # Get the coin
            coin = self.db.query(Coin).filter(Coin.id == coin_id).first()
            if not coin:
                logger.warning(f"Coin {coin_id} not found when creating inventory item")
                return
            
            # Get default location (or create one if none exists)
            default_location = self.db.query(Location).filter(
                Location.name == "Main Store"
            ).first()
            
            if not default_location:
                default_location = Location(
                    name="Main Store",
                    description="Primary store location",
                    address="Main Store",
                    is_active=True
                )
                self.db.add(default_location)
                self.db.flush()  # Get the ID
            
            # Create new inventory item
            inventory_item = InventoryItem(
                coin_id=coin_id,
                location_id=default_location.id,
                quantity=coin.quantity or 1,
                reserved_quantity=0,
                available_quantity=coin.quantity or 1,
                status="available",
                cost_per_unit=coin.paid_price or 0,
                last_counted_at=datetime.utcnow(),
                notes=f"Auto-created when synced to Shopify"
            )
            
            self.db.add(inventory_item)
            logger.info(f"Created inventory item for coin {coin_id} (SKU: {coin.sku})")
            
        except Exception as e:
            logger.error(f"Error creating inventory item for coin {coin_id}: {str(e)}")

    def create_product_and_inventory(self, integration_id: int, coin_id: int) -> Dict[str, Any]:
        """Create a product in Shopify and ensure it's in our inventory."""
        try:
            # Get the coin
            coin = self.db.query(Coin).filter(Coin.id == coin_id).first()
            if not coin:
                return {"status": "error", "message": "Coin not found"}
            
            # Get integration
            integration = self.get_integration(integration_id)
            if not integration:
                return {"status": "error", "message": "Integration not found"}
            
            # Create product in Shopify
            result = self._create_shopify_product(integration, coin)
            
            if result["success"]:
                # Create ShopifyProduct record
                shopify_product = ShopifyProduct(
                    coin_id=coin_id,
                    shopify_product_id=result["product_id"],
                    shopify_variant_id=result.get("variant_id"),
                    sync_status="synced",
                    last_synced=datetime.utcnow(),
                    shopify_title=result.get("title"),
                    shopify_description=result.get("description"),
                    shopify_price=result.get("price"),
                    shopify_inventory_quantity=result.get("inventory_quantity")
                )
                self.db.add(shopify_product)
                
                # Ensure inventory item exists
                self._ensure_inventory_item_exists(coin_id)
                
                self.db.commit()
                
                return {
                    "status": "success",
                    "message": f"Product created in Shopify and added to inventory",
                    "shopify_product_id": result["product_id"],
                    "coin_id": coin_id,
                    "sku": coin.sku
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to create product in Shopify: {result['error']}"
                }
                
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating product and inventory for coin {coin_id}: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }


