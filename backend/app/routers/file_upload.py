"""
File Upload API Router for Miracle Coins CoinSync Pro
Provides endpoints for uploading and managing coin images and documents
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import JSONResponse
from typing import Optional, List
from sqlalchemy.orm import Session
from pydantic import BaseModel
import logging

from app.database import get_db
from app.services.file_upload_service import FileUploadService, UploadResult
from app.auth import get_current_admin_user

logger = logging.getLogger(__name__)

router = APIRouter()

class FileUploadResponse(BaseModel):
    """Response model for file upload operations"""
    success: bool
    data: Optional[UploadResult] = None
    message: str
    error: Optional[str] = None

class FileListResponse(BaseModel):
    """Response model for file listing operations"""
    success: bool
    data: List[dict] = []
    message: str
    error: Optional[str] = None

class FolderStatsResponse(BaseModel):
    """Response model for folder statistics"""
    success: bool
    data: Optional[dict] = None
    message: str
    error: Optional[str] = None

class BatchUploadRequest(BaseModel):
    """Request model for batch upload operations"""
    files: List[dict]
    collection: str
    year: Optional[int] = None
    sku: Optional[str] = None
    user_email: Optional[str] = None

class BatchUploadResponse(BaseModel):
    """Response model for batch upload operations"""
    success: bool
    data: List[Optional[UploadResult]] = []
    message: str
    error: Optional[str] = None

@router.get("/config", response_model=dict)
async def get_upload_config(
    current_user: dict = Depends(get_current_admin_user)
):
    """Get file upload service configuration status"""
    try:
        service = FileUploadService()
        config = service.get_configuration_status()
        
        return {
            "success": True,
            "data": config,
            "message": "Configuration retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Failed to get upload config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload/image", response_model=FileUploadResponse)
async def upload_coin_image(
    file: UploadFile = File(...),
    collection: str = Form(...),
    sku: Optional[str] = Form(None),
    user_email: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_admin_user)
):
    """Upload a coin image with organized folder structure"""
    try:
        # Read file content
        file_content = await file.read()
        
        service = FileUploadService()
        if not service.is_configured():
            return FileUploadResponse(
                success=False,
                message="File upload service not configured - AUTH_SERVICE_TOKEN required",
                error="Configuration error"
            )
        
        # Upload the file
        result = await service.upload_coin_image(
            file_content=file_content,
            filename=file.filename,
            collection=collection,
            sku=sku,
            user_email=user_email
        )
        
        if result:
            return FileUploadResponse(
                success=True,
                data=result,
                message=f"Image uploaded successfully to {result.folder}"
            )
        else:
            return FileUploadResponse(
                success=False,
                message="Failed to upload image",
                error="Upload failed"
            )
            
    except Exception as e:
        logger.error(f"Failed to upload coin image: {e}")
        return FileUploadResponse(
            success=False,
            message="Internal server error during upload",
            error=str(e)
        )

@router.post("/upload/document", response_model=FileUploadResponse)
async def upload_coin_document(
    file: UploadFile = File(...),
    collection: str = Form(...),
    year: Optional[int] = Form(None),
    sku: Optional[str] = Form(None),
    user_email: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_admin_user)
):
    """Upload a coin document (certificate, appraisal, etc.) with organized folder structure"""
    try:
        # Read file content
        file_content = await file.read()
        
        service = FileUploadService()
        if not service.is_configured():
            return FileUploadResponse(
                success=False,
                message="File upload service not configured - AUTH_SERVICE_TOKEN required",
                error="Configuration error"
            )
        
        # Upload the file
        result = await service.upload_coin_document(
            file_content=file_content,
            filename=file.filename,
            collection=collection,
            year=year,
            sku=sku,
            user_email=user_email
        )
        
        if result:
            return FileUploadResponse(
                success=True,
                data=result,
                message=f"Document uploaded successfully to {result.folder}"
            )
        else:
            return FileUploadResponse(
                success=False,
                message="Failed to upload document",
                error="Upload failed"
            )
            
    except Exception as e:
        logger.error(f"Failed to upload coin document: {e}")
        return FileUploadResponse(
            success=False,
            message="Internal server error during upload",
            error=str(e)
        )

@router.post("/upload/batch", response_model=BatchUploadResponse)
async def batch_upload_files(
    request: BatchUploadRequest,
    current_user: dict = Depends(get_current_admin_user)
):
    """Upload multiple files for a coin"""
    try:
        service = FileUploadService()
        if not service.is_configured():
            return BatchUploadResponse(
                success=False,
                message="File upload service not configured - AUTH_SERVICE_TOKEN required",
                error="Configuration error"
            )
        
        # Upload files
        results = await service.batch_upload_coin_files(
            files=request.files,
            collection=request.collection,
            year=request.year,
            sku=request.sku,
            user_email=request.user_email
        )
        
        successful_uploads = sum(1 for result in results if result is not None)
        
        return BatchUploadResponse(
            success=successful_uploads > 0,
            data=results,
            message=f"Batch upload completed: {successful_uploads}/{len(request.files)} files uploaded successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to batch upload files: {e}")
        return BatchUploadResponse(
            success=False,
            message="Internal server error during batch upload",
            error=str(e)
        )

@router.get("/list", response_model=FileListResponse)
async def list_coin_files(
    collection: Optional[str] = Query(None, description="Collection name to filter by"),
    year: Optional[int] = Query(None, description="Year to filter by"),
    sku: Optional[str] = Query(None, description="SKU to filter by"),
    user_email: Optional[str] = Query(None, description="User email to filter by"),
    current_user: dict = Depends(get_current_admin_user)
):
    """List files for a specific coin or collection"""
    try:
        service = FileUploadService()
        if not service.is_configured():
            return FileListResponse(
                success=False,
                message="File upload service not configured - AUTH_SERVICE_TOKEN required",
                error="Configuration error"
            )
        
        files = await service.list_coin_files(
            collection=collection,
            year=year,
            sku=sku,
            user_email=user_email
        )
        
        return FileListResponse(
            success=True,
            data=files,
            message=f"Found {len(files)} files"
        )
        
    except Exception as e:
        logger.error(f"Failed to list coin files: {e}")
        return FileListResponse(
            success=False,
            message="Internal server error during file listing",
            error=str(e)
        )

@router.get("/search", response_model=FileListResponse)
async def search_coin_files(
    filename_pattern: Optional[str] = Query(None, description="Pattern to match in filename"),
    mime_type: Optional[str] = Query(None, description="MIME type to filter by"),
    collection: Optional[str] = Query(None, description="Collection to search in"),
    user_email: Optional[str] = Query(None, description="User email to filter by"),
    current_user: dict = Depends(get_current_admin_user)
):
    """Search for coin files with specific criteria"""
    try:
        service = FileUploadService()
        if not service.is_configured():
            return FileListResponse(
                success=False,
                message="File upload service not configured - AUTH_SERVICE_TOKEN required",
                error="Configuration error"
            )
        
        files = await service.search_coin_files(
            filename_pattern=filename_pattern,
            mime_type=mime_type,
            collection=collection,
            user_email=user_email
        )
        
        return FileListResponse(
            success=True,
            data=files,
            message=f"Found {len(files)} files matching search criteria"
        )
        
    except Exception as e:
        logger.error(f"Failed to search coin files: {e}")
        return FileListResponse(
            success=False,
            message="Internal server error during file search",
            error=str(e)
        )

@router.get("/download-url")
async def get_download_url(
    file_key: str = Query(..., description="Unique key of the file"),
    current_user: dict = Depends(get_current_admin_user)
):
    """Get download URL for a file"""
    try:
        service = FileUploadService()
        if not service.is_configured():
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": "File upload service not configured - AUTH_SERVICE_TOKEN required",
                    "error": "Configuration error"
                }
            )
        
        download_url = await service.get_download_url(file_key)
        
        if download_url:
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "data": {"download_url": download_url},
                    "message": "Download URL generated successfully"
                }
            )
        else:
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "message": "Failed to generate download URL",
                    "error": "File not found or access denied"
                }
            )
            
    except Exception as e:
        logger.error(f"Failed to get download URL: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "Internal server error",
                "error": str(e)
            }
        )

@router.get("/stats", response_model=FolderStatsResponse)
async def get_folder_stats(
    collection: Optional[str] = Query(None, description="Collection name"),
    year: Optional[int] = Query(None, description="Year of the coin"),
    sku: Optional[str] = Query(None, description="SKU of the coin"),
    user_email: Optional[str] = Query(None, description="User email to filter by"),
    current_user: dict = Depends(get_current_admin_user)
):
    """Get statistics for a coin folder"""
    try:
        service = FileUploadService()
        if not service.is_configured():
            return FolderStatsResponse(
                success=False,
                message="File upload service not configured - AUTH_SERVICE_TOKEN required",
                error="Configuration error"
            )
        
        stats = await service.get_folder_stats(
            collection=collection,
            year=year,
            sku=sku,
            user_email=user_email
        )
        
        if stats:
            return FolderStatsResponse(
                success=True,
                data=stats,
                message="Folder statistics retrieved successfully"
            )
        else:
            return FolderStatsResponse(
                success=False,
                message="Failed to retrieve folder statistics",
                error="Folder not found or access denied"
            )
            
    except Exception as e:
        logger.error(f"Failed to get folder stats: {e}")
        return FolderStatsResponse(
            success=False,
            message="Internal server error during stats retrieval",
            error=str(e)
        )
