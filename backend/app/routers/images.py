from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Form
from typing import Optional
from app.routers.file_upload import upload_coin_image
from app.auth import get_current_admin_user

router = APIRouter()

@router.post("/upload")
async def upload_image(
    file: UploadFile = File(...),
    coin_id: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Legacy image upload endpoint - redirects to file uploader
    This endpoint is maintained for backward compatibility
    """
    try:
        # Redirect to the file uploader with default collection
        collection = "general"
        sku = None
        
        # If coin_id is provided and not 'new', we could look up the coin's SKU
        # For now, we'll use a default collection
        
        # Call the file uploader function directly
        from app.services.file_upload_service import FileUploadService
        
        service = FileUploadService()
        if not service.is_configured():
            raise HTTPException(
                status_code=500, 
                detail="File upload service not configured - AUTH_SERVICE_TOKEN required"
            )
        
        # Read file content
        file_content = await file.read()
        
        # Upload the file
        result = await service.upload_coin_image(
            file_content=file_content,
            filename=file.filename,
            collection=collection,
            sku=sku
        )
        
        if result:
            return {
                "success": True,
                "data": result,
                "message": f"Image uploaded successfully to {result.folder}"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to upload image")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{image_id}")
async def get_image(image_id: int):
    return {"message": f"Get image {image_id} - not implemented yet"}