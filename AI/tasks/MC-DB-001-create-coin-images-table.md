# MC-DB-001: Create coin_images Table

## Task Metadata
- **Task ID**: MC-DB-001
- **Priority**: High
- **Status**: Pending
- **Assigned To**: AI Assistant
- **Created**: 2025-01-28
- **Updated**: 2025-01-28
- **Estimated Time**: 30 minutes
- **Actual Time**: TBD

## Context
The file uploader integration is working correctly with the simplified folder structure `coins/{collection}/{sku}`, but coin creation with images fails because the `coin_images` table doesn't exist in the database. This table is needed to store image metadata associated with coins.

## Objective
Create the `coin_images` table in the PostgreSQL database to store image metadata for coins, enabling the complete file upload workflow.

## Core Responsibilities
1. **Database Schema Design**: Design the `coin_images` table with appropriate columns
2. **Table Creation**: Execute SQL to create the table in the database
3. **Testing**: Verify the table works with the coin creation endpoint
4. **Documentation**: Update memory with table creation status

## Implementation Plan

### Phase 1: Database Schema Design
- [ ] Design `coin_images` table schema with columns:
  - `id` (Primary Key, Serial)
  - `coin_id` (Foreign Key to coins table)
  - `url` (Public URL of the image)
  - `file_key` (File key for signed URL generation)
  - `filename` (Original filename)
  - `mime_type` (MIME type of the image)
  - `size` (File size in bytes)
  - `is_primary` (Boolean flag for primary image)
  - `created_at` (Timestamp)
  - `updated_at` (Timestamp)

### Phase 2: Table Creation
- [ ] Connect to PostgreSQL database
- [ ] Execute CREATE TABLE SQL statement
- [ ] Verify table creation
- [ ] Test foreign key relationship with coins table

### Phase 3: Testing
- [ ] Run the file upload workflow test
- [ ] Verify coin creation with images works
- [ ] Test image metadata storage
- [ ] Verify signed URL generation

### Phase 4: Documentation
- [ ] Update memory with table creation status
- [ ] Update task status to completed
- [ ] Document any issues or considerations

## Technical Requirements
- PostgreSQL database connection
- Proper foreign key constraints
- Appropriate indexes for performance
- Timestamp columns for audit trail

## Testing Strategy
- Run `backend/test_file_upload_workflow.py` to verify complete workflow
- Test coin creation with multiple images
- Verify image metadata is stored correctly
- Test signed URL generation for stored images

## Deliverables
1. `coin_images` table created in database
2. Successful file upload workflow test
3. Updated memory documentation
4. Completed task documentation

## Review Criteria
- [ ] `coin_images` table exists in database
- [ ] All file upload workflow tests pass
- [ ] Coin creation with images works end-to-end
- [ ] Image metadata is properly stored and retrievable
- [ ] Signed URLs can be generated for stored images

## Memory Notes
- Folder structure successfully updated to `coins/{collection}/{sku}`
- File uploader integration working correctly
- Only remaining issue is missing `coin_images` table
- Table creation will complete the file upload workflow

## Dependencies
- PostgreSQL database access
- Existing `coins` table for foreign key relationship
- File uploader service working correctly

## Risks
- Database connection issues
- Foreign key constraint problems
- Performance impact of additional table

## Success Metrics
- All file upload workflow tests pass (5/5)
- Coin creation with images successful
- Image metadata properly stored
- Signed URL generation working
