# MC-017-addcoin-modal-image-pricing-fixes.md

## Task Metadata
- **ID**: MC-017
- **Owner**: AI Assistant
- **Date**: 2025-01-29
- **Branch**: main
- **Dependencies**: MC-016 (AddCoinModal redesign)
- **Priority**: High

## Task Summary
Fix image display issues in AddCoinModal and enhance pricing strategy with live spot price integration and set price options.

## Current Context
- AddCoinModal redesigned with new components (TagSelector, ImageManager, RichTextEditor)
- Images not displaying despite being uploaded to file server
- Pricing strategy needs enhancement: add "set price" option and live spot price integration
- Need to pull live metals prices from existing spot price service

## Goals & Acceptance Criteria

### Primary Goals:
1. **Fix Image Display**: Images uploaded to file server should display properly in ImageManager
2. **Enhance Pricing Strategy**: Add "Set Price" option alongside "Fixed Price" and "Market Scaling"
3. **Live Spot Price Integration**: Pull real-time silver/gold spot prices from existing service
4. **Price Preview Updates**: Show live spot prices and calculated values in real-time

### Acceptance Criteria:
- [ ] Images display properly in ImageManager component
- [ ] Pricing strategy includes: Fixed Price, Set Price, Market Scaling
- [ ] Live spot prices pulled from existing metals price service
- [ ] Price preview shows real-time calculations
- [ ] All pricing options work correctly with form validation

## Implementation Plan

### Phase 1: Fix Image Display (Priority 1)
1. Debug why images aren't displaying in ImageManager
2. Check file server response format and URL structure
3. Verify image URLs are accessible and properly formatted
4. Test image upload and display workflow

### Phase 2: Enhance Pricing Strategy (Priority 1)
1. Add "Set Price" option to pricing strategy enum
2. Update form schema to include set_price field
3. Modify pricing logic to handle three strategies:
   - Fixed Price: Never changes
   - Set Price: Can be manually updated
   - Market Scaling: Scales with spot prices

### Phase 3: Live Spot Price Integration (Priority 2)
1. Integrate with existing spot price service
2. Fetch real-time silver and gold prices
3. Update price preview calculations with live data
4. Add spot price display in pricing section

### Phase 4: UI/UX Improvements (Priority 2)
1. Update pricing section UI to show live spot prices
2. Improve price preview with real-time updates
3. Add visual indicators for different pricing strategies
4. Test all pricing scenarios

## Testing Strategy

### Unit Tests:
- ImageManager component image display
- Pricing calculation logic with live spot prices
- Form validation for all pricing strategies

### Integration Tests:
- Image upload and display workflow
- Spot price service integration
- Price preview calculations

### User Acceptance Tests:
- Test complete coin creation with all pricing options
- Verify images display correctly
- Confirm live spot price integration works

## Deliverables

### Components:
1. **Fixed ImageManager** - Properly displays uploaded images
2. **Enhanced PricingSection** - Three pricing strategies with live spot prices
3. **Spot Price Integration** - Real-time metals price fetching

### Updated Files:
1. **AddCoinModal.tsx** - Enhanced pricing strategy and image handling
2. **Form Schema** - Updated Zod validation for new pricing options
3. **Spot Price Service** - Integration with existing metals price service

## Review Criteria

### Code Quality:
- [ ] All components use TypeScript with strict typing
- [ ] Proper error handling for image display and spot price fetching
- [ ] Clean, maintainable code structure
- [ ] Follows existing code patterns

### User Experience:
- [ ] Images display immediately after upload
- [ ] Live spot prices update in real-time
- [ ] Clear pricing strategy options
- [ ] Intuitive price preview

### Functionality:
- [ ] All pricing strategies work correctly
- [ ] Images display from file server
- [ ] Live spot price integration functional
- [ ] No breaking changes to existing functionality

## Memory Notes

### Decisions Made:
- Pricing strategy enhanced to include Set Price option
- Live spot price integration using existing service
- Image display issues need debugging and fixing

### Technical Choices:
- Use existing spot price service for live data
- Maintain backward compatibility with existing pricing
- Fix image display without breaking upload functionality

## DevOps Checklist

### Frontend:
- [ ] Test ImageManager component fixes
- [ ] Test pricing strategy enhancements
- [ ] Test spot price integration
- [ ] Verify no breaking changes

### Backend:
- [ ] Verify spot price service is accessible
- [ ] Test image upload endpoints
- [ ] Confirm pricing calculation endpoints

### Database:
- [ ] Verify schema supports new pricing fields
- [ ] Test data persistence for all pricing strategies

---

**Status**: Completed
**Completed At**: 2025-01-29T01:00:00Z
**Next Steps**: All issues resolved and enhancements implemented
