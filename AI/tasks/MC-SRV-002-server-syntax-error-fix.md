# MC-SRV-002: Server Syntax Error Fix

## Metadata
- **Task ID**: MC-SRV-002
- **Owner**: AI Assistant
- **Date**: 2025-01-29
- **Branch**: main
- **Dependencies**: None
- **Priority**: Critical

## Task Summary
Fix syntax error in `shopify_collections.py` that is preventing server startup and blocking Shopify import testing.

## Current Context
- **Server Status**: Cannot start due to syntax error
- **Error Location**: `backend/app/routers/shopify_collections.py` line 752
- **Error Type**: `SyntaxError: expected 'except' or 'finally' block`
- **Root Cause**: Indentation issues in product processing loop causing except block to not match try block
- **Impact**: Blocking all Shopify import testing and debugging

## Goals & Acceptance Criteria

### Primary Goal
Fix syntax error to allow server startup

### Acceptance Criteria
- [ ] Server starts successfully without syntax errors
- [ ] Python compilation passes (`python -m py_compile app/routers/shopify_collections.py`)
- [ ] Server runs on port 13000
- [ ] API endpoints accessible
- [ ] Ready for Shopify import testing

## Implementation Plan

### Phase 1: Diagnose Syntax Error
1. **Identify the exact issue**
   - Check line 752 and surrounding code
   - Verify try/except block structure
   - Identify indentation problems

2. **Analyze the code structure**
   - Review product processing loop (line 367+)
   - Check try block starts at line 368
   - Verify except block at line 752

### Phase 2: Fix Syntax Error
**Option A: Remove Problematic Except Block**
- Remove the duplicate except block at line 752
- Let existing error handling manage issues
- Simplest and safest approach

**Option B: Fix Indentation**
- Properly indent `imported_coins.append()` to be inside try block
- Ensure all code between try and except is properly indented
- More complex but preserves error handling

**Option C: Start Fresh**
- Revert to clean version of file
- Re-add debugging without syntax errors
- Most thorough but time-consuming

### Phase 3: Test Server Startup
1. **Verify syntax**
   - Run `python -m py_compile app/routers/shopify_collections.py`
   - Ensure no syntax errors

2. **Start server**
   - Run `python main.py`
   - Verify server starts on port 13000
   - Check API endpoints accessible

3. **Test basic functionality**
   - Verify collections API works
   - Test coins API endpoint
   - Confirm debugging is ready

## Testing Strategy

### Syntax Testing
- **Python Compilation**: `python -m py_compile app/routers/shopify_collections.py`
- **AST Parsing**: `python -c "import ast; ast.parse(open('app/routers/shopify_collections.py').read())"`

### Server Testing
- **Startup Test**: Server starts without errors
- **Port Test**: Server listens on port 13000
- **API Test**: Basic endpoints respond correctly

### Integration Testing
- **Collections API**: `/api/v1/collections` returns data
- **Coins API**: `/api/v1/coins` returns coin data
- **Shopify Import**: Ready for testing (not executed yet)

## Deliverables
- [ ] Fixed `shopify_collections.py` file
- [ ] Server running successfully
- [ ] API endpoints accessible
- [ ] Ready for Shopify import testing

## Review Criteria
- Server starts without syntax errors
- All API endpoints respond correctly
- Debugging logging is intact and ready
- No regression in existing functionality

## Memory Notes
- **State Update**: Server status changed from "running" to "syntax_error_blocking_startup"
- **Issue Added**: Critical syntax error blocking server startup
- **Context**: Debugging was added to GraphQL products import but introduced syntax error
- **Next Steps**: After fix, test Shopify import with debugging to identify products import failure

## DevOps Checklist
- [ ] Backup current file before changes
- [ ] Test syntax fix in isolation
- [ ] Verify server startup
- [ ] Test API endpoints
- [ ] Update memory with resolution
- [ ] Document solution in issues.json

## Risk Assessment
- **Low Risk**: Syntax fix is isolated to one file
- **Mitigation**: Backup file before changes
- **Rollback**: Revert to previous working version if needed

## Success Metrics
- Server startup time < 10 seconds
- All API endpoints return 200 status
- No syntax errors in Python compilation
- Ready for Shopify import testing

---

**Status**: In Progress  
**Last Updated**: 2025-01-29T23:30:00Z
