# 🪙 Miracle Coins – CoinSync Pro Specification

**Project Purpose:**
An internal admin-only system to manage coin and bullion inventory, pricing, images, and marketplace listings for *Miracle Coins*.
Frontend (Next.js) and backend (FastAPI) communicate with shared Stream-Line authentication and PostgreSQL database.

---

## ⚙️ Environment Setup

| Service          | Port      | Description                      |
| ---------------- | --------- | -------------------------------- |
| FastAPI Backend  | **13000** | Inventory + pricing API          |
| Next.js Frontend | **8100**  | Admin-only dashboard             |
| PostgreSQL       | **5432**  | Database host                    |
| Redis (existing) | —         | Used for Celery background tasks |

**Environment Variables**

```env
NEXT_PUBLIC_API_URL_PROD=https://server.stream-lineai.com
FILE_SERVER_BASE_URL=https://file-server.stream-lineai.com
AUTH_JWT_PUBLIC_KEY_BASE64=...
AUTH_SERVICE_TOKEN=...
ENCRYPTION_KEY=...
```

**File SDK:**
`pip install git+https://github.com/streamline-ai/file-uploader.git`

**Database:**
New DB: `miracle-coins`
Uses existing Postgres cluster.
Auth: Shared JWT from Stream-Line users. Only `user.isAdmin` can access UI or APIs.

---

## 🧩 Core Features

### 1. Admin Dashboard

* Stream-Line login only, `user.isAdmin` required.
* Add/Edit/Delete coins.
* Bulk import via CSV.
* Auto-list or delist items from Shopify (later eBay).
* Bulk reprice based on spot + multiplier.
* KPIs:

  * Inventory Melt Value
  * Inventory List Value
  * Gross Profit
  * Melt vs List Ratio

### 2. Inventory Management

* Track each coin’s:

  * Title, year, denomination, mint mark, grade, composition, weight, silver %, condition, and metadata.
  * Cost (`paid_price`) and computed `list_price`.
  * Quantity, SKU, and listing status.
  * Linked images (via file-server SDK).
* CSV import/export support.
* Auto-square & gold/black themed image formatting for consistency.

### 3. Pricing System

* **Default Pricing:** 30% over melt (`1.30x`)
* **Base-from-entry:** Use spot at purchase time to compute melt base.
* **Override flag:** Allows manual fixed price.
* **Melt Formula:**
  `melt = silver_content_oz * spot_silver`
* **Computed Price:**
  `computed_price = (base_from_entry ? entry_melt : melt) * multiplier`
* **Spot Refresh:** Hourly task (Celery/Redis) updates spot silver.

### 4. Silver Linkage

Each silver item stores:

| Field             | Example |
| ----------------- | ------- |
| silver_percent    | 0.900   |
| silver_content_oz | 0.7734  |
| entry_spot        | 52.50   |
| entry_melt        | 40.68   |

### 5. Image System

* Upload via file-server SDK.
* Auto-square, gold border, centered coin, black background.
* Save URLs to `coin_images` table.
* Maintain `sort_order` and `alt`.

### 6. Marketplaces

#### Shopify (Phase 1)

* Create product with `computed_price`, metafields, and images.
* Store listing URL + external ID.
* Webhook `/webhooks/shopify/order-created`:

  * Marks sold.
  * Inserts into `orders`.
  * Auto-delist other channels (future).
  * Logs audit trail.

#### eBay (Phase 2)

* Use default listing policy (GTC, US Coins, default shipping/payment).
* Sync same data as Shopify.

### 7. Background Tasks

* Redis + Celery (already configured)
* Jobs:

  * Refresh spot silver hourly.
  * Bulk reprice on demand.
  * Async Shopify/eBay syncs.
  * Auto-delist sold coins.

---

## 🗃️ Database Schema

**Database:** `miracle-coins`

