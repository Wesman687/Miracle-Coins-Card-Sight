# Stream-Line File Server SDK - Installation & Usage Guide

## Overview

This guide provides step-by-step instructions for downloading, installing, and using the Stream-Line File Server SDK in your own application.

---

## Method 1: Copy SDK Files (Recommended for Quick Start)

### Step 1: Download the SDK Files

Copy these files from the Miracle Coins project to your new project:

**Required Files**:
1. `streamline_file_uploader.py` - Main SDK client
2. (Optional) `file_upload_service.py` - Higher-level service wrapper

**File Locations**:
- Source: `backend/streamline_file_uploader.py`
- Source: `backend/app/services/file_upload_service.py` (optional)

**Download Instructions**:

```bash
# Option A: Install via pip from GitHub (Recommended)
pip install git+https://github.com/streamline-ai/file-uploader.git

# Option B: Clone the repository
git clone https://github.com/streamline-ai/file-uploader.git
cd file-uploader
# Copy the SDK file to your project
cp streamline_file_uploader.py /path/to/your-project/

# Option C: Copy files directly from local project
# Copy streamline_file_uploader.py to your project directory
```

### Step 2: Create Project Structure

```
your-project/
├── streamline_file_uploader.py    # SDK file
├── requirements.txt                # Dependencies
├── .env                            # Environment variables
└── main.py                         # Your application
```

### Step 3: Install Dependencies

Create `requirements.txt`:

```txt
aiohttp>=3.8.0
pydantic>=2.0.0
python-dotenv>=1.0.0
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Or install individually:

```bash
pip install aiohttp pydantic python-dotenv
```

### Step 4: Configure Environment

Create `.env` file:

```env
UPLOAD_BASE_URL=https://file-server.stream-lineai.com
AUTH_SERVICE_TOKEN=your_service_token_here
```

**Getting Your Service Token**:
- Contact Stream-Line AI support to obtain your `AUTH_SERVICE_TOKEN`
- This token authenticates your application with the file server

### Step 5: Basic Usage Example

Create `main.py`:

```python
import asyncio
import os
from dotenv import load_dotenv
from streamline_file_uploader import StreamlineFileUploader

# Load environment variables
load_dotenv()

async def main():
    # Initialize uploader
    async with StreamlineFileUploader() as uploader:
        # Read file to upload
        with open("test_image.jpg", "rb") as f:
            file_content = f.read()
        
        # Upload file
        result = await uploader.upload_file(
            file_content=file_content,
            filename="test_image.jpg",
            folder="my-folder",
            user_email="user@example.com"
        )
        
        print(f"✓ Upload successful!")
        print(f"  Public URL: {result.public_url}")
        print(f"  File Key: {result.file_key}")
        print(f"  Size: {result.size} bytes")

if __name__ == "__main__":
    asyncio.run(main())
```

Run:

```bash
python main.py
```

---

## Method 2: Install from GitHub (Recommended)

### Quick Install

```bash
pip install git+https://github.com/streamline-ai/file-uploader.git
```

### Usage After Installation

```python
from streamline_file_uploader import StreamlineFileUploader
import asyncio

async def upload_file():
    async with StreamlineFileUploader() as uploader:
        # Your upload code here
        pass

asyncio.run(upload_file())
```

### Update to Latest Version

```bash
pip install --upgrade git+https://github.com/streamline-ai/file-uploader.git
```

---

## Method 3: Install as Python Package (Local)

### Step 1: Create Package Structure

```
streamline-fileserver-sdk/
├── setup.py
├── README.md
├── streamline_file_uploader/
│   ├── __init__.py
│   └── client.py          # Copy streamline_file_uploader.py content here
└── requirements.txt
```

### Step 2: Create setup.py

```python
from setuptools import setup, find_packages

setup(
    name="streamline-fileserver-sdk",
    version="1.0.0",
    description="Stream-Line File Server SDK",
    author="Your Name",
    packages=find_packages(),
    install_requires=[
        "aiohttp>=3.8.0",
        "pydantic>=2.0.0",
        "python-dotenv>=1.0.0",
    ],
    python_requires=">=3.8",
)
```

### Step 3: Install Package

```bash
# Install in development mode
pip install -e .

