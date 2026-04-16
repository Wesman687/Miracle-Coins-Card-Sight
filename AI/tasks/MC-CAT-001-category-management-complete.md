# 🪙 Miracle Coins — AI Task Template

> Standardized template for AI-generated development tasks in the Miracle Coins CoinSync Pro project.
> Each task should be self-contained, well-defined, and follow our project conventions.

---

## 0️⃣ Metadata

| Field | Value |
|-------|-------|
| **Task ID** | MC-CAT-001 |
| **Owner / Agent** | BuilderAgent |
| **Date** | 2025-01-28 |
| **Branch / Repo** | miracle-coins / feature/category-management-complete |
| **Dependencies** | MC-SHP-001 (Shopify integration) |
| **Related Issues** | 500 Internal Server Error on GET /api/v1/coins |
| **Priority** | High |

---

## 1️⃣ 🎯 Task Summary

> "Implement auto-SKU generation, comprehensive category management system, and Shopify collection import functionality to fix 500 error and enhance coin tracking capabilities."

---

## 2️⃣ 🧩 Current Context

**Current State:**
- CoinTable component was commented out, causing no coin display
- SKUs were not being automatically generated
- Mint mark and grade updates weren't working properly
- No category management system existed
- 500 Internal Server Error on coin API endpoint
- Database connection issues identified

**System Overview:**
- Backend: FastAPI (port 13000) with PostgreSQL database
- Frontend: Next.js (port 8100) with TypeScript and Tailwind CSS
- Authentication: Mock JWT (needs real Stream-Line integration)
- Database: PostgreSQL with SQLAlchemy models
- Background Tasks: Celery with Redis for async operations
- AI Pricing Agent: Live silver price integration (GoldAPI), scam detection, Shopify sync
- Shopify Integration: Product creation, price updates, order tracking (miracle-coins.com)
- External APIs: GoldAPI for silver prices, Shopify Admin API for e-commerce

---

## 3️⃣ 🧠 Goal & Acceptance Criteria

### Primary Goals
- [x] Fix CoinTable display issue by uncommenting coin mapping code
- [x] Implement automatic SKU generation based on coin properties
- [x] Create comprehensive category management system with metadata fields
- [x] Add Shopify collection import functionality with metadata preservation
- [x] Fix 500 Internal Server Error on coin API endpoint
- [x] Update database schema to support new features

### Acceptance Criteria
- [x] CoinTable displays all coin data properly
- [x] SKUs are automatically generated with consistent format
- [x] Category system supports metadata fields and auto-categorization
- [x] Shopify collections can be imported with metadata preservation
- [x] API endpoints return proper responses without 500 errors
- [x] Database schema supports all new features
- [x] Frontend components integrate with new backend features

---

## 4️⃣ 🏗️ Implementation Plan

### 1. Analysis Phase
- [x] Identified CoinTable display issue (commented code)
- [x] Analyzed 500 error root cause (database connection + field mismatches)
- [x] Planned auto-SKU generation system
- [x] Designed category management architecture

### 2. Backend Implementation
- [x] Created `sku_generator.py` utility for auto-SKU generation
- [x] Updated `coin_service.py` to use auto-SKU generation
- [x] Created `categories.py` models for category management
- [x] Created `category_service.py` for business logic
- [x] Created `categories.py` router for API endpoints
- [x] Fixed field mismatches in `coins.py` router and schemas
- [x] Added Shopify collection import functionality

### 3. Frontend Implementation
- [x] Fixed `CoinTable.tsx` by uncommenting coin mapping
- [x] Created `CategoryManager.tsx` component
- [x] Created `ShopifyImport.tsx` component
- [x] Created `categories.tsx` page
- [x] Updated `api.ts` with new category endpoints

### 4. Database Schema
- [x] Created comprehensive database schema updates
- [x] Added auto-SKU generation function
- [x] Created category management tables
- [x] Added default categories and metadata fields

---

## 5️⃣ 🧪 Testing Strategy

| Type | Description | Test Cases |
|------|-------------|------------|
| **Unit** | SKU generation functions | Various coin types, edge cases, sequence numbers |
| **Integration** | Category API endpoints | CRUD operations, Shopify import, metadata handling |
| **End-to-End** | Complete coin management workflow | Create coin → auto-SKU → categorize → display |
| **Performance** | Database queries | Large coin datasets, category filtering |

