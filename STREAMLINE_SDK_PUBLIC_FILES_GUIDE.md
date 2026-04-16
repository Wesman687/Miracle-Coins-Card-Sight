# Stream-Line File Server SDK - Making Files Public

## Overview

This guide explains how to set files as public after uploading them with the Stream-Line File Server SDK. Files can be made public either during upload or after upload using the API.

---

## Method 1: Set Files as Public During Upload (Recommended)

### Update the SDK to Support Public Files

Modify the `upload_file` method in `streamline_file_uploader.py` to include an `is_public` parameter:

```python
async def upload_file(
    self,
    file_content: bytes,
    filename: str,
    folder: str,
    user_email: str,
    is_public: bool = True  # Add this parameter
) -> UploadResult:
    """Upload a file to Stream-Line file server"""
    if not self.service_token:
        raise ValueError("AUTH_SERVICE_TOKEN not configured")
    
    if not self.session:
        self.session = aiohttp.ClientSession()
    
    try:
        # Prepare headers
        headers = {
            "X-Service-Token": self.service_token,
            "Content-Type": "application/octet-stream"
        }
        
        # Prepare data
        data = aiohttp.FormData()
        data.add_field('file', file_content, filename=filename)
        data.add_field('folder', folder)
        data.add_field('user_email', user_email)
        data.add_field('is_public', str(is_public).lower())  # Add this line
        
        # Upload file
        async with self.session.post(
            f"{self.base_url}/v1/files/upload",
            headers=headers,
            data=data
        ) as response:
            if response.status == 200:
                result_data = await response.json()
                
                # Generate file key and public URL
                file_key = result_data.get('file_key', hashlib.sha256(f"{folder}/{filename}".encode()).hexdigest()[:16])
                public_url = result_data.get('public_url', f"{self.base_url}/storage/{user_email}/{folder}/{filename}")
                
                return UploadResult(
                    file_key=file_key,
                    public_url=public_url,
                    size=len(file_content),
                    mime_type=self._get_mime_type(filename),
                    folder=folder,
                    filename=filename,
                    sha256=hashlib.sha256(file_content).hexdigest()
                )
            else:
                error_text = await response.text()
                raise Exception(f"Upload failed: {response.status} - {error_text}")
                
    except Exception as e:
        logger.error(f"Failed to upload file {filename}: {e}")
        raise
```

### Usage Example

```python
import asyncio
from streamline_file_uploader import StreamlineFileUploader

async def upload_public_file():
    async with StreamlineFileUploader() as uploader:
        with open("image.jpg", "rb") as f:
            file_content = f.read()
        
        # Upload as public file
        result = await uploader.upload_file(
            file_content=file_content,
            filename="image.jpg",
            folder="my-folder",
            user_email="user@example.com",
            is_public=True  # Set to True for public access
        )
        
        print(f"Public URL: {result.public_url}")
        print(f"File is publicly accessible: {result.public_url}")

asyncio.run(upload_public_file())
```

---

## Method 2: Set Files as Public After Upload

### Add a Method to Make Files Public

Add this method to the `StreamlineFileUploader` class:

```python
async def set_file_public(
    self,
    file_key: str,
    is_public: bool = True
) -> bool:
    """Set a file's public status after upload"""
    if not self.service_token or not self.session:
        return False
    
    try:
        headers = {"X-Service-Token": self.service_token}
        data = {
            "file_key": file_key,
            "is_public": is_public
        }
        
        async with self.session.post(
            f"{self.base_url}/v1/files/set-public",
            headers=headers,
            json=data
        ) as response:
            if response.status == 200:
                logger.info(f"File {file_key} public status set to {is_public}")
                return True
            else:
                error_text = await response.text()
                logger.error(f"Failed to set file public: {response.status} - {error_text}")
                return False
    except Exception as e:
        logger.error(f"Failed to set file public: {e}")
        return False
```

### Usage Example

```python
import asyncio
from streamline_file_uploader import StreamlineFileUploader

async def upload_and_make_public():
    async with StreamlineFileUploader() as uploader:
        # Upload file
        with open("image.jpg", "rb") as f:
            file_content = f.read()
        
        result = await uploader.upload_file(
            file_content=file_content,
            filename="image.jpg",
            folder="my-folder",
            user_email="user@example.com"
        )
        
        print(f"Uploaded: {result.file_key}")
        
        # Make file public after upload
        success = await uploader.set_file_public(
            file_key=result.file_key,
            is_public=True
        )
        
        if success:
            print(f"✓ File is now public: {result.public_url}")
        else:
            print("✗ Failed to make file public")

asyncio.run(upload_and_make_public())
```

