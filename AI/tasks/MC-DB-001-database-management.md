# 🪙 Miracle Coins — AI Task Template

> Standardized template for AI-generated development tasks in the Miracle Coins CoinSync Pro project.
> Each task should be self-contained, well-defined, and follow our project conventions.

---

## 0️⃣ Metadata
| Field | Value |
|-------|-------|
| **Task ID** | MC-DB-001 |
| **Owner / Agent** | DatabaseAgent / SystemArchitectAgent |
| **Date** | 2025-01-27 |
| **Branch / Repo** | miracle-coins / feature/database-management |
| **Dependencies** | None - foundational task |
| **Related Issues** | Database schema consolidation and management |
| **Priority** | High |

---

## 1️⃣ 🎯 Task Summary
> Comprehensive database management system for Miracle Coins CoinSync Pro with unified schema, migration management, and data integrity.

**Example:**  
> "Implement comprehensive database management system with unified schema, automated migrations, data validation, and performance optimization for the complete Miracle Coins CoinSync Pro platform."

---

## 2️⃣ 🧩 Current Context
Describe the current state of the system relevant to this task.

**Current State:**
- Database schema exists across 5 migration files with comprehensive tables
- Multiple model files with overlapping and duplicate definitions
- SQLAlchemy models scattered across different files
- Manual database setup process with setup_db.py
- No unified database management system
- Missing data validation and integrity checks
- No automated migration management
- Performance optimization not implemented

**System Overview:**
- Backend: FastAPI (port 13000) with PostgreSQL database
- Frontend: Next.js (port 8100) with TypeScript and Tailwind CSS
- Database: PostgreSQL with comprehensive schema (25+ tables)
- Migration System: Manual SQL files with no versioning
- Models: SQLAlchemy with scattered definitions
- Background Tasks: Celery with Redis for async operations
- AI Pricing Agent: Live silver price integration (GoldAPI), scam detection, Shopify sync
- Shopify Integration: Product creation, price updates, order tracking (miracle-coins.com)
- External APIs: GoldAPI for silver prices, Shopify Admin API for e-commerce

---

## 3️⃣ 🧠 Goal & Acceptance Criteria

### Primary Goals
- [ ] Consolidate and unify database schema across all migration files
- [ ] Create comprehensive SQLAlchemy model definitions with proper relationships
- [ ] Implement automated migration management system
- [ ] Add data validation and integrity constraints
- [ ] Optimize database performance with proper indexing
- [ ] Create database management utilities and scripts
- [ ] Implement data backup and recovery procedures
- [ ] Add comprehensive database documentation

### Acceptance Criteria
- [ ] All database tables properly defined with relationships
- [ ] Automated migration system working correctly
- [ ] Data validation preventing invalid data entry
- [ ] Performance optimized with proper indexes
- [ ] Database management scripts functional
- [ ] Backup and recovery procedures tested
- [ ] Comprehensive documentation available
- [ ] All tests pass (unit, integration, e2e)
- [ ] Code follows project conventions
- [ ] Performance requirements met

---

## 4️⃣ 🏗️ Implementation Plan
Step-by-step approach for implementing this task.

1. **Analysis Phase**
   - Review all existing migration files and model definitions
   - Identify duplicate and conflicting table definitions
   - Map out all relationships between entities
   - Plan unified schema structure

2. **Schema Consolidation**
   - Create unified database schema file
   - Consolidate all table definitions
   - Resolve conflicts and duplicates
   - Implement proper foreign key relationships

3. **Model Implementation**
   - Create comprehensive SQLAlchemy models
   - Implement proper relationships and constraints
   - Add data validation and business rules
   - Ensure type safety and consistency

4. **Migration System**
   - Implement Alembic-based migration system
   - Create migration scripts for existing data
   - Add migration validation and rollback capabilities
   - Implement automated migration testing

5. **Performance Optimization**
   - Add proper database indexes
   - Implement query optimization
   - Add database connection pooling
   - Create performance monitoring

6. **Management Utilities**
   - Create database management scripts
   - Implement backup and recovery procedures
   - Add data validation utilities
   - Create database health checks

7. **Testing & Validation**
   - Write comprehensive database tests
   - Test migration procedures
   - Validate data integrity
   - Performance testing

---

## 5️⃣ 🧪 Testing Strategy

| Type | Description | Test Cases |
|------|-------------|------------|
| **Unit** | Individual model validation and constraints | Field validation, relationship integrity, business rules |
| **Integration** | Database operations and migrations | CRUD operations, migration scripts, data consistency |
| **End-to-End** | Complete database workflows | Data flow, backup/restore, performance benchmarks |
| **Performance** | Database performance and scalability | Query performance, index effectiveness, connection pooling |

### Test Data Requirements
- Sample data for all table types
- Test migration scenarios
- Performance benchmark data
- Backup and recovery test data

---

## 6️⃣ 📂 Deliverables
Specific files and artifacts that will be created or modified.

