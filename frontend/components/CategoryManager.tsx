import React, { useState, useEffect } from 'react';
import { 
  PlusIcon, 
  PencilIcon, 
  TrashIcon, 
  Cog6ToothIcon,
  ChartBarIcon,
  TagIcon,
  MagnifyingGlassIcon
} from '@heroicons/react/24/outline';

interface CategoryMetadata {
  id: number;
  field_name: string;
  field_type: 'text' | 'number' | 'boolean' | 'select' | 'date';
  field_label: string;
  field_description?: string;
  is_required: boolean;
  default_value?: string;
  select_options?: string[];
  sort_order: number;
  is_searchable: boolean;
  is_filterable: boolean;
  is_display_in_list: boolean;
}

interface CategoryRule {
  id: number;
  rule_name: string;
  rule_description?: string;
  conditions: Record<string, any>;
  priority: number;
  is_active: boolean;
  match_count: number;
  last_matched_at?: string;
}

interface CoinCategory {
  id: number;
  name: string;
  display_name: string;
  description?: string;
  category_type: string;
  parent_category_id?: number;
  keywords: string[];
  denomination_patterns: string[];
  year_ranges: Array<{ min: number; max: number }>;
  mint_mark_patterns: string[];
  grade_patterns: string[];
  default_price_multiplier: number;
  min_price_multiplier: number;
  max_price_multiplier: number;
  is_precious_metal: boolean;
  metal_type?: string;
  expected_silver_content?: number;
  shopify_category_id?: number;
  auto_sync_to_shopify: boolean;
  sort_order: number;
  status: 'active' | 'inactive' | 'archived';
  icon?: string;
  color?: string;
  coin_count: number;
  total_value: number;
  avg_price: number;
  metadata?: CategoryMetadata[];
  rules?: CategoryRule[];
  created_at: string;
  updated_at: string;
}

interface CategoryManagerProps {
  onCategorySelect?: (category: CoinCategory) => void;
  selectedCategoryId?: number;
}

