# Fix: 405 Error on set-public Endpoint

## The Problem

The `/v1/files/set-public` endpoint returns 405, which means:
- The endpoint doesn't exist, OR
- The HTTP method is wrong, OR
- Files are already public when uploaded with `is_public=True`

## Solution 1: Check if Files Are Already Public

Files uploaded with `is_public=True` might already be public. Test this:

```python
import asyncio
import requests
from streamline_file_uploader import StreamlineFileUploader

async def upload_and_verify_public():
    # Upload with is_public (if SDK supports it)
    async with StreamlineFileUploader() as uploader:
        with open("test.jpg", "rb") as f:
            file_content = f.read()
        
        result = await uploader.upload_file(
            file_content=file_content,
            filename="test.jpg",
            folder="test",
            user_email="user@example.com"
        )
        
        print(f"File Key: {result.file_key}")
        print(f"Public URL: {result.public_url}")
        
        # Test if file is already accessible
        try:
            response = requests.get(result.public_url, timeout=10)
            if response.status_code == 200:
                print("✓ File is ALREADY PUBLIC - no need for set-public!")
                print(f"  Content-Type: {response.headers.get('Content-Type')}")
                return True
            else:
                print(f"✗ File is NOT public: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ Error checking file: {e}")
            return False

asyncio.run(upload_and_verify_public())
```

## Solution 2: Modify SDK to Include is_public During Upload

If files aren't public, add `is_public` to the upload request:

```python
# In streamline_file_uploader.py, modify upload_file method:

async def upload_file(
    self,
    file_content: bytes,
    filename: str,
    folder: str,
    user_email: str,
    is_public: bool = True  # ADD THIS
) -> UploadResult:
    """Upload a file to Stream-Line file server"""
    if not self.service_token:
        raise ValueError("AUTH_SERVICE_TOKEN not configured")
    
    if not self.session:
        self.session = aiohttp.ClientSession()
    
    try:
        headers = {
            "X-Service-Token": self.service_token,
            "Content-Type": "application/octet-stream"
        }
        
        data = aiohttp.FormData()
        data.add_field('file', file_content, filename=filename)
        data.add_field('folder', folder)
        data.add_field('user_email', user_email)
        data.add_field('is_public', 'true' if is_public else 'false')  # ADD THIS LINE
        
        async with self.session.post(
            f"{self.base_url}/v1/files/upload",
            headers=headers,
            data=data
        ) as response:
            # ... rest of code
```

## Solution 3: Try Alternative Endpoints

The endpoint might be different. Try these:

```python
import asyncio
import aiohttp
import os
from dotenv import load_dotenv

load_dotenv()

async def try_different_endpoints(file_key):
    service_token = os.getenv("AUTH_SERVICE_TOKEN")
    base_url = os.getenv("UPLOAD_BASE_URL", "https://file-server.stream-lineai.com")
    headers = {"X-Service-Token": service_token, "Content-Type": "application/json"}
    
    endpoints_to_try = [
        "/v1/files/set-public",      # Original
        "/v1/files/public",          # Alternative 1
        "/v1/files/make-public",     # Alternative 2
        "/v1/files/update",          # Alternative 3
    ]
    
    data = {"file_key": file_key, "is_public": True}
    
    async with aiohttp.ClientSession() as session:
        for endpoint in endpoints_to_try:
            # Try POST
            async with session.post(f"{base_url}{endpoint}", headers=headers, json=data) as response:
                print(f"POST {endpoint}: {response.status}")
                if response.status == 200:
                    print(f"✓ SUCCESS with {endpoint}")
                    return await response.json()
            
            # Try PUT
            async with session.put(f"{base_url}{endpoint}", headers=headers, json=data) as response:
                print(f"PUT {endpoint}: {response.status}")
                if response.status == 200:
                    print(f"✓ SUCCESS with {endpoint}")
                    return await response.json()
    
    print("✗ None of the endpoints worked")
    return None

# Usage
asyncio.run(try_different_endpoints("your-file-key"))
```

## Solution 4: Complete Working Code (Skip set-public if 405)

