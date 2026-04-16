# Stream-Line File Server SDK - Usage Guide

## Overview

This guide provides instructions for downloading, installing, and using the Stream-Line File Server SDK in the Miracle Coins CoinSync Pro project.

## Current Implementation

The project includes a custom `StreamlineFileUploader` client located at:
- **File**: `backend/streamline_file_uploader.py`
- **Service Wrapper**: `backend/app/services/file_upload_service.py`

This is a Python async client that communicates with the Stream-Line file server API.

---

## Prerequisites

### Required Python Packages

Install the following dependencies:

```bash
pip install aiohttp pydantic python-dotenv
```

Or add to `requirements.txt`:

```txt
aiohttp>=3.8.0
pydantic>=2.0.0
python-dotenv>=1.0.0
```

### Environment Configuration

Set the following environment variables in your `.env` file:

```env
# Stream-Line File Server Configuration
UPLOAD_BASE_URL=https://file-server.stream-lineai.com
AUTH_SERVICE_TOKEN=your_service_token_here
```

**Getting the Service Token**:
- Contact Stream-Line AI to obtain your `AUTH_SERVICE_TOKEN`
- This token authenticates your application with the file server
- Keep this token secure and never commit it to version control

---

## Installation Steps

### Step 1: Verify SDK File Exists

The SDK is already included in the project. Verify it exists:

```bash
# Check if the file exists
ls backend/streamline_file_uploader.py

# Or on Windows
dir backend\streamline_file_uploader.py
```

### Step 2: Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

If `aiohttp` and `pydantic` are not in requirements.txt, install them:

```bash
pip install aiohttp pydantic python-dotenv
```

### Step 3: Configure Environment

1. Copy the example environment file:
   ```bash
   cp env.example .env
   ```

2. Edit `.env` and add your credentials:
   ```env
   UPLOAD_BASE_URL=https://file-server.stream-lineai.com
   AUTH_SERVICE_TOKEN=your_actual_token_here
   ```

3. Verify configuration:
   ```python
   import os
   from dotenv import load_dotenv
   
   load_dotenv()
   
   token = os.getenv("AUTH_SERVICE_TOKEN")
   base_url = os.getenv("UPLOAD_BASE_URL")
   
   print(f"Base URL: {base_url}")
   print(f"Token configured: {token is not None}")
   ```

---

## Basic Usage

### Method 1: Using StreamlineFileUploader Directly

```python
import asyncio
from streamline_file_uploader import StreamlineFileUploader

async def upload_example():
    # Initialize uploader
    uploader = StreamlineFileUploader()
    
    # Read file content
    with open("image.jpg", "rb") as f:
        file_content = f.read()
    
    # Upload file
    result = await uploader.upload_file(
        file_content=file_content,
        filename="image.jpg",
        folder="coins/mercury-dimes",
        user_email="user@example.com"
    )
    
    print(f"Uploaded: {result.public_url}")
    print(f"File Key: {result.file_key}")
    
    # Close session
    await uploader.close()

# Run the async function
asyncio.run(upload_example())
```

### Method 2: Using Context Manager (Recommended)

```python
import asyncio
from streamline_file_uploader import StreamlineFileUploader

async def upload_with_context():
    async with StreamlineFileUploader() as uploader:
        with open("image.jpg", "rb") as f:
            file_content = f.read()
        
        result = await uploader.upload_file(
            file_content=file_content,
            filename="image.jpg",
            folder="coins/mercury-dimes",
            user_email="user@example.com"
        )
        
        print(f"Uploaded: {result.public_url}")

asyncio.run(upload_with_context())
```

### Method 3: Using FileUploadService (Recommended for Coin Images)

```python
import asyncio
from app.services.file_upload_service import FileUploadService

async def upload_coin_image():
    service = FileUploadService()
    
    # Read image file
    with open("coin_image.jpg", "rb") as f:
        file_content = f.read()
    
    # Upload with organized folder structure
    result = await service.upload_coin_image(
        file_content=file_content,
        filename="coin_image.jpg",
        collection="mercury-dimes",
        sku="MC-12345"
    )
    
    if result:
        print(f"Uploaded to: {result.public_url}")
        print(f"Folder: {result.folder}")
    else:
        print("Upload failed")

asyncio.run(upload_coin_image())
```

---

## API Reference

### StreamlineFileUploader Class

#### Initialization

```python
uploader = StreamlineFileUploader(service_token=None)
```

