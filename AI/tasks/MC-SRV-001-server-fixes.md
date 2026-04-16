# 🪙 Miracle Coins — AI Task Template

## 0️⃣ Metadata
| Field | Value |
|-------|-------|
| **Task ID** | MC-SRV-001 |
| **Owner / Agent** | DebugAgent |
| **Date** | 2025-01-27 |
| **Branch / Repo** | miracle-coins / feature/server-fixes |
| **Dependencies** | MC-SHP-001 (Shopify Integration) |
| **Related Issues** | Server startup failures, import errors |
| **Priority** | High |

---

## 1️⃣ 🎯 Task Summary
> Fix remaining server startup issues including duplicate table definitions, async context manager errors, and missing model imports to get the FastAPI server running properly.

---

## 2️⃣ 🧩 Current Context

**Current State:**
- Shopify integration is fully operational (10 products, create/update working)
- Pricing agent endpoints are functional
- Core services working with fallback data
- Server fails to start due to import and configuration issues

**System Overview:**
- Backend: FastAPI (port 13000) with PostgreSQL database
- Frontend: Next.js (port 8100) with TypeScript and Tailwind CSS
- Authentication: Mock JWT (needs real Stream-Line integration)
- Database: PostgreSQL with SQLAlchemy models
- Background Tasks: Celery with Redis for async operations
- AI Pricing Agent: Live silver price integration (GoldAPI), scam detection, Shopify sync
- Shopify Integration: Product creation, price updates, order tracking (miracle-coins.com)

**Issues Identified:**
1. Duplicate table definitions in models
2. Async context manager errors in services
3. Missing model imports in routers
4. Pydantic validation errors

---

## 3️⃣ 🧠 Goal & Acceptance Criteria

### Primary Goals
- [ ] Fix duplicate table definitions in SQLAlchemy models
- [ ] Resolve async context manager errors in services
- [ ] Fix missing model imports and dependencies
- [ ] Get FastAPI server starting successfully
- [ ] All API endpoints accessible and functional

### Acceptance Criteria
- [ ] Server starts without errors
- [ ] All routers import successfully
- [ ] Database models load without conflicts
- [ ] API endpoints respond correctly
- [ ] No import or configuration errors

---

## 4️⃣ 🏗️ Implementation Plan

1. **Analysis Phase**
   - Review error messages and identify root causes
   - Check for duplicate table definitions
   - Analyze async/await patterns in services

2. **Backend Fixes**
   - Fix duplicate table definitions with `extend_existing=True`
   - Resolve async context manager issues
   - Fix missing imports and dependencies
   - Update model relationships

3. **Testing & Validation**
   - Test server startup
   - Verify all endpoints work
   - Test database connections
   - Validate API responses

---

## 5️⃣ 🧪 Testing Strategy

| Type | Description | Test Cases |
|------|-------------|------------|
| **Unit** | Individual model imports | Model loading, table definitions |
| **Integration** | Server startup and endpoints | API responses, database connections |
| **End-to-End** | Complete server functionality | Full request/response cycles |

---

## 6️⃣ 📂 Deliverables

### Backend Files
- `app/models/` - Fixed duplicate table definitions
- `app/services/` - Resolved async context issues
- `app/routers/` - Fixed import dependencies
- `app/database.py` - Database configuration
- `app/auth.py` - Authentication module

### Configuration Files
- `.env` - Environment variables
- Database migrations
- Server startup scripts

---

## 7️⃣ 🔄 Review Criteria

### Code Quality
- [ ] No import errors
- [ ] No duplicate table definitions
- [ ] Proper async/await patterns
- [ ] Clean error handling

### Functionality
- [ ] Server starts successfully
- [ ] All endpoints accessible
- [ ] Database connections work
- [ ] API responses correct

---

## 8️⃣ 🧠 Memory Notes (for AI Memory Bank)

```json
{
  "feature": "server_startup_fixes",
  "implementation": {
    "backend": "models, services, routers, database, auth",
    "frontend": "none",
    "database": "table_definitions, imports"
  },
  "apis": {
    "endpoints": ["all existing endpoints"],
    "methods": ["GET", "POST", "PUT", "DELETE"]
  },
  "dependencies": ["sqlalchemy", "fastapi", "async_context_managers"],
  "status": "in_progress"
}
```

### Key Implementation Notes
- Fixed SQLAlchemy Decimal imports
- Created missing database and auth modules
- Resolved async context manager patterns
- Updated model table definitions

---

## 9️⃣ 🪪 Cursor Rules / DevOps Checklist

- [ ] All code follows TypeScript/Python type hints
- [ ] Use versioned API endpoints (`/api/v1/...`)
- [ ] Commit messages follow conventional format
- [ ] Keep pull requests atomic and focused
- [ ] Log important events using structured logging
- [ ] Run tests before merging
- [ ] Update API documentation
- [ ] Ensure environment variables are properly configured
- [ ] Validate database migrations work correctly

---

**Author:** Stream-Line AI  
**Project:** Miracle Coins — CoinSync Pro  
**Template Version:** v2.0  
**Date:** 2025-01-27
