import React, { useState, useEffect } from 'react';
import { 
  PlusIcon, 
  PencilIcon, 
  TrashIcon, 
  MagnifyingGlassIcon,
  TagIcon,
  DocumentTextIcon,
  CubeIcon,
  CheckCircleIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';

interface CoinMetadata {
  id: number;
  field_name: string;
  field_value: string;
  field_type: 'text' | 'number' | 'boolean' | 'select' | 'date';
}

interface CoinWithMetadata {
  id: number;
  sku: string;
  title: string;
  year?: number;
  denomination?: string;
  mint_mark?: string;
  grade?: string;
  category?: string;
  description?: string;
  condition_notes?: string;
  is_silver: boolean;
  silver_percent?: number;
  silver_content_oz?: number;
  paid_price?: number;
  price_strategy: string;
  price_multiplier: number;
  base_from_entry: boolean;
  entry_spot?: number;
  entry_melt?: number;
  override_price: boolean;
  override_value?: number;
  computed_price?: number;
  quantity: number;
  status: string;
  created_by?: string;
  category_id?: number;
  created_at: string;
  updated_at: string;
  metadata: CoinMetadata[];
  category_info?: {
    id: number;
    name: string;
    display_name: string;
    category_type: string;
  };
}

interface CategoryMetadataTemplate {
  field_name: string;
  field_type: 'text' | 'number' | 'boolean' | 'select' | 'date';
  field_label: string;
  field_description?: string;
  is_required: boolean;
  default_value?: string;
  select_options?: string[];
  validation_rules?: Record<string, any>;
}

interface CoinManagerProps {
  categoryId?: number;
  onCoinSelect?: (coin: CoinWithMetadata) => void;
  selectedCoinId?: number;
}

const CoinManager: React.FC<CoinManagerProps> = ({ 
  categoryId, 
  onCoinSelect, 
  selectedCoinId 
}) => {
  const [coins, setCoins] = useState<CoinWithMetadata[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCoin, setSelectedCoin] = useState<CoinWithMetadata | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showMetadataModal, setShowMetadataModal] = useState(false);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [metadataTemplates, setMetadataTemplates] = useState<CategoryMetadataTemplate[]>([]);

  useEffect(() => {
    fetchCoins();
    if (categoryId) {
      fetchMetadataTemplates(categoryId);
    }
  }, [page, searchTerm, categoryId]);

  const fetchCoins = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        page: page.toString(),
        per_page: '20',
        ...(searchTerm && { search: searchTerm }),
        ...(categoryId && { category_id: categoryId.toString() })
      });

      const response = await fetch(`/api/v1/coins?${params}`);
      if (!response.ok) {
        throw new Error('Failed to fetch coins');
      }

      const data = await response.json();
      setCoins(data.coins);
      setTotalPages(data.total_pages);
      
      // Select coin if provided
      if (selectedCoinId && !selectedCoin) {
        const coin = data.coins.find((c: CoinWithMetadata) => c.id === selectedCoinId);
        if (coin) {
          setSelectedCoin(coin);
          onCoinSelect?.(coin);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const fetchMetadataTemplates = async (categoryId: number) => {
    try {
      const response = await fetch(`/api/v1/coins/metadata-templates/${categoryId}`);
      if (response.ok) {
        const templates = await response.json();
        setMetadataTemplates(templates);
      }
    } catch (err) {
      console.error('Failed to fetch metadata templates:', err);
    }
  };

  const handleCoinClick = async (coin: CoinWithMetadata) => {
    setSelectedCoin(coin);
    onCoinSelect?.(coin);
    
    // Fetch full coin details with metadata
    try {
      const response = await fetch(`/api/v1/coins/${coin.id}`);
      if (response.ok) {
        const fullCoin = await response.json();
        setSelectedCoin(fullCoin);
      }
    } catch (err) {
      console.error('Failed to fetch coin details:', err);
    }
  };

  const handleDeleteCoin = async (coinId: number) => {
    if (!confirm('Are you sure you want to delete this coin?')) {
      return;
    }

    try {
      const response = await fetch(`/api/v1/coins/${coinId}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        setCoins(coins.filter(c => c.id !== coinId));
        if (selectedCoin?.id === coinId) {
          setSelectedCoin(null);
        }
      } else {
        const errorData = await response.json();
        alert(`Failed to delete coin: ${errorData.detail}`);
      }
    } catch (err) {
      alert('Failed to delete coin');
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const getMetadataValue = (coin: CoinWithMetadata, fieldName: string) => {
    const metadata = coin.metadata.find(m => m.field_name === fieldName);
    return metadata?.field_value || '-';
  };

  if (loading && coins.length === 0) {
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
          <h2 className="text-2xl font-bold text-gray-900">Coin Manager</h2>
          <p className="text-gray-600">
            {categoryId ? 'Manage coins in this category' : 'Manage all coins with metadata'}
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="bg-gold-600 text-white px-4 py-2 rounded-lg hover:bg-gold-700 flex items-center gap-2"
        >
          <PlusIcon className="h-5 w-5" />
          Add Coin
        </button>
      </div>

      {/* Search */}
      <div className="bg-white p-4 rounded-lg border border-gray-200">
        <div className="relative">
          <MagnifyingGlassIcon className="h-5 w-5 absolute left-3 top-3 text-gray-400" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search coins by title, SKU, or description..."
            className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gold-500 focus:border-gold-500"
          />
        </div>
      </div>

      {/* Coins Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        {coins.map((coin) => (
          <div
            key={coin.id}
            className={`bg-white rounded-lg border-2 p-6 cursor-pointer transition-all hover:shadow-lg ${
              selectedCoin?.id === coin.id 
                ? 'border-gold-500 shadow-lg' 
                : 'border-gray-200 hover:border-gold-300'
            }`}
            onClick={() => handleCoinClick(coin)}
          >
            <div className="flex items-start justify-between mb-4">
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-gray-900 mb-1">
                  {coin.title}
                </h3>
                <p className="text-sm text-gray-600 mb-2">
                  SKU: {coin.sku}
                </p>
                {coin.category_info && (
                  <div className="flex items-center gap-2 mb-2">
                    <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
                      {coin.category_info.display_name}
                    </span>
                  </div>
                )}
              </div>
              <div className="flex gap-1">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedCoin(coin);
                    setShowEditModal(true);
                  }}
                  className="p-1 text-gray-400 hover:text-gold-600"
                >
                  <PencilIcon className="h-4 w-4" />
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDeleteCoin(coin.id);
                  }}
                  className="p-1 text-gray-400 hover:text-red-600"
                >
                  <TrashIcon className="h-4 w-4" />
                </button>
              </div>
            </div>

            {/* Basic Info */}
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <div className="text-2xl font-bold text-gray-900">
                  {formatCurrency(coin.computed_price || 0)}
                </div>
                <div className="text-sm text-gray-600">Computed Price</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-gray-900">
                  {coin.quantity}
                </div>
                <div className="text-sm text-gray-600">Quantity</div>
              </div>
            </div>

            {/* Key Metadata Fields */}
            {coin.metadata.length > 0 && (
              <div className="mb-4">
                <div className="text-sm font-medium text-gray-700 mb-2">Key Details</div>
                <div className="space-y-1">
                  {coin.metadata.slice(0, 3).map((metadata) => (
                    <div key={metadata.id} className="flex justify-between text-sm">
                      <span className="text-gray-600">{metadata.field_name}:</span>
                      <span className="text-gray-900">{metadata.field_value}</span>
                    </div>
                  ))}
                  {coin.metadata.length > 3 && (
                    <div className="text-xs text-gray-500">
                      +{coin.metadata.length - 3} more fields
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex gap-2">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setSelectedCoin(coin);
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
                  setSelectedCoin(coin);
                  setShowEditModal(true);
                }}
                className="flex-1 flex items-center justify-center gap-2 px-3 py-2 text-sm bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200"
              >
                <PencilIcon className="h-4 w-4" />
                Edit
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

      {/* Modals */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-semibold mb-4">Create New Coin</h3>
            <p className="text-gray-600 mb-4">Coin creation form with metadata fields would go here.</p>
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

      {showEditModal && selectedCoin && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-semibold mb-4">Edit Coin: {selectedCoin.title}</h3>
            <p className="text-gray-600 mb-4">Coin editing form with metadata fields would go here.</p>
            <div className="flex gap-2 justify-end">
              <button
                onClick={() => setShowEditModal(false)}
                className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={() => setShowEditModal(false)}
                className="px-4 py-2 bg-gold-600 text-white rounded-lg hover:bg-gold-700"
              >
                Save Changes
              </button>
            </div>
          </div>
        </div>
      )}

      {showMetadataModal && selectedCoin && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-semibold mb-4">Metadata: {selectedCoin.title}</h3>
            
            {selectedCoin.metadata.length > 0 ? (
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {selectedCoin.metadata.map((metadata) => (
                    <div key={metadata.id} className="bg-gray-50 p-4 rounded-lg">
                      <div className="text-sm font-medium text-gray-900 mb-1">
                        {metadata.field_name}
                      </div>
                      <div className="text-sm text-gray-600 mb-1">
                        Type: {metadata.field_type}
                      </div>
                      <div className="text-lg text-gray-900">
                        {metadata.field_value || '-'}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <DocumentTextIcon className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                <p>No metadata fields defined for this coin's category.</p>
              </div>
            )}
            
            <div className="flex gap-2 justify-end mt-6">
              <button
                onClick={() => setShowMetadataModal(false)}
                className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Close
              </button>
              <button
                onClick={() => {
                  setShowMetadataModal(false);
                  setShowEditModal(true);
                }}
                className="px-4 py-2 bg-gold-600 text-white rounded-lg hover:bg-gold-700"
              >
                Edit Metadata
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CoinManager;
