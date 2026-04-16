# Shopify Integration Guide for Miracle Coins CoinSync Pro

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Database Models](#database-models)
4. [Services](#services)
5. [API Endpoints](#api-endpoints)
6. [Authentication & Configuration](#authentication--configuration)
7. [Product Management](#product-management)
8. [Inventory Synchronization](#inventory-synchronization)
9. [Order Processing](#order-processing)
10. [Collections Management](#collections-management)
11. [Webhooks](#webhooks)
12. [Pricing Integration](#pricing-integration)
13. [Implementation Examples](#implementation-examples)
14. [Error Handling](#error-handling)
15. [Best Practices](#best-practices)
16. [How to Use the Integration](#how-to-use-the-integration)
17. [Integration Checklist](#integration-checklist)
18. [Support & Troubleshooting](#support--troubleshooting)

---

## Overview

The Shopify integration in Miracle Coins CoinSync Pro provides bidirectional synchronization between the local coin inventory system and Shopify store. It supports:

- **Product Creation**: Automatically create Shopify products from coin inventory
- **Product Updates**: Sync product details, prices, and descriptions
- **Inventory Sync**: Bidirectional inventory quantity synchronization
- **Order Processing**: Import orders from Shopify and match to coins
- **Collections Management**: Sync Shopify collections to local database
- **Webhook Support**: Real-time updates via Shopify webhooks
- **Pricing Integration**: Automatic price updates based on spot prices

### Key Technologies
- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **API**: Shopify Admin REST API (v2023-10) and GraphQL
- **Authentication**: Private App Access Token
- **HTTP Client**: `requests` library with retry strategy

---

## Architecture

### Component Structure

```
backend/app/
├── models/
│   └── alerts.py              # ShopifyIntegration, ShopifyProduct, ShopifyOrder models
├── services/
│   ├── shopify_service.py     # Main Shopify integration service
│   └── shopify_pricing_service.py  # Price update service
├── routers/
│   ├── alerts.py              # Shopify integration endpoints
│   └── shopify_collections.py # Collections and product import endpoints
└── schemas/
    └── alerts.py              # Pydantic schemas for Shopify data
```

### Data Flow

1. **Product Sync (Local → Shopify)**
   ```
   Coin (Local DB) → ShopifyService → Shopify API → ShopifyProduct (Local DB)
   ```

2. **Order Sync (Shopify → Local)**
   ```
   Shopify Order → Webhook/API → ShopifyService → ShopifyOrder (Local DB) → Coin Update
   ```

3. **Inventory Sync (Bidirectional)**
   ```
   Local Inventory ↔ ShopifyService ↔ Shopify API ↔ Shopify Inventory
   ```

---

## Database Models

### ShopifyIntegration

Stores Shopify store configuration and sync settings.

```python
class ShopifyIntegration(Base):
    id: int
    shop_domain: str                    # e.g., "b99ycv-3e.myshopify.com"
    access_token: str                   # Private app access token
    webhook_secret: Optional[str]       # For webhook verification
    
    # Sync settings
    sync_products: bool = True
    sync_inventory: bool = True
    sync_orders: bool = True
    sync_pricing: bool = True
    sync_frequency: str = "hourly"     # real_time, hourly, daily
    
    # Status tracking
    active: bool = True
    last_sync: Optional[datetime]
    last_error: Optional[str]
    error_count: int = 0
    
    created_at: datetime
    created_by: str
    updated_at: datetime
```

### ShopifyProduct

Maps local coins to Shopify products.

```python
class ShopifyProduct(Base):
    id: int
    coin_id: int                        # Foreign key to coins table
    shopify_product_id: str             # Shopify product ID
    shopify_variant_id: Optional[str]    # Shopify variant ID
    shopify_handle: Optional[str]       # Product handle/URL slug
    
    # Sync status
    sync_status: str                    # pending, synced, error
    last_synced: Optional[datetime]
    sync_error: Optional[str]
    
    # Cached product data
    shopify_title: Optional[str]
    shopify_description: Optional[str]
    shopify_price: Optional[Decimal]
    shopify_inventory_quantity: Optional[int]
    
    created_at: datetime
    updated_at: datetime
```

### ShopifyOrder

Stores imported Shopify orders.

```python
class ShopifyOrder(Base):
    id: int
    shopify_order_id: str                # Shopify order ID
    order_number: Optional[str]
    
    # Customer info
    customer_email: Optional[str]
    customer_name: Optional[str]
    
    # Order details
    total_price: Decimal
    currency: str = "USD"
    order_status: Optional[str]          # pending, paid, fulfilled, cancelled
    fulfillment_status: Optional[str]    # unfulfilled, partial, fulfilled
    
    # Sync status
    sync_status: str                     # pending, synced, error
    last_synced: Optional[datetime]
    sync_error: Optional[str]
    
    order_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
```

### ShopifyOrderItem

Links order items to coins.

```python
class ShopifyOrderItem(Base):
    id: int
    order_id: int                        # Foreign key to shopify_orders
    coin_id: int                         # Foreign key to coins
    shopify_line_item_id: Optional[str]
    
    product_title: Optional[str]
    variant_title: Optional[str]
    quantity: int
    price: Decimal
```

### ShopifySyncLog

Tracks sync operations for auditing.

```python
class ShopifySyncLog(Base):
    id: int
    integration_id: int                  # Foreign key to shopify_integration
    sync_type: str                       # products, inventory, orders, pricing
    sync_direction: str                  # to_shopify, from_shopify, bidirectional
    
    # Results
    items_processed: int = 0
    items_successful: int = 0
    items_failed: int = 0
    
    # Error details
    error_message: Optional[str]
    error_details: Optional[Dict]
    
    # Timing
    started_at: datetime
    completed_at: Optional[datetime]
    duration_seconds: Optional[int]
    
    # Status
    status: str                          # running, completed, failed, cancelled
```

---

## Services

### ShopifyService

Main service class for Shopify integration operations.

**Location**: `backend/app/services/shopify_service.py`

**Key Methods**:

#### Integration Management
- `create_integration()` - Create new Shopify integration
- `update_integration()` - Update integration settings
- `get_integration()` - Get integration by ID
- `get_active_integration()` - Get currently active integration
- `test_connection()` - Test API connectivity

#### Product Sync
- `sync_products_to_shopify()` - Sync local coins to Shopify products
- `_create_shopify_product()` - Create new product in Shopify
- `_update_shopify_product()` - Update existing Shopify product
- `create_product_and_inventory()` - Create product and ensure inventory item exists

#### Order Sync
- `sync_orders_from_shopify()` - Import orders from Shopify
- `_find_coin_by_shopify_item()` - Match Shopify line items to coins

#### Inventory Sync
- `sync_inventory_from_shopify()` - Pull inventory levels from Shopify

#### Webhook Processing
- `process_webhook()` - Process incoming Shopify webhooks
- `_process_order_webhook()` - Handle order creation webhooks
- `_process_order_update_webhook()` - Handle order update webhooks
- `_process_order_paid_webhook()` - Handle order paid webhooks
- `_process_inventory_webhook()` - Handle inventory update webhooks

#### Utilities
- `get_sync_logs()` - Get sync operation history
- `get_shopify_products()` - List all synced products
- `get_shopify_orders()` - List imported orders
- `get_sync_statistics()` - Get sync performance metrics
- `_ensure_inventory_item_exists()` - Auto-create inventory items

**HTTP Client Configuration**:
```python
# Retry strategy for API calls
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
)
```

### ShopifyPricingService

Handles price updates for Shopify products.

**Location**: `backend/app/services/shopify_pricing_service.py`

**Key Methods**:
- `update_product_price()` - Update single product price
- `get_products_needing_updates()` - List products that need price updates
- `create_test_product()` - Create test product for integration testing

**Price Update Threshold**: $3.00 minimum change required

---

## API Endpoints

### Integration Management

#### Create Integration
```
POST /api/v1/shopify/integrations
```
**Request Body**:
```json
{
  "shop_domain": "b99ycv-3e.myshopify.com",
  "access_token": "shpat_...",
  "webhook_secret": "optional_secret",
  "sync_products": true,
  "sync_inventory": true,
  "sync_orders": true,
  "sync_pricing": true,
  "sync_frequency": "hourly"
}
```

#### Get Integrations
```
GET /api/v1/shopify/integrations
```

#### Get Integration
```
GET /api/v1/shopify/integrations/{integration_id}
```

#### Test Connection
```
POST /api/v1/shopify/integrations/{integration_id}/test
```

### Product Sync

#### Sync Products to Shopify
```
POST /api/v1/shopify/sync/products
```
**Request Body**:
```json
{
  "force_sync": false
}
```

#### Create Product and Inventory
```
POST /api/v1/shopify/create-product-inventory/{coin_id}?integration_id={id}
```

### Order Sync

#### Sync Orders from Shopify
```
POST /api/v1/shopify/sync/orders?hours_back=24
```

### Inventory Sync

#### Sync Inventory from Shopify
```
POST /api/v1/shopify/sync/inventory
```

### Collections

#### Get Shopify Collections
```
GET /api/v1/shopify/collections
```

#### Import Collections
```
POST /api/v1/shopify/collections/import
```
**Request Body**:
```json
{
  "collection_ids": ["123", "456"]  // Optional: filter specific collections
}
```

#### Get Shopify Products
```
GET /api/v1/shopify/products?limit=250&page_info={cursor}
```

#### Import Products
```
POST /api/v1/shopify/products/import
```
**Request Body**:
```json
{
  "product_ids": ["123", "456"],  // Optional: filter specific products
  "collection_mapping": {}        // Optional: map collections
}
```

### Webhooks

#### Process Webhook
```
POST /api/v1/shopify/webhooks
```
**Request Body**:
```json
{
  "topic": "orders/create",
  "data": { /* webhook payload */ }
}
```

### Statistics & Logs

#### Get Sync Logs
```
GET /api/v1/shopify/sync-logs/{integration_id}?limit=50
```

#### Get Shopify Products
```
GET /api/v1/shopify/products/{integration_id}
```

#### Get Shopify Orders
```
GET /api/v1/shopify/orders/{integration_id}?limit=100
```

#### Get Statistics
```
GET /api/v1/shopify/statistics/{integration_id}
```

#### Get Dashboard
```
GET /api/v1/shopify/dashboard
```

---

## Authentication & Configuration

### Step-by-Step Setup Guide

#### Step 1: Create Shopify Private App

1. **Log into Shopify Admin**
   - Go to your Shopify store admin panel
   - Navigate to: `Settings` → `Apps and sales channels` → `Develop apps`

2. **Create New App**
   - Click "Create an app"
   - Enter app name: "Miracle Coins Integration" (or your preferred name)
   - Enter app developer: Your name/company
   - Click "Create app"

3. **Configure Admin API Scopes**
   - Click "Configure Admin API scopes"
   - Select the following scopes:
     ```
     ✓ read_products
     ✓ write_products
     ✓ read_product_listings
     ✓ write_product_listings
     ✓ read_inventory
     ✓ write_inventory
     ✓ read_locations
     ✓ read_orders
     ✓ write_orders
     ✓ read_customers
     ✓ read_price_rules
     ✓ write_price_rules
     ✓ read_reports
     ✓ read_webhooks
     ✓ write_webhooks
     ```
   - Click "Save"

4. **Install App**
   - Click "Install app" button
   - Review permissions and click "Install"

5. **Get Access Token**
   - After installation, you'll see "Admin API access token"
   - Click "Reveal token once" to view it
   - **IMPORTANT**: Copy this token immediately - you won't be able to see it again!
   - Token format: `shpat_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

6. **Get Shop Domain**
   - Your shop domain is visible in the app settings
   - Format: `your-store-name.myshopify.com`
   - Example: `b99ycv-3e.myshopify.com`

#### Step 2: Configure Environment Variables

Create or update your `.env` file in the `backend/` directory:

```env
# Shopify Configuration
SHOPIFY_API_KEY=shpat_your_token_here
SHOPIFY_SHOP_DOMAIN=b99ycv-3e.myshopify.com
SHOPIFY_WEBHOOK_SECRET=your_webhook_secret_here

# Application Authentication (for API endpoints)
JWT_SECRET_KEY=your-secret-key-here
AUTH_SERVICE_TOKEN=your-service-token-here
```

**Security Notes**:
- Never commit `.env` files to version control
- Use different tokens for development and production
- Rotate tokens if compromised
- Store tokens securely (use secrets management in production)

#### Step 3: Verify Configuration

Test your configuration with a simple connection test:

```python
import requests
import os

shop_domain = os.getenv("SHOPIFY_SHOP_DOMAIN")
access_token = os.getenv("SHOPIFY_API_KEY")

url = f"https://{shop_domain}/admin/api/2023-10/shop.json"
headers = {
    "X-Shopify-Access-Token": access_token,
    "Content-Type": "application/json"
}

response = requests.get(url, headers=headers)
if response.status_code == 200:
    shop_data = response.json()
    print(f"✓ Connected to: {shop_data['shop']['name']}")
else:
    print(f"✗ Connection failed: {response.status_code}")
```

### API Authentication Methods

#### Method 1: Private App Access Token (Current Implementation)

**How it works**:
- Private app access tokens are permanent (until revoked)
- No OAuth flow required
- Direct API access with token in header

**Usage**:
```python
headers = {
    "X-Shopify-Access-Token": access_token,
    "Content-Type": "application/json"
}

response = requests.get(url, headers=headers)
```

**Token Format**:
- Starts with `shpat_`
- 32+ character hexadecimal string
- Example: `shpat_your_token_here`

#### Method 2: OAuth (For Public Apps)

If building a public app, use OAuth 2.0:

```python
# OAuth flow (not currently implemented, but available)
# 1. Redirect user to Shopify OAuth URL
# 2. User authorizes app
# 3. Receive authorization code
# 4. Exchange code for access token
```

#### Method 3: Session Token (For Embedded Apps)

For embedded Shopify apps using Shopify CLI:
- Uses session tokens from Shopify
- Automatically handled by Shopify App Bridge

### Application Authentication (API Endpoints)

The application uses JWT tokens for securing API endpoints:

#### Getting an Authentication Token

**Option 1: Using Stream-Line Auth Service**

```python
import requests

auth_url = "https://auth.stream-lineai.com/api/v1/auth/login"
credentials = {
    "username": "your_username",
    "password": "your_password"
}

response = requests.post(auth_url, json=credentials)
token = response.json()["access_token"]
```

**Option 2: Development Token (Testing)**

For development/testing, you can use a simple JWT:

```python
import jwt
import datetime

payload = {
    "user_id": "admin",
    "username": "admin",
    "isAdmin": True,
    "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
}

token = jwt.encode(payload, "your-secret-key", algorithm="HS256")
```

#### Using Authentication Token

All API endpoints require authentication:

```python
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

response = requests.get(
    "http://localhost:13000/api/v1/shopify/integrations",
    headers=headers
)
```

#### Frontend Authentication Example

```typescript
// Login and store token
const login = async (username: string, password: string) => {
  const response = await fetch('/api/v1/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  });
  
  const data = await response.json();
  localStorage.setItem('token', data.access_token);
  return data;
};

// Use token for API calls
const apiCall = async (endpoint: string) => {
  const token = localStorage.getItem('token');
  const response = await fetch(`/api/v1${endpoint}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });
  return response.json();
};
```

### Required API Scopes

Complete scope list (copy/paste ready):

```
read_products,write_products,read_product_listings,write_product_listings,read_inventory,write_inventory,read_locations,read_orders,write_orders,read_customers,read_price_rules,write_price_rules,read_reports,read_webhooks,write_webhooks
```

**Scope Breakdown**:

| Scope | Purpose | Required For |
|-------|---------|--------------|
| `read_products` | View products | Product sync, import |
| `write_products` | Create/update products | Product creation |
| `read_product_listings` | View product listings | Product management |
| `write_product_listings` | Update listings | Product updates |
| `read_inventory` | View inventory levels | Inventory sync |
| `write_inventory` | Update inventory | Inventory sync |
| `read_locations` | View store locations | Inventory management |
| `read_orders` | View orders | Order import |
| `write_orders` | Update orders | Order processing |
| `read_customers` | View customers | Order details |
| `read_price_rules` | View discounts | Pricing |
| `write_price_rules` | Create discounts | Pricing |
| `read_reports` | View analytics | Reporting |
| `read_webhooks` | View webhooks | Webhook management |
| `write_webhooks` | Create webhooks | Webhook setup |

### API Version

Current API version: **2023-10**

**Base URL Format**:
```
https://{shop_domain}/admin/api/{api_version}/{endpoint}
```

**Example URLs**:
```
https://b99ycv-3e.myshopify.com/admin/api/2023-10/products.json
https://b99ycv-3e.myshopify.com/admin/api/2023-10/orders.json
https://b99ycv-3e.myshopify.com/admin/api/2023-10/custom_collections.json
```

**GraphQL Endpoint**:
```
https://{shop_domain}/admin/api/{api_version}/graphql.json
```

### Rate Limiting

Shopify API rate limits:
- **REST API**: 40 requests per second (bucket size: 40)
- **GraphQL API**: 50 points per second (cost varies by query)

**Handling Rate Limits**:

```python
# Automatic retry with backoff (already implemented)
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
)

# Manual rate limit handling
if response.status_code == 429:
    retry_after = int(response.headers.get('Retry-After', 2))
    time.sleep(retry_after)
    # Retry request
```

**Rate Limit Headers**:
```
X-Shopify-Shop-Api-Call-Limit: 40/40
Retry-After: 2
```

---

## Product Management

### Creating Products from Coins

When syncing a coin to Shopify, the system:

1. **Maps Coin Data to Product**:
   ```python
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
   ```

2. **Creates Product via API**:
   ```python
   POST https://{shop_domain}/admin/api/2023-10/products.json
   ```

3. **Stores Mapping**:
   - Creates `ShopifyProduct` record linking `coin_id` to `shopify_product_id`
   - Stores cached product data for quick access

4. **Ensures Inventory Item**:
   - Automatically creates `InventoryItem` if it doesn't exist
   - Links to default location

### Updating Products

Product updates check for changes:
- Only syncs coins that haven't been synced OR have been updated since last sync
- Updates product title, description, price, and inventory quantity
- Preserves other Shopify product data

### Product Data Mapping

| Coin Field | Shopify Field | Notes |
|------------|--------------|-------|
| `title` | `product.title` | Product title |
| `description` | `product.body_html` | HTML description |
| `sku` | `variant.sku` | Product SKU |
| `computed_price` | `variant.price` | Selling price |
| `quantity` | `variant.inventory_quantity` | Stock quantity |
| `category` | `product.tags` | Added to tags |
| `year` | `product.tags` | Added to tags |

---

## Inventory Synchronization

### Sync Direction

The system supports bidirectional inventory sync:

#### Local → Shopify
- Updates Shopify inventory when local quantity changes
- Triggered by product sync operations
- Updates variant inventory quantity

#### Shopify → Local
- Pulls inventory levels from Shopify
- Updates local coin quantity
- Useful for reconciling stock after sales

### Inventory Sync Process

1. **Get Shopify Products**: Query all products with `shopify_product_id`
2. **Fetch Current Inventory**: Get product data from Shopify API
3. **Update Local Quantity**: Update `coin.quantity` from Shopify variant
4. **Log Sync Operation**: Record in `ShopifySyncLog`

### Inventory Item Creation

When a product is created in Shopify, the system automatically:
- Creates `InventoryItem` record if missing
- Links to default location ("Main Store")
- Sets initial quantity from coin data
- Marks as "available" status

---

## Order Processing

### Order Import Process

1. **Fetch Orders from Shopify**:
   ```python
   GET https://{shop_domain}/admin/api/2023-10/orders.json
   ```
   Parameters:
   - `created_at_min`: Date range filter
   - `status`: Order status filter
   - `limit`: Pagination (max 250)

2. **Process Each Order**:
   - Check if order already exists (by `shopify_order_id`)
   - Create `ShopifyOrder` record
   - Process line items

3. **Match Line Items to Coins**:
   - Try matching by SKU first
   - Try matching by `shopify_product_id`
   - Fallback to title matching (fuzzy)

4. **Create Order Items**:
   - Create `ShopifyOrderItem` for each matched product
   - Link to coin via `coin_id`

### Order Data Mapping

| Shopify Field | Local Field | Notes |
|--------------|-------------|-------|
| `order.id` | `shopify_order_id` | Unique identifier |
| `order.order_number` | `order_number` | Display number |
| `customer.email` | `customer_email` | Customer email |
| `customer.first_name + last_name` | `customer_name` | Full name |
| `order.total_price` | `total_price` | Order total |
| `order.currency` | `currency` | Currency code |
| `order.financial_status` | `order_status` | Payment status |
| `order.fulfillment_status` | `fulfillment_status` | Shipping status |
| `order.created_at` | `order_date` | Order timestamp |

### Order Status Values

- **Financial Status**: `pending`, `paid`, `refunded`, `voided`
- **Fulfillment Status**: `unfulfilled`, `partial`, `fulfilled`, `restocked`

---

## Collections Management

### Collection Sync Process

1. **Fetch Collections from Shopify**:
   - Custom collections: `/admin/api/2023-10/custom_collections.json`
   - Smart collections: `/admin/api/2023-10/smart_collections.json`

2. **Import to Local Database**:
   - Creates/updates `Collection` records
   - Stores `shopify_collection_id` for mapping
   - Preserves collection metadata

3. **Product-Collection Association**:
   - When importing products, extracts collection associations
   - Creates entries in `coin_collections` junction table
   - Links local collections to coins

### Collection Data Structure

```json
{
  "id": "123456",
  "title": "Silver Coins",
  "handle": "silver-coins",
  "description": "Collection of silver coins",
  "updated_at": "2024-01-01T00:00:00Z",
  "product_count": 42
}
```

### GraphQL Product Import

The system uses GraphQL for comprehensive product import:

```graphql
query getProducts($first: Int!) {
  products(first: $first) {
    edges {
      node {
        id
        title
        description
        descriptionHtml
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
            }
          }
        }
        variants(first: 10) {
          edges {
            node {
              id
              sku
              price
              inventoryQuantity
            }
          }
        }
        images(first: 10) {
          edges {
            node {
              url
              altText
            }
          }
        }
      }
    }
  }
}
```

This provides:
- Complete product data including HTML descriptions
- Collection associations
- Metafields (custom data)
- Variant information
- Product images

---

## Webhooks

### Supported Webhook Topics

- `orders/create` - New order created
- `orders/updated` - Order status changed
- `orders/paid` - Order payment received
- `inventory_levels/update` - Inventory quantity changed

### Webhook Processing

1. **Signature Verification** (recommended):
   ```python
   import hmac
   import hashlib
   
   signature = hmac.new(
       webhook_secret.encode(),
       request_body.encode(),
       hashlib.sha256
   ).hexdigest()
   
   if signature != request_headers['X-Shopify-Hmac-Sha256']:
       raise HTTPException(401, "Invalid signature")
   ```

2. **Route to Handler**:
   - `process_webhook()` routes by topic
   - Calls appropriate handler method

3. **Process Data**:
   - Updates local database
   - Creates sync log entry
   - Triggers related operations

### Webhook Endpoint

```
POST /api/v1/shopify/webhooks
```

**Headers**:
- `X-Shopify-Topic`: Webhook topic
- `X-Shopify-Hmac-Sha256`: Signature (for verification)
- `X-Shopify-Shop-Domain`: Shop domain

**Body**: Full Shopify webhook payload

---

## Pricing Integration

### Price Update Service

The `ShopifyPricingService` handles automatic price updates:

1. **Price Change Detection**:
   - Compares current Shopify price to new price
   - Only updates if change exceeds threshold ($3.00 default)

2. **Update Process**:
   ```python
   # Get current product
   current_product = _get_product(product_id)
   
   # Check if update needed
   if _should_update_price(current_price, new_price):
       # Update variant price
       _update_product_in_shopify(product_id, new_price)
   ```

3. **Price Update Threshold**:
   - Minimum $3.00 change required
   - Prevents excessive API calls for minor fluctuations
   - Configurable via `price_update_threshold`

### Price Update Endpoint

```
POST /api/v1/pricing-agent/shopify/update-price?product_id={id}&new_price={price}
```

### Test Product Creation

```
POST /api/v1/pricing-agent/shopify/create-test-product
```

Creates a test product for integration testing.

---

## Implementation Examples

### Example 1: Create Integration

```python
from app.services.shopify_service import ShopifyService
from app.schemas.alerts import ShopifyIntegrationCreate

# Create integration
integration_data = ShopifyIntegrationCreate(
    shop_domain="b99ycv-3e.myshopify.com",
    access_token="shpat_...",
    webhook_secret="secret",
    sync_products=True,
    sync_inventory=True,
    sync_orders=True,
    sync_pricing=True,
    sync_frequency="hourly"
)

service = ShopifyService(db)
integration = service.create_integration(integration_data, "admin_user")
```

### Example 2: Sync Products

```python
# Sync all products to Shopify
result = service.sync_products_to_shopify(
    integration_id=integration.id,
    force_sync=False  # Only sync changed products
)

print(f"Processed: {result['processed']}")
print(f"Successful: {result['successful']}")
print(f"Failed: {result['failed']}")
```

### Example 3: Import Orders

```python
# Import orders from last 24 hours
result = service.sync_orders_from_shopify(
    integration_id=integration.id,
    hours_back=24
)

print(f"Imported {result['successful']} orders")
```

### Example 4: Create Product for Coin

```python
# Create Shopify product for a specific coin
result = service.create_product_and_inventory(
    integration_id=integration.id,
    coin_id=123
)

if result["status"] == "success":
    print(f"Product created: {result['shopify_product_id']}")
```

### Example 5: Update Product Price

```python
from app.services.shopify_pricing_service import ShopifyPricingService

pricing_service = ShopifyPricingService()

result = pricing_service.update_product_price(
    product_id="123456",
    new_price=Decimal("85.50"),
    reason="spot_price_update"
)

if result.success:
    print(f"Price updated: ${result.old_price} → ${result.new_price}")
```

### Example 6: Process Webhook

```python
from app.schemas.alerts import ShopifyWebhookPayload

webhook_data = ShopifyWebhookPayload(
    topic="orders/create",
    data=webhook_json_data
)

result = service.process_webhook(webhook_data)
```

### Example 7: Get Sync Statistics

```python
stats = service.get_sync_statistics(integration_id)

print(f"Total syncs: {stats['total_syncs']}")
print(f"Success rate: {stats['success_rate']}%")
print(f"Recent syncs (7 days): {stats['recent_syncs']}")
```

---

## Error Handling

### Retry Strategy

The service implements automatic retry for transient errors:

```python
retry_strategy = Retry(
    total=3,                    # Maximum 3 attempts
    backoff_factor=1,          # Exponential backoff
    status_forcelist=[429, 500, 502, 503, 504]  # Retry on these status codes
)
```

### Error Logging

All errors are logged with context:

```python
logger.error(f"Error syncing coin {coin.id}: {str(e)}")
```

### Sync Error Tracking

- Errors stored in `ShopifySyncLog.error_message`
- Integration tracks `error_count` and `last_error`
- Failed items logged in sync results

### Common Error Scenarios

1. **Rate Limiting (429)**:
   - Automatically retried with backoff
   - Consider implementing rate limit tracking

2. **Authentication Failure (401)**:
   - Check access token validity
   - Verify token hasn't expired

3. **Product Not Found (404)**:
   - Product may have been deleted in Shopify
   - Update local `ShopifyProduct` sync_status to "error"

4. **Validation Errors (422)**:
   - Check product data format
   - Verify required fields are present

---

## Best Practices

### 1. Batch Operations

- Sync products in batches (default: 100 per batch)
- Use pagination for large datasets
- Process orders in time-based chunks

### 2. Rate Limiting

- Shopify allows 40 requests/second
- Implement request queuing for bulk operations
- Use exponential backoff for retries

### 3. Data Consistency

- Always check for existing records before creating
- Use transactions for multi-step operations
- Implement idempotent operations

### 4. Error Recovery

- Log all sync operations
- Track failed items for retry
- Implement manual retry endpoints

### 5. Webhook Security

- Always verify webhook signatures
- Validate webhook payload structure
- Handle duplicate webhook deliveries

### 6. Inventory Management

- Sync inventory regularly (hourly recommended)
- Reconcile discrepancies manually
- Track inventory changes in sync logs

### 7. Product Mapping

- Use SKU as primary matching key
- Store `shopify_product_id` for direct lookups
- Implement fallback matching strategies

### 8. Testing

- Use test products for integration testing
- Test webhook endpoints with Shopify webhook simulator
- Verify all sync directions work correctly

---

## How to Use the Integration

### Complete Workflow: Initial Setup

#### Step 1: First-Time Setup

1. **Create Shopify Private App** (see [Authentication & Configuration](#authentication--configuration))
   - Get access token
   - Note your shop domain

2. **Configure Environment**
   ```bash
   # In backend/.env
   SHOPIFY_API_KEY=shpat_your_token_here
   SHOPIFY_SHOP_DOMAIN=your-store.myshopify.com
   ```

3. **Start the Application**
   ```bash
   cd backend
   python -m uvicorn main:app --reload --port 13000
   ```

4. **Create Integration via API**
   ```bash
   curl -X POST http://localhost:13000/api/v1/shopify/integrations \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "shop_domain": "your-store.myshopify.com",
       "access_token": "shpat_your_token_here",
       "sync_products": true,
       "sync_inventory": true,
       "sync_orders": true,
       "sync_pricing": true,
       "sync_frequency": "hourly"
     }'
   ```

5. **Test Connection**
   ```bash
   curl -X POST http://localhost:13000/api/v1/shopify/integrations/1/test \
     -H "Authorization: Bearer YOUR_JWT_TOKEN"
   ```

   Expected response:
   ```json
   {
     "status": "success",
     "message": "Connection successful",
     "shop_name": "Your Store Name"
   }
   ```

### Workflow: Syncing Products to Shopify

#### Option A: Sync All Products

1. **Get Active Integration**
   ```bash
   curl http://localhost:13000/api/v1/shopify/integrations \
     -H "Authorization: Bearer YOUR_JWT_TOKEN"
   ```

2. **Sync Products**
   ```bash
   curl -X POST http://localhost:13000/api/v1/shopify/sync/products \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"force_sync": false}'
   ```

   Response:
   ```json
   {
     "status": "success",
     "processed": 150,
     "successful": 148,
     "failed": 2,
     "errors": ["Coin 45: Invalid price format", "Coin 67: Missing SKU"]
   }
   ```

3. **Check Sync Logs**
   ```bash
   curl http://localhost:13000/api/v1/shopify/sync-logs/1?limit=10 \
     -H "Authorization: Bearer YOUR_JWT_TOKEN"
   ```

#### Option B: Create Single Product

1. **Create Product for Specific Coin**
   ```bash
   curl -X POST "http://localhost:13000/api/v1/shopify/create-product-inventory/123?integration_id=1" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN"
   ```

   Response:
   ```json
   {
     "status": "success",
     "message": "Product created in Shopify and added to inventory",
     "shopify_product_id": "456789",
     "coin_id": 123,
     "sku": "MC-123"
   }
   ```

2. **Verify Product in Shopify**
   - Log into Shopify admin
   - Navigate to Products
   - Search for the product by SKU or title

### Workflow: Importing Products from Shopify

1. **Fetch Shopify Collections** (Optional - to see what's available)
   ```bash
   curl http://localhost:13000/api/v1/shopify/collections \
     -H "Authorization: Bearer YOUR_JWT_TOKEN"
   ```

2. **Import Collections** (Optional)
   ```bash
   curl -X POST http://localhost:13000/api/v1/shopify/collections/import \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"collection_ids": ["123", "456"]}'
   ```

3. **Import Products**
   ```bash
   curl -X POST http://localhost:13000/api/v1/shopify/products/import \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "product_ids": ["789", "101112"],
       "collection_mapping": {}
     }'
   ```

   Response:
   ```json
   {
     "message": "Successfully imported 2 products as coins",
     "coins": [
       {"id": 201, "sku": "SHOP-789", "title": "Silver Eagle 2024"},
       {"id": 202, "sku": "SHOP-101112", "title": "Gold Maple Leaf 2024"}
     ]
   }
   ```

### Workflow: Order Processing

1. **Sync Orders from Shopify**
   ```bash
   curl -X POST "http://localhost:13000/api/v1/shopify/sync/orders?hours_back=24" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN"
   ```

   Response:
   ```json
   {
     "status": "success",
     "processed": 15,
     "successful": 15,
     "failed": 0,
     "errors": []
   }
   ```

2. **View Imported Orders**
   ```bash
   curl http://localhost:13000/api/v1/shopify/orders/1?limit=50 \
     -H "Authorization: Bearer YOUR_JWT_TOKEN"
   ```

3. **Check Order Details**
   - Orders are stored in `shopify_orders` table
   - Order items linked to coins via `shopify_order_items`
   - Use order data to update coin status (e.g., mark as sold)

### Workflow: Inventory Synchronization

1. **Sync Inventory from Shopify** (Pull Shopify → Local)
   ```bash
   curl -X POST http://localhost:13000/api/v1/shopify/sync/inventory \
     -H "Authorization: Bearer YOUR_JWT_TOKEN"
   ```

   This updates local coin quantities based on Shopify inventory levels.

2. **Sync Products** (Push Local → Shopify)
   ```bash
   curl -X POST http://localhost:13000/api/v1/shopify/sync/products \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"force_sync": false}'
   ```

   This updates Shopify product quantities based on local coin quantities.

### Workflow: Price Updates

1. **Update Single Product Price**
   ```bash
   curl -X POST "http://localhost:13000/api/v1/pricing-agent/shopify/update-price?product_id=456789&new_price=85.50" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN"
   ```

2. **Get Products Needing Updates**
   ```python
   from app.services.shopify_pricing_service import ShopifyPricingService
   
   service = ShopifyPricingService()
   products = service.get_products_needing_updates()
   
   for product in products:
       # Calculate new price based on spot price
       new_price = calculate_price(product)
       service.update_product_price(product['product_id'], new_price)
   ```

### Workflow: Webhook Setup

1. **Configure Webhook in Shopify Admin**
   - Go to: Settings → Notifications → Webhooks
   - Click "Create webhook"
   - Event: Select webhook type (e.g., "Order creation")
   - Format: JSON
   - URL: `https://your-domain.com/api/v1/shopify/webhooks`
   - API version: 2023-10
   - Click "Save webhook"

2. **Update Integration with Webhook Secret**
   ```bash
   curl -X PUT http://localhost:13000/api/v1/shopify/integrations/1 \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"webhook_secret": "your_webhook_secret"}'
   ```

3. **Test Webhook** (Using Shopify webhook simulator or create test order)

### Workflow: Monitoring & Troubleshooting

1. **View Dashboard**
   ```bash
   curl http://localhost:13000/api/v1/shopify/dashboard \
     -H "Authorization: Bearer YOUR_JWT_TOKEN"
   ```

   Returns:
   - Integration status
   - Recent syncs
   - Sync statistics
   - Product sync status
   - Recent orders

2. **Check Sync Statistics**
   ```bash
   curl http://localhost:13000/api/v1/shopify/statistics/1 \
     -H "Authorization: Bearer YOUR_JWT_TOKEN"
   ```

   Response:
   ```json
   {
     "total_syncs": 245,
     "successful_syncs": 240,
     "failed_syncs": 5,
     "success_rate": 97.96,
     "recent_syncs": 12
   }
   ```

3. **View Sync Logs**
   ```bash
   curl http://localhost:13000/api/v1/shopify/sync-logs/1?limit=20 \
     -H "Authorization: Bearer YOUR_JWT_TOKEN"
   ```

4. **Check Failed Items**
   - Review sync logs for error messages
   - Check `ShopifyProduct.sync_error` field
   - Review `ShopifyIntegration.last_error`

### Frontend Usage Examples

#### React/TypeScript Example

```typescript
import { useState, useEffect } from 'react';

interface ShopifyIntegration {
  id: number;
  shop_domain: string;
  active: boolean;
  last_sync: string | null;
}

// Get authentication token (from login)
const getToken = () => localStorage.getItem('token');

// Fetch integrations
const useShopifyIntegrations = () => {
  const [integrations, setIntegrations] = useState<ShopifyIntegration[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchIntegrations = async () => {
      try {
        const response = await fetch('http://localhost:13000/api/v1/shopify/integrations', {
          headers: {
            'Authorization': `Bearer ${getToken()}`,
            'Content-Type': 'application/json'
          }
        });
        const data = await response.json();
        setIntegrations(data);
      } catch (error) {
        console.error('Failed to fetch integrations:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchIntegrations();
  }, []);

  return { integrations, loading };
};

// Create integration
const createIntegration = async (data: {
  shop_domain: string;
  access_token: string;
  sync_products: boolean;
  sync_inventory: boolean;
  sync_orders: boolean;
  sync_pricing: boolean;
}) => {
  const response = await fetch('http://localhost:13000/api/v1/shopify/integrations', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${getToken()}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(data)
  });
  return response.json();
};

// Sync products
const syncProducts = async (forceSync: boolean = false) => {
  const response = await fetch('http://localhost:13000/api/v1/shopify/sync/products', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${getToken()}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ force_sync: forceSync })
  });
  return response.json();
};

// Test connection
const testConnection = async (integrationId: number) => {
  const response = await fetch(
    `http://localhost:13000/api/v1/shopify/integrations/${integrationId}/test`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${getToken()}`,
        'Content-Type': 'application/json'
      }
    }
  );
  return response.json();
};
```

#### Python Client Example

```python
import requests
from typing import Dict, Any, Optional

class ShopifyIntegrationClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def create_integration(self, shop_domain: str, access_token: str, 
                          sync_settings: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new Shopify integration"""
        url = f"{self.base_url}/api/v1/shopify/integrations"
        data = {
            "shop_domain": shop_domain,
            "access_token": access_token,
            **sync_settings
        }
        response = requests.post(url, json=data, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def test_connection(self, integration_id: int) -> Dict[str, Any]:
        """Test Shopify API connection"""
        url = f"{self.base_url}/api/v1/shopify/integrations/{integration_id}/test"
        response = requests.post(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def sync_products(self, force_sync: bool = False) -> Dict[str, Any]:
        """Sync products to Shopify"""
        url = f"{self.base_url}/api/v1/shopify/sync/products"
        data = {"force_sync": force_sync}
        response = requests.post(url, json=data, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def sync_orders(self, hours_back: int = 24) -> Dict[str, Any]:
        """Sync orders from Shopify"""
        url = f"{self.base_url}/api/v1/shopify/sync/orders"
        params = {"hours_back": hours_back}
        response = requests.post(url, params=params, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_dashboard(self) -> Dict[str, Any]:
        """Get Shopify dashboard data"""
        url = f"{self.base_url}/api/v1/shopify/dashboard"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

# Usage
client = ShopifyIntegrationClient(
    base_url="http://localhost:13000",
    token="your_jwt_token"
)

# Create integration
integration = client.create_integration(
    shop_domain="your-store.myshopify.com",
    access_token="shpat_your_token",
    sync_settings={
        "sync_products": True,
        "sync_inventory": True,
        "sync_orders": True,
        "sync_pricing": True,
        "sync_frequency": "hourly"
    }
)

# Test connection
result = client.test_connection(integration["id"])
print(f"Connection: {result['status']}")

# Sync products
sync_result = client.sync_products(force_sync=False)
print(f"Synced {sync_result['successful']} products")
```

### Scheduled Sync Tasks

#### Using Celery (Recommended)

```python
# backend/app/tasks/shopify_tasks.py
from celery import shared_task
from app.database import SessionLocal
from app.services.shopify_service import ShopifyService

@shared_task
def sync_shopify_products():
    """Scheduled task to sync products to Shopify"""
    db = SessionLocal()
    try:
        service = ShopifyService(db)
        integration = service.get_active_integration()
        if integration:
            result = service.sync_products_to_shopify(integration.id, force_sync=False)
            return result
    finally:
        db.close()

@shared_task
def sync_shopify_orders():
    """Scheduled task to sync orders from Shopify"""
    db = SessionLocal()
    try:
        service = ShopifyService(db)
        integration = service.get_active_integration()
        if integration:
            result = service.sync_orders_from_shopify(integration.id, hours_back=24)
            return result
    finally:
        db.close()

@shared_task
def sync_shopify_inventory():
    """Scheduled task to sync inventory"""
    db = SessionLocal()
    try:
        service = ShopifyService(db)
        integration = service.get_active_integration()
        if integration:
            result = service.sync_inventory_from_shopify(integration.id)
            return result
    finally:
        db.close()
```

#### Celery Beat Configuration

```python
# backend/celery_app.py
from celery.schedules import crontab

app.conf.beat_schedule = {
    'sync-shopify-products-hourly': {
        'task': 'app.tasks.shopify_tasks.sync_shopify_products',
        'schedule': crontab(minute=0),  # Every hour
    },
    'sync-shopify-orders-hourly': {
        'task': 'app.tasks.shopify_tasks.sync_shopify_orders',
        'schedule': crontab(minute=15),  # Every hour at :15
    },
    'sync-shopify-inventory-hourly': {
        'task': 'app.tasks.shopify_tasks.sync_shopify_inventory',
        'schedule': crontab(minute=30),  # Every hour at :30
    },
}
```

#### Using Cron (Alternative)

```bash
# Add to crontab: crontab -e
# Sync products every hour
0 * * * * cd /path/to/backend && python -c "from app.services.shopify_service import ShopifyService; from app.database import SessionLocal; db = SessionLocal(); service = ShopifyService(db); integration = service.get_active_integration(); service.sync_products_to_shopify(integration.id) if integration else None; db.close()"

# Sync orders every hour at :15
15 * * * * cd /path/to/backend && python -c "from app.services.shopify_service import ShopifyService; from app.database import SessionLocal; db = SessionLocal(); service = ShopifyService(db); integration = service.get_active_integration(); service.sync_orders_from_shopify(integration.id, 24) if integration else None; db.close()"
```

---

## Integration Checklist

When integrating this system into another application:

- [ ] Set up environment variables (API key, domain, webhook secret)
- [ ] Create Shopify private app with required scopes
- [ ] Implement database models (or adapt to your schema)
- [ ] Set up API endpoints (or adapt to your framework)
- [ ] Configure webhook endpoints in Shopify admin
- [ ] Test connection with `test_connection()` method
- [ ] Create initial integration record
- [ ] Test product creation
- [ ] Test order import
- [ ] Test inventory sync
- [ ] Set up scheduled sync tasks (Celery/cron)
- [ ] Implement error monitoring
- [ ] Set up logging and alerting

---

## Additional Resources

### Shopify API Documentation
- [Admin REST API](https://shopify.dev/api/admin-rest)
- [GraphQL Admin API](https://shopify.dev/api/admin-graphql)
- [Webhooks](https://shopify.dev/apps/webhooks)

### Project Files Reference
- Service: `backend/app/services/shopify_service.py`
- Pricing Service: `backend/app/services/shopify_pricing_service.py`
- Collections Router: `backend/app/routers/shopify_collections.py`
- Models: `backend/app/models/alerts.py`
- Schemas: `backend/app/schemas/alerts.py`

---

## Support & Troubleshooting

### Common Issues

1. **"Integration not found"**
   - Ensure integration is created before use
   - Check `active=True` status

2. **"No active integration found"**
   - Create integration or activate existing one
   - Verify `active` field is `True`

3. **API Connection Failures**
   - Verify access token is valid
   - Check shop domain format
   - Ensure network connectivity

4. **Product Sync Failures**
   - Check coin data completeness
   - Verify required fields (title, price, SKU)
   - Review sync logs for specific errors

5. **Order Matching Issues**
   - Ensure products are synced first
   - Check SKU matching
   - Review `_find_coin_by_shopify_item()` logic

---

**Last Updated**: 2025-01-28  
**Version**: 1.0  
**Project**: Miracle Coins CoinSync Pro