---

## Method 3: Using Direct API Call

If the SDK method doesn't work, you can make a direct API call:

```python
import asyncio
import aiohttp
import os
from dotenv import load_dotenv

load_dotenv()

async def set_file_public_direct(file_key: str, is_public: bool = True):
    """Set file as public using direct API call"""
    service_token = os.getenv("AUTH_SERVICE_TOKEN")
    base_url = os.getenv("UPLOAD_BASE_URL", "https://file-server.stream-lineai.com")
    
    headers = {
        "X-Service-Token": service_token,
        "Content-Type": "application/json"
    }
    
    data = {
        "file_key": file_key,
        "is_public": is_public
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{base_url}/v1/files/set-public",
            headers=headers,
            json=data
        ) as response:
            if response.status == 200:
                result = await response.json()
                print(f"✓ File set to public: {result.get('public_url')}")
                return result
            else:
                error_text = await response.text()
                print(f"✗ Error: {response.status} - {error_text}")
                return None

# Usage
asyncio.run(set_file_public_direct("your-file-key-here", is_public=True))
```

---

## Complete Updated SDK Example

Here's the complete updated `upload_file` method with public file support:

```python
async def upload_file(
    self,
    file_content: bytes,
    filename: str,
    folder: str,
    user_email: str,
    is_public: bool = True  # New parameter
) -> UploadResult:
    """Upload a file to Stream-Line file server
    
    Args:
        file_content: Binary content of the file
        filename: Name of the file
        folder: Folder path
        user_email: User email
        is_public: Whether the file should be publicly accessible (default: True)
    
    Returns:
        UploadResult with file information
    """
    if not self.service_token:
        raise ValueError("AUTH_SERVICE_TOKEN not configured")
    
    if not self.session:
        self.session = aiohttp.ClientSession()
    
    try:
        # Prepare headers
        headers = {
            "X-Service-Token": self.service_token,
            "Content-Type": "application/octet-stream"
        }
        
        # Prepare data
        data = aiohttp.FormData()
        data.add_field('file', file_content, filename=filename)
        data.add_field('folder', folder)
        data.add_field('user_email', user_email)
        data.add_field('is_public', 'true' if is_public else 'false')  # Add public flag
        
        # Upload file
        async with self.session.post(
            f"{self.base_url}/v1/files/upload",
            headers=headers,
            data=data
        ) as response:
            if response.status == 200:
                result_data = await response.json()
                
                # Generate file key and public URL
                file_key = result_data.get('file_key', hashlib.sha256(f"{folder}/{filename}".encode()).hexdigest()[:16])
                public_url = result_data.get('public_url', f"{self.base_url}/storage/{user_email}/{folder}/{filename}")
                
                return UploadResult(
                    file_key=file_key,
                    public_url=public_url,
                    size=len(file_content),
                    mime_type=self._get_mime_type(filename),
                    folder=folder,
                    filename=filename,
                    sha256=hashlib.sha256(file_content).hexdigest()
                )
            else:
                error_text = await response.text()
                raise Exception(f"Upload failed: {response.status} - {error_text}")
                
    except Exception as e:
        logger.error(f"Failed to upload file {filename}: {e}")
        raise
```

---

## Updated upload_files Method

Also update the `upload_files` method to support public files:

```python
async def upload_files(
    self,
    files: List[Dict[str, Any]],
    user_email: str,
    is_public: bool = True  # Add this parameter
) -> List[UploadResult]:
    """Upload multiple files
    
    Args:
        files: List of file dictionaries with 'content', 'filename', 'folder'
        user_email: User email
        is_public: Whether files should be publicly accessible (default: True)
    """
    results = []
    for file_info in files:
        try:
            result = await self.upload_file(
                file_content=file_info['content'],
                filename=file_info['filename'],
                folder=file_info['folder'],
                user_email=user_email,
                is_public=is_public  # Pass the public flag
            )
            results.append(result)
        except Exception as e:
            logger.error(f"Failed to upload {file_info.get('filename', 'unknown')}: {e}")
            results.append(UploadResult(
                file_key="",
                public_url="",
                size=0,
                mime_type="",
                folder=file_info.get('folder', ''),
                filename=file_info.get('filename', ''),
                sha256=""
            ))
    return results
```

---

## Complete Working Example

