from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime

class CollectionImageBase(BaseModel):
    image_url: str = Field(..., min_length=1, max_length=500, description="URL of the image")
    alt_text: Optional[str] = Field(None, max_length=200, description="Alt text for accessibility")
    caption: Optional[str] = Field(None, description="Image caption")
    is_featured: bool = Field(False, description="Whether this is the featured image")
    sort_order: int = Field(0, ge=0, description="Sort order for display")

class CollectionImageCreate(CollectionImageBase):
    pass

class CollectionImageUpdate(BaseModel):
    alt_text: Optional[str] = Field(None, max_length=200)
    caption: Optional[str] = None
    is_featured: Optional[bool] = None
    sort_order: Optional[int] = Field(None, ge=0)

class CollectionImageResponse(CollectionImageBase):
    id: int
    collection_id: int
    file_size: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    mime_type: Optional[str] = None
    uploaded_at: datetime
    updated_at: datetime
    file_size_formatted: Optional[str] = None
    dimensions_formatted: Optional[str] = None

    class Config:
        from_attributes = True

class CollectionImageUpload(BaseModel):
    alt_text: Optional[str] = Field(None, max_length=200)
    caption: Optional[str] = None
    is_featured: bool = Field(False)

class CollectionImageBulkUpdate(BaseModel):
    images: List[CollectionImageUpdate] = Field(..., min_items=1)

class CollectionImageStats(BaseModel):
    total_images: int
    featured_images: int
    total_size: int
    total_size_formatted: str
    average_size: int
    average_size_formatted: str

    class Config:
        from_attributes = True

