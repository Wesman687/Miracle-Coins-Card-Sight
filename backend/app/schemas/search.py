from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import date
from decimal import Decimal

class SearchRequest(BaseModel):
    query: Optional[str] = None
    year: Optional[int] = Field(None, ge=1800, le=2030)
    denomination: Optional[str] = None
    grade: Optional[str] = None
    category: Optional[str] = None
    min_price: Optional[Decimal] = Field(None, ge=0)
    max_price: Optional[Decimal] = Field(None, ge=0)
    min_paid_price: Optional[Decimal] = Field(None, ge=0)
    max_paid_price: Optional[Decimal] = Field(None, ge=0)
    is_silver: Optional[bool] = None
    status: Optional[str] = None
    mint_mark: Optional[str] = None
    silver_percent_min: Optional[Decimal] = Field(None, ge=0, le=100)
    silver_percent_max: Optional[Decimal] = Field(None, ge=0, le=100)
    silver_content_min: Optional[Decimal] = Field(None, ge=0)
    silver_content_max: Optional[Decimal] = Field(None, ge=0)
    created_after: Optional[date] = None
    created_before: Optional[date] = None
    sort_by: str = Field("created_at", pattern="^(created_at|updated_at|title|year|computed_price|paid_price)$")
    sort_order: str = Field("desc", pattern="^(asc|desc)$")
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)

class FacetItem(BaseModel):
    value: str
    count: int

class SearchFacets(BaseModel):
    years: List[FacetItem]
    denominations: List[FacetItem]
    grades: List[FacetItem]
    categories: List[FacetItem]
    mint_marks: List[FacetItem]
    status: List[FacetItem]

class SearchResponse(BaseModel):
    coins: List[Dict[str, Any]]
    total_count: int
    limit: int
    offset: int
    facets: SearchFacets
    search_criteria: Dict[str, Any]

class BulkOperationRequest(BaseModel):
    operation_type: str = Field(..., pattern="^(price_update|category_change|status_change|location_transfer)$")
    selected_coins: List[int] = Field(..., min_items=1)
    operation_data: Dict[str, Any]
    individual_tracking: bool = True

class BulkPriceUpdateData(BaseModel):
    strategy: str = Field(..., pattern="^(fixed|multiplier|profit_margin)$")
    price: Optional[Decimal] = Field(None, ge=0)
    multiplier: Optional[Decimal] = Field(None, ge=0.1, le=10)
    profit_margin: Optional[Decimal] = Field(None, ge=0, le=5)

class BulkCategoryUpdateData(BaseModel):
    category: str = Field(..., min_length=1, max_length=100)

class BulkStatusUpdateData(BaseModel):
    status: str = Field(..., pattern="^(active|inactive|sold|reserved)$")

class BulkOperationPreview(BaseModel):
    coin_id: int
    coin_title: str
    current_value: Any
    new_value: Any
    change_description: str

class BulkOperationResponse(BaseModel):
    operation_id: str
    operation_type: str
    coins_affected: int
    preview_changes: List[BulkOperationPreview]
    estimated_time: str
    warnings: List[str] = []

class BulkOperationResult(BaseModel):
    updated: int
    total_selected: int
    errors: List[str]
    price_changes: Optional[List[Dict[str, Any]]] = None

class SearchSuggestionResponse(BaseModel):
    suggestions: List[str]
    query: str

class QuickFilter(BaseModel):
    name: str
    label: str
    criteria: Dict[str, Any]
    count: int

class SearchHistoryItem(BaseModel):
    query: str
    filters: Dict[str, Any]
    result_count: int
    searched_at: str

class SearchHistoryResponse(BaseModel):
    recent_searches: List[SearchHistoryItem]
    saved_searches: List[SearchHistoryItem]

class AdvancedSearchFilters(BaseModel):
    # Text search
    query: Optional[str] = None
    
    # Basic filters
    year: Optional[int] = None
    denomination: Optional[str] = None
    grade: Optional[str] = None
    category: Optional[str] = None
    mint_mark: Optional[str] = None
    status: Optional[str] = None
    
    # Price filters
    min_price: Optional[Decimal] = None
    max_price: Optional[Decimal] = None
    min_paid_price: Optional[Decimal] = None
    max_paid_price: Optional[Decimal] = None
    
    # Silver filters
    is_silver: Optional[bool] = None
    silver_percent_min: Optional[Decimal] = None
    silver_percent_max: Optional[Decimal] = None
    silver_content_min: Optional[Decimal] = None
    silver_content_max: Optional[Decimal] = None
    
    # Date filters
    created_after: Optional[date] = None
    created_before: Optional[date] = None
    
    # Sorting
    sort_by: str = "created_at"
    sort_order: str = "desc"
    
    # Pagination
    limit: int = 100
    offset: int = 0

class SearchStats(BaseModel):
    total_coins: int
    active_coins: int
    sold_coins: int
    total_value: Decimal
    average_price: Decimal
    price_range: Dict[str, Decimal]
    category_breakdown: Dict[str, int]
    year_range: Dict[str, int]


