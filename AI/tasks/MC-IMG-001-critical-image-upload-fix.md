# MC-IMG-001: Critical Image Upload Fix

## Task Metadata
- **Task ID**: MC-IMG-001
- **Priority**: Critical
- **Status**: In Progress
- **Assigned To**: AI Assistant
- **Created**: 2025-01-28
- **Updated**: 2025-01-28
- **Estimated Time**: 1 hour
- **Actual Time**: TBD

## Context
**CRITICAL ISSUE**: User reported that adding pictures to coins is not working. The frontend is calling `/api/v1/images/upload?coin_id=new` which returns 404. This is blocking the core functionality of adding images to coins.

## Root Cause Analysis
The issue is that there are two different image upload systems:
1. **Old system**: `/api/v1/images/upload` (stub endpoint that returns "not implemented yet")
2. **New system**: `/api/v1/files/upload/image` (properly implemented with Stream-Line file uploader)

The frontend `AddCoinModal.tsx` was still using the old endpoint, causing the 404 error.

## Objective
Fix the image upload functionality so users can successfully add pictures to coins in the inventory system.

## Core Responsibilities
1. **Frontend Fix**: Update AddCoinModal to use correct file upload endpoint
2. **Backend Fix**: Update images router to redirect to file uploader for backward compatibility
3. **Testing**: Verify image upload works end-to-end
4. **Documentation**: Update memory with fix status

## Implementation Plan

### Phase 1: Frontend Fix ✅ COMPLETED
- [x] Update `AddCoinModal.tsx` to use `/files/upload/image` endpoint
- [x] Add proper form data with collection and sku parameters
- [x] Handle response format from file uploader service
- [x] Add proper error handling

### Phase 2: Backend Fix ✅ COMPLETED
- [x] Update `images.py` router to redirect to file uploader
- [x] Maintain backward compatibility for existing calls
- [x] Add proper error handling and authentication
- [x] Use FileUploadService for actual upload functionality

### Phase 3: Testing 🔄 IN PROGRESS
- [ ] Test image upload from frontend
- [ ] Verify images are stored correctly
- [ ] Test coin creation with images
- [ ] Verify signed URL generation

### Phase 4: Documentation
- [ ] Update memory with fix status
- [ ] Update task status to completed
- [ ] Document any remaining issues

## Technical Details

### Frontend Changes
```typescript
// OLD (broken)
const response = await api.post(`/images/upload?coin_id=${coin?.id || 'new'}`, formData)

// NEW (working)
const response = await api.post('/files/upload/image', formData, {
  headers: { 'Content-Type': 'multipart/form-data' }
})
```

### Backend Changes
```python
# OLD (stub)
@router.post("/upload")
async def upload_image():
    return {"message": "Upload image endpoint - not implemented yet"}

# NEW (working)
@router.post("/upload")
async def upload_image(file: UploadFile = File(...), ...):
    # Redirects to FileUploadService
    result = await service.upload_coin_image(...)
    return {"success": True, "data": result, ...}
```

## Testing Strategy
1. **Unit Tests**: Verify endpoint responses
2. **Integration Tests**: Test file upload workflow
3. **End-to-End Tests**: Test complete coin creation with images
4. **User Acceptance**: Verify user can add images to coins

## Deliverables
1. ✅ Fixed frontend image upload functionality
2. ✅ Fixed backend image upload endpoint
3. 🔄 Working image upload system
4. 🔄 Updated documentation

## Review Criteria
- [ ] Image upload works from frontend
- [ ] Images are stored in correct folder structure
- [ ] Coin creation with images works
- [ ] No 404 errors on image upload
- [ ] Proper error handling and user feedback

## Memory Notes
- **CRITICAL**: Image upload was completely broken due to endpoint mismatch
- Frontend was calling non-existent `/images/upload` endpoint
- File uploader system was properly implemented but not connected
- Both frontend and backend fixes required for full functionality

## Dependencies
- Stream-Line file uploader service (working)
- File upload service configuration (working)
- Database coin_images table (pending - MC-DB-001)

## Risks
- **HIGH**: User cannot add images to coins (blocking core functionality)
- File uploader service configuration issues
- Database table missing for image metadata storage

## Success Metrics
- ✅ No more 404 errors on image upload
- 🔄 Images successfully uploaded and stored
- 🔄 Coin creation with images works end-to-end
- 🔄 User can add pictures to coins in inventory

## Related Tasks
- MC-DB-001: Create coin_images table (required for full functionality)
- MC-FILE-002: File uploader modal integration (completed)
