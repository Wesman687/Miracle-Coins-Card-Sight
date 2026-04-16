# MC-API-001: Collections API Debug and Fix

## Metadata
- **ID**: MC-API-001
- **Owner**: AI Assistant
- **Date**: 2025-01-28
- **Branch**: main
- **Dependencies**: None

## Task Summary
Debug and fix the collections API endpoints that are returning 422 and 500 errors, ensuring both `/api/v1/collections` and `/api/v1/collections/stats` work correctly.

## Current Context
- Collections API endpoints are returning 422 Unprocessable Content and 500 Internal Server Error
- Database has collections table with 5 collections
- Model and schema have been updated to match database schema
- Collections router is included in main.py
- Service layer has been updated to handle missing columns

## Goals & Acceptance Criteria
- [ ] `/api/v1/collections` endpoint returns 200 OK with collection data
- [ ] `/api/v1/collections/stats` endpoint returns 200 OK with statistics
- [ ] Both endpoints work with mock-token authentication
- [ ] Response validation passes without errors
- [ ] All collection data is properly serialized

## Implementation Plan
1. **Deep Debug Collections Endpoint (422 Error)**
   - Check response validation errors in detail
   - Verify CollectionResponse schema matches actual data
   - Test schema conversion from model to response
   - Fix any field mismatches

2. **Deep Debug Collections Stats Endpoint (500 Error)**
   - Check for database query errors
   - Verify Coin model import is working
   - Test collection stats service method
   - Fix any relationship or query issues

3. **Test Both Endpoints**
   - Verify both endpoints return 200 OK
   - Confirm response data is valid JSON
   - Test with different parameters

## Testing Strategy
- Test collections service directly
- Test schema conversion
- Test API endpoints with curl/PowerShell
- Verify response validation passes

## Deliverables
- Working collections API endpoints
- Fixed response validation
- Test results confirming functionality

## Review Criteria
- Both endpoints return 200 OK
- Response data is properly formatted
- No validation errors in logs
- Authentication works correctly

## Memory Notes
- Collections system uses collections-only approach (no categories)
- Database has 5 collections with proper schema
- Authentication uses mock-token for development

## DevOps Checklist
- [ ] Server starts without errors
- [ ] Database connection works
- [ ] Collections router loads correctly
- [ ] Service layer functions properly
- [ ] Response validation passes
