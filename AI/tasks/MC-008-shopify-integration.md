# MC-008: Shopify Marketplace Integration

## 0️⃣ Metadata
| Field | Value |
|-------|-------|
| **Task ID** | MC-008 |
| **Owner / Agent** | BuilderAgent |
| **Date** | 2025-01-27 |
| **Branch / Repo** | miracle-coins / feature/shopify-integration |
| **Dependencies** | MC-001 (System Scaffolding), MC-006 (Auth Integration) |
| **Related Issues** | Shopify Integration |
| **Priority** | Medium |

---

## 1️⃣ 🎯 Task Summary
> Implement full Shopify API integration for automatic product creation, inventory sync, and order processing with webhook support.

---

## 2️⃣ 🧩 Current Context
The system has placeholder Shopify integration with mock listing creation in the Celery task `sync_shopify_listing()`. The database schema includes listings table, but no real Shopify API integration exists.

**Current State:**
- Backend: Mock Shopify listing creation
- Database: `listings` table ready for Shopify data
- Webhooks: Placeholder endpoint `/webhooks/shopify/order-created`
- Frontend: No Shopify-specific UI components

**Why This Task is Needed:**
- Production requires real marketplace integration
- Automatic product creation saves manual work
- Order processing needs webhook integration
- Inventory sync ensures accurate stock levels

---

## 3️⃣ 🧠 Goal & Acceptance Criteria

### Primary Goals
- [ ] Integrate with Shopify Admin API
- [ ] Implement automatic product creation
- [ ] Add inventory synchronization
- [ ] Process order webhooks
- [ ] Handle product updates and delisting

### Acceptance Criteria
- [ ] Creates Shopify products from coin data
- [ ] Syncs inventory quantities automatically
- [ ] Processes order webhooks correctly
- [ ] Updates product prices when spot prices change
- [ ] Handles API rate limiting and errors
- [ ] Stores Shopify product IDs in database
- [ ] Implements webhook signature verification
- [ ] Provides Shopify-specific admin interface

---

## 4️⃣ 🏗️ Implementation Plan

### Shopify API Integration
1. **Create Shopify Service** (`app/services/shopify_service.py`)
   - Implement Shopify Admin API client
   - Add product creation and updates
   - Handle inventory management
   - Implement webhook processing

2. **Add Shopify Models** (`app/models.py`)
   - Enhance listings model for Shopify data
   - Add Shopify-specific fields
   - Store product variants and metafields
   - Track sync status and errors

3. **Implement Webhook Handler** (`app/routers/webhooks.py`)
   - Process order created webhooks
   - Verify webhook signatures
   - Update inventory and mark coins as sold
   - Handle webhook failures gracefully

### Product Management
1. **Product Creation Service** (`app/services/shopify_product_service.py`)
   - Map coin data to Shopify product format
   - Create product variants for different quantities
   - Add metafields for coin-specific data
   - Handle product images and descriptions

2. **Inventory Sync Service** (`app/services/shopify_inventory_service.py`)
   - Sync inventory levels with Shopify
   - Handle quantity updates
   - Process stock adjustments
   - Track inventory changes

### Celery Tasks
1. **Update Shopify Tasks** (`app/tasks.py`)
   - Replace mock listing with real Shopify API calls
   - Add product update tasks
   - Implement inventory sync tasks
   - Add error handling and retries

2. **Add Shopify Background Jobs** (`app/tasks/shopify_tasks.py`)
   - Bulk product creation
   - Price update synchronization
   - Inventory level synchronization
   - Product delisting automation

### Frontend Integration
1. **Shopify Management UI** (`components/ShopifyManagement.tsx`)
   - Display Shopify product status
   - Show sync status and errors
   - Provide manual sync controls
   - Display Shopify-specific metrics

2. **Product Sync Dashboard** (`pages/shopify.tsx`)
   - Overview of Shopify integration status
   - Sync history and error logs
   - Manual sync controls
   - Product performance metrics

### Configuration
1. **Environment Variables** (`.env`)
   - Add Shopify API credentials
   - Configure webhook endpoints
   - Set sync intervals and limits
   - Add Shopify store configuration

2. **Shopify Configuration** (`app/config/shopify.py`)
   - Define API endpoints and limits
   - Configure webhook settings
   - Set product creation rules
   - Add error handling policies

---

## 5️⃣ 🧪 Testing

| Type | Description | Test Cases |
|------|-------------|------------|
| **Unit** | Shopify API client | Product creation, product update, inventory sync, API errors |
| **Unit** | Webhook processing | Valid webhook, invalid signature, malformed data, processing errors |
| **Unit** | Product mapping | Coin to product conversion, metafields, variants, images |
| **Integration** | End-to-end sync | Create product → sync inventory → process order → update status |
| **Integration** | Webhook flow | Order webhook → inventory update → coin status change |
| **End-to-end** | Complete workflow | Add coin → create Shopify product → receive order → mark sold |