```python
import asyncio
import aiohttp
import requests
import os
from dotenv import load_dotenv
from streamline_file_uploader import StreamlineFileUploader

load_dotenv()

async def upload_file_public():
    """Upload file and ensure it's public"""
    
    # STEP 1: Upload file
    async with StreamlineFileUploader() as uploader:
        with open("image.jpg", "rb") as f:
            file_content = f.read()
        
        result = await uploader.upload_file(
            file_content=file_content,
            filename="image.jpg",
            folder="my-folder",
            user_email="user@example.com"
        )
        
        print(f"✓ Uploaded: {result.file_key}")
        print(f"  Public URL: {result.public_url}")
        
        # STEP 2: Check if already public
        try:
            response = requests.get(result.public_url, timeout=10)
            if response.status_code == 200:
                print("✓ File is already public - no action needed!")
                return result
        except:
            pass
        
        # STEP 3: Try to make public (if not already)
        service_token = os.getenv("AUTH_SERVICE_TOKEN")
        base_url = os.getenv("UPLOAD_BASE_URL", "https://file-server.stream-lineai.com")
        
        headers = {
            "X-Service-Token": service_token,
            "Content-Type": "application/json"
        }
        
        data = {"file_key": result.file_key, "is_public": True}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{base_url}/v1/files/set-public",
                headers=headers,
                json=data
            ) as response:
                if response.status == 200:
                    print("✓ Made file public via API")
                elif response.status == 405:
                    print("⚠ set-public endpoint not available (405)")
                    print("  File may already be public, or endpoint doesn't exist")
                    print(f"  Try accessing: {result.public_url}")
                else:
                    error = await response.text()
                    print(f"⚠ Unexpected response: {response.status} - {error}")
        
        return result

asyncio.run(upload_file_public())
```

## Solution 5: Verify File Key Format

The file_key might need to be in a specific format. Check what the server returns:

```python
import asyncio
from streamline_file_uploader import StreamlineFileUploader

async def check_file_key_format():
    async with StreamlineFileUploader() as uploader:
        with open("test.jpg", "rb") as f:
            result = await uploader.upload_file(
                file_content=f.read(),
                filename="test.jpg",
                folder="test",
                user_email="user@example.com"
            )
        
        print("=== FILE KEY ANALYSIS ===")
        print(f"Raw file_key: {result.file_key}")
        print(f"Type: {type(result.file_key)}")
        print(f"Length: {len(result.file_key)}")
        print(f"Public URL: {result.public_url}")
        
        # Try different formats
        formats_to_try = [
            result.file_key,                    # Original
            f"test/test.jpg",                   # folder/filename
            result.file_key.split('/')[-1],     # Just filename
            result.public_url.split('/')[-1],   # From URL
        ]
        
        print("\nFormats to try:")
        for fmt in formats_to_try:
            print(f"  - {fmt}")

asyncio.run(check_file_key_format())
```

## Recommended Approach

**Use this code - it handles everything:**

```python
import asyncio
import requests
from streamline_file_uploader import StreamlineFileUploader

async def upload_public_file_simple():
    """Simple upload - files are likely already public"""
    
    async with StreamlineFileUploader() as uploader:
        with open("image.jpg", "rb") as f:
            file_content = f.read()
        
        # Upload
        result = await uploader.upload_file(
            file_content=file_content,
            filename="image.jpg",
            folder="my-folder",
            user_email="user@example.com"
        )
        
        # Verify it's accessible
        try:
            response = requests.get(result.public_url, timeout=10)
            if response.status_code == 200:
                print(f"✓ SUCCESS! File is public: {result.public_url}")
                return result
            else:
                print(f"⚠ File returned HTTP {response.status_code}")
                print(f"  URL: {result.public_url}")
        except Exception as e:
            print(f"✗ Error accessing file: {e}")
            print(f"  URL: {result.public_url}")
        
        return result

asyncio.run(upload_public_file_simple())
```

## Summary

1. **Files might already be public** - Test the `public_url` directly
2. **405 means endpoint doesn't exist** - Don't call set-public if you get 405
3. **Add `is_public=True` to upload** - Modify SDK to include it in form data
4. **Verify with requests.get()** - Check if URL is accessible

**Most likely**: Files are already public when uploaded. Just use the `public_url` from the upload result!