### Backend Files
- `backend/app/models/` - Unified SQLAlchemy models
- `backend/migrations/` - Alembic migration files
- `backend/app/database.py` - Database configuration and utilities
- `backend/app/schemas/` - Pydantic schemas for validation
- `backend/scripts/` - Database management scripts
- `backend/tests/` - Database test files

### Database Schema
- Unified database schema definition
- Migration scripts for existing data
- Index definitions for performance
- Constraint definitions for data integrity

### Configuration Files
- Alembic configuration
- Database connection settings
- Backup and recovery configurations
- Performance monitoring settings

### Documentation
- Database schema documentation
- Migration procedures
- Backup and recovery procedures
- Performance optimization guide

---

## 7️⃣ 🔄 Review Criteria
Quality standards that must be met before task completion.

### Code Quality
- [ ] SQLAlchemy models properly defined with relationships
- [ ] Data validation comprehensive and effective
- [ ] Migration scripts tested and validated
- [ ] Performance optimization implemented
- [ ] Security best practices followed

### Functionality
- [ ] Database operations work correctly
- [ ] Migration system functions properly
- [ ] Data integrity maintained
- [ ] Performance requirements met
- [ ] Backup and recovery procedures tested

### Testing
- [ ] Unit test coverage > 80%
- [ ] Integration tests cover all operations
- [ ] Migration tests validate data integrity
- [ ] Performance tests meet benchmarks
- [ ] All tests pass consistently

---

## 8️⃣ 🧠 Memory Notes (for AI Memory Bank)
Key information to store for future reference and context.

```json
{
  "feature": "database_management",
  "implementation": {
    "backend": "unified_models, migration_system, performance_optimization",
    "database": "postgresql_schema, alembic_migrations, data_validation",
    "utilities": "backup_recovery, health_checks, management_scripts"
  },
  "apis": {
    "endpoints": ["/api/v1/database/health", "/api/v1/database/backup", "/api/v1/database/migrate"],
    "methods": ["GET", "POST"]
  },
  "dependencies": ["alembic", "sqlalchemy", "postgresql", "redis"],
  "status": "in_progress"
}
```

### Key Implementation Notes
- Unified schema consolidates 5 migration files into coherent structure
- Alembic-based migration system replaces manual SQL files
- Comprehensive data validation prevents invalid data entry
- Performance optimization with proper indexing and query optimization
- Backup and recovery procedures ensure data safety

### Reusable Patterns
- SQLAlchemy model patterns for consistent relationships
- Migration patterns for schema changes
- Validation patterns for data integrity
- Performance optimization patterns for scalability

---

## 9️⃣ 🪪 Cursor Rules / DevOps Checklist
Development and deployment requirements.

- [ ] All database models follow SQLAlchemy best practices
- [ ] Migration scripts are tested and validated
- [ ] Data validation prevents invalid data entry
- [ ] Performance optimization implemented
- [ ] Backup and recovery procedures documented
- [ ] Database health checks implemented
- [ ] Connection pooling configured
- [ ] Index optimization completed
- [ ] Data integrity constraints enforced
- [ ] Comprehensive testing implemented

---

## 🔟 Database Schema Overview

### Core Tables (25+ tables across 5 categories):

#### 1. Core Coin Management
- `coins` - Main coin inventory
- `coin_images` - Coin image storage
- `listings` - Marketplace listings
- `orders` - Order tracking
- `spot_prices` - Silver price data
- `audit_log` - System audit trail

#### 2. AI Pricing System
- `market_prices` - Market pricing data
- `pricing_config` - Pricing configuration
- `scam_detection_results` - AI scam detection
- `price_history` - Price change tracking

#### 3. Sales Management
- `sales_channels` - Sales channel configuration
- `sales` - Individual sales records
- `sales_forecasts` - Revenue forecasting
- `forecast_periods` - Forecast time periods
- `sales_metrics` - Sales performance metrics

#### 4. Inventory Management
- `locations` - Physical storage locations
- `inventory_items` - Inventory tracking
- `inventory_movements` - Movement history
- `dead_stock_analysis` - Slow-moving inventory
- `inventory_metrics` - Inventory performance
- `turnover_analysis` - Turnover rates

#### 5. Financial Management
- `financial_periods` - Financial reporting periods
- `cash_flow` - Cash flow tracking
- `pricing_strategies` - Dynamic pricing
- `pricing_updates` - Price change history
- `financial_metrics` - Financial performance
- `expense_categories` - Expense classification
- `expenses` - Expense tracking

#### 6. Alert & Integration System
- `alert_rules` - Alert configuration
- `alerts` - Generated alerts
- `notification_templates` - Alert templates
- `notification_logs` - Notification history
- `shopify_integrations` - Shopify configuration
- `shopify_sync_logs` - Sync operation logs
- `shopify_products` - Shopify product mapping
- `shopify_orders` - Shopify order tracking
- `shopify_order_items` - Order item details

---

**Author:** Stream-Line AI  
**Project:** Miracle Coins — CoinSync Pro  
**Template Version:** v2.0  
**Date:** 2025-01-27