### Test Scenarios
```python
# Mock Shopify API responses
test_cases = {
    "product_creation": {
        "coin_id": 123,
        "expected_shopify_product_id": "gid://shopify/Product/456",
        "metafields": ["year", "grade", "mint_mark"]
    },
    "order_webhook": {
        "order_id": "gid://shopify/Order/789",
        "line_items": [{"product_id": "456", "quantity": 1}],
        "expected_coin_status": "sold"
    }
}
```

---

## 6️⃣ 📂 Deliverables

### Backend Files
- `app/services/shopify_service.py` - Main Shopify API integration
- `app/services/shopify_product_service.py` - Product management
- `app/services/shopify_inventory_service.py` - Inventory synchronization
- `app/routers/webhooks.py` - Webhook handling
- `app/tasks/shopify_tasks.py` - Shopify background tasks
- `app/config/shopify.py` - Shopify configuration
- `tests/test_shopify_integration.py` - Shopify integration tests

### Updated Files
- `app/tasks.py` - Updated with real Shopify integration
- `app/models.py` - Enhanced listings model
- `app/routers/listings.py` - Added Shopify-specific endpoints
- `app/services/pricing_service.py` - Added Shopify price sync

### Frontend Files
- `components/ShopifyManagement.tsx` - Shopify management interface
- `pages/shopify.tsx` - Shopify dashboard page
- `hooks/useShopify.ts` - Shopify data hook
- `types/shopify.ts` - Shopify type definitions

### Configuration Files
- `.env.example` - Updated with Shopify credentials
- `backend/env.example` - Backend Shopify configuration
- `docs/shopify-integration.md` - Shopify integration documentation

### Documentation
- Shopify API integration guide
- Webhook setup and configuration
- Product mapping and metafields documentation
- Error handling and troubleshooting guide

---

## 7️⃣ 🔄 Review Criteria

### Code Quality
- [ ] TypeScript types properly defined for all Shopify components
- [ ] Error handling comprehensive with proper fallbacks
- [ ] API integration follows Shopify best practices
- [ ] Proper logging for Shopify operations
- [ ] Rate limiting and retry logic implemented

### Functionality
- [ ] Shopify product creation working correctly
- [ ] Inventory synchronization accurate
- [ ] Webhook processing functional
- [ ] Product updates and delisting working
- [ ] Error handling graceful and informative

### Performance
- [ ] API calls optimized with batching
- [ ] Database queries efficient
- [ ] Background tasks performant
- [ ] Webhook processing fast
- [ ] Memory usage optimized

### Security
- [ ] Shopify credentials stored securely
- [ ] Webhook signatures verified
- [ ] No sensitive data in logs
- [ ] Input validation prevents injection
- [ ] Rate limiting prevents abuse

### Testing
- [ ] Unit tests cover all Shopify logic
- [ ] Integration tests verify API operations
- [ ] End-to-end tests cover complete workflow
- [ ] Test coverage above 90% for Shopify components
- [ ] Mock Shopify API for reliable testing

---

## 8️⃣ 🧠 Memory Notes (for AI Memory Bank)

```json
{
  "shopify": {
    "api_version": "2023-10",
    "rate_limit": "40_requests_per_second",
    "webhook_verification": "hmac_sha256",
    "product_metafields": ["coin_year", "coin_grade", "coin_mint_mark", "silver_content"],
    "inventory_tracking": "shopify"
  },
  "product_mapping": {
    "title": "coin.title",
    "description": "coin.description",
    "price": "coin.computed_price",
    "sku": "coin.sku",
    "inventory_quantity": "coin.quantity"
  },
  "webhooks": {
    "order_created": "/webhooks/shopify/order-created",
    "product_updated": "/webhooks/shopify/product-updated",
    "inventory_updated": "/webhooks/shopify/inventory-updated"
  }
}
```

### Key Implementation Notes
- Use Shopify Admin API v2023-10 for latest features
- Implement proper webhook signature verification
- Store Shopify product IDs for future reference
- Handle API rate limiting with exponential backoff
- Add comprehensive error logging for debugging

### Reusable Patterns
- Shopify API integration pattern
- Webhook processing pattern
- Product mapping pattern
- Inventory sync pattern
- Error handling and retry pattern

---

## 9️⃣ 🪪 Cursor Rules / DevOps Checklist

- [ ] Verify Shopify credentials are properly secured
- [ ] Use versioned endpoints (/api/v1/...)
- [ ] Commit Shopify integration changes separately
- [ ] Keep PRs atomic and type-safe
- [ ] Log Shopify operations using structured logging
- [ ] Run Shopify integration tests before merging
- [ ] Update API documentation for Shopify endpoints
- [ ] Ensure environment variables are properly typed
- [ ] Validate webhook signatures match Shopify format
- [ ] Test with real Shopify store in staging environment

---

**Author:** Stream-Line AI  
**Project:** Miracle Coins — CoinSync Pro  
**Task Version:** v1.0  
**Date:** 2025-01-27




