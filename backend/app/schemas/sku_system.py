"""
Two-Part SKU System Schemas
Format: [PREFIX]-[SEQUENCE] (e.g., ASE-001, MOR-002)
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime

class SKUPrefixBase(BaseModel):
    prefix: str = Field(..., min_length=2, max_length=20, description="SKU prefix (e.g., ASE, MOR)")
    description: Optional[str] = Field(None, description="Description of the prefix")
    auto_increment: bool = Field(True, description="Whether to auto-increment sequences")

class SKUPrefixCreate(SKUPrefixBase):
    pass

class SKUPrefixUpdate(BaseModel):
    prefix: Optional[str] = Field(None, min_length=2, max_length=20)
    description: Optional[str] = None
    auto_increment: Optional[bool] = None

class SKUPrefixResponse(SKUPrefixBase):
    id: int
    current_sequence: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class SKUSequenceBase(BaseModel):
    prefix: str = Field(..., min_length=2, max_length=20)
    sequence_number: int = Field(..., gt=0)
    coin_id: Optional[int] = None

class SKUSequenceCreate(SKUSequenceBase):
    pass

class SKUSequenceResponse(SKUSequenceBase):
    id: int
    used_at: datetime
    
    class Config:
        from_attributes = True

class SKUGenerationRequest(BaseModel):
    prefix: str = Field(..., min_length=2, max_length=20)
    count: int = Field(1, ge=1, le=10000, description="Number of SKUs to generate")

class SKUGenerationResponse(BaseModel):
    prefix: str
    start_sequence: int
    end_sequence: int
    skus: List[str]
    total_generated: int

class SKUBulkOperationRequest(BaseModel):
    prefix: str = Field(..., min_length=2, max_length=20)
    start_sequence: Optional[int] = Field(None, gt=0)
    count: int = Field(..., ge=1, le=10000)
    description: Optional[str] = None

class SKUBulkOperationResponse(BaseModel):
    operation_id: int
    prefix: str
    start_sequence: int
    end_sequence: int
    total_skus: int
    status: str
    created_at: datetime

class SKUStatsResponse(BaseModel):
    total_prefixes: int
    total_sequences_used: int
    most_used_prefix: Optional[str]
    least_used_prefix: Optional[str]
    recent_activity: List[dict]