**Parameters**:
- `service_token` (optional): Service token. If not provided, reads from `AUTH_SERVICE_TOKEN` environment variable.

#### Methods

##### `upload_file()`

Upload a single file to the server.

```python
async def upload_file(
    file_content: bytes,
    filename: str,
    folder: str,
    user_email: str
) -> UploadResult
```

**Parameters**:
- `file_content` (bytes): Binary content of the file
- `filename` (str): Name of the file
- `folder` (str): Folder path (e.g., "coins/mercury-dimes")
- `user_email` (str): User email for organization

**Returns**: `UploadResult` object with:
- `file_key` (str): Unique file identifier
- `public_url` (str): Public URL to access the file
- `size` (int): File size in bytes
- `mime_type` (str): MIME type of the file
- `folder` (str): Folder where file was uploaded
- `filename` (str): Original filename
- `sha256` (str): SHA256 hash of the file

**Example**:
```python
result = await uploader.upload_file(
    file_content=b"file content here",
    filename="test.jpg",
    folder="coins/mercury-dimes",
    user_email="user@example.com"
)
```

##### `upload_files()`

Upload multiple files in batch.

```python
async def upload_files(
    files: List[Dict[str, Any]],
    user_email: str
) -> List[UploadResult]
```

**Parameters**:
- `files` (List[Dict]): List of file dictionaries with:
  - `content` (bytes): File content
  - `filename` (str): File name
  - `folder` (str): Folder path
- `user_email` (str): User email

**Returns**: List of `UploadResult` objects

**Example**:
```python
files = [
    {
        "content": b"file1 content",
        "filename": "image1.jpg",
        "folder": "coins/mercury-dimes"
    },
    {
        "content": b"file2 content",
        "filename": "image2.jpg",
        "folder": "coins/mercury-dimes"
    }
]

results = await uploader.upload_files(files, "user@example.com")
```

##### `list_files()`

List files in a folder.

```python
async def list_files(
    folder: str,
    user_email: str
) -> List[Dict[str, Any]]
```

**Example**:
```python
files = await uploader.list_files(
    folder="coins/mercury-dimes",
    user_email="user@example.com"
)
```

##### `search_files()`

Search for files with criteria.

```python
async def search_files(
    filename_pattern: Optional[str] = None,
    mime_type: Optional[str] = None,
    folder: str = "",
    user_email: str = ""
) -> List[Dict[str, Any]]
```

**Example**:
```python
# Search for all JPG images
files = await uploader.search_files(
    filename_pattern="*.jpg",
    mime_type="image/jpeg",
    folder="coins",
    user_email="user@example.com"
)
```

##### `get_folder_stats()`

Get statistics for a folder.

```python
async def get_folder_stats(
    user_email: str,
    folder: str
) -> Optional[Dict[str, Any]]
```

**Example**:
```python
stats = await uploader.get_folder_stats(
    user_email="user@example.com",
    folder="coins/mercury-dimes"
)
```

---

## FileUploadService Class

The `FileUploadService` provides higher-level methods specifically for coin images and documents.

### Methods

#### `upload_coin_image()`

Upload a coin image with organized folder structure.

```python
async def upload_coin_image(
    file_content: bytes,
    filename: str,
    collection: str,
    sku: Optional[str] = None,
    user_email: Optional[str] = None
) -> Optional[UploadResult]
```

**Folder Structure**: `coins/{collection}/{sku}/`

**Example**:
```python
service = FileUploadService()

with open("coin.jpg", "rb") as f:
    result = await service.upload_coin_image(
        file_content=f.read(),
        filename="coin.jpg",
        collection="mercury-dimes",
        sku="MC-12345"
    )
```

#### `upload_coin_document()`

Upload a coin document (certificate, appraisal, etc.).

```python
async def upload_coin_document(
    file_content: bytes,
    filename: str,
    collection: str,
    year: Optional[int] = None,
    sku: Optional[str] = None,
    user_email: Optional[str] = None
) -> Optional[UploadResult]
```

**Folder Structure**: `coins/{collection}/{sku}/documents/`

#### `list_coin_files()`

List files for a specific coin or collection.

```python
async def list_coin_files(
    collection: Optional[str] = None,
    year: Optional[int] = None,
    sku: Optional[str] = None,
    user_email: Optional[str] = None
) -> List[Dict[str, Any]]
```

#### `batch_upload_coin_files()`

Upload multiple files for a coin.

