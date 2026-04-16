"""
File Upload Service for Miracle Coins CoinSync Pro
Integrates with Stream-Line File Uploader for organized coin image storage
"""

import asyncio
import os
from typing import Optional, List, Dict, Any
from datetime import datetime
from streamline_file_uploader import StreamlineFileUploader
from pydantic import BaseModel
import logging

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

class FileUploadService:
    """Service for uploading and managing coin images and documents"""
    
    def __init__(self):
        self.base_url = os.getenv("UPLOAD_BASE_URL", "https://file-server.stream-lineai.com")
        self.service_token = os.getenv("AUTH_SERVICE_TOKEN")
        self.default_user_email = "coins@miracle-coins.com"
        
        if not self.service_token:
            logger.warning("AUTH_SERVICE_TOKEN not set - file upload functionality will be limited")
    
    def _get_folder_structure(self, collection: str, sku: Optional[str] = None) -> str:
        """
        Generate organized folder structure for coin files
        
        Args:
            collection: Collection name (e.g., 'mercury-dimes', 'morgan-dollars')
            sku: SKU of the coin (optional)
        
        Returns:
            Organized folder path
        """
        folder_parts = ["coins", collection]
        
        if sku:
            folder_parts.append(sku)
        
        return "/".join(folder_parts)
    
    async def upload_coin_image(
        self,
        file_content: bytes,
        filename: str,
        collection: str,
        sku: Optional[str] = None,
        user_email: Optional[str] = None
    ) -> Optional[UploadResult]:
        """
        Upload a coin image with organized folder structure
        
        Args:
            file_content: Binary content of the image file
            filename: Name of the file
            collection: Collection name (e.g., 'mercury-dimes')
            sku: SKU of the coin
            user_email: User email (defaults to coins@miracle-coins.com)
        
        Returns:
            UploadResult if successful, None if failed
        """
        if not self.service_token:
            logger.error("Cannot upload file: AUTH_SERVICE_TOKEN not set")
            return None
        
        try:
            folder = self._get_folder_structure(collection, sku=sku)
            user_email = user_email or self.default_user_email
            
            uploader = StreamlineFileUploader(service_token=self.service_token)
            
            result = await uploader.upload_file(
                file_content=file_content,
                filename=filename,
                folder=folder,
                user_email=user_email
            )
            
            await uploader.close()
            
            logger.info(f"Successfully uploaded coin image: {filename} to {folder}")
            return UploadResult(
                file_key=result.file_key,
                public_url=result.public_url,
                size=result.size,
                mime_type=result.mime_type,
                folder=result.folder,
                filename=result.filename,
                sha256=result.sha256
            )
                
        except Exception as e:
            logger.error(f"Failed to upload coin image {filename}: {e}")
            return None
    
    async def upload_coin_document(
        self,
        file_content: bytes,
        filename: str,
        collection: str,
        year: Optional[int] = None,
        sku: Optional[str] = None,
        user_email: Optional[str] = None
    ) -> Optional[UploadResult]:
        """
        Upload a coin document (certificate, appraisal, etc.) with organized folder structure
        
        Args:
            file_content: Binary content of the document file
            filename: Name of the file
            collection: Collection name
            year: Year of the coin
            sku: SKU of the coin
            user_email: User email (defaults to coins@miracle-coins.com)
        
        Returns:
            UploadResult if successful, None if failed
        """
        if not self.service_token:
            logger.error("Cannot upload file: AUTH_SERVICE_TOKEN not set")
            return None
        
        try:
            folder = self._get_folder_structure(collection, year, sku)
            folder = f"{folder}/documents"  # Add documents subfolder
            user_email = user_email or self.default_user_email
            
            uploader = StreamlineFileUploader(service_token=self.service_token)
            
            result = await uploader.upload_file(
                file_content=file_content,
                filename=filename,
                folder=folder,
                user_email=user_email
            )
            
            await uploader.close()
            
            logger.info(f"Successfully uploaded coin document: {filename} to {folder}")
            return UploadResult(
                file_key=result.file_key,
                public_url=result.public_url,
                size=result.size,
                mime_type=result.mime_type,
                folder=result.folder,
                filename=result.filename,
                sha256=result.sha256
            )
                
        except Exception as e:
            logger.error(f"Failed to upload coin document {filename}: {e}")
            return None
    
    async def list_coin_files(
        self,
        collection: Optional[str] = None,
        year: Optional[int] = None,
        sku: Optional[str] = None,
        user_email: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List files for a specific coin or collection
        
        Args:
            collection: Collection name to filter by
            year: Year to filter by
            sku: SKU to filter by
            user_email: User email (defaults to coins@miracle-coins.com)
        
        Returns:
            List of file information dictionaries
        """
        if not self.service_token:
            logger.error("Cannot list files: AUTH_SERVICE_TOKEN not set")
            return []
        
        try:
            folder = self._get_folder_structure(collection, year, sku) if collection else "coins"
            user_email = user_email or self.default_user_email
            
            uploader = StreamlineFileUploader(service_token=self.service_token)
            
            files = await uploader.list_files(
                folder=folder,
                user_email=user_email
            )
            
            await uploader.close()
            
            logger.info(f"Found {len(files)} files in {folder}")
            return files
                
        except Exception as e:
            logger.error(f"Failed to list files in {folder}: {e}")
            return []
    
    async def search_coin_files(
        self,
        filename_pattern: Optional[str] = None,
        mime_type: Optional[str] = None,
        collection: Optional[str] = None,
        user_email: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for coin files with specific criteria
        
        Args:
            filename_pattern: Pattern to match in filename
            mime_type: MIME type to filter by
            collection: Collection to search in
            user_email: User email (defaults to coins@miracle-coins.com)
        
        Returns:
            List of matching file information dictionaries
        """
        if not self.service_token:
            logger.error("Cannot search files: AUTH_SERVICE_TOKEN not set")
            return []
        
        try:
            folder = f"coins/{collection}" if collection else "coins"
            user_email = user_email or self.default_user_email
            
            uploader = StreamlineFileUploader(service_token=self.service_token)
            
            files = await uploader.search_files(
                filename_pattern=filename_pattern,
                mime_type=mime_type,
                folder=folder,
                user_email=user_email
            )
            
            await uploader.close()
            
            logger.info(f"Found {len(files)} files matching search criteria")
            return files
                
        except Exception as e:
            logger.error(f"Failed to search files: {e}")
            return []
    
    async def get_download_url(self, file_key: str) -> Optional[str]:
        """
        Get signed download URL for a file
        
        Args:
            file_key: Unique key of the file
        
        Returns:
            Signed download URL if successful, None if failed
        """
        if not self.service_token:
            logger.error("Cannot get download URL: AUTH_SERVICE_TOKEN not set")
            return None
        
        try:
            import requests
            
            # Get signed URL using direct API call
            headers = {"X-Service-Token": self.service_token}
            response = requests.get(
                f"{self.base_url}/v1/files/signed-url",
                headers=headers,
                params={"key": file_key}
            )
            
            if response.status_code == 200:
                signed_url = response.json()["url"]
                logger.info(f"Generated signed download URL for file: {file_key}")
                return signed_url
            else:
                logger.error(f"Failed to get signed URL: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get download URL for {file_key}: {e}")
            return None
    
    async def get_folder_stats(
        self,
        collection: Optional[str] = None,
        year: Optional[int] = None,
        sku: Optional[str] = None,
        user_email: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get statistics for a coin folder
        
        Args:
            collection: Collection name
            year: Year of the coin
            sku: SKU of the coin
            user_email: User email (defaults to coins@miracle-coins.com)
        
        Returns:
            Folder statistics dictionary if successful, None if failed
        """
        if not self.service_token:
            logger.error("Cannot get folder stats: AUTH_SERVICE_TOKEN not set")
            return None
        
        try:
            folder = self._get_folder_structure(collection, year, sku) if collection else "coins"
            user_email = user_email or self.default_user_email
            
            uploader = StreamlineFileUploader(service_token=self.service_token)
            
            stats = await uploader.get_folder_stats(
                user_email=user_email,
                folder=folder
            )
            
            await uploader.close()
            
            logger.info(f"Retrieved folder stats for {folder}")
            return stats
                
        except Exception as e:
            logger.error(f"Failed to get folder stats for {folder}: {e}")
            return None
    
    async def batch_upload_coin_files(
        self,
        files: List[Dict[str, Any]],
        collection: str,
        year: Optional[int] = None,
        sku: Optional[str] = None,
        user_email: Optional[str] = None
    ) -> List[Optional[UploadResult]]:
        """
        Upload multiple files for a coin
        
        Args:
            files: List of file dictionaries with 'content', 'filename', and optional 'folder_suffix'
            collection: Collection name
            year: Year of the coin
            sku: SKU of the coin
            user_email: User email (defaults to coins@miracle-coins.com)
        
        Returns:
            List of UploadResult objects (None for failed uploads)
        """
        if not self.service_token:
            logger.error("Cannot batch upload files: AUTH_SERVICE_TOKEN not set")
            return [None] * len(files)
        
        try:
            base_folder = self._get_folder_structure(collection, year, sku)
            user_email = user_email or self.default_user_email
            
            uploader = StreamlineFileUploader(service_token=self.service_token)
            
            # Prepare files for batch upload
            batch_files = []
            for file_info in files:
                folder_suffix = file_info.get('folder_suffix', '')
                folder = f"{base_folder}/{folder_suffix}".rstrip('/')
                
                batch_files.append({
                    'content': file_info['content'],
                    'filename': file_info['filename'],
                    'folder': folder
                })
            
            results = await uploader.upload_files(
                files=batch_files,
                user_email=user_email
            )
            
            await uploader.close()
            
            logger.info(f"Successfully batch uploaded {len(results)} files to {base_folder}")
            return [
                UploadResult(
                    file_key=result.file_key,
                    public_url=result.public_url,
                    size=result.size,
                    mime_type=result.mime_type,
                    folder=result.folder,
                    filename=result.filename,
                    sha256=result.sha256
                ) for result in results
            ]
                
        except Exception as e:
            logger.error(f"Failed to batch upload files: {e}")
            return [None] * len(files)
    
    def is_configured(self) -> bool:
        """Check if the service is properly configured"""
        return self.service_token is not None
    
    def get_configuration_status(self) -> Dict[str, Any]:
        """Get configuration status of the service"""
        return {
            "base_url": self.base_url,
            "service_token_configured": self.service_token is not None,
            "default_user_email": self.default_user_email,
            "service_ready": self.is_configured()
        }