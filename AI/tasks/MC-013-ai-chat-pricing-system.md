# 🪙 Miracle Coins — AI Task Template (Stream-Line AI Compatible)

## 0️⃣ Metadata
- **Task ID:** MC-013
- **Owner:** BuilderAgent
- **Date:** 2025-01-28
- **Repo / Branch:** miracle-coins / feature/ai-chat-pricing-system
- **Environment:** Frontend (Next.js) + Backend (FastAPI)
- **Related Issues / PRs:** AI Chat Pricing System Implementation

---

## 1️⃣ 🎯 Task Summary
> Implement comprehensive AI chat system for quick coin pricing searches with preset search types, caching system, and improved AI evaluation capabilities.

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
- AI evaluation system exists (MC-012 completed)
- Basic AI evaluation button component implemented
- Pricing dashboard with AI suggestions working
- Need comprehensive chat interface for quick searches
- Need preset search types for different scenarios
- Need caching system for frequently searched coins

---

## 3️⃣ 🧩 Task Objective
Define *exactly* what needs to be done.

- **Goal:** Create AI chat system for quick coin pricing searches with presets and caching
- **Inputs:** Coin descriptions, search presets, cached data, AI evaluation API
- **Outputs:** Quick pricing responses, detailed analysis, cached results, preset suggestions
- **Dependencies:** MC-012 (AI Evaluation System), existing AI services
- **Risks / Caveats:** AI API response times, cache invalidation, real-time pricing accuracy

---

## 4️⃣ 🏗️ Implementation Plan
Lay out the **precise steps** for the AI Builder Agent.

1. Create AI chat modal component with preset search types
2. Implement caching system for frequently searched coins
3. Add preset search types (Quick, In-Depth, Descriptions, Year/Mintage, Pricing)
4. Create backend API endpoints for chat-based searches
5. Integrate with existing AI evaluation system
6. Add AI chat button to main dashboard
7. Implement real-time chat interface with typing indicators
8. Add search history and favorites functionality
9. Test all search presets and caching functionality

---

## 5️⃣ 🧪 Testing & Validation
Ensure every feature meets quality standards.

| Type | Example |
|------|----------|
| Unit | Verify AI chat modal renders and preset buttons work |
| Integration | Test AI chat API calls with different preset types |
| E2E | Complete workflow: open chat → select preset → get pricing → apply suggestion |
| Performance | Test caching system with repeated searches |
| UX | Test chat interface responsiveness and user experience |

---

## 6️⃣ 📌 Acceptance Criteria
Use measurable checkboxes for completion tracking.

- [ ] AI chat modal component created with professional UI
- [ ] Preset search types implemented (Quick, In-Depth, Descriptions, Year/Mintage, Pricing)
- [ ] Caching system for frequently searched coins
- [ ] Backend API endpoints for chat-based searches
- [ ] Integration with existing AI evaluation system
- [ ] AI chat button added to main dashboard
- [ ] Real-time chat interface with typing indicators
- [ ] Search history and favorites functionality
- [ ] All search presets tested and working
- [ ] Professional UI/UX with black/gold theme maintained

---

## 7️⃣ 🧱 Project Conventions
Follow these project rules:

- **Architecture:** Modular FastAPI with Pydantic models and clear separation of concerns.  
- **Frontend:** Next.js + TypeScript + React Query.  
- **Database:** PostgreSQL via SQLAlchemy.  
- **File Handling:** File-Server SDK (auto-square images).  
- **Naming:** Use snake_case for Python, camelCase for TypeScript.  
- **Versioning:** `/api/v1/...` endpoints only.  
- **Auth Check:** Always confirm `user.isAdmin`.  
- **Error Handling:** JSON response `{ "error": "message" }`, HTTP 400–500 codes.  
- **Background Jobs:** Celery tasks should log status and completion.  

---

## 8️⃣ 💾 Deliverables
- [ ] Backend modules (models, routes, services)
- [ ] Frontend components / hooks
- [ ] Database migration scripts
- [ ] Tests
- [ ] Documentation in `/docs/`
- [ ] Entry in `/AI/memory/state.json`

**Files Created:**
- `frontend/components/AIChatModal.tsx` - Main AI chat interface
- `frontend/components/SearchPresets.tsx` - Preset search type buttons
- `frontend/components/SearchHistory.tsx` - Search history and favorites
- `frontend/hooks/useAIChat.ts` - AI chat functionality hook
- `backend/app/routers/ai_chat.py` - AI chat API endpoints
- `backend/app/services/ai_chat_service.py` - AI chat business logic
- `backend/app/services/search_cache_service.py` - Caching system
- Updated `frontend/pages/index.tsx` - Added AI chat button

---

## 9️⃣ 🧠 AI Notes / Memory Fields
> Each task should write to `/AI/memory/coinsync/` for recall and future context.

```json
{
  "feature": "ai_chat_pricing_system",
  "components": [
    "AIChatModal",
    "SearchPresets", 
    "SearchHistory"
  ],
  "api_endpoints": [
    "/api/v1/ai-chat/search",
    "/api/v1/ai-chat/presets",
    "/api/v1/ai-chat/history",
    "/api/v1/ai-chat/cache"
  ],
  "permissions": ["admin-only"],
  "search_presets": [
    "quick_response",
    "in_depth_analysis", 
    "descriptions",
    "year_mintage",
    "pricing_only"
  ],
  "caching": {
    "enabled": true,
    "ttl": 3600,
    "max_entries": 1000
  },
  "ai_features": [
    "quick_pricing",
    "detailed_analysis",
    "scam_detection",
    "market_analysis",
    "confidence_scoring"
  ],
  "status": "in_progress"
}
```

---

## 🔟 🚀 DevOps Checklist
- [ ] Database migrations tested
- [ ] API endpoints documented
- [ ] Frontend components tested
- [ ] Integration tests passing
- [ ] Performance benchmarks met
- [ ] Security review completed
- [ ] Documentation updated
- [ ] Memory system updated

---

**Last Updated**: 2025-01-28  
**Version**: 1.0  
**Project**: Miracle Coins CoinSync Pro