# Or install from directory
pip install /path/to/streamline-fileserver-sdk
```

### Step 4: Use in Your Project

```python
from streamline_file_uploader.client import StreamlineFileUploader
import asyncio

async def upload_file():
    async with StreamlineFileUploader() as uploader:
        # Your upload code here
        pass

asyncio.run(upload_file())
```

---

## Method 3: Download from Source Code

### Step 1: Get the SDK Code

**Option A: Install via pip from GitHub (Recommended)**

```bash
# Install directly from GitHub
pip install git+https://github.com/streamline-ai/file-uploader.git
```

Then import in your code:
```python
from streamline_file_uploader import StreamlineFileUploader
```

**Option B: Clone the Repository**

```bash
# Clone the repository
git clone https://github.com/streamline-ai/file-uploader.git
cd file-uploader

# Copy the SDK file to your project
cp streamline_file_uploader.py /path/to/your-project/
```

**Option C: Download Raw File**

```bash
# Using curl
curl -O https://raw.githubusercontent.com/streamline-ai/file-uploader/main/streamline_file_uploader.py

# Using wget
wget https://raw.githubusercontent.com/streamline-ai/file-uploader/main/streamline_file_uploader.py
```

**Option C: Copy File Content**

1. Open `backend/streamline_file_uploader.py` from the Miracle Coins project
2. Copy the entire file content
3. Create `streamline_file_uploader.py` in your project
4. Paste the content

### Step 2: Save the SDK File

Save the content as `streamline_file_uploader.py` in your project root:

```python
# streamline_file_uploader.py
"""
Stream-Line File Uploader Client
"""

import asyncio
import aiohttp
import os
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import logging
import hashlib

logger = logging.getLogger(__name__)

class UploadResult(BaseModel):
    """Result of a file upload operation"""
    file_key: str
    public_url: str
    size: int
    mime_type: str
    folder: str
    filename: str
    sha256: str

