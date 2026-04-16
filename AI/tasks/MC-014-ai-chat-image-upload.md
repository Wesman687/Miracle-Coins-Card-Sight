# 🪙 Miracle Coins — AI Task Template (Stream-Line AI Compatible)

## 0️⃣ Metadata
- **Task ID:** MC-014
- **Owner:** BuilderAgent
- **Date:** 2025-01-28
- **Repo / Branch:** miracle-coins / feature/ai-chat-image-upload
- **Environment:** Frontend (Next.js) + Backend (FastAPI)
- **Related Issues / PRs:** AI Chat Image Upload Enhancement

---

## 1️⃣ 🎯 Task Summary
> Add image upload functionality to AI chat system for coin identification and pricing analysis.

---

## 2️⃣ 🧭 Current Context
Summarize the **state of the system** relevant to this task.

- **System Overview:** FastAPI backend (port 13000) + Next.js admin dashboard (port 8100)
- **Database:** PostgreSQL (`miracle-coins`) on Stream-Line cluster  
- **Auth:** Shared JWT from `stream-lineai.com` → must check `user.isAdmin`
- **Storage:** File-Server SDK for image uploads (already integrated and working)
- **Integration Targets:** Shopify (phase 1), eBay (phase 2)
- **Other Services:** Redis + Celery for background syncs (spot price, bulk updates)

**Current State:**
- AI chat system exists and is working (MC-013 completed)
- File uploader system is integrated and production ready
- Need to add image upload to AI chat for coin identification
- Need image analysis capabilities for coin recognition

---

## 3️⃣ 🧩 Task Objective
Define *exactly* what needs to be done.

- **Goal:** Add image upload functionality to AI chat system for coin identification and analysis
- **Inputs:** Image files (JPG, PNG, WebP), existing file uploader system, AI analysis
- **Outputs:** Image-based coin identification, pricing suggestions, visual analysis
- **Dependencies:** MC-013 (AI Chat System), existing file uploader integration
- **Risks / Caveats:** Image processing performance, file size limits, image quality requirements

---

## 4️⃣ 🏗️ Implementation Plan
Lay out the **precise steps** for the AI Builder Agent.

1. Add image upload button to AI chat modal
2. Integrate with existing file uploader system
3. Add image preview and drag-and-drop functionality
4. Create image analysis service for coin identification
5. Update AI chat service to handle image-based queries
6. Add image-based search presets (Visual ID, Grade Assessment, etc.)
7. Implement image caching and optimization
8. Test image upload and analysis workflow
9. Add image history and favorites functionality

---

## 5️⃣ 🧪 Testing & Validation
Ensure every feature meets quality standards.

| Type | Example |
|------|----------|
| Unit | Verify image upload button renders and functions correctly |
| Integration | Test image upload with file uploader system |
| E2E | Complete workflow: upload image → AI analysis → pricing suggestion |
| Performance | Test image processing with various file sizes and formats |
| UX | Test drag-and-drop, image preview, and error handling |

---

## 6️⃣ 📌 Acceptance Criteria
Use measurable checkboxes for completion tracking.

- [ ] Image upload button added to AI chat modal
- [ ] Drag-and-drop functionality implemented
- [ ] Image preview and validation working
- [ ] Integration with existing file uploader system
- [ ] Image analysis service for coin identification
- [ ] Image-based search presets (Visual ID, Grade Assessment)
- [ ] Image caching and optimization
- [ ] Image history and favorites functionality
- [ ] Error handling for invalid images
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
- `frontend/components/ImageUpload.tsx` - Image upload component
- `frontend/components/ImagePreview.tsx` - Image preview component
- `backend/app/services/image_analysis_service.py` - Image analysis service
- `backend/app/routers/image_analysis.py` - Image analysis API endpoints
- Updated `frontend/components/AIChatModal.tsx` - Added image upload functionality
- Updated `backend/app/services/ai_chat_service.py` - Added image analysis support

---

## 9️⃣ 🧠 AI Notes / Memory Fields
> Each task should write to `/AI/memory/coinsync/` for recall and future context.

```json
{
  "feature": "ai_chat_image_upload",
  "components": [
    "ImageUpload",
    "ImagePreview", 
    "ImageAnalysis"
  ],
  "api_endpoints": [
    "/api/v1/ai-chat/upload-image",
    "/api/v1/ai-chat/analyze-image",
    "/api/v1/image-analysis/identify-coin",
    "/api/v1/image-analysis/grade-assessment"
  ],
  "permissions": ["admin-only"],
  "image_formats": ["jpg", "jpeg", "png", "webp"],
  "max_file_size": "10MB",
  "image_presets": [
    "visual_identification",
    "grade_assessment",
    "authenticity_check",
    "pricing_with_image"
  ],
  "ai_features": [
    "coin_identification",
    "grade_assessment",
    "authenticity_verification",
    "visual_analysis",
    "image_based_pricing"
  ],
  "status": "in_progress"
}
```

---

**Last Updated**: 2025-01-28  
**Version**: 1.0  
**Project**: Miracle Coins CoinSync Pro

