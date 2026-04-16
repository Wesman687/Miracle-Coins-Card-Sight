# 🪙 Miracle Coins — AI Task Template

> Standardized template for AI-generated development tasks in the Miracle Coins CoinSync Pro project.
> Each task should be self-contained, well-defined, and follow our project conventions.

---

## 0️⃣ Metadata
| Field | Value |
|-------|-------|
| **Task ID** | MC-DB-002 |
| **Owner / Agent** | DatabaseAgent / SystemArchitectAgent |
| **Date** | 2025-01-27 |
| **Branch / Repo** | miracle-coins / feature/unified-schema |
| **Dependencies** | MC-DB-001 (Database Management System) |
| **Related Issues** | Database schema consolidation and simplification |
| **Priority** | High |

---

## 1️⃣ 🎯 Task Summary
> Update database schema to match the unified structure defined in database_setup.sql, replacing the complex multi-file migration system with a simplified, consolidated schema.

**Example:**  
> "Migrate from complex multi-file database schema (5 migration files, 25+ tables) to unified database_setup.sql schema (18 core tables) with simplified structure, updated SQLAlchemy models, and streamlined data management."

---

## 2️⃣ 🧩 Current Context
Describe the current state of the system relevant to this task.

**Current State:**
- Complex database schema across 5 migration files (001-005)
- 25+ tables with overlapping and redundant structures
- Multiple SQLAlchemy model files with conflicting definitions
- Complex relationships and dependencies between tables
- Manual migration management system
- Inconsistent field naming and data types
- Performance issues due to over-normalization

**Target State (database_setup.sql):**
- Unified schema with 18 core tables
- Simplified structure with clear relationships
- Consistent field naming and data types
- Built-in sample data and default configurations
- Optimized indexes and triggers
- Streamlined for actual business needs

**System Overview:**
- Backend: FastAPI (port 13000) with PostgreSQL database
- Frontend: Next.js (port 8100) with TypeScript and Tailwind CSS
- Database: PostgreSQL with unified schema (18 tables)
- Current Schema: Complex multi-file system (25+ tables)
- Target Schema: Simplified unified structure (18 tables)
- Background Tasks: Celery with Redis for async operations
- AI Pricing Agent: Live silver price integration (GoldAPI), scam detection, Shopify sync
- Shopify Integration: Product creation, price updates, order tracking (miracle-coins.com)
- External APIs: GoldAPI for silver prices, Shopify Admin API for e-commerce

---

## 3️⃣ 🧠 Goal & Acceptance Criteria

### Primary Goals
- [ ] Replace complex multi-file migration system with unified schema
- [ ] Update SQLAlchemy models to match new simplified structure
- [ ] Migrate existing data to new schema format
- [ ] Update all API endpoints to work with new schema
- [ ] Update frontend components to work with new data structure
- [ ] Remove redundant tables and consolidate functionality
- [ ] Optimize database performance with new structure
- [ ] Ensure data integrity during migration

### Acceptance Criteria
- [ ] Database schema matches database_setup.sql exactly
- [ ] All SQLAlchemy models updated and working
- [ ] Existing data migrated successfully
- [ ] All API endpoints functional with new schema
- [ ] Frontend components work with new data structure
- [ ] Performance improved with simplified schema
- [ ] Data integrity maintained throughout migration
- [ ] All tests pass (unit, integration, e2e)
- [ ] Documentation updated
- [ ] Code follows project conventions

---

## 4️⃣ 🏗️ Implementation Plan
Step-by-step approach for implementing this task.

1. **Analysis Phase**
   - Compare current schema vs target schema
   - Identify data migration requirements
   - Map field relationships and transformations
   - Plan data preservation strategy

2. **Schema Migration**
   - Backup existing database
   - Create new unified schema
   - Migrate existing data to new structure
   - Validate data integrity

3. **Model Updates**
   - Update SQLAlchemy models to match new schema
   - Remove redundant model files
   - Update relationships and constraints
   - Ensure type safety and consistency

4. **API Updates**
   - Update all API endpoints for new schema
   - Modify request/response schemas
   - Update business logic for simplified structure
   - Test all API functionality

5. **Frontend Updates**
   - Update components to work with new data structure
   - Modify API calls and data handling
   - Update forms and validation
   - Test all frontend functionality

6. **Testing & Validation**
   - Write comprehensive tests for new schema
   - Test data migration procedures
   - Validate all functionality works
   - Performance testing

7. **Cleanup**
   - Remove old migration files
   - Update documentation
   - Clean up unused code
   - Update deployment scripts

---

## 5️⃣ 🧪 Testing Strategy

| Type | Description | Test Cases |
|------|-------------|------------|
| **Unit** | Model validation and data integrity | Field validation, relationships, constraints |
| **Integration** | API endpoints and database operations | CRUD operations, data flow, business logic |
| **End-to-End** | Complete user workflows | User journeys, data consistency, performance |
| **Migration** | Data migration and schema changes | Data preservation, integrity, transformation |

### Test Data Requirements
- Backup of existing database
- Sample data for new schema
- Migration test scenarios
- Performance benchmark data

---