class StreamlineFileUploader:
    """Stream-Line File Uploader Client"""
    
    def __init__(self, service_token: Optional[str] = None):
        self.service_token = service_token or os.getenv("AUTH_SERVICE_TOKEN")
        self.base_url = os.getenv("UPLOAD_BASE_URL", "https://file-server.stream-lineai.com")
        self.session: Optional[aiohttp.ClientSession] = None
        
        if not self.service_token:
            logger.warning("AUTH_SERVICE_TOKEN not set - file upload functionality will be limited")
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def upload_file(
        self,
        file_content: bytes,
        filename: str,
        folder: str,
        user_email: str
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
    
    async def upload_files(
        self,
        files: List[Dict[str, Any]],
        user_email: str
    ) -> List[UploadResult]:
        """Upload multiple files"""
        results = []
        for file_info in files:
            try:
                result = await self.upload_file(
                    file_content=file_info['content'],
                    filename=file_info['filename'],
                    folder=file_info['folder'],
                    user_email=user_email
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
    
    async def list_files(
        self,
        folder: str,
        user_email: str
    ) -> List[Dict[str, Any]]:
        """List files in a folder"""
        if not self.service_token or not self.session:
            return []
        
        try:
            headers = {"X-Service-Token": self.service_token}
            params = {"folder": folder, "user_email": user_email}
            
            async with self.session.get(
                f"{self.base_url}/v1/files/list",
                headers=headers,
                params=params
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to list files: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Failed to list files in {folder}: {e}")
            return []
    
    async def search_files(
        self,
        filename_pattern: Optional[str] = None,
        mime_type: Optional[str] = None,
        folder: str = "",
        user_email: str = ""
    ) -> List[Dict[str, Any]]:
        """Search for files"""
        if not self.service_token or not self.session:
            return []
        
        try:
            headers = {"X-Service-Token": self.service_token}
            params = {
                "folder": folder,
                "user_email": user_email
            }
            if filename_pattern:
                params["filename_pattern"] = filename_pattern
            if mime_type:
                params["mime_type"] = mime_type
            
            async with self.session.get(
                f"{self.base_url}/v1/files/search",
                headers=headers,
                params=params
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to search files: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Failed to search files: {e}")
            return []
    
    async def get_folder_stats(
        self,
        user_email: str,
        folder: str
    ) -> Optional[Dict[str, Any]]:
        """Get folder statistics"""
        if not self.service_token or not self.session:
            return None
        
        try:
            headers = {"X-Service-Token": self.service_token}
            params = {"folder": folder, "user_email": user_email}
            
            async with self.session.get(
                f"{self.base_url}/v1/files/stats",
                headers=headers,
                params=params
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to get folder stats: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Failed to get folder stats for {folder}: {e}")
            return None
    
    async def close(self):
        """Close the session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    def _get_mime_type(self, filename: str) -> str:
        """Get MIME type based on file extension"""
        ext = filename.lower().split('.')[-1] if '.' in filename else ''
        mime_types = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'webp': 'image/webp',
            'pdf': 'application/pdf',
            'txt': 'text/plain',
            'doc': 'application/msword',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        }
        return mime_types.get(ext, 'application/octet-stream')
```

---

## Complete Setup Example

### Project Structure

```
my-project/
├── streamline_file_uploader.py
├── requirements.txt
├── .env
├── .gitignore
└── app.py
```

### requirements.txt

```txt
aiohttp>=3.8.0
pydantic>=2.0.0
python-dotenv>=1.0.0
```

### .env

```env
UPLOAD_BASE_URL=https://file-server.stream-lineai.com
AUTH_SERVICE_TOKEN=your_token_here
```

### .gitignore

```gitignore
.env
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
venv/
env/
```

### app.py - Complete Example

```python
"""
Example application using Stream-Line File Server SDK
"""

import asyncio
import os
from dotenv import load_dotenv
from streamline_file_uploader import StreamlineFileUploader

# Load environment variables
load_dotenv()

async def upload_single_file():
    """Upload a single file"""
    print("Uploading single file...")
    
    async with StreamlineFileUploader() as uploader:
        # Read file
        with open("example.jpg", "rb") as f:
            file_content = f.read()
        
        # Upload
        result = await uploader.upload_file(
            file_content=file_content,
            filename="example.jpg",
            folder="my-folder",
            user_email="user@example.com"
        )
        
        print(f"✓ Uploaded: {result.public_url}")
        return result

async def upload_multiple_files():
    """Upload multiple files"""
    print("Uploading multiple files...")
    
    files = [
        {
            "content": b"File 1 content",
            "filename": "file1.txt",
            "folder": "my-folder"
        },
        {
            "content": b"File 2 content",
            "filename": "file2.txt",
            "folder": "my-folder"
        }
    ]
    
    async with StreamlineFileUploader() as uploader:
        results = await uploader.upload_files(
            files=files,
            user_email="user@example.com"
        )
        
        for result in results:
            if result.file_key:
                print(f"✓ Uploaded: {result.filename} -> {result.public_url}")
            else:
                print(f"✗ Failed: {result.filename}")

async def list_files():
    """List files in a folder"""
    print("Listing files...")
    
    async with StreamlineFileUploader() as uploader:
        files = await uploader.list_files(
            folder="my-folder",
            user_email="user@example.com"
        )
        
        print(f"Found {len(files)} files:")
        for file_info in files:
            print(f"  - {file_info.get('filename', 'unknown')}")

async def search_files():
    """Search for files"""
    print("Searching files...")
    
    async with StreamlineFileUploader() as uploader:
        files = await uploader.search_files(
            filename_pattern="*.jpg",
            mime_type="image/jpeg",
            folder="my-folder",
            user_email="user@example.com"
        )
        
        print(f"Found {len(files)} matching files")

async def get_stats():
    """Get folder statistics"""
    print("Getting folder stats...")
    
    async with StreamlineFileUploader() as uploader:
        stats = await uploader.get_folder_stats(
            user_email="user@example.com",
            folder="my-folder"
        )
        
        if stats:
            print(f"Folder stats: {stats}")
        else:
            print("No stats available")

async def main():
    """Main function"""
    # Check configuration
    token = os.getenv("AUTH_SERVICE_TOKEN")
    if not token:
        print("Error: AUTH_SERVICE_TOKEN not set in .env file")
        return
    
    print("Stream-Line File Server SDK Example")
    print("=" * 40)
    
    # Run examples
    try:
        # Uncomment the example you want to run:
        # await upload_single_file()
        # await upload_multiple_files()
        # await list_files()
        # await search_files()
        # await get_stats()
        
        print("\n✓ Examples completed")
    except Exception as e:
        print(f"\n✗ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Using in Different Frameworks

### Flask Example

```python
from flask import Flask, request, jsonify
import asyncio
from streamline_file_uploader import StreamlineFileUploader

app = Flask(__name__)

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    folder = request.form.get('folder', 'default')
    user_email = request.form.get('user_email', 'user@example.com')
    
    # Run async upload
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    async def do_upload():
        async with StreamlineFileUploader() as uploader:
            file_content = file.read()
            result = await uploader.upload_file(
                file_content=file_content,
                filename=file.filename,
                folder=folder,
                user_email=user_email
            )
            return result
    
    result = loop.run_until_complete(do_upload())
    loop.close()
    
    return jsonify({
        "success": True,
        "url": result.public_url,
        "file_key": result.file_key
    })

if __name__ == '__main__':
    app.run(debug=True)
```

### Django Example

```python
# views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import asyncio
from streamline_file_uploader import StreamlineFileUploader

@csrf_exempt
def upload_file(request):
    if request.method != 'POST':
        return JsonResponse({"error": "Method not allowed"}, status=405)
    
    file = request.FILES.get('file')
    if not file:
        return JsonResponse({"error": "No file provided"}, status=400)
    
    folder = request.POST.get('folder', 'default')
    user_email = request.POST.get('user_email', 'user@example.com')
    
    # Run async upload
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    async def do_upload():
        async with StreamlineFileUploader() as uploader:
            file_content = file.read()
            result = await uploader.upload_file(
                file_content=file_content,
                filename=file.name,
                folder=folder,
                user_email=user_email
            )
            return result
    
    result = loop.run_until_complete(do_upload())
    loop.close()
    
    return JsonResponse({
        "success": True,
        "url": result.public_url,
        "file_key": result.file_key
    })
```

### FastAPI Example

```python
from fastapi import FastAPI, UploadFile, File, Form
from streamline_file_uploader import StreamlineFileUploader
import asyncio

app = FastAPI()

@app.post("/upload")
async def upload(
    file: UploadFile = File(...),
    folder: str = Form("default"),
    user_email: str = Form("user@example.com")
):
    async with StreamlineFileUploader() as uploader:
        file_content = await file.read()
        result = await uploader.upload_file(
            file_content=file_content,
            filename=file.filename,
            folder=folder,
            user_email=user_email
        )
        
        return {
            "success": True,
            "url": result.public_url,
            "file_key": result.file_key
        }
```

---

## Quick Start Checklist

- [ ] Copy `streamline_file_uploader.py` to your project
- [ ] Create `requirements.txt` with dependencies
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Create `.env` file with `AUTH_SERVICE_TOKEN`
- [ ] Get service token from Stream-Line AI
- [ ] Test upload with example code
- [ ] Integrate into your application

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'aiohttp'"

**Solution**: Install dependencies
```bash
pip install aiohttp pydantic python-dotenv
```

### "AUTH_SERVICE_TOKEN not configured"

**Solution**: 
1. Create `.env` file
2. Add `AUTH_SERVICE_TOKEN=your_token_here`
3. Load with `load_dotenv()`

### "Upload failed: 401"

**Solution**: Check your service token is valid and has proper permissions

### Import Error

**Solution**: Ensure `streamline_file_uploader.py` is in your Python path or project directory

---

**Last Updated**: 2025-01-28  
**Version**: 1.0

