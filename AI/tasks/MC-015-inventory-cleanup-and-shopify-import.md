# MC-015: Inventory Cleanup and Shopify Import

## Task Metadata
- **ID**: MC-015
- **Owner**: AI Assistant
- **Date**: 2025-01-28
- **Branch**: main
- **Dependencies**: MC-012 (AI evaluation system), MC-013 (AI chat system)
- **Priority**: High

## Task Summary
Delete all fake inventory data from the database and import real inventory from Shopify store to replace it.

## Current Context
- **Database**: PostgreSQL with 15 tables created
- **Current State**: Database contains fake/test data for coins
- **Shopify Integration**: Already configured (domain: b99ycv-3e.myshopify.com)
- **Collections**: Already imported from Shopify (10 real collections)
- **Decision**: "shopify-complete-integration" is approved for products, orders, inventory, pricing sync

## Goals & Acceptance Criteria

### Primary Goals
1. **Delete All Fake Data**: Remove all existing fake coins from the database
2. **Import Real Inventory**: Pull all products from Shopify store and convert to coins
3. **Maintain Data Integrity**: Ensure collections and other data remain intact
4. **Preserve System Functionality**: Keep all existing features working

### Acceptance Criteria
- [ ] All fake coins deleted from database
- [ ] All Shopify products imported as coins
- [ ] Collections remain intact and linked properly
- [ ] SKU generation works for imported products
- [ ] Pricing strategies applied correctly
- [ ] Images imported and linked properly
- [ ] System remains functional after import

## Implementation Plan

### Phase 1: Delete Fake Data
1. **Create Delete All Endpoint**
   - Add `DELETE /api/v1/coins/clear` endpoint
   - Delete all coins from database
   - Preserve collections and other system data
   - Add confirmation mechanism

2. **Safety Measures**
   - Add backup confirmation
   - Log all deletions
   - Provide count of deleted items

### Phase 2: Shopify Products Import
1. **Create Products Import Endpoint**
   - Add `GET /api/v1/shopify/products` endpoint
   - Fetch all products from Shopify store
   - Handle pagination for large product catalogs

2. **Create Products Import Endpoint**
   - Add `POST /api/v1/shopify/products/import` endpoint
   - Convert Shopify products to coins
   - Map Shopify collections to local collections
   - Generate SKUs for imported products
   - Apply pricing strategies

3. **Data Mapping**
   - Map Shopify product fields to coin fields
   - Handle variants (different grades/conditions)
   - Import product images
   - Link to appropriate collections

### Phase 3: Testing & Validation
1. **Test Delete Functionality**
   - Verify all fake data removed
   - Confirm collections preserved
   - Test system functionality

2. **Test Import Functionality**
   - Verify all Shopify products imported
   - Confirm SKU generation works
   - Test pricing calculations
   - Verify image imports

## Testing Strategy

### Unit Tests
- Test delete all coins endpoint
- Test Shopify products fetch
- Test product to coin conversion
- Test SKU generation for imported products

### Integration Tests
- Test full delete and import workflow
- Test collection linking
- Test pricing strategy application
- Test image import and linking

### Manual Testing
- Verify database state before and after
- Test frontend functionality after import
- Verify all coins display correctly
- Test search and filtering

## Deliverables
1. **Delete All Coins Endpoint**: `DELETE /api/v1/coins/clear`
2. **Shopify Products Fetch Endpoint**: `GET /api/v1/shopify/products`
3. **Shopify Products Import Endpoint**: `POST /api/v1/shopify/products/import`
4. **Updated Memory**: State and decisions updated
5. **Documentation**: API endpoints documented

## Review Criteria
- All fake data successfully deleted
- All Shopify products imported as coins
- Collections properly linked
- SKU generation working
- Pricing strategies applied
- Images imported and linked
- System remains functional
- No data loss or corruption

## Memory Notes
- **State Updates**: Inventory system status, fake data removal, Shopify import completion
- **Decision Updates**: Shopify products import strategy, data cleanup procedures
- **Issue Tracking**: Any import errors or data mapping issues

## DevOps Checklist
- [ ] Database backup before deletion
- [ ] Test in development environment first
- [ ] Monitor system performance during import
- [ ] Verify all endpoints working
- [ ] Update documentation
- [ ] Notify user of completion

## Risk Assessment
- **High Risk**: Data loss if delete operation fails
- **Medium Risk**: Import errors if Shopify API changes
- **Low Risk**: Performance impact during large imports

## Mitigation Strategies
- **Backup**: Full database backup before operations
- **Validation**: Extensive testing before production
- **Rollback**: Ability to restore from backup if needed
- **Monitoring**: Real-time monitoring during operations

