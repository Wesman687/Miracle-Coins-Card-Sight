# Simple: Upload File and Make It Public

## Step 1: Upload the File

```python
import asyncio
import os
from dotenv import load_dotenv
from streamline_file_uploader import StreamlineFileUploader

load_dotenv()

async def upload_file():
    async with StreamlineFileUploader() as uploader:
        # Read your file
        with open("your-file.jpg", "rb") as f:
            file_content = f.read()
        
        # Upload it
        result = await uploader.upload_file(
            file_content=file_content,
            filename="your-file.jpg",
            folder="my-folder",
            user_email="user@example.com"
        )
        
        print(f"Uploaded! File Key: {result.file_key}")
        print(f"Public URL: {result.public_url}")
        
        return result.file_key  # Save this for step 2

asyncio.run(upload_file())
```

## Step 2: Make It Public

```python
import asyncio
import aiohttp
import os
from dotenv import load_dotenv

load_dotenv()

async def make_file_public(file_key):
    service_token = os.getenv("AUTH_SERVICE_TOKEN")
    base_url = os.getenv("UPLOAD_BASE_URL", "https://file-server.stream-lineai.com")
    
    headers = {
        "X-Service-Token": service_token,
        "Content-Type": "application/json"
    }
    
    data = {
        "file_key": file_key,
        "is_public": True
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{base_url}/v1/files/set-public",
            headers=headers,
            json=data
        ) as response:
            if response.status == 200:
                print("✓ File is now public!")
                result = await response.json()
                return result
            else:
                error = await response.text()
                print(f"✗ Error: {response.status} - {error}")
                return None

# Use the file_key from step 1
asyncio.run(make_file_public("your-file-key-here"))
```

## Complete Example (Skip set-public if 405 Error)

**IMPORTANT**: If you get 405 error, the endpoint doesn't exist. Files are likely already public!

```python
import asyncio
import aiohttp
import requests
import os
from dotenv import load_dotenv
from streamline_file_uploader import StreamlineFileUploader

load_dotenv()

async def upload_and_make_public():
    # STEP 1: Upload
    async with StreamlineFileUploader() as uploader:
        with open("image.jpg", "rb") as f:
            file_content = f.read()
        
        result = await uploader.upload_file(
            file_content=file_content,
            filename="image.jpg",
            folder="my-folder",
            user_email="user@example.com"
        )
        
        print(f"✓ Uploaded: {result.public_url}")
        
        # STEP 2: Check if already public (BEFORE calling set-public)
        try:
            response = requests.get(result.public_url, timeout=10)
            if response.status_code == 200:
                print("✓ File is ALREADY PUBLIC - no set-public needed!")
                return result
        except:
            pass
        
        # STEP 3: Try set-public (only if not already public)
        service_token = os.getenv("AUTH_SERVICE_TOKEN")
        base_url = os.getenv("UPLOAD_BASE_URL", "https://file-server.stream-lineai.com")
        
        headers = {
            "X-Service-Token": service_token,
            "Content-Type": "application/json"
        }
        
        data = {
            "file_key": result.file_key,
            "is_public": True
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{base_url}/v1/files/set-public",
                headers=headers,
                json=data
            ) as response:
                if response.status == 200:
                    print("✓ Made file public via API")
                elif response.status == 405:
                    print("⚠ set-public endpoint returns 405 - endpoint may not exist")
                    print(f"  File might already be public. Check: {result.public_url}")
                else:
                    error = await response.text()
                    print(f"⚠ Response: {response.status} - {error}")
        
        return result

asyncio.run(upload_and_make_public())
```

## Even Simpler: Just Upload and Test

**If set-public gives 405, files are probably already public:**

```python
import asyncio
import requests
from streamline_file_uploader import StreamlineFileUploader

async def upload_simple():
    async with StreamlineFileUploader() as uploader:
        with open("image.jpg", "rb") as f:
            result = await uploader.upload_file(
                file_content=f.read(),
                filename="image.jpg",
                folder="my-folder",
                user_email="user@example.com"
            )
        
        # Test if public
        response = requests.get(result.public_url, timeout=10)
        if response.status_code == 200:
            print(f"✓ File is public: {result.public_url}")
        else:
            print(f"✗ File not accessible: HTTP {response.status_code}")

asyncio.run(upload_simple())
```

## That's It!

1. Upload file → Get `public_url`
2. Test `public_url` with `requests.get()` 
3. If 200, file is public! ✅
4. If 405 on set-public, ignore it - file is likely already public

