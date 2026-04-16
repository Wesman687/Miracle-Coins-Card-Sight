# 🪙 Miracle Coins — AI Task Template

> Standardized template for AI-generated development tasks in the Miracle Coins CoinSync Pro project.
> Each task should be self-contained, well-defined, and follow our project conventions.

---

## 0️⃣ Metadata
| Field | Value |
|-------|-------|
| **Task ID** | MC-XXX (e.g., MC-001, MC-002) |
| **Owner / Agent** | BuilderAgent / ArchitectAgent / ReviewerAgent |
| **Date** | YYYY-MM-DD |
| **Branch / Repo** | miracle-coins / feature/task-name |
| **Dependencies** | List of prerequisite tasks |
| **Related Issues** | GitHub issues or PRs |
| **Priority** | High / Medium / Low |

---

## 1️⃣ 🎯 Task Summary
> One-sentence description of what this task accomplishes.

**Example:**  
> "Implement Stream-Line JWT authentication integration to replace mock authentication with real user verification."

---

## 2️⃣ 🧩 Current Context
Describe the current state of the system relevant to this task.

**Current State:**
- What exists now
- What's working/not working
- Why this task is needed

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
- [ ] Specific, measurable objective 1
- [ ] Specific, measurable objective 2
- [ ] Specific, measurable objective 3

### Acceptance Criteria
- [ ] Feature works as described
- [ ] Passes TypeScript type checks and linting
- [ ] All tests pass (unit, integration, e2e)
- [ ] Documentation updated
- [ ] Code follows project conventions
- [ ] Performance requirements met

---

## 4️⃣ 🏗️ Implementation Plan
Step-by-step approach for implementing this task.

1. **Analysis Phase**
   - Review existing code and architecture
   - Identify files that need modification
   - Plan data flow and API changes

2. **Backend Implementation**
   - Update/create models in `app/models.py`
   - Implement business logic in `app/services/`
   - Create/update API endpoints in `app/routers/`
   - Add proper error handling and logging

3. **Frontend Implementation**
   - Create/update components in `components/`
   - Update API calls in `lib/api.ts`
   - Add proper TypeScript types
   - Implement error handling and loading states

4. **Testing & Validation**
   - Write unit tests for business logic
   - Add integration tests for API endpoints
   - Test frontend components
   - Verify end-to-end functionality

---

## 5️⃣ 🧪 Testing Strategy

| Type | Description | Test Cases |
|------|-------------|------------|
| **Unit** | Individual functions/components | Input validation, edge cases, error handling |
| **Integration** | API endpoints and database | CRUD operations, authentication, data flow |
| **End-to-End** | Complete user workflows | User journeys, cross-component interactions |
| **Performance** | System performance | Response times, memory usage, scalability |

### Test Data Requirements
- Sample data for testing
- Mock responses for external APIs
- Test user accounts and permissions

---

## 6️⃣ 📂 Deliverables
Specific files and artifacts that will be created or modified.

### Backend Files
- `app/models/` - Database models (including collections.py, pricing_models.py)
- `app/routers/` - API endpoints (including collections.py, pricing_agent.py)
- `app/services/` - Business logic (collection_service.py, spot_price_service, scam_detection_service, pricing_engine_service, shopify_pricing_service)
- `app/schemas/` - Pydantic schemas (including collections.py, pricing_schemas.py)
- `app/tasks/` - Celery background tasks (pricing_tasks.py)
- `tests/` - Test files

### Frontend Files
- `components/` - React components
- `pages/` - Next.js pages
- `lib/` - API client and utilities
- `types/` - TypeScript type definitions
- `__tests__/` - Frontend tests

### Configuration Files
- Database migrations (including pricing agent schema)
- Environment variables (GoldAPI key, Shopify credentials)
- Documentation updates
- Shopify API scopes configuration

---

## 7️⃣ 🔄 Review Criteria
Quality standards that must be met before task completion.

### Code Quality
- [ ] TypeScript types properly defined
- [ ] Error handling comprehensive
- [ ] Code follows established patterns
- [ ] Proper logging and monitoring
- [ ] Security best practices implemented

### Functionality
- [ ] Feature works as specified
- [ ] Edge cases handled properly
- [ ] Performance requirements met
- [ ] User experience is smooth
- [ ] Integration points work correctly

### Testing
- [ ] Unit test coverage > 80%
- [ ] Integration tests cover API endpoints
- [ ] End-to-end tests cover user workflows
- [ ] All tests pass consistently
- [ ] Test data is realistic and comprehensive

---

## 8️⃣ 🧠 Memory Notes (for AI Memory Bank)
Key information to store for future reference and context.

```json
{
  "feature": "feature_name",
  "implementation": {
    "backend": "files_modified",
    "frontend": "components_created",
    "database": "tables_affected"
  },
  "apis": {
    "endpoints": ["/api/v1/endpoint1", "/api/v1/endpoint2"],
    "methods": ["GET", "POST", "PUT", "DELETE"]
  },
  "dependencies": ["external_service", "internal_module"],
  "status": "completed|in_progress|pending"
}
```

### Key Implementation Notes
- Important technical decisions made
- Patterns established for future use
- Integration points with other systems
- Performance considerations
- Security implications
- Clear Seperation of Concerns, Avoid Large parges where yo ucan.
- When seperating large pages, use consitent folder structure  components/admin/(ALL Admin folders here)
- Document in memory and in corresponding task, folder structure.  

### Reusable Patterns
- Code patterns that can be reused
- Component structures for similar features
- API design patterns
- Error handling approaches

---

## 9️⃣ 🪪 Cursor Rules / DevOps Checklist
Development and deployment requirements.

- [ ] All code follows TypeScript/Python type hints
- [ ] Use versioned API endpoints (`/api/v1/...`)
- [ ] Commit messages follow conventional format
- [ ] Keep pull requests atomic and focused
- [ ] Log important events using structured logging
- [ ] Run tests before merging
- [ ] Update API documentation
- [ ] Ensure environment variables are properly configured
- [ ] Validate database migrations work correctly
- [ ] Test with real data in staging environment

---

**Author:** Stream-Line AI  
**Project:** Miracle Coins — CoinSync Pro  
**Template Version:** v2.0  
**Date:** 2025-01-27