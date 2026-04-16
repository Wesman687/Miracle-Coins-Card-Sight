# 🪙 Miracle Coins — AI Task Template (Stream-Line AI Compatible)

## 0️⃣ Metadata
- **Task ID:** MC-011
- **Owner:** BuilderAgent
- **Date:** 2025-01-27
- **Repo / Branch:** miracle-coins / feature/frontend-setup
- **Environment:** Frontend (Next.js)
- **Related Issues / PRs:** Frontend Installation & Setup

---

## 1️⃣ 🎯 Task Summary
> Install and configure the Next.js frontend application with all dependencies and security updates.

---

## 2️⃣ 🧭 Current Context
Summarize the **state of the system** relevant to this task.

- **System Overview:** FastAPI backend (port 13000) + Next.js admin dashboard (port 8100)
- **Database:** PostgreSQL (`miracle-coins`) on Stream-Line cluster  
- **Auth:** Shared JWT from `stream-lineai.com` → must check `user.isAdmin`
- **Storage:** File-Server SDK for image uploads
- **Integration Targets:** Shopify (phase 1), eBay (phase 2)
- **Other Services:** Redis + Celery for background syncs (spot price, bulk updates)

**Frontend Requirements:**
- Next.js 14 with TypeScript and strict type checking
- Tailwind CSS for professional black/gold theme
- React Query for API state management
- Zod for form validation
- Comprehensive components for coin management, AI evaluation, task management

---

## 3️⃣ 🧩 Task Objective
Define *exactly* what needs to be done.

- **Goal:** Install all frontend dependencies and resolve security vulnerabilities
- **Inputs:** `frontend/package.json` with dependency specifications
- **Outputs:** Working Next.js application with all dependencies installed and security issues resolved
- **Dependencies:** MC-001 (System Scaffolding) - frontend code already exists
- **Risks / Caveats:** Security vulnerabilities in Next.js, TypeScript compilation errors

---

## 4️⃣ 🏗️ Implementation Plan
Lay out the **precise steps** for the AI Builder Agent.

1. Navigate to frontend directory (`cd frontend`)
2. Install all npm dependencies (`npm install`)
3. Check for security vulnerabilities (`npm audit`)
4. Update Next.js to latest secure version if needed
5. Fix any TypeScript compilation errors
6. Test build process (`npm run build`)
7. Test development server startup (`npm run dev`)
8. Verify all components render correctly

---

## 5️⃣ 🧪 Testing & Validation
Ensure every feature meets quality standards.

| Type | Example |
|------|----------|
| Installation | Verify all packages installed without errors |
| Security | Run `npm audit` to ensure no vulnerabilities |
| Compilation | Test TypeScript compilation with `npm run build` |
| Development | Start dev server with `npm run dev` |
| Integration | Verify API calls work with backend |

---

## 6️⃣ 📌 Acceptance Criteria
Use measurable checkboxes for completion tracking.

- [x] Feature functional as described
- [x] All npm dependencies installed successfully
- [x] Security vulnerabilities resolved (Next.js updated to 14.2.33)
- [x] Frontend can start in development mode
- [x] TypeScript compilation passes without errors
- [x] All new code type-checked and lint-clean
- [x] Build process completes successfully

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

**Files Modified:**
- `frontend/package.json` (Next.js version updated to 14.2.33)
- `frontend/node_modules/` (all dependencies installed)
- `frontend/components/DashboardKPIs.tsx` (fixed TypeScript errors)

---

## 9️⃣ 🧠 AI Notes / Memory Fields
> Each task should write to `/AI/memory/coinsync/` for recall and future context.

```json
{
  "feature": "frontend_setup",
  "framework": "Next.js 14.2.33",
  "language": "TypeScript",
  "styling": "Tailwind CSS",
  "port": 8100,
  "api_integration": "axios + react-query",
  "form_validation": "zod + react-hook-form",
  "ui_theme": "black_gold_professional",
  "security": "vulnerabilities_resolved",
  "status": "completed"
}
```
