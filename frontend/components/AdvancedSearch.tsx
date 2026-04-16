import { useState, useEffect } from 'react'
import { useQuery } from 'react-query'
import { 
  MagnifyingGlassIcon,
  FunnelIcon,
  AdjustmentsHorizontalIcon,
  XMarkIcon,
  CheckIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline'
import { api } from '../lib/api'

interface SearchFilters {
  query?: string
  year?: number
  denomination?: string
  grade?: string
  category?: string
  min_price?: number
  max_price?: number
  min_paid_price?: number
  max_paid_price?: number
  is_silver?: boolean
  status?: string
  mint_mark?: string
  silver_percent_min?: number
  silver_percent_max?: number
  silver_content_min?: number
  silver_content_max?: number
  created_after?: string
  created_before?: string
  sort_by?: string
  sort_order?: string
  limit?: number
  offset?: number
}

interface SearchResult {
  coins: any[]
  total_count: number
  limit: number
  offset: number
  facets: {
    years: Array<{value: string, count: number}>
    denominations: Array<{value: string, count: number}>
    grades: Array<{value: string, count: number}>
    categories: Array<{value: string, count: number}>
    mint_marks: Array<{value: string, count: number}>
    status: Array<{value: string, count: number}>
  }
  search_criteria: SearchFilters
}

interface SelectedCoins {
  [key: number]: boolean
}

interface OperationData {
  strategy?: string
  price?: number
  multiplier?: number
  category?: string
  status?: string
}

export default function AdvancedSearch() {
  const [filters, setFilters] = useState<SearchFilters>({
    sort_by: 'created_at',
    sort_order: 'desc',
    limit: 50,
    offset: 0
  })
  
  const [showFilters, setShowFilters] = useState(false)
  const [selectedCoins, setSelectedCoins] = useState<SelectedCoins>({})
  const [showBulkOperations, setShowBulkOperations] = useState(false)
  const [searchSuggestions, setSearchSuggestions] = useState<string[]>([])

  const { data: searchResults, isLoading, error, refetch } = useQuery(
    ['advanced-search', filters],
    () => api.post('/search/advanced', filters),
    {
      retry: 3,
    }
  )

  const { data: facets } = useQuery(
    ['search-facets'],
    () => api.get('/search/facets'),
    {
      retry: 3,
    }
  )

  const results = searchResults?.data as SearchResult

  const handleFilterChange = (key: string, value: any) => {
    setFilters(prev => ({
      ...prev,
      [key]: value,
      offset: 0 // Reset pagination when filters change
    }))
  }

  const handleSearch = () => {
    refetch()
  }

  const handleClearFilters = () => {
    setFilters({
      sort_by: 'created_at',
      sort_order: 'desc',
      limit: 50,
      offset: 0
    })
  }

  const handleSelectCoin = (coinId: number) => {
    setSelectedCoins(prev => ({
      ...prev,
      [coinId]: !prev[coinId]
    }))
  }

  const handleSelectAll = () => {
    if (!results?.coins) return
    
    const allSelected = results.coins.every(coin => selectedCoins[coin.id])
    
    if (allSelected) {
      setSelectedCoins({})
    } else {
      const newSelection: SelectedCoins = {}
      results.coins.forEach(coin => {
        newSelection[coin.id] = true
      })
      setSelectedCoins(newSelection)
    }
  }

  const getSelectedCoinIds = () => {
    return Object.keys(selectedCoins)
      .filter(id => selectedCoins[parseInt(id)])
      .map(id => parseInt(id))
  }

  const selectedCount = getSelectedCoinIds().length

  const handleSearchInputChange = async (value: string) => {
    if (value.length >= 2) {
      try {
        const response = await api.get(`/search/suggestions?q=${encodeURIComponent(value)}&limit=5`)
        setSearchSuggestions(response.data.suggestions || [])
      } catch (error) {
        setSearchSuggestions([])
      }
    } else {
      setSearchSuggestions([])
    }
    
    handleFilterChange('query', value)
  }

  if (isLoading) {
    return (
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-700 rounded w-1/4 mb-6"></div>
          <div className="h-64 bg-gray-700 rounded-lg"></div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <MagnifyingGlassIcon className="h-6 w-6 text-yellow-500" />
          <h2 className="text-xl font-semibold text-white">Advanced Search</h2>
        </div>
        
        <div className="flex space-x-2">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="bg-gray-700 hover:bg-gray-600 px-3 py-2 rounded-lg flex items-center space-x-2 transition-colors"
          >
            <FunnelIcon className="h-4 w-4" />
            <span>Filters</span>
          </button>
          
          <button
            onClick={handleSearch}
            className="bg-yellow-500 hover:bg-yellow-600 text-black px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors font-medium"
          >
            <MagnifyingGlassIcon className="h-4 w-4" />
            <span>Search</span>
          </button>
        </div>
      </div>

      {/* Search Bar */}
      <div className="relative mb-6">
        <div className="relative">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            type="text"
            value={filters.query || ''}
            onChange={(e) => handleSearchInputChange(e.target.value)}
            placeholder="Search coins by title, description, or condition notes..."
            className="w-full bg-gray-700 border border-gray-600 rounded-lg pl-10 pr-4 py-3 text-white placeholder-gray-400 focus:outline-none focus:border-yellow-500"
          />
        </div>
        
        {/* Search Suggestions */}
        {searchSuggestions.length > 0 && (
          <div className="absolute top-full left-0 right-0 bg-gray-700 border border-gray-600 rounded-lg mt-1 z-10">
            {searchSuggestions.map((suggestion, index) => (
              <button
                key={index}
                onClick={() => {
                  handleFilterChange('query', suggestion)
                  setSearchSuggestions([])
                }}
                className="w-full text-left px-4 py-2 text-white hover:bg-gray-600 first:rounded-t-lg last:rounded-b-lg"
              >
                {suggestion}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Filters Panel */}
      {showFilters && (
        <div className="bg-gray-700 rounded-lg p-4 mb-6 border border-gray-600">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">Search Filters</h3>
            <button
              onClick={handleClearFilters}
              className="text-gray-400 hover:text-white text-sm"
            >
              Clear All
            </button>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {/* Year */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Year</label>
              <input
                type="number"
                value={filters.year || ''}
                onChange={(e) => handleFilterChange('year', e.target.value ? parseInt(e.target.value) : undefined)}
                placeholder="e.g., 1921"
                className="w-full bg-gray-600 border border-gray-500 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
              />
            </div>
            
            {/* Denomination */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Denomination</label>
              <input
                type="text"
                value={filters.denomination || ''}
                onChange={(e) => handleFilterChange('denomination', e.target.value || undefined)}
                placeholder="e.g., Morgan Dollar"
                className="w-full bg-gray-600 border border-gray-500 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
              />
            </div>
            
            {/* Grade */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Grade</label>
              <input
                type="text"
                value={filters.grade || ''}
                onChange={(e) => handleFilterChange('grade', e.target.value || undefined)}
                placeholder="e.g., MS65"
                className="w-full bg-gray-600 border border-gray-500 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
              />
            </div>
            
            {/* Category */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Category</label>
              <select
                value={filters.category || ''}
                onChange={(e) => handleFilterChange('category', e.target.value || undefined)}
                className="w-full bg-gray-600 border border-gray-500 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
              >
                <option value="">All Categories</option>
                <option value="premium">Premium</option>
                <option value="standard">Standard</option>
                <option value="bulk">Bulk</option>
                <option value="bullion">Bullion</option>
              </select>
            </div>
            
            {/* Min Price */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Min Price</label>
              <input
                type="number"
                step="0.01"
                value={filters.min_price || ''}
                onChange={(e) => handleFilterChange('min_price', e.target.value ? parseFloat(e.target.value) : undefined)}
                placeholder="0.00"
                className="w-full bg-gray-600 border border-gray-500 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
              />
            </div>
            
            {/* Max Price */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Max Price</label>
              <input
                type="number"
                step="0.01"
                value={filters.max_price || ''}
                onChange={(e) => handleFilterChange('max_price', e.target.value ? parseFloat(e.target.value) : undefined)}
                placeholder="1000.00"
                className="w-full bg-gray-600 border border-gray-500 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
              />
            </div>
            
            {/* Status */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Status</label>
              <select
                value={filters.status || ''}
                onChange={(e) => handleFilterChange('status', e.target.value || undefined)}
                className="w-full bg-gray-600 border border-gray-500 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
              >
                <option value="">All Status</option>
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
                <option value="sold">Sold</option>
                <option value="reserved">Reserved</option>
              </select>
            </div>
            
            {/* Silver Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Silver Content</label>
              <select
                value={filters.is_silver === undefined ? '' : filters.is_silver.toString()}
                onChange={(e) => handleFilterChange('is_silver', e.target.value === '' ? undefined : e.target.value === 'true')}
                className="w-full bg-gray-600 border border-gray-500 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
              >
                <option value="">All Coins</option>
                <option value="true">Silver Only</option>
                <option value="false">Non-Silver Only</option>
              </select>
            </div>
          </div>
        </div>
      )}

      {/* Results Header */}
      {results && (
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-4">
            <span className="text-white">
              {results.total_count.toLocaleString()} coins found
            </span>
            
            {selectedCount > 0 && (
              <span className="text-yellow-400 font-medium">
                {selectedCount} selected
              </span>
            )}
          </div>
          
          <div className="flex items-center space-x-2">
            {selectedCount > 0 && (
              <button
                onClick={() => setShowBulkOperations(true)}
                className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors"
              >
                <AdjustmentsHorizontalIcon className="h-4 w-4" />
                <span>Bulk Operations ({selectedCount})</span>
              </button>
            )}
            
            <select
              value={`${filters.sort_by}-${filters.sort_order}`}
              onChange={(e) => {
                const [sort_by, sort_order] = e.target.value.split('-')
                handleFilterChange('sort_by', sort_by)
                handleFilterChange('sort_order', sort_order)
              }}
              className="bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
            >
              <option value="created_at-desc">Newest First</option>
              <option value="created_at-asc">Oldest First</option>
              <option value="title-asc">Title A-Z</option>
              <option value="title-desc">Title Z-A</option>
              <option value="computed_price-desc">Price High-Low</option>
              <option value="computed_price-asc">Price Low-High</option>
              <option value="year-desc">Year Newest</option>
              <option value="year-asc">Year Oldest</option>
            </select>
          </div>
        </div>
      )}

      {/* Results Table */}
      {results && (
        <div className="bg-gray-700 rounded-lg border border-gray-600 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-600">
                <tr>
                  <th className="px-4 py-3 text-left">
                    <input
                      type="checkbox"
                      checked={results.coins.length > 0 && results.coins.every(coin => selectedCoins[coin.id])}
                      onChange={handleSelectAll}
                      className="rounded border-gray-500 bg-gray-600 text-yellow-500 focus:ring-yellow-500"
                    />
                  </th>
                  <th className="px-4 py-3 text-left text-gray-300">Coin</th>
                  <th className="px-4 py-3 text-left text-gray-300">Year</th>
                  <th className="px-4 py-3 text-left text-gray-300">Grade</th>
                  <th className="px-4 py-3 text-left text-gray-300">Price</th>
                  <th className="px-4 py-3 text-left text-gray-300">Status</th>
                  <th className="px-4 py-3 text-left text-gray-300">Actions</th>
                </tr>
              </thead>
              <tbody>
                {results.coins.map((coin) => (
                  <tr key={coin.id} className="border-b border-gray-600 hover:bg-gray-600">
                    <td className="px-4 py-3">
                      <input
                        type="checkbox"
                        checked={selectedCoins[coin.id] || false}
                        onChange={() => handleSelectCoin(coin.id)}
                        className="rounded border-gray-500 bg-gray-600 text-yellow-500 focus:ring-yellow-500"
                      />
                    </td>
                    <td className="px-4 py-3">
                      <div>
                        <div className="text-white font-medium">{coin.title}</div>
                        <div className="text-sm text-gray-400">{coin.denomination}</div>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-white">{coin.year}</td>
                    <td className="px-4 py-3 text-white">{coin.grade || '-'}</td>
                    <td className="px-4 py-3 text-green-400 font-medium">
                      ${coin.computed_price?.toFixed(2) || '0.00'}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 rounded text-xs ${
                        coin.status === 'active' ? 'bg-green-500/20 text-green-400' :
                        coin.status === 'sold' ? 'bg-red-500/20 text-red-400' :
                        coin.status === 'reserved' ? 'bg-yellow-500/20 text-yellow-400' :
                        'bg-gray-500/20 text-gray-400'
                      }`}>
                        {coin.status}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <button className="text-blue-400 hover:text-blue-300 text-sm">
                        View Details
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          {/* Pagination */}
          {results.total_count > results.limit && (
            <div className="px-4 py-3 bg-gray-600 flex items-center justify-between">
              <div className="text-sm text-gray-300">
                Showing {results.offset + 1} to {Math.min(results.offset + results.limit, results.total_count)} of {results.total_count}
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={() => handleFilterChange('offset', Math.max(0, results.offset - results.limit))}
                  disabled={results.offset === 0}
                  className="px-3 py-1 bg-gray-700 text-white rounded disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Previous
                </button>
                <button
                  onClick={() => handleFilterChange('offset', results.offset + results.limit)}
                  disabled={results.offset + results.limit >= results.total_count}
                  className="px-3 py-1 bg-gray-700 text-white rounded disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Bulk Operations Modal */}
      {showBulkOperations && (
        <BulkOperationsModal
          selectedCoinIds={getSelectedCoinIds()}
          onClose={() => setShowBulkOperations(false)}
          onSuccess={() => {
            setShowBulkOperations(false)
            setSelectedCoins({})
            refetch()
          }}
        />
      )}

      {/* Error State */}
      {error && (
        <div className="text-center text-red-400 py-8">
          <p>Failed to load search results</p>
          <p className="text-sm text-gray-400 mt-1">Please try again</p>
        </div>
      )}
    </div>
  )
}

// Bulk Operations Modal Component
function BulkOperationsModal({ selectedCoinIds, onClose, onSuccess }) {
  const [operationType, setOperationType] = useState('price_update')
  const [operationData, setOperationData] = useState<OperationData>({})
  const [isExecuting, setIsExecuting] = useState(false)

  const handleExecute = async () => {
    setIsExecuting(true)
    
    try {
      const response = await api.post('/search/bulk/execute', {
        operation_type: operationType,
        selected_coins: selectedCoinIds,
        operation_data: operationData,
        individual_tracking: true
      })
      
      onSuccess()
    } catch (error) {
      console.error('Bulk operation failed:', error)
    } finally {
      setIsExecuting(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-lg p-6 w-full max-w-md">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white">Bulk Operations</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white"
          >
            <XMarkIcon className="h-5 w-5" />
          </button>
        </div>
        
        <div className="mb-4">
          <p className="text-gray-300">
            {selectedCoinIds.length} coins selected
          </p>
        </div>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Operation Type
            </label>
            <select
              value={operationType}
              onChange={(e) => setOperationType(e.target.value)}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
            >
              <option value="price_update">Price Update</option>
              <option value="category_change">Category Change</option>
              <option value="status_change">Status Change</option>
            </select>
          </div>
          
          {operationType === 'price_update' && (
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Price Strategy
                </label>
                <select
                  value={operationData.strategy || 'fixed'}
                  onChange={(e) => setOperationData(prev => ({ ...prev, strategy: e.target.value }))}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
                >
                  <option value="fixed">Fixed Price</option>
                  <option value="multiplier">Multiplier</option>
                  <option value="profit_margin">Profit Margin</option>
                </select>
              </div>
              
              {operationData.strategy === 'fixed' && (
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    New Price
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={operationData.price || ''}
                    onChange={(e) => setOperationData(prev => ({ ...prev, price: parseFloat(e.target.value) }))}
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
                    placeholder="0.00"
                  />
                </div>
              )}
              
              {operationData.strategy === 'multiplier' && (
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Multiplier
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={operationData.multiplier || ''}
                    onChange={(e) => setOperationData(prev => ({ ...prev, multiplier: parseFloat(e.target.value) }))}
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
                    placeholder="1.30"
                  />
                </div>
              )}
            </div>
          )}
          
          {operationType === 'category_change' && (
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                New Category
              </label>
              <select
                value={operationData.category || ''}
                onChange={(e) => setOperationData(prev => ({ ...prev, category: e.target.value }))}
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
              >
                <option value="">Select Category</option>
                <option value="premium">Premium</option>
                <option value="standard">Standard</option>
                <option value="bulk">Bulk</option>
                <option value="bullion">Bullion</option>
              </select>
            </div>
          )}
          
          {operationType === 'status_change' && (
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                New Status
              </label>
              <select
                value={operationData.status || ''}
                onChange={(e) => setOperationData(prev => ({ ...prev, status: e.target.value }))}
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
              >
                <option value="">Select Status</option>
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
                <option value="sold">Sold</option>
                <option value="reserved">Reserved</option>
              </select>
            </div>
          )}
        </div>
        
        <div className="flex justify-end space-x-3 mt-6">
          <button
            onClick={onClose}
            className="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded-lg transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleExecute}
            disabled={isExecuting}
            className="bg-yellow-500 hover:bg-yellow-600 text-black px-4 py-2 rounded-lg transition-colors font-medium disabled:opacity-50"
          >
            {isExecuting ? 'Executing...' : 'Execute'}
          </button>
        </div>
      </div>
    </div>
  )
}