```python
"""
Complete example: Upload files and make them public
"""

import asyncio
import os
from dotenv import load_dotenv
from streamline_file_uploader import StreamlineFileUploader

load_dotenv()

async def main():
    async with StreamlineFileUploader() as uploader:
        # Example 1: Upload single file as public
        print("Uploading single file as public...")
        with open("image.jpg", "rb") as f:
            file_content = f.read()
        
        result = await uploader.upload_file(
            file_content=file_content,
            filename="image.jpg",
            folder="public-images",
            user_email="user@example.com",
            is_public=True  # Make it public
        )
        
        print(f"✓ Uploaded: {result.public_url}")
        print(f"  File Key: {result.file_key}")
        print(f"  Public URL: {result.public_url}")
        
        # Example 2: Upload multiple files as public
        print("\nUploading multiple files as public...")
        files = [
            {
                "content": b"File 1 content",
                "filename": "file1.txt",
                "folder": "public-docs"
            },
            {
                "content": b"File 2 content",
                "filename": "file2.txt",
                "folder": "public-docs"
            }
        ]
        
        results = await uploader.upload_files(
            files=files,
            user_email="user@example.com",
            is_public=True  # Make all files public
        )
        
        for result in results:
            if result.file_key:
                print(f"✓ {result.filename}: {result.public_url}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Troubleshooting

### Issue: Files are not accessible publicly

**Possible Solutions**:

1. **Check if `is_public` parameter is being sent**:
   ```python
   # Debug: Check what's being sent
   print(f"is_public value: {is_public}")
   print(f"Form data: {data}")
   ```

2. **Verify API endpoint supports public files**:
   - Check if the API endpoint `/v1/files/upload` accepts `is_public` parameter
   - Contact Stream-Line AI support to confirm the parameter name

3. **Try alternative parameter names**:
   ```python
   # Try different parameter names
   data.add_field('public', 'true')
   # or
   data.add_field('make_public', 'true')
   # or
   data.add_field('public_access', 'true')
   ```

4. **Check file permissions after upload**:
   ```python
   # After upload, verify the file is public
   # Try accessing the public_url directly
   import requests
   response = requests.get(result.public_url)
   if response.status_code == 200:
       print("File is publicly accessible")
   else:
       print(f"File is not public: {response.status_code}")
   ```

### Issue: API returns error when setting is_public

**Check**:
1. API endpoint might use different parameter name
2. API might require separate endpoint to set public status
3. Your service token might not have permission to set public files

**Solution**: Contact Stream-Line AI support to confirm:
- Correct parameter name for public files
- API endpoint for setting files as public
- Required permissions for public file access

---

## Alternative: Using Public Folder Structure

If the API doesn't support `is_public` parameter, you can organize files in a public folder:

```python
async def upload_to_public_folder():
    """Upload files to a public folder structure"""
    async with StreamlineFileUploader() as uploader:
        # Upload to public folder
        result = await uploader.upload_file(
            file_content=file_content,
            filename="image.jpg",
            folder="public/my-folder",  # Use "public" prefix
            user_email="user@example.com"
        )
        
        # Files in "public" folder are typically publicly accessible
        return result
```

---

## Testing Public File Access

```python
import asyncio
import requests
from streamline_file_uploader import StreamlineFileUploader

async def test_public_access():
    async with StreamlineFileUploader() as uploader:
        # Upload file as public
        with open("test.jpg", "rb") as f:
            result = await uploader.upload_file(
                file_content=f.read(),
                filename="test.jpg",
                folder="test",
                user_email="user@example.com",
                is_public=True
            )
        
        # Test if file is publicly accessible
        try:
            response = requests.get(result.public_url, timeout=10)
            if response.status_code == 200:
                print(f"✓ File is publicly accessible: {result.public_url}")
                print(f"  Content-Type: {response.headers.get('Content-Type')}")
                print(f"  Size: {len(response.content)} bytes")
            else:
                print(f"✗ File is not public: HTTP {response.status_code}")
        except Exception as e:
            print(f"✗ Error accessing file: {e}")

asyncio.run(test_public_access())
```

---

## Summary

1. **During Upload**: Add `is_public=True` parameter to `upload_file()` method
2. **After Upload**: Use `set_file_public()` method or direct API call
3. **Folder Structure**: Upload to "public" folder if API supports it
4. **Testing**: Always test public URL accessibility after upload

---

**Note**: If you're still having issues, contact Stream-Line AI support to confirm:
- The correct API parameter name for public files
- Whether your service token has permissions for public file access
- The exact API endpoint and format for setting files as public

---

**Last Updated**: 2025-01-28  
**Version**: 1.0

