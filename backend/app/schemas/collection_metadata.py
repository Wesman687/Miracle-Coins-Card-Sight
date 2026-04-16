from pydantic import BaseModel, Field, validator
from typing import Optional, List, Any, Union
from datetime import datetime
from enum import Enum

class MetadataFieldType(str, Enum):
    TEXT = "text"
    TEXTAREA = "textarea"
    NUMBER = "number"
    DATE = "date"
    BOOLEAN = "boolean"
    SELECT = "select"

class CollectionMetadataBase(BaseModel):
    field_name: str = Field(..., min_length=1, max_length=100, description="Internal field name")
    field_type: MetadataFieldType = Field(..., description="Type of metadata field")
    field_value: Optional[str] = Field(None, description="Field value as string")
    field_options: Optional[List[str]] = Field(None, description="Options for select fields")
    field_label: Optional[str] = Field(None, max_length=200, description="Display label")
    field_description: Optional[str] = Field(None, description="Help text")
    is_required: bool = Field(False, description="Whether field is required")
    is_searchable: bool = Field(True, description="Whether field can be searched")
    sort_order: int = Field(0, ge=0, description="Sort order for display")

class CollectionMetadataCreate(CollectionMetadataBase):
    pass

class CollectionMetadataUpdate(BaseModel):
    field_name: Optional[str] = Field(None, min_length=1, max_length=100)
    field_type: Optional[MetadataFieldType] = None
    field_value: Optional[str] = None
    field_options: Optional[List[str]] = None
    field_label: Optional[str] = Field(None, max_length=200)
    field_description: Optional[str] = None
    is_required: Optional[bool] = None
    is_searchable: Optional[bool] = None
    sort_order: Optional[int] = Field(None, ge=0)

class CollectionMetadataResponse(CollectionMetadataBase):
    id: int
    collection_id: int
    created_at: datetime
    updated_at: datetime
    formatted_value: Optional[Union[str, int, float, bool, datetime]] = None

    class Config:
        from_attributes = True

class CollectionMetadataBulkCreate(BaseModel):
    metadata_fields: List[CollectionMetadataCreate] = Field(..., min_items=1)

class CollectionMetadataBulkUpdate(BaseModel):
    metadata_fields: List[CollectionMetadataUpdate] = Field(..., min_items=1)

class MetadataFieldValueUpdate(BaseModel):
    field_value: Optional[str] = None

    @validator('field_value')
    def validate_field_value(cls, v, values):
        # Additional validation can be added here based on field type
        return v

class CollectionMetadataStats(BaseModel):
    total_fields: int
    required_fields: int
    searchable_fields: int
    field_types: dict = Field(..., description="Count of each field type")

    class Config:
        from_attributes = True

