# MC-IMP-001: Fix Metafields Processing and Duplicate Prevention

## Metadata
- **Task ID**: MC-IMP-001
- **Owner**: AI Assistant
- **Date**: 2025-01-30
- **Branch**: master
- **Dependencies**: MC-SRV-002 (completed)

## Task Summary
Fix critical issues with Shopify import: metafields are imported but not processed into the correct format, and duplicate coins are being created despite duplicate prevention logic.

## Current Context
- ✅ Server is running successfully on port 13000
- ✅ Shopify GraphQL query is working and returning metafields
- ✅ Raw metafields are being stored in `shopify_metadata.metafields`
- ❌ Metafields are NOT being processed into `product_metafields` and `category_metafields`
- ❌ Duplicate coins are being created (78 products imported, only 50 coins in database)
- ❌ Frontend cannot display coin details because metafields are in wrong format

## Goals & Acceptance Criteria

### Primary Goals
1. **Fix Metafields Processing**: Ensure metafields are processed from raw format to `product_metafields`/`category_metafields`
2. **Fix Duplicate Prevention**: Prevent duplicate coins during import
3. **Verify Frontend Display**: Confirm coin details show in edit modal

### Acceptance Criteria
- [ ] Metafields processing code executes during import
- [ ] `product_metafields` and `category_metafields` are populated
- [ ] No duplicate coins created during import
- [ ] Frontend displays coin details (year, silver content, condition, etc.)
- [ ] All 78 products imported as unique coins

## Implementation Plan

### Phase 1: Debug Metafields Processing
1. **Identify why processing code isn't executing**
   - Check if metafields processing is in correct location
   - Verify no exceptions are being caught silently
   - Add debug logging to trace execution

2. **Fix metafields processing execution**
   - Ensure processing happens after GraphQL response
   - Fix any indentation or syntax issues
   - Test with single product import

### Phase 2: Fix Duplicate Prevention
1. **Debug duplicate check logic**
   - Verify `shopify_id` comparison is working
   - Check if existing coin query is correct
   - Test duplicate prevention with known duplicates

2. **Implement proper duplicate handling**
   - Ensure UPDATE logic works for existing coins
   - Test with fresh import

### Phase 3: End-to-End Testing
1. **Clear existing data**
2. **Run fresh import**
3. **Verify metafields are processed**
4. **Verify no duplicates**
5. **Test frontend display**

## Testing Strategy

### Unit Tests
- Test metafields processing logic with sample data
- Test duplicate check logic with known scenarios

### Integration Tests
- Test complete import flow
- Verify database state after import
- Test frontend coin details display

### Manual Testing
- Clear database and run fresh import
- Check coin details in edit modal
- Verify all 78 products imported as unique coins

## Deliverables
- [ ] Fixed metafields processing in import function
- [ ] Fixed duplicate prevention logic
- [ ] Working coin details display in frontend
- [ ] Clean import with no duplicates
- [ ] Updated memory with resolution details

## Review Criteria
- All metafields are processed and displayed
- No duplicate coins in database
- Frontend shows complete coin details
- Import completes successfully with all products

## Memory Notes
- Metafields are being imported correctly from Shopify
- Processing code exists but isn't executing
- Duplicate prevention logic exists but isn't working
- Root cause: execution flow issues in import function

## DevOps Checklist
- [ ] Test on development environment
- [ ] Verify no breaking changes
- [ ] Update memory files
- [ ] Document solution in task log