```python
async def batch_upload_coin_files(
    files: List[Dict[str, Any]],
    collection: str,
    year: Optional[int] = None,
    sku: Optional[str] = None,
    user_email: Optional[str] = None
) -> List[Optional[UploadResult]]
```

---

## Complete Examples

### Example 1: Upload Single Coin Image

```python
import asyncio
from app.services.file_upload_service import FileUploadService

async def upload_single_image():
    service = FileUploadService()
    
    # Check if service is configured
    if not service.is_configured():
        print("Error: AUTH_SERVICE_TOKEN not configured")
        return
    
    # Read image file
    with open("coin_image.jpg", "rb") as f:
        file_content = f.read()
    
    # Upload
    result = await service.upload_coin_image(
        file_content=file_content,
        filename="coin_image.jpg",
        collection="mercury-dimes",
        sku="MC-12345"
    )
    
    if result:
        print(f"✓ Uploaded successfully")
        print(f"  URL: {result.public_url}")
        print(f"  Folder: {result.folder}")
        print(f"  Size: {result.size} bytes")
        print(f"  SHA256: {result.sha256}")
    else:
        print("✗ Upload failed")

asyncio.run(upload_single_image())
```

### Example 2: Upload Multiple Images

```python
import asyncio
from app.services.file_upload_service import FileUploadService

async def upload_multiple_images():
    service = FileUploadService()
    
    # Prepare files
    files = []
    for i in range(1, 4):
        with open(f"image_{i}.jpg", "rb") as f:
            files.append({
                "content": f.read(),
                "filename": f"image_{i}.jpg"
            })
    
    # Batch upload
    results = await service.batch_upload_coin_files(
        files=files,
        collection="mercury-dimes",
        sku="MC-12345"
    )
    
    # Check results
    successful = sum(1 for r in results if r is not None)
    print(f"Uploaded {successful}/{len(files)} files")
    
    for i, result in enumerate(results):
        if result:
            print(f"  Image {i+1}: {result.public_url}")

asyncio.run(upload_multiple_images())
```

### Example 3: List Files in Collection

```python
import asyncio
from app.services.file_upload_service import FileUploadService

async def list_collection_files():
    service = FileUploadService()
    
    files = await service.list_coin_files(
        collection="mercury-dimes",
        sku="MC-12345"
    )
    
    print(f"Found {len(files)} files:")
    for file_info in files:
        print(f"  - {file_info.get('filename', 'unknown')}")

asyncio.run(list_collection_files())
```

### Example 4: Search for Files

```python
import asyncio
from app.services.file_upload_service import FileUploadService

async def search_files():
    service = FileUploadService()
    
    # Search for all JPG images in mercury-dimes collection
    files = await service.search_coin_files(
        filename_pattern="*.jpg",
        mime_type="image/jpeg",
        collection="mercury-dimes"
    )
    
    print(f"Found {len(files)} matching files")

asyncio.run(search_files())
```

### Example 5: Using in FastAPI Endpoint

```python
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.file_upload_service import FileUploadService

router = APIRouter()

@router.post("/upload")
async def upload_endpoint(
    file: UploadFile = File(...),
    collection: str = "default",
    sku: str = None
):
    service = FileUploadService()
    
    if not service.is_configured():
        raise HTTPException(
            status_code=500,
            detail="File upload service not configured"
        )
    
    # Read file content
    file_content = await file.read()
    
    # Upload
    result = await service.upload_coin_image(
        file_content=file_content,
        filename=file.filename,
        collection=collection,
        sku=sku
    )
    
    if result:
        return {
            "success": True,
            "url": result.public_url,
            "file_key": result.file_key
        }
    else:
        raise HTTPException(
            status_code=500,
            detail="Failed to upload file"
        )
```

---

## Error Handling

### Common Errors and Solutions

#### 1. "AUTH_SERVICE_TOKEN not configured"

**Error**: `ValueError: AUTH_SERVICE_TOKEN not configured`

**Solution**:
```python
# Check configuration
service = FileUploadService()
if not service.is_configured():
    print("Set AUTH_SERVICE_TOKEN in .env file")
```

#### 2. Upload Failed

**Error**: `Exception: Upload failed: 401 - Unauthorized`

**Solutions**:
- Verify `AUTH_SERVICE_TOKEN` is correct
- Check token hasn't expired
- Ensure token has proper permissions

#### 3. Network Errors

**Error**: Connection timeout or network errors

