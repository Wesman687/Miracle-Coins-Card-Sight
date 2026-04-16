"""
Stream-Line File Uploader Client
Based on the working implementation from MC-FILE-001
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
                # Create a failed result
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


