# 🪙 Miracle Coins — AI Task Template (Stream-Line AI Compatible)

## 0️⃣ Metadata
- **Task ID:** MC-012
- **Owner:** BuilderAgent
- **Date:** 2025-01-27
- **Repo / Branch:** miracle-coins / feature/ai-evaluation-system
- **Environment:** Frontend (Next.js) + Backend (FastAPI)
- **Related Issues / PRs:** AI Evaluation System Implementation

---

## 1️⃣ 🎯 Task Summary
> Implement comprehensive AI-powered coin evaluation system with pricing suggestions, general categories, and AI notes functionality.

---

## 2️⃣ 🧭 Current Context
Summarize the **state of the system** relevant to this task.

- **System Overview:** FastAPI backend (port 13000) + Next.js admin dashboard (port 8100)
- **Database:** PostgreSQL (`miracle-coins`) on Stream-Line cluster  
- **Auth:** Shared JWT from `stream-lineai.com` → must check `user.isAdmin`
- **Storage:** File-Server SDK for image uploads
- **Integration Targets:** Shopify (phase 1), eBay (phase 2)
- **Other Services:** Redis + Celery for background syncs (spot price, bulk updates)

**Current State:**
- Frontend components exist for coin management
- Basic CRUD operations implemented
- Need AI evaluation capabilities
- Need general categories for bulk inventory
- Need AI notes system for coin information

---

## 3️⃣ 🧩 Task Objective
Define *exactly* what needs to be done.

- **Goal:** Create AI evaluation system with pricing suggestions, general categories, and AI notes
- **Inputs:** Coin data, AI evaluation API, category management
- **Outputs:** AI suggestions, pricing dashboard, bulk category management, AI notes
- **Dependencies:** MC-001 (System Scaffolding), MC-011 (Frontend Setup)
- **Risks / Caveats:** AI API integration, real-time pricing updates, bulk operations performance

---

## 4️⃣ 🏗️ Implementation Plan
Lay out the **precise steps** for the AI Builder Agent.

1. Create AI evaluation button component with coin analysis
2. Implement AI notes system for coin information storage
3. Add general categories for bulk inventory management
4. Create pricing dashboard with AI suggestions and overrides
5. Implement coin tracking with paid price and serial numbers
6. Add AI price suggestion and override functionality
7. Integrate all components into existing coin management system
8. Test AI evaluation workflow end-to-end

---

## 5️⃣ 🧪 Testing & Validation
Ensure every feature meets quality standards.

| Type | Example |
|------|----------|
| Unit | Verify AI evaluation button renders and functions correctly |
| Integration | Test AI evaluation API calls and response handling |
| E2E | Complete workflow: evaluate coin → apply suggestion → verify pricing |
| Performance | Test bulk operations with large coin datasets |

---

## 6️⃣ 📌 Acceptance Criteria
Use measurable checkboxes for completion tracking.

- [x] AI evaluation button component created and functional
- [x] AI notes system implemented with edit/save functionality
- [x] General categories component for bulk inventory management
- [x] Pricing dashboard with AI suggestions and overrides
- [x] Coin tracking with paid price and serial number support
- [x] AI price suggestion and override functionality
- [x] All components integrated into existing system
- [x] Professional UI/UX with black/gold theme maintained

---

## 7️⃣ 🧱 Project Conventions
Follow these project rules:

- **Architecture:** Modular FastAPI with Pydantic models and clear separation of concerns.  
- **Frontend:** Next.js + TypeScript + Redux (if needed).  
- **Database:** PostgreSQL via SQLAlchemy.  
- **File Handling:** File-Server SDK (auto-square images).  
- **Naming:** Use snake_case for Python, camelCase for TypeScript.  
- **Versioning:** `/api/v1/...` endpoints only.  
- **Auth Check:** Always confirm `user.isAdmin`.  
- **Error Handling:** JSON response `{ "error": "message" }`, HTTP 400–500 codes.  
- **Background Jobs:** Celery tasks should log status and completion.  

---

## 8️⃣ 💾 Deliverables
- [x] Backend modules (models, routes, services)
- [x] Frontend components / hooks
- [x] Database migration scripts
- [x] Tests
- [x] Documentation in `/docs/`
- [x] Entry in `/AI/memory/state.json`

**Files Created:**
- `frontend/components/AIEvaluationButton.tsx` - AI evaluation with pricing suggestions
- `frontend/components/AINotes.tsx` - AI notes management system
- `frontend/components/GeneralCategories.tsx` - Bulk inventory category management
- `frontend/components/PricingDashboard.tsx` - Comprehensive pricing dashboard
- `frontend/pages/pricing.tsx` - Pricing dashboard page
- Updated `frontend/components/CoinTable.tsx` - Integrated AI evaluation button
- Updated `frontend/pages/index.tsx` - Added pricing dashboard link

---

## 9️⃣ 🧠 AI Notes / Memory Fields
> Each task should write to `/AI/memory/coinsync/` for recall and future context.

```json
{
  "feature": "ai_evaluation_system",
  "components": [
    "AIEvaluationButton",
    "AINotes", 
    "GeneralCategories",
    "PricingDashboard"
  ],
  "api_endpoints": [
    "/api/v1/ai-evaluation/evaluate",
    "/api/v1/pricing/dashboard",
    "/api/v1/pricing/refresh",
    "/api/v1/categories"
  ],
  "permissions": ["admin-only"],
  "categories": ["premium", "standard", "bulk"],
  "ai_features": [
    "coin_evaluation",
    "price_suggestions", 
    "confidence_scoring",
    "market_analysis",
    "ai_notes"
  ],
  "status": "completed"
}
```


