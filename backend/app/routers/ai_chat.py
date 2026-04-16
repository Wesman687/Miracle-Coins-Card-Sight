from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from app.database import get_db
from app.auth_utils import get_current_user
from app.services.ai_chat_service import AIChatService
from app.services.search_cache_service import SearchCacheService
import logging
import os
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(tags=["AI Chat"])

# Pydantic models
class ChatSearchRequest(BaseModel):
    query: str = Field(..., description="The coin description or question")
    preset: str = Field(default="quick_response", description="Search preset type")
    context: Optional[List[Dict[str, Any]]] = Field(default=None, description="Previous chat context")
    image_url: Optional[str] = Field(default=None, description="Image URL for analysis")
    image_analysis: Optional[bool] = Field(default=False, description="Whether to perform image analysis")

class ChatSearchResponse(BaseModel):
    response: str
    confidence_score: float
    pricing: Optional[Dict[str, Any]] = None
    cached: bool
    search_time_ms: float

class SearchHistoryItem(BaseModel):
    id: str
    query: str
    preset: str
    response: str
    confidence: float
    timestamp: str
    is_favorite: bool

class SearchHistoryResponse(BaseModel):
    history: List[SearchHistoryItem]

class FavoriteRequest(BaseModel):
    is_favorite: bool

class CacheStatsResponse(BaseModel):
    total_entries: int
    expired_entries: int
    active_entries: int
    total_hits: int
    popular_queries: List[Dict[str, Any]]
    cache_hit_rate: float

@router.post("/search", response_model=ChatSearchResponse)
async def search_coin(
    request: ChatSearchRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Search for coin pricing and information using AI chat"""
    
    if not current_user.get("isAdmin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        ai_chat_service = AIChatService(db)
        
        result = await ai_chat_service.search_coin(
            query=request.query,
            preset=request.preset,
            context=request.context,
            image_url=request.image_url,
            image_analysis=request.image_analysis
        )
        
        return ChatSearchResponse(**result)
        
    except Exception as e:
        logger.error(f"AI chat search error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process AI chat search"
        )

@router.get("/presets")
async def get_search_presets(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get available search presets"""
    
    if not current_user.get("isAdmin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    presets = [
        {
            "id": "quick_response",
            "name": "Quick Response",
            "description": "Fast pricing for auctions",
            "estimated_time": "5-10 seconds",
            "use_cases": ["Live auctions", "Quick price checks", "Fast decisions"]
        },
        {
            "id": "in_depth_analysis",
            "name": "In-Depth Analysis",
            "description": "Detailed analysis with scam detection",
            "estimated_time": "30-60 seconds",
            "use_cases": ["Detailed evaluation", "Scam detection", "Comprehensive analysis"]
        },
        {
            "id": "descriptions",
            "name": "Descriptions",
            "description": "Generate coin descriptions",
            "estimated_time": "10-15 seconds",
            "use_cases": ["Product descriptions", "Catalog entries", "Documentation"]
        },
        {
            "id": "year_mintage",
            "name": "Year & Mintage",
            "description": "Historical data and rarity",
            "estimated_time": "15-20 seconds",
            "use_cases": ["Historical research", "Rarity assessment", "Market trends"]
        },
        {
            "id": "pricing_only",
            "name": "Pricing Only",
            "description": "Just the price, nothing else",
            "estimated_time": "3-5 seconds",
            "use_cases": ["Quick price checks", "Simple queries", "Fast responses"]
        }
    ]
    
    return {"presets": presets}

@router.get("/history", response_model=SearchHistoryResponse)
async def get_search_history(
    limit: int = 50,
    offset: int = 0,
    favorites_only: bool = False,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get search history"""
    
    if not current_user.get("isAdmin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        # This would typically query a search_history table
        # For now, return mock data
        history = [
            {
                "id": "1",
                "query": "1921 Morgan Silver Dollar MS65",
                "preset": "quick_response",
                "response": "Quick Price: $45.00\nMelt Value: $19.35",
                "confidence": 0.85,
                "timestamp": "2025-01-28T10:30:00Z",
                "is_favorite": True
            },
            {
                "id": "2",
                "query": "1964 Kennedy Half Dollar",
                "preset": "pricing_only",
                "response": "$8.50",
                "confidence": 0.90,
                "timestamp": "2025-01-28T09:15:00Z",
                "is_favorite": False
            }
        ]
        
        if favorites_only:
            history = [item for item in history if item["is_favorite"]]
        
        return SearchHistoryResponse(history=history[offset:offset+limit])
        
    except Exception as e:
        logger.error(f"Error getting search history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get search history"
        )

class SaveHistoryRequest(BaseModel):
    query: str
    preset: str
    response: str
    confidence: float
    image_url: Optional[str] = None

@router.post("/history")
async def save_search_history(
    request: SaveHistoryRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Save search to history"""
    
    if not current_user.get("isAdmin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        # This would typically save to a search_history table
        # For now, just return success
        logger.info(f"Saving search history: query='{request.query}', preset='{request.preset}', image_url='{request.image_url}'")
        return {"message": "Search saved to history"}
        
    except Exception as e:
        logger.error(f"Error saving search history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save search history"
        )

@router.put("/history/{item_id}/favorite")
async def toggle_favorite(
    item_id: str,
    request: FavoriteRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Toggle favorite status for search history item"""
    
    if not current_user.get("isAdmin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        # This would typically update the search_history table
        # For now, just return success
        return {"message": "Favorite status updated"}
        
    except Exception as e:
        logger.error(f"Error toggling favorite: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update favorite status"
        )

@router.delete("/history/{item_id}")
async def delete_search_history(
    item_id: str,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete search history item"""
    
    if not current_user.get("isAdmin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        # This would typically delete from the search_history table
        # For now, just return success
        return {"message": "Search history item deleted"}
        
    except Exception as e:
        logger.error(f"Error deleting search history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete search history item"
        )

@router.delete("/history/clear")
async def clear_search_history(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Clear all search history"""
    
    if not current_user.get("isAdmin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        # This would typically clear the search_history table
        # For now, just return success
        return {"message": "All search history cleared"}
        
    except Exception as e:
        logger.error(f"Error clearing search history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear search history"
        )

@router.get("/cache/stats", response_model=CacheStatsResponse)
async def get_cache_stats(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get cache statistics"""
    
    if not current_user.get("isAdmin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        cache_service = SearchCacheService(db)
        stats = await cache_service.get_cache_stats()
        return CacheStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Error getting cache stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get cache statistics"
        )

@router.delete("/cache/clear")
async def clear_cache(
    preset: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Clear cache entries"""
    
    if not current_user.get("isAdmin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        cache_service = SearchCacheService(db)
        deleted_count = await cache_service.clear_cache(preset)
        
        return {
            "message": f"Cleared {deleted_count} cache entries",
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear cache"
        )

@router.post("/upload-image")
async def upload_image_for_analysis(
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Upload image for AI chat analysis"""
    
    if not current_user.get("isAdmin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be an image"
            )
        
        # Validate file size (10MB max)
        file_content = await file.read()
        if len(file_content) > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size must be less than 10MB"
            )
        
        # Create uploads directory if it doesn't exist
        upload_dir = "uploads/ai-chat"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        # Save file
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)
        
        # Generate public URL (for development, use local path)
        # In production, this would be a proper CDN URL
        public_url = f"/uploads/ai-chat/{unique_filename}"
        
        return {
            "success": True,
            "data": {
                "public_url": public_url,
                "filename": file.filename,
                "size": len(file_content),
                "content_type": file.content_type,
                "file_key": unique_filename
            },
            "message": "Image uploaded successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading image: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload image"
        )
