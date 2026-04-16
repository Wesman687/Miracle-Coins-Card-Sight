# MC-016-addcoin-modal-comprehensive-redesign.md

## Task Metadata
- **ID**: MC-016
- **Owner**: AI Assistant
- **Date**: 2025-01-28
- **Branch**: main
- **Dependencies**: MC-015 (inventory cleanup), existing CollectionSelector component
- **Priority**: High

## Task Summary
Comprehensive redesign of AddCoinModal to improve UX, fix collection selector issues, simplify pricing strategy, add image management, rich text editor, tags system, and metadata integration.

## Current Context
- AddCoinModal has confusing pricing strategy with unclear terminology
- CollectionSelector bubbles not displaying selected collections properly
- Missing image management (display, remove, reorder)
- No rich text editor for descriptions (showing HTML)
- Missing tags system like Shopify
- Missing metadata fields from Shopify integration
- No clear paid price field for inventory tracking
- Melt value not auto-calculated from silver percentage + content

## Goals & Acceptance Criteria

### Primary Goals:
1. **Fix Collection Selector**: Selected collections display as removable bubbles
2. **Simplify Pricing Strategy**: Fixed price OR market-based (silver/gold) scaling
3. **Auto-calculate Melt Value**: Read-only field calculated from silver % + content
4. **Add Image Management**: Display, remove (X), drag & drop reorder, thumbnail preview
5. **Rich Text Editor**: WYSIWYG description editor with preview
6. **Tags System**: Shopify-like tags with bubbles, dropdown suggestions, keyboard navigation
7. **Metadata Integration**: Pull existing metadata from Shopify products/collections
8. **Clear Paid Price Field**: Separate field for inventory cost tracking

### Acceptance Criteria:
- [ ] CollectionSelector shows selected collections as removable yellow bubbles
- [ ] Pricing strategy simplified to: Fixed Price OR Silver/Gold Market Scaling
- [ ] Melt value auto-calculates and is read-only when silver % + content entered
- [ ] Images display as thumbnails with X to remove, drag & drop to reorder
- [ ] Rich text editor for descriptions with live preview
- [ ] Tags system with bubbles, dropdown suggestions (max 10), keyboard navigation
- [ ] Collections and tags on same line or stacked
- [ ] Metadata fields populated from Shopify integration
- [ ] Clear paid price field separate from list price
- [ ] Remove status field (not needed for coin creation)

## Implementation Plan

### Phase 1: Fix Collection Selector (Priority 1)
1. Debug CollectionSelector component - selected collections not showing as bubbles
2. Test collection selection and removal functionality
3. Ensure proper state management between parent and child components

### Phase 2: Simplify Pricing Strategy (Priority 1)
1. Remove confusing pricing fields (entry_spot, entry_melt, etc.)
2. Implement simplified pricing options:
   - **Fixed Price**: Set specific price that doesn't change
   - **Market Scaling**: Price = (Silver Content × Current Spot × Multiplier)
3. Add auto-calculated melt value field (read-only)
4. Add clear price preview showing final calculated price

### Phase 3: Image Management (Priority 2)
1. Create ImageManager component with:
   - Thumbnail grid display
   - X button to remove images
   - Drag & drop reordering
   - Click thumbnail for full-size preview
2. Integrate with existing file uploader service
3. Update form schema to handle image arrays

### Phase 4: Rich Text Editor (Priority 2)
1. Install and configure rich text editor (TinyMCE or similar)
2. Add live preview functionality
3. Update description field to use rich text
4. Ensure proper HTML sanitization

### Phase 5: Tags System (Priority 2)
1. Create TagSelector component similar to CollectionSelector
2. Implement tag bubbles with X to remove
3. Add dropdown with existing tags (max 10 suggestions)
4. Keyboard navigation (arrow keys, enter to select)
5. Allow creation of new tags
6. Position collections and tags on same line or stacked

### Phase 6: Metadata Integration (Priority 3)
1. Identify metadata fields from Shopify products/collections
2. Add metadata fields to form schema
3. Auto-populate metadata when selecting from existing coins
4. Ensure proper data mapping

### Phase 7: UI/UX Improvements (Priority 3)
1. Add clear paid price field separate from list price
2. Remove status field
3. Improve form layout and organization
4. Add proper validation and error handling

## Testing Strategy

### Unit Tests:
- CollectionSelector component functionality
- TagSelector component functionality
- ImageManager component functionality
- Pricing calculation logic
- Form validation

### Integration Tests:
- End-to-end coin creation workflow
- Image upload and management
- Collection and tag selection
- Rich text editor functionality

### User Acceptance Tests:
- Test complete coin creation workflow
- Verify all new features work as expected
- Ensure backward compatibility with existing data

## Deliverables

### Components:
1. **Fixed CollectionSelector** - Working collection bubbles
2. **Simplified PricingSection** - Clear pricing strategy options
3. **ImageManager** - Image display, remove, reorder functionality
4. **RichTextEditor** - WYSIWYG description editor
5. **TagSelector** - Shopify-like tags system
6. **MetadataFields** - Shopify metadata integration

### Updated Files:
1. **AddCoinModal.tsx** - Main modal with all improvements
2. **Form Schema** - Updated Zod validation
3. **Type Definitions** - Updated TypeScript interfaces

## Review Criteria

### Code Quality:
- [ ] All components use TypeScript with strict typing
- [ ] Proper error handling and validation
- [ ] Clean, maintainable code structure
- [ ] Follows existing code patterns

### User Experience:
- [ ] Intuitive and easy to use
- [ ] Clear visual feedback
- [ ] Keyboard accessible
- [ ] Mobile responsive

### Functionality:
- [ ] All features work as specified
- [ ] Proper integration with existing systems
- [ ] No breaking changes to existing functionality

## Memory Notes

### Decisions Made:
- Pricing strategy simplified to Fixed Price OR Market Scaling
- Melt value auto-calculated and read-only
- Tags system modeled after Shopify
- Rich text editor for descriptions
- Image management with drag & drop
- Collections and tags can be on same line or stacked

### Technical Choices:
- Use existing file uploader service for images
- Implement drag & drop for image reordering
- Rich text editor with live preview
- Tag suggestions limited to 10 for performance
- Metadata pulled from existing Shopify integration

## DevOps Checklist

### Frontend:
- [ ] Install required dependencies (rich text editor, drag & drop)
- [ ] Update TypeScript types
- [ ] Test all components in isolation
- [ ] Test integration with existing systems

### Backend:
- [ ] Verify API endpoints support new fields
- [ ] Test image upload functionality
- [ ] Verify metadata integration
- [ ] Test pricing calculation endpoints

### Database:
- [ ] Verify schema supports all new fields
- [ ] Test data migration if needed
- [ ] Verify metadata storage

---

**Status**: Ready for Implementation
**Next Steps**: Begin with Phase 1 (Fix Collection Selector)
