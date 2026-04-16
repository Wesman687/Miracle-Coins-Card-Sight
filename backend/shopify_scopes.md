# Shopify API Scopes for Miracle Coins AI Pricing System

## Complete Scope List (Copy/Paste Ready)

```
read_products,write_products,read_product_listings,write_product_listings,read_inventory,write_inventory,read_locations,read_orders,write_orders,read_customers,read_price_rules,write_price_rules,read_reports,read_webhooks,write_webhooks
```

## Individual Scopes Explained

### Product Management
- `read_products` - Read product information and details
- `write_products` - Create and update products
- `read_product_listings` - Read product listings and variants
- `write_product_listings` - Update product listings and variants

### Inventory Management
- `read_inventory` - Read inventory levels and stock
- `write_inventory` - Update inventory levels
- `read_locations` - Read store locations and warehouses

### Order Management
- `read_orders` - Read order information and details
- `write_orders` - Update order status and fulfillment
- `read_customers` - Read customer data and information

### Pricing & Analytics
- `read_price_rules` - Read pricing rules and discounts
- `write_price_rules` - Create and update pricing rules
- `read_reports` - Read analytics and sales reports

### Webhooks & Notifications
- `read_webhooks` - Read webhook configurations
- `write_webhooks` - Create webhooks for real-time updates

## Setup Instructions

1. **Go to Shopify Partner Dashboard**
2. **Create/Edit Private App**
3. **Admin API Access Scopes**
4. **Paste the complete scope list above**
5. **Save and Install**

## Local Development Setup

For local development, update your `.env` file:

```env
# Shopify Configuration
SHOPIFY_API_KEY=your_local_api_key
SHOPIFY_API_SECRET=your_local_api_secret
SHOPIFY_SHOP_DOMAIN=your-local-store.myshopify.com
```

## Testing the Integration

After setting up the scopes, test with:

```bash
# Test product creation
curl -X POST http://localhost:13000/api/v1/pricing-agent/shopify/create-test-product

# Test product listing
curl http://localhost:13000/api/v1/pricing-agent/shopify/products

# Test price update
curl -X POST "http://localhost:13000/api/v1/pricing-agent/shopify/update-price?product_id=1&new_price=85.50"
```

## Webhook Endpoints (Future)

The system will support these webhook endpoints:
- `/api/v1/webhooks/shopify/orders/created` - New order notifications
- `/api/v1/webhooks/shopify/orders/updated` - Order status updates
- `/api/v1/webhooks/shopify/products/updated` - Product changes




