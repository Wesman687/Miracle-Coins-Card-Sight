// Core types for the Miracle Coins application

export interface Coin {
  id: number
  sku?: string
  title: string
  year?: number
  denomination?: string
  mint_mark?: string
  grade?: string
  category?: string
  description?: string
  condition_notes?: string
  is_silver: boolean
  silver_percent?: number
  silver_content_oz?: number
  paid_price?: number
  price_strategy: 'paid_price_multiplier' | 'silver_spot_multiplier' | 'gold_spot_multiplier' | 'fixed_price' | 'entry_based'
  price_multiplier: number
  base_from_entry: boolean
  entry_spot?: number
  entry_melt?: number
  override_price: boolean
  override_value?: number
  fixed_price?: number  // For hardcoded pricing
  computed_price?: number
  quantity: number
  status: 'active' | 'sold' | 'inactive' | 'pending'
  created_by?: string
  created_at: string
  updated_at: string
}

export interface CoinImage {
  id: number
  coin_id: number
  url: string
  alt: string
  sort_order: number
  created_at: string
}

export interface Listing {
  id: number
  coin_id: number
  channel: 'shopify' | 'ebay' | 'etsy' | 'tiktok' | 'facebook'
  external_id?: string
  external_variant_id?: string
  url?: string
  status: 'unlisted' | 'listed' | 'sold' | 'error'
  last_error?: string
  updated_at: string
}

export interface Order {
  id: number
  coin_id: number
  channel: 'shopify' | 'ebay' | 'etsy' | 'tiktok' | 'facebook'
  external_order_id: string
  qty: number
  sold_price: number
  fees: number
  shipping_cost: number
  created_at: string
}

export interface SpotPrice {
  id: number
  metal: 'silver' | 'gold' | 'platinum' | 'palladium'
  price: number
  source?: string
  fetched_at: string
}

export interface MetalsPrice {
  price: number | null
  currency: string
  source: string
  timestamp: string | null
  confidence: number
}

export interface DashboardKPIs {
  inventory_melt_value: number
  inventory_list_value: number
  gross_profit: number
  melt_vs_list_ratio: number
  total_coins: number
  active_listings: number
  sold_this_month: number
  metals_prices: {
    silver: MetalsPrice
    gold: MetalsPrice
  }
}

export interface AIEvaluation {
  suggested_price: number
  confidence_score: number
  selling_recommendation: 'individual' | 'bulk' | 'either'
  reasoning: string
  market_analysis: {
    coin_type: string
    rarity_score: number
    condition_score: number
    market_demand: 'low' | 'medium' | 'high'
    historical_performance: string
    grade_premium: number
    year_significance: number
    mint_mark_premium: number
    melt_value?: number
    melt_premium_potential?: number
  }
}

export interface Collection {
  id: number
  name: string
  description?: string
  description_html?: string
  color: string
  icon?: string
  shopify_collection_id?: string
  coin_count: number
  created_at: string
  updated_at: string
  metadata_fields?: CollectionMetadata[]
  images?: CollectionImage[]
  featured_image?: CollectionImage
  // Temporary fields that exist in database but are not used in UI
  sort_order?: number
  default_markup?: number
}

export interface CollectionMetadata {
  id: number
  collection_id: number
  field_name: string
  field_type: 'text' | 'textarea' | 'number' | 'date' | 'boolean' | 'select'
  field_value?: string
  field_options?: string[]
  field_label?: string
  field_description?: string
  is_required: boolean
  is_searchable: boolean
  sort_order: number
  created_at: string
  updated_at: string
  formatted_value?: any
}

export interface CollectionImage {
  id: number
  collection_id: number
  image_url: string
  alt_text?: string
  caption?: string
  is_featured: boolean
  sort_order: number
  file_size?: number
  width?: number
  height?: number
  mime_type?: string
  uploaded_at: string
  updated_at: string
  file_size_formatted?: string
  dimensions_formatted?: string
}

export interface CollectionAnalytics {
  collection_id: number
  collection_name: string
  created_at: string
  updated_at: string
  days_since_creation: number
  days_since_update: number
  metadata_fields_count: number
  metadata_completion_percentage: number
  field_types: Record<string, number>
  required_fields_completed: number
  total_required_fields: number
  required_fields_completion_percentage: number
  images_count: number
  has_featured_image: boolean
  total_image_size: number
  average_image_size: number
  image_size_formatted: string
  description_length: number
  description_html_length: number
  has_description: boolean
  has_rich_description: boolean
  has_shopify_integration: boolean
  views: number
  searches: number
  interactions: number
  engagement_score: number
}

// Form types
export interface CoinFormData {
  sku?: string
  title: string
  year?: number
  denomination?: string
  mint_mark?: string
  grade?: string
  category?: string
  description?: string
  condition_notes?: string
  is_silver: boolean
  silver_percent?: number
  silver_content_oz?: number
  paid_price?: number
  price_strategy: 'paid_price_multiplier' | 'silver_spot_multiplier' | 'gold_spot_multiplier' | 'fixed_price' | 'entry_based'
  price_multiplier: number
  base_from_entry: boolean
  entry_spot?: number
  entry_melt?: number
  override_price: boolean
  override_value?: number
  fixed_price?: number  // For hardcoded pricing
  quantity: number
  status: 'active' | 'sold' | 'inactive' | 'pending'
}