```sql
CREATE TABLE coins (
  id BIGSERIAL PRIMARY KEY,
  sku TEXT UNIQUE,
  title TEXT NOT NULL,
  year INT,
  denomination TEXT,
  mint_mark TEXT,
  grade TEXT,
  category TEXT,
  description TEXT,
  condition_notes TEXT,
  is_silver BOOLEAN DEFAULT FALSE,
  silver_percent DECIMAL(5,4),
  silver_content_oz DECIMAL(7,4),
  paid_price DECIMAL(10,2),
  price_strategy TEXT DEFAULT 'spot_multiplier',
  price_multiplier DECIMAL(6,3) DEFAULT 1.300,
  base_from_entry BOOLEAN DEFAULT TRUE,
  entry_spot DECIMAL(10,2),
  entry_melt DECIMAL(10,2),
  override_price BOOLEAN DEFAULT FALSE,
  override_value DECIMAL(10,2),
  computed_price DECIMAL(10,2),
  quantity INT DEFAULT 1,
  status TEXT DEFAULT 'active',
  created_by UUID,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE coin_images (
  id BIGSERIAL PRIMARY KEY,
  coin_id BIGINT REFERENCES coins(id) ON DELETE CASCADE,
  url TEXT NOT NULL,
  alt TEXT,
  sort_order INT DEFAULT 0,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE listings (
  id BIGSERIAL PRIMARY KEY,
  coin_id BIGINT REFERENCES coins(id) ON DELETE CASCADE,
  channel TEXT NOT NULL,
  external_id TEXT,
  external_variant_id TEXT,
  url TEXT,
  status TEXT DEFAULT 'unlisted',
  last_error TEXT,
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE orders (
  id BIGSERIAL PRIMARY KEY,
  coin_id BIGINT REFERENCES coins(id),
  channel TEXT NOT NULL,
  external_order_id TEXT NOT NULL,
  qty INT DEFAULT 1,
  sold_price DECIMAL(10,2) NOT NULL,
  fees DECIMAL(10,2) DEFAULT 0.00,
  shipping_cost DECIMAL(10,2) DEFAULT 0.00,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE spot_prices (
  id BIGSERIAL PRIMARY KEY,
  metal TEXT NOT NULL,
  price DECIMAL(10,2) NOT NULL,
  source TEXT,
  fetched_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE audit_log (
  id BIGSERIAL PRIMARY KEY,
  actor UUID,
  action TEXT NOT NULL,
  entity TEXT NOT NULL,
  entity_id TEXT,
  payload JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 🧠 AI Agent System

### Folder Structure

```
/AI/
 ├─ tasks/coinsync/
 │   ├─ 01_backend_scaffold.md
 │   ├─ 02_db_migrations.md
 │   ├─ 03_inventory_crud.md
 │   ├─ 04_pricing_engine.md
 │   ├─ 05_shopify_sync.md
 │   ├─ 06_dashboard_ui.md
 │   ├─ 07_bulk_import.md
 │   └─ 08_autodelist_logic.md
 ├─ memory/coinsync/
 │   ├─ state.json
 │   ├─ decisions.json
 │   ├─ issues.json
 │   ├─ features/
 │   │   ├─ pricing.json
 │   │   ├─ marketplaces.json
 │   │   └─ images.json
 └─ status.md
```

### Cursor Rules

* Use `/api/v1` versioning.
* Keep small, typed PRs.
* Maintain repo parity (backend/services/repos/models).
* Commit DB migrations per change.
* Verify `user.isAdmin` in all write routes.
* Auto-document endpoints.

### Task Template Example

```markdown
# Task: <Feature Name>
## Summary
## Context
## Plan
## Acceptance Criteria
## Testing
## Deliverables
```

---

## 🗟️ Milestones

| Phase | Feature          | Description                  |
| ----- | ---------------- | ---------------------------- |
| 1     | Backend Scaffold | FastAPI + JWT auth           |
| 2     | DB Migrations    | Full schema setup            |
| 3     | Inventory CRUD   | Add/Edit/Delete coins        |
| 4     | File Server      | Image upload + auto-square   |
| 5     | Pricing Engine   | Spot-based and overrides     |
| 6     | Shopify Sync     | Create/list/delist + webhook |
| 7     | Dashboard        | Melt, list, profit KPIs      |
| 8     | Bulk Import      | CSV-based add/update         |
| 9     | eBay Sync        | Phase 2 rollout              |
| 10    | Final Polish     | Docs, AI memory, tests       |

---

## ✅ Acceptance Criteria

* Admins only; JWT-authenticated.
* Each coin shows correct melt, computed, and list price.
* Shopify sync successful; metafields populated.
* Auto-delist triggers on order webhook.
* Dashboard shows correct melt vs list totals.
* All images formatted square & branded.

---

## 🎨 UI / Branding

* Theme: Black background, gold accents.
* Use uploaded Miracle Coins logo.
* Keep layout minimal and mobile-friendly.

---

## 🔧 Roadmap Extensions

* Etsy & TikTok next (use same listing adapters).
* FB Marketplace final phase.
* AI-assisted pricing later (estimate collector premium).

---

## 📦 Final Output

Deliverables generated by the AI agent:

1. `backend/` FastAPI service
2. `frontend/` Next.js admin dashboard
3. `db/` migration files
4. `/AI/` folders (tasks, memory, status)
5. Configurable `.env` example
6. Deployment-ready systemd unit or Dockerfile

---

**Author:** Stream-Line AI
**Project:** Miracle Coins — CoinSync Pro
**Version:** v1.0
**Date:** 2025-10
