import axios from 'axios';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:13000/api/v1',
  timeout: 120000, // 2 minutes timeout for Shopify imports
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    // Add JWT token if available, otherwise use development token
    const token = localStorage.getItem('auth_token') || 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoiYWRtaW4iLCJ1c2VybmFtZSI6ImFkbWluIiwiaXNBZG1pbiI6dHJ1ZSwiZXhwIjoxNzM4MjQ4MDAwLCJpYXQiOjE3MzgyNDAwMDB9.8K8Q8K8Q8K8Q8K8Q8K8Q8K8Q8K8Q8K8Q8K8Q8K8Q';
    config.headers.Authorization = `Bearer ${token}`;
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Category Management API functions
export const categoryAPI = {
  // Coin Categories
  getCategories: (params?: {
    category_type?: string;
    status?: string;
    parent_id?: number;
    search?: string;
    page?: number;
    per_page?: number;
  }) => api.get('/categories', { params }),
  
  getCategory: (id: number) => api.get(`/categories/${id}`),
  
  createCategory: (data: any) => api.post('/categories', data),
  
  updateCategory: (id: number, data: any) => api.put(`/categories/${id}`, data),
  
  deleteCategory: (id: number) => api.delete(`/categories/${id}`),
  
  // Auto-categorization
  autoCategorizeCoin: (coinId: number, force?: boolean) => 
    api.post('/categories/auto-categorize', { coin_id: coinId, force }),
  
  bulkCategorizeCoins: (coinIds: number[], force?: boolean) => 
    api.post('/categories/bulk-categorize', { coin_ids: coinIds, force }),
  
  // Statistics
  getCategoryStats: () => api.get('/categories/stats/overview'),
  
  updateCategoryStats: (categoryId: number) => 
    api.post(`/categories/${categoryId}/update-stats`),
  
  // Category Metadata
  getCategoryMetadata: (categoryId: number) => 
    api.get(`/categories/${categoryId}/metadata`),
  
  createCategoryMetadata: (categoryId: number, data: any) => 
    api.post(`/categories/${categoryId}/metadata`, data),
  
  updateCategoryMetadata: (metadataId: number, data: any) => 
    api.put(`/categories/metadata/${metadataId}`, data),
  
  deleteCategoryMetadata: (metadataId: number) => 
    api.delete(`/categories/metadata/${metadataId}`),
  
  // Category Rules
  getCategoryRules: (categoryId: number) => 
    api.get(`/categories/${categoryId}/rules`),
  
  createCategoryRule: (categoryId: number, data: any) => 
    api.post(`/categories/${categoryId}/rules`, data),
  
  updateCategoryRule: (ruleId: number, data: any) => 
    api.put(`/categories/rules/${ruleId}`, data),
  
  deleteCategoryRule: (ruleId: number) => 
    api.delete(`/categories/rules/${ruleId}`),
  
  // Shopify Categories
  getShopifyCategories: (params?: { page?: number; per_page?: number }) => 
    api.get('/categories/shopify', { params }),
  
  createShopifyCategory: (data: any) => api.post('/categories/shopify', data),
  
  syncShopifyCategories: (data: any) => api.post('/categories/shopify/sync', data),
  
  // Shopify Import
  fetchShopifyCollections: (integrationId: number) => 
    api.get(`/categories/shopify/fetch?integration_id=${integrationId}`),
  
  importShopifyCollections: (integrationId: number, collectionIds?: number[]) => 
    api.post('/categories/shopify/import', { integration_id: integrationId, collection_ids: collectionIds }),
};

// Enhanced Coin Management API functions
export const coinAPI = {
  // Coin CRUD with Metadata
  getCoins: (params?: {
    category_id?: number;
    search?: string;
    page?: number;
    per_page?: number;
  }) => api.get('/coins', { params }),
  
  getCoin: (id: number) => api.get(`/coins/${id}`),
  
  createCoin: (data: any) => api.post('/coins', data),
  
  updateCoin: (id: number, data: any) => api.put(`/coins/${id}`, data),
  
  deleteCoin: (id: number) => api.delete(`/coins/${id}`),
  
  // Metadata Management
  getCoinMetadata: (coinId: number) => api.get(`/coins/${coinId}/metadata`),
  
  updateCoinMetadata: (coinId: number, metadata: Record<string, any>) => 
    api.put(`/coins/${coinId}/metadata`, metadata),
  
  bulkUpdateMetadata: (updates: Array<{coin_id: number, metadata: Record<string, any>}>) => 
    api.post('/coins/bulk-metadata', updates),
  
  // Category Integration
  getCoinsByCategory: (categoryId: number, params?: {search?: string, page?: number, per_page?: number}) => 
    api.get(`/coins/categories/${categoryId}/coins`, { params }),
  
  getMetadataTemplates: (categoryId: number) => api.get(`/coins/metadata-templates/${categoryId}`),
  
  // Advanced Search
  advancedSearch: (params?: {
    search?: string;
    category_id?: number;
    metadata_filters?: Record<string, any>;
    page?: number;
    per_page?: number;
  }) => api.get('/coins/search/advanced', { params }),
};

// Shopify Integration API functions
export const shopifyAPI = {
  // Product and Inventory Management
  createProductAndInventory: (coinId: number, integrationId: number) =>
    api.post(`/alerts/shopify/create-product-inventory/${coinId}?integration_id=${integrationId}`),
  
  // Sync Operations
  syncProductsToShopify: (integrationId: number, forceSync?: boolean) =>
    api.post('/alerts/shopify/sync-products', { 
      integration_id: integrationId, 
      force_sync: forceSync 
    }),
  
  syncOrdersFromShopify: (integrationId: number, hoursBack?: number) =>
    api.post('/alerts/shopify/sync-orders', { 
      integration_id: integrationId, 
      hours_back: hoursBack 
    }),
  
  syncInventoryFromShopify: (integrationId: number) =>
    api.post('/alerts/shopify/sync-inventory', { 
      integration_id: integrationId 
    }),
  
  // Integration Management
  getIntegrations: () => api.get('/alerts/shopify/integrations'),
  
  createIntegration: (data: any) => api.post('/alerts/shopify/integrations', data),
  
  updateIntegration: (integrationId: number, data: any) =>
    api.put(`/alerts/shopify/integrations/${integrationId}`, data),
  
  testConnection: (integrationId: number) =>
    api.post(`/alerts/shopify/integrations/${integrationId}/test`),
  
  // Data Retrieval
  getShopifyProducts: (integrationId: number) =>
    api.get(`/alerts/shopify/products/${integrationId}`),
  
  getShopifyOrders: (integrationId: number, limit?: number) =>
    api.get(`/alerts/shopify/orders/${integrationId}`, { 
      params: { limit } 
    }),
  
  getSyncLogs: (integrationId: number, limit?: number) =>
    api.get(`/alerts/shopify/sync-logs/${integrationId}`, { 
      params: { limit } 
    }),
  
  getSyncStatistics: (integrationId: number) =>
    api.get(`/alerts/shopify/statistics/${integrationId}`),
  
  // Dashboard
  getShopifyDashboard: () => api.get('/alerts/shopify/dashboard'),
};

export { api };
export default api;