## 6️⃣ 📂 Deliverables
Specific files and artifacts that will be created or modified.

### Backend Files
- `backend/app/models/` - Updated SQLAlchemy models
- `backend/app/schemas/` - Updated Pydantic schemas
- `backend/app/routers/` - Updated API endpoints
- `backend/app/services/` - Updated business logic
- `backend/database_setup.sql` - Unified schema file
- `backend/setup_db.py` - Updated database setup script

### Database Schema
- Unified database schema (18 tables)
- Data migration scripts
- Index definitions for performance
- Sample data and default configurations

### Frontend Files
- `frontend/components/` - Updated React components
- `frontend/pages/` - Updated Next.js pages
- `frontend/types/` - Updated TypeScript types
- `frontend/lib/api.ts` - Updated API client

### Documentation
- Updated database schema documentation
- Migration procedures
- API documentation updates
- Frontend component documentation

---

## 7️⃣ 🔄 Review Criteria
Quality standards that must be met before task completion.

### Code Quality
- [ ] SQLAlchemy models match new schema exactly
- [ ] API endpoints work with new data structure
- [ ] Frontend components handle new data format
- [ ] Data migration preserves all important information
- [ ] Performance improved with simplified schema

### Functionality
- [ ] All features work with new schema
- [ ] Data integrity maintained
- [ ] User workflows function correctly
- [ ] Performance requirements met
- [ ] Error handling comprehensive

### Testing
- [ ] Unit test coverage > 80%
- [ ] Integration tests cover all operations
- [ ] Migration tests validate data integrity
- [ ] End-to-end tests pass
- [ ] All tests pass consistently

---

## 8️⃣ 🧠 Memory Notes (for AI Memory Bank)
Key information to store for future reference and context.

```json
{
  "feature": "unified_database_schema",
  "implementation": {
    "backend": "unified_models, simplified_api, streamlined_services",
    "database": "unified_schema, 18_tables, sample_data",
    "frontend": "updated_components, new_data_handling"
  },
  "apis": {
    "endpoints": ["/api/v1/coins", "/api/v1/sales", "/api/v1/inventory", "/api/v1/alerts"],
    "methods": ["GET", "POST", "PUT", "DELETE"]
  },
  "dependencies": ["postgresql", "sqlalchemy", "fastapi", "nextjs"],
  "status": "in_progress"
}
```

### Key Implementation Notes
- Simplified schema reduces complexity from 25+ tables to 18 core tables
- Unified structure improves maintainability and performance
- Built-in sample data provides immediate functionality
- Streamlined relationships reduce database complexity
- Optimized indexes improve query performance

### Reusable Patterns
- Unified model patterns for consistent data handling
- Simplified API patterns for better maintainability
- Streamlined frontend patterns for improved UX
- Migration patterns for future schema changes

---

## 9️⃣ 🪪 Cursor Rules / DevOps Checklist
Development and deployment requirements.

- [ ] Database schema matches database_setup.sql exactly
- [ ] All SQLAlchemy models updated and tested
- [ ] API endpoints work with new schema
- [ ] Frontend components handle new data structure
- [ ] Data migration preserves all important information
- [ ] Performance improved with simplified schema
- [ ] All tests pass consistently
- [ ] Documentation updated
- [ ] Deployment scripts updated
- [ ] Backup and recovery procedures tested

---

## 🔟 Schema Comparison

### Current Schema (Complex - 25+ Tables):
- **Core Tables**: coins, coin_images, spot_prices, listings, orders, audit_log
- **AI Pricing**: market_prices, pricing_config, scam_detection_results, price_history
- **Sales Management**: sales_channels, sales, sales_forecasts, forecast_periods, sales_metrics
- **Inventory Management**: locations, inventory_items, inventory_movements, dead_stock_analysis, inventory_metrics, turnover_analysis
- **Financial Management**: financial_periods, cash_flow, pricing_strategies, pricing_updates, financial_metrics, expense_categories, expenses
- **Alert & Integration**: alert_rules, alerts, notification_templates, notification_logs, shopify_integrations, shopify_sync_logs, shopify_products, shopify_orders, shopify_order_items

### Target Schema (Simplified - 18 Tables):
- **Core Tables**: coins, coin_images, spot_prices, listings, orders
- **Sales Management**: sales, sales_forecasts, sales_metrics
- **Inventory Management**: inventory_items, locations
- **Financial Management**: transactions, expenses, profit_loss_statements
- **Alert System**: alert_rules, alerts
- **Shopify Integration**: shopify_integrations, shopify_products, shopify_orders, shopify_order_items

### Key Simplifications:
1. **Removed AI Pricing System** - Simplified to basic spot pricing
2. **Consolidated Sales Management** - Removed complex forecasting
3. **Simplified Inventory Management** - Basic tracking only
4. **Streamlined Financial Management** - Basic P&L tracking
5. **Simplified Alert System** - Core alerts only
6. **Maintained Shopify Integration** - Full functionality preserved

---

**Author:** Stream-Line AI  
**Project:** Miracle Coins — CoinSync Pro  
**Template Version:** v2.0  
**Date:** 2025-01-27
