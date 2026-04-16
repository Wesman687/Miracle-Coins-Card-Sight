# MC-COL-001: Shopify Collections Sync Investigation and Fix

## Metadata
- **ID**: MC-COL-001
- **Owner**: AI Assistant
- **Date**: 2025-01-28
- **Branch**: main
- **Dependencies**: None

## Task Summary
Investigate and fix the collections sync issue - current collections are test data, need to sync with actual Shopify collections.

## Current Context
- Collections page showing "Gold Bullion" and other test collections
- User confirms these are not real collections from Shopify
- Need to investigate where these collections came from
- Critical: Collections must be synced with Shopify for proper product association
- User mentioned collections exist in "add coin" functionality

## Goals & Acceptance Criteria
- [ ] Identify source of current test collections in database
- [ ] Verify Shopify collections integration is working
- [ ] Clear test collections from database
- [ ] Sync actual Shopify collections to local database
- [ ] Ensure collections are properly associated when adding coins
- [ ] Verify collections page shows only real Shopify collections

## Implementation Plan
1. **Database Investigation**
   - Query collections table to see current data
   - Identify source of test collections
   - Check if collections were added via migration or API

2. **Shopify Integration Review**
   - Check Shopify collections API integration
   - Verify collection import functionality
   - Test fetching collections from Shopify

3. **Clean Up and Sync**
   - Remove test collections from database
   - Import actual Shopify collections
   - Verify collection-product association

4. **Frontend Integration**
   - Ensure "add coin" uses Shopify collections
   - Verify collections page displays correct data
   - Test collection selection in coin creation

## Testing Strategy
- Query database directly to verify collections
- Test Shopify API integration
- Verify frontend displays correct collections
- Test coin creation with collection association

## Deliverables
- Database cleaned of test collections
- Real Shopify collections synced and displayed
- Collections properly associated with coin creation
- Documentation of Shopify collections sync process

## Review Criteria
- Collections page shows only real Shopify collections
- No test/fake collections visible
- Coin creation properly associates with collections
- Shopify sync working correctly

## Memory Notes
- User confirmed collections exist in Shopify
- Critical for product-collection association
- Must maintain sync between Shopify and local database

## DevOps Checklist
- [ ] Database queries executed
- [ ] Shopify API tested
- [ ] Collections cleaned and synced
- [ ] Frontend integration verified
- [ ] Coin creation tested with collections