const CategoryManager: React.FC<CategoryManagerProps> = ({ 
  onCategorySelect, 
  selectedCategoryId 
}) => {
  const [categories, setCategories] = useState<CoinCategory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryType, setCategoryType] = useState<string>('');
  const [status, setStatus] = useState<string>('');
  const [selectedCategory, setSelectedCategory] = useState<CoinCategory | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showMetadataModal, setShowMetadataModal] = useState(false);
  const [showRulesModal, setShowRulesModal] = useState(false);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  const categoryTypes = [
    'silver_coins', 'gold_coins', 'collector_coins', 'bullion', 
    'proof_coins', 'error_coins', 'ancient_coins', 'world_coins', 
    'us_coins', 'commemorative', 'custom'
  ];

  const statusOptions = ['active', 'inactive', 'archived'];

  useEffect(() => {
    fetchCategories();
  }, [page, searchTerm, categoryType, status]);

  const fetchCategories = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        page: page.toString(),
        per_page: '20',
        ...(searchTerm && { search: searchTerm }),
        ...(categoryType && { category_type: categoryType }),
        ...(status && { status: status })
      });

      const response = await fetch(`/api/v1/categories?${params}`);
      if (!response.ok) {
        throw new Error('Failed to fetch categories');
      }

      const data = await response.json();
      setCategories(data.categories);
      setTotalPages(data.total_pages);
      
      // Select category if provided
      if (selectedCategoryId && !selectedCategory) {
        const category = data.categories.find((c: CoinCategory) => c.id === selectedCategoryId);
        if (category) {
          setSelectedCategory(category);
          onCategorySelect?.(category);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleCategoryClick = async (category: CoinCategory) => {
    setSelectedCategory(category);
    onCategorySelect?.(category);
    
    // Fetch full category details with metadata and rules
    try {
      const response = await fetch(`/api/v1/categories/${category.id}`);
      if (response.ok) {
        const fullCategory = await response.json();
        setSelectedCategory(fullCategory);
      }
    } catch (err) {
      console.error('Failed to fetch category details:', err);
    }
  };

  const handleDeleteCategory = async (categoryId: number) => {
    if (!confirm('Are you sure you want to delete this category?')) {
      return;
    }

    try {
      const response = await fetch(`/api/v1/categories/${categoryId}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        setCategories(categories.filter(c => c.id !== categoryId));
        if (selectedCategory?.id === categoryId) {
          setSelectedCategory(null);
        }
      } else {
        const errorData = await response.json();
        alert(`Failed to delete category: ${errorData.detail}`);
      }
    } catch (err) {
      alert('Failed to delete category');
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const getCategoryTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      silver_coins: 'bg-gray-100 text-gray-800',
      gold_coins: 'bg-yellow-100 text-yellow-800',
      collector_coins: 'bg-blue-100 text-blue-800',
      bullion: 'bg-green-100 text-green-800',
      proof_coins: 'bg-purple-100 text-purple-800',
      error_coins: 'bg-red-100 text-red-800',
      ancient_coins: 'bg-orange-100 text-orange-800',
      world_coins: 'bg-indigo-100 text-indigo-800',
      us_coins: 'bg-pink-100 text-pink-800',
      commemorative: 'bg-teal-100 text-teal-800',
      custom: 'bg-slate-100 text-slate-800'
    };
    return colors[type] || 'bg-gray-100 text-gray-800';
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      active: 'bg-green-100 text-green-800',
      inactive: 'bg-yellow-100 text-yellow-800',
      archived: 'bg-gray-100 text-gray-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  if (loading && categories.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gold-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Category Manager</h2>
          <p className="text-gray-600">Manage coin categories and metadata</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="bg-gold-600 text-white px-4 py-2 rounded-lg hover:bg-gold-700 flex items-center gap-2"
        >
          <PlusIcon className="h-5 w-5" />
          Create Category
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg border border-gray-200">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Search
            </label>
            <div className="relative">
              <MagnifyingGlassIcon className="h-5 w-5 absolute left-3 top-3 text-gray-400" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search categories..."
                className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gold-500 focus:border-gold-500"
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Category Type
            </label>
            <select
              value={categoryType}
              onChange={(e) => setCategoryType(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gold-500 focus:border-gold-500"
            >
              <option value="">All Types</option>
              {categoryTypes.map(type => (
                <option key={type} value={type}>
                  {type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Status
            </label>
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gold-500 focus:border-gold-500"
            >
              <option value="">All Statuses</option>
              {statusOptions.map(statusOption => (
                <option key={statusOption} value={statusOption}>
                  {statusOption.charAt(0).toUpperCase() + statusOption.slice(1)}
                </option>
              ))}
            </select>
          </div>
          <div className="flex items-end">
            <button
              onClick={() => {
                setSearchTerm('');
                setCategoryType('');
                setStatus('');
                setPage(1);
              }}
              className="w-full px-3 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Clear Filters
            </button>
          </div>
        </div>
      </div>

      {/* Categories Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        {categories.map((category) => (
          <div
            key={category.id}
            className={`bg-white rounded-lg border-2 p-6 cursor-pointer transition-all hover:shadow-lg ${
              selectedCategory?.id === category.id 
                ? 'border-gold-500 shadow-lg' 
                : 'border-gray-200 hover:border-gold-300'
            }`}
            onClick={() => handleCategoryClick(category)}
          >
            <div className="flex items-start justify-between mb-4">
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-gray-900 mb-1">
                  {category.display_name}
                </h3>
                <p className="text-sm text-gray-600 mb-2">
                  {category.description || 'No description'}
                </p>
                <div className="flex flex-wrap gap-2">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getCategoryTypeColor(category.category_type)}`}>
                    {category.category_type.replace('_', ' ')}
                  </span>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(category.status)}`}>
                    {category.status}
                  </span>
                </div>
              </div>
              <div className="flex gap-1">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedCategory(category);
                    setShowEditModal(true);
                  }}
                  className="p-1 text-gray-400 hover:text-gold-600"
                >
                  <PencilIcon className="h-4 w-4" />
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDeleteCategory(category.id);
                  }}
                  className="p-1 text-gray-400 hover:text-red-600"
                >
                  <TrashIcon className="h-4 w-4" />
                </button>
              </div>
            </div>

            {/* Statistics */}
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <div className="text-2xl font-bold text-gray-900">
                  {category.coin_count}
                </div>
                <div className="text-sm text-gray-600">Coins</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-gray-900">
                  {formatCurrency(category.total_value)}
                </div>
                <div className="text-sm text-gray-600">Total Value</div>
              </div>
            </div>

            {/* Keywords */}
            {category.keywords.length > 0 && (
              <div className="mb-4">
                <div className="text-sm font-medium text-gray-700 mb-1">Keywords</div>
                <div className="flex flex-wrap gap-1">
                  {category.keywords.slice(0, 3).map((keyword, index) => (
                    <span
                      key={index}
                      className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded"
                    >
                      {keyword}
                    </span>
                  ))}
                  {category.keywords.length > 3 && (
                    <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                      +{category.keywords.length - 3} more
                    </span>
                  )}
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex gap-2">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setSelectedCategory(category);
                  setShowMetadataModal(true);
                }}
                className="flex-1 flex items-center justify-center gap-2 px-3 py-2 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
              >
                <TagIcon className="h-4 w-4" />
                Metadata
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setSelectedCategory(category);
                  setShowRulesModal(true);
                }}
                className="flex-1 flex items-center justify-center gap-2 px-3 py-2 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
              >
                <Cog6ToothIcon className="h-4 w-4" />
                Rules
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <div className="text-sm text-gray-700">
            Page {page} of {totalPages}
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setPage(Math.max(1, page - 1))}
              disabled={page === 1}
              className="px-3 py-2 text-sm border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
            >
              Previous
            </button>
            <button
              onClick={() => setPage(Math.min(totalPages, page + 1))}
              disabled={page === totalPages}
              className="px-3 py-2 text-sm border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
            >
              Next
            </button>
          </div>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="text-red-800">{error}</div>
        </div>
      )}

      {/* Modals would go here - CreateCategoryModal, EditCategoryModal, etc. */}
      {/* For now, we'll add placeholder modals */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4">
            <h3 className="text-lg font-semibold mb-4">Create New Category</h3>
            <p className="text-gray-600 mb-4">Category creation form would go here.</p>
            <div className="flex gap-2 justify-end">
              <button
                onClick={() => setShowCreateModal(false)}
                className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={() => setShowCreateModal(false)}
                className="px-4 py-2 bg-gold-600 text-white rounded-lg hover:bg-gold-700"
              >
                Create
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CategoryManager;