export interface CoinImageFormData {
  coin_id: number
  url: string
  alt: string
  sort_order: number
}

export interface ListingFormData {
  coin_id: number
  channel: 'shopify' | 'ebay' | 'etsy' | 'tiktok' | 'facebook'
  external_id?: string
  external_variant_id?: string
  url?: string
  status: 'unlisted' | 'listed' | 'sold' | 'error'
}

export interface OrderFormData {
  coin_id: number
  channel: 'shopify' | 'ebay' | 'etsy' | 'tiktok' | 'facebook'
  external_order_id: string
  qty: number
  sold_price: number
  fees: number
  shipping_cost: number
}

// API Response types
export interface APIResponse<T = any> {
  success: boolean
  message: string
  data?: T
  errors?: string[]
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  per_page: number
  pages: number
}

// Search and filter types
export interface CoinSearchParams {
  query?: string
  status?: 'active' | 'sold' | 'inactive' | 'pending'
  is_silver?: boolean
  category?: string
  year_min?: number
  year_max?: number
  price_min?: number
  price_max?: number
  sort_by?: 'title' | 'year' | 'computed_price' | 'created_at' | 'updated_at'
  sort_order?: 'asc' | 'desc'
  page?: number
  per_page?: number
}

export interface BulkOperationRequest {
  coin_ids?: number[]
  operation: 'delete' | 'update_status' | 'reprice' | 'export'
  parameters?: Record<string, any>
}

// Chart and analytics types
export interface ChartDataPoint {
  label: string
  value: number
  color?: string
}

export interface TimeSeriesDataPoint {
  date: string
  value: number
}

export interface InventoryAnalytics {
  total_value: number
  melt_value: number
  premium_value: number
  coin_count: number
  silver_count: number
  average_price: number
  price_distribution: ChartDataPoint[]
  category_breakdown: ChartDataPoint[]
  grade_distribution: ChartDataPoint[]
}

export interface SalesAnalytics {
  total_sales: number
  total_revenue: number
  average_sale_price: number
  sales_by_channel: ChartDataPoint[]
  sales_by_month: TimeSeriesDataPoint[]
  top_selling_coins: Array<{
    coin: Coin
    sales_count: number
    total_revenue: number
  }>
}

// User and authentication types
export interface User {
  id: string
  email: string
  name: string
  isAdmin: boolean
  permissions: string[]
  last_login?: string
}

export interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
}

// Notification types
export interface Notification {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  message: string
  timestamp: string
  read: boolean
  actions?: Array<{
    label: string
    action: () => void
  }>
}

// Settings types
export interface AppSettings {
  pricing: {
    default_strategy: 'paid_price_multiplier' | 'silver_spot_multiplier' | 'gold_spot_multiplier' | 'fixed_price' | 'entry_based'
    default_multiplier: number
    spot_refresh_interval: number
    auto_reprice_enabled: boolean
  }
  marketplace: {
    shopify_enabled: boolean
    ebay_enabled: boolean
    auto_sync_enabled: boolean
  }
  notifications: {
    email_enabled: boolean
    low_inventory_threshold: number
    price_change_threshold: number
  }
  ui: {
    theme: 'dark' | 'light'
    currency: string
    date_format: string
    items_per_page: number
  }
}

// Error types
export interface AppError {
  code: string
  message: string
  details?: any
  timestamp: string
}

// File upload types
export interface FileUploadProgress {
  file: File
  progress: number
  status: 'uploading' | 'processing' | 'completed' | 'error'
  error?: string
  result?: {
    url: string
    id: string
  }
}

// Export types
export interface ExportOptions {
  format: 'csv' | 'xlsx' | 'pdf'
  fields: string[]
  filters?: CoinSearchParams
  include_images: boolean
}

export interface ImportOptions {
  format: 'csv' | 'xlsx'
  update_existing: boolean
  skip_errors: boolean
  field_mapping: Record<string, string>
}

// Utility types
export type LoadingState = 'idle' | 'loading' | 'success' | 'error'

export type SortDirection = 'asc' | 'desc'

export type StatusFilter = 'all' | 'active' | 'sold' | 'inactive' | 'pending'

export type ChannelFilter = 'all' | 'shopify' | 'ebay' | 'etsy' | 'tiktok' | 'facebook'

// Component prop types
export interface ModalProps {
  isOpen: boolean
  onClose: () => void
  title?: string
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full'
}

export interface TableColumn<T> {
  key: keyof T
  label: string
  sortable?: boolean
  render?: (value: any, item: T) => React.ReactNode
  width?: string
  align?: 'left' | 'center' | 'right'
}

export interface TableProps<T> {
  data: T[]
  columns: TableColumn<T>[]
  loading?: boolean
  pagination?: {
    page: number
    per_page: number
    total: number
    onPageChange: (page: number) => void
  }
  sorting?: {
    sort_by: keyof T
    sort_order: SortDirection
    onSort: (key: keyof T) => void
  }
  selection?: {
    selected: T[]
    onSelectionChange: (selected: T[]) => void
  }
}