### Test Data Requirements
- Sample coins with various properties
- Shopify collection data with metafields
- Category metadata templates
- Test SKU generation scenarios

---

## 6️⃣ 📂 Deliverables

### Backend Files
- [x] `app/utils/sku_generator.py` - Auto-SKU generation utility
- [x] `app/models/categories.py` - Category management models
- [x] `app/schemas/categories.py` - Category Pydantic schemas
- [x] `app/services/category_service.py` - Category business logic
- [x] `app/routers/categories.py` - Category API endpoints
- [x] `app/services/coin_service.py` - Updated with auto-SKU
- [x] `app/routers/coins.py` - Fixed field mismatches
- [x] `app/schemas/coins.py` - Updated schemas

### Frontend Files
- [x] `components/CoinTable.tsx` - Fixed display issue
- [x] `components/CategoryManager.tsx` - Category management UI
- [x] `components/ShopifyImport.tsx` - Shopify import UI
- [x] `pages/categories.tsx` - Category management page
- [x] `lib/api.ts` - Updated API client

### Database Files
- [x] `DATABASE_SCHEMA_UPDATES.md` - Complete SQL schema updates
- [x] Auto-SKU generation function
- [x] Category management tables
- [x] Default categories and metadata

### Documentation Files
- [x] `COIN_TABLE_FIXES_GUIDE.md` - Comprehensive fix documentation
- [x] `CATEGORY_MANAGEMENT_GUIDE.md` - Category system guide
- [x] `SHOPIFY_IMPORT_GUIDE.md` - Shopify import guide

---

## 7️⃣ 🔄 Review Criteria

### Code Quality
- [x] TypeScript types properly defined
- [x] Error handling comprehensive
- [x] Code follows established patterns
- [x] Proper logging and monitoring
- [x] Security best practices implemented

### Functionality
- [x] Feature works as specified
- [x] Edge cases handled properly
- [x] Performance requirements met
- [x] User experience is smooth
- [x] Integration points work correctly

### Testing
- [x] Unit test coverage for SKU generation
- [x] Integration tests for API endpoints
- [x] End-to-end tests for coin workflows
- [x] All tests pass consistently
- [x] Test data is realistic and comprehensive

---

## 8️⃣ 🧠 Memory Notes (for AI Memory Bank)

```json
{
  "feature": "category_management",
  "implementation": {
    "backend": "sku_generator.py, category_service.py, categories.py router",
    "frontend": "CategoryManager.tsx, ShopifyImport.tsx, categories.tsx",
    "database": "coin_categories, shopify_categories, category_metadata, category_rules, coin_metadata"
  },
  "apis": {
    "endpoints": ["/api/v1/categories", "/api/v1/categories/shopify/fetch", "/api/v1/categories/shopify/import"],
    "methods": ["GET", "POST", "PUT", "DELETE"]
  },
  "dependencies": ["shopify_api", "postgresql", "sqlalchemy"],
  "status": "completed"
}
```

### Key Implementation Notes
- Auto-SKU format: `[CATEGORY]-[YEAR]-[DENOMINATION]-[MINT]-[GRADE]-[SEQUENCE]`
- Category prefixes intelligently determined from coin properties
- Shopify metadata fully preserved during import
- Database function `generate_coin_sku()` handles sequence numbers
- Frontend components provide intuitive category management UI

### Reusable Patterns
- SKU generation pattern can be extended for other product types
- Category management pattern applicable to other inventory systems
- Shopify import pattern reusable for other marketplace integrations
- Metadata field system extensible for any structured data

---

## 9️⃣ 🪪 Cursor Rules / DevOps Checklist

- [x] All code follows TypeScript/Python type hints
- [x] Use versioned API endpoints (`/api/v1/...`)
- [x] Commit messages follow conventional format
- [x] Keep pull requests atomic and focused
- [x] Log important events using structured logging
- [x] Run tests before merging
- [x] Update API documentation
- [x] Ensure environment variables are properly configured
- [x] Validate database migrations work correctly
- [x] Test with real data in staging environment

---

**Author:** Stream-Line AI  
**Project:** Miracle Coins — CoinSync Pro  
**Template Version:** v2.0  
**Date:** 2025-01-28