**Solutions**:
- Check internet connectivity
- Verify `UPLOAD_BASE_URL` is correct
- Check firewall settings

### Error Handling Example

```python
import asyncio
from app.services.file_upload_service import FileUploadService

async def safe_upload():
    service = FileUploadService()
    
    try:
        # Check configuration
        if not service.is_configured():
            print("Error: Service not configured")
            return
        
        # Read file
        with open("image.jpg", "rb") as f:
            file_content = f.read()
        
        # Upload with error handling
        result = await service.upload_coin_image(
            file_content=file_content,
            filename="image.jpg",
            collection="mercury-dimes"
        )
        
        if result:
            print(f"Success: {result.public_url}")
        else:
            print("Upload returned None - check logs")
            
    except ValueError as e:
        print(f"Configuration error: {e}")
    except Exception as e:
        print(f"Upload error: {e}")

asyncio.run(safe_upload())
```

---

## Testing

### Test Configuration

```python
from app.services.file_upload_service import FileUploadService

def test_configuration():
    service = FileUploadService()
    status = service.get_configuration_status()
    
    print("Configuration Status:")
    print(f"  Base URL: {status['base_url']}")
    print(f"  Token Configured: {status['service_token_configured']}")
    print(f"  Service Ready: {status['service_ready']}")

test_configuration()
```

### Test Upload

```python
import asyncio
from app.services.file_upload_service import FileUploadService

async def test_upload():
    service = FileUploadService()
    
    # Create test file content
    test_content = b"This is a test file"
    
    result = await service.upload_coin_image(
        file_content=test_content,
        filename="test.txt",
        collection="test",
        sku="TEST-001"
    )
    
    if result:
        print("✓ Test upload successful")
        print(f"  URL: {result.public_url}")
    else:
        print("✗ Test upload failed")

asyncio.run(test_upload())
```

---

## Best Practices

### 1. Always Use Context Manager

```python
# Good
async with StreamlineFileUploader() as uploader:
    result = await uploader.upload_file(...)

# Bad
uploader = StreamlineFileUploader()
result = await uploader.upload_file(...)
# Forgot to close!
```

### 2. Check Configuration Before Use

```python
service = FileUploadService()
if not service.is_configured():
    raise HTTPException(500, "Service not configured")
```

### 3. Handle Errors Gracefully

```python
try:
    result = await service.upload_coin_image(...)
    if not result:
        # Handle failure
        pass
except Exception as e:
    logger.error(f"Upload failed: {e}")
    # Handle error
```

### 4. Use Organized Folder Structure

```python
# Good - organized structure
folder = f"coins/{collection}/{sku}"

# Bad - flat structure
folder = "all_files"
```

### 5. Validate File Types

```python
ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp"]

if file.content_type not in ALLOWED_TYPES:
    raise HTTPException(400, "Invalid file type")
```

---

## Troubleshooting

### Issue: "Module not found: streamline_file_uploader"

**Solution**: Ensure you're in the correct directory:
```bash
cd backend
python your_script.py
```

Or add to Python path:
```python
import sys
sys.path.append('backend')
from streamline_file_uploader import StreamlineFileUploader
```

### Issue: "AUTH_SERVICE_TOKEN not set"

**Solution**: 
1. Check `.env` file exists in `backend/` directory
2. Verify `AUTH_SERVICE_TOKEN` is set
3. Load environment variables:
   ```python
   from dotenv import load_dotenv
   load_dotenv()
   ```

### Issue: Upload returns None

**Check**:
1. Service token is valid
2. Network connectivity
3. File server is accessible
4. Check logs for error messages

### Issue: Files not appearing in expected folder

**Check**:
1. Folder path format is correct
2. User email matches
3. Check folder structure in file server

---

## API Endpoints Reference

The file server API endpoints:

- **Upload**: `POST /v1/files/upload`
- **List**: `GET /v1/files/list`
- **Search**: `GET /v1/files/search`
- **Stats**: `GET /v1/files/stats`
- **Signed URL**: `GET /v1/files/signed-url`

Base URL: `https://file-server.stream-lineai.com`

---

## Additional Resources

- **SDK File**: `backend/streamline_file_uploader.py`
- **Service Wrapper**: `backend/app/services/file_upload_service.py`
- **API Router**: `backend/app/routers/file_upload.py`

---

**Last Updated**: 2025-01-28  
**Version**: 1.0  
**Project**: Miracle Coins CoinSync Pro

