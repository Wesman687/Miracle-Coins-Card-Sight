import { useState, useEffect } from 'react'
import { PencilIcon, TrashIcon, EyeIcon, ChevronUpIcon, ChevronDownIcon } from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'
import api from '../lib/api'

interface Coin {
  shopify_metadata?: {
    storefront?: {
      productType?: 'card' | 'bundle'
      metal?: 'gold' | 'platinum' | 'silver'
      badge?: string
      weightLabel?: string
    }
    ebay?: {
      itemId?: string
      url?: string
      seller?: string
    }
  }
  id: number
  sku?: string
  title: string
  year?: number
  denomination?: string
  mint_mark?: string
  grade?: string
  is_silver: boolean
  silver_content_oz?: number
  paid_price?: number
  computed_price?: number
  fixed_price?: number
  price_strategy?: string
  ai_suggested_price?: number
  confidence_score?: number
  category?: 'premium' | 'standard' | 'bulk'
  ai_notes?: string
  quantity: number
  status: string
  created_at: string
  updated_at: string
  images?: string[]
  collection_ids?: number[]
}

interface Collection {
  id: number
  name: string
  description?: string
}

interface CoinTableProps {
  coins: Coin[]
  onEdit: (coin: Coin) => void
  onStorefrontEdit: (coin: Coin) => void
  onRefresh: () => void
}

type SortField = 'title' | 'year' | 'quantity' | 'paid_price' | 'computed_price'
type SortDirection = 'asc' | 'desc'
type FilterField = 'is_silver' | 'category' | 'status' | 'source' | 'productType'

interface FilterState {
  is_silver?: boolean
  category?: string
  status?: string
  source?: 'ebay'
  productType?: 'card' | 'bundle'
}

export default function CoinTable({ coins, onEdit, onStorefrontEdit, onRefresh }: CoinTableProps) {
  const [deletingId, setDeletingId] = useState<number | null>(null)
  const [sortField, setSortField] = useState<SortField>('title')
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc')
  const [collections, setCollections] = useState<Collection[]>([])
  const [filters, setFilters] = useState<FilterState>({})

  // Fetch collections on component mount
  useEffect(() => {
    const fetchCollections = async () => {
      try {
        const response = await api.get('/collections')
        setCollections(response.data)
      } catch (error) {
        console.error('Error fetching collections:', error)
      }
    }
    fetchCollections()
  }, [])

  // Helper function to get collection name by ID
  const getCollectionName = (id: number): string => {
    const collection = collections.find(c => c.id === id)
    return collection ? collection.name : `Collection #${id}`
  }

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDirection('asc')
    }
  }

  const handleFilter = (field: FilterField, value: any) => {
    setFilters(prev => ({
      ...prev,
      [field]: prev[field] === value ? undefined : value
    }))
  }

  const filteredCoins = coins.filter(coin => {
    if (filters.is_silver !== undefined && coin.is_silver !== filters.is_silver) return false
    if (filters.category && coin.category !== filters.category) return false
    if (filters.status && coin.status !== filters.status) return false
    if (filters.source === 'ebay' && coin.shopify_metadata?.ebay?.seller !== 'miracle_coins') return false
    if (filters.productType && coin.shopify_metadata?.storefront?.productType !== filters.productType) return false
    return true
  })

  const sortedCoins = [...filteredCoins].sort((a, b) => {
    let aValue: any = a[sortField]
    let bValue: any = b[sortField]

    // Handle null/undefined values
    if (aValue === null || aValue === undefined) aValue = ''
    if (bValue === null || bValue === undefined) bValue = ''

    // Convert to strings for comparison if needed
    if (typeof aValue === 'number' && typeof bValue === 'number') {
      return sortDirection === 'asc' ? aValue - bValue : bValue - aValue
    }

    const aStr = String(aValue).toLowerCase()
    const bStr = String(bValue).toLowerCase()

    if (sortDirection === 'asc') {
      return aStr.localeCompare(bStr)
    } else {
      return bStr.localeCompare(aStr)
    }
  })

  const handleDelete = async (coinId: number) => {
    if (!confirm('Are you sure you want to delete this coin?')) {
      return
    }

    setDeletingId(coinId)
    try {
      await api.delete(`/coins/${coinId}`)
      toast.success('Coin deleted successfully!')
      onRefresh()
    } catch (error) {
      toast.error('Failed to delete coin')
      console.error('Error deleting coin:', error)
    } finally {
      setDeletingId(null)
    }
  }

  const formatPrice = (price?: number | null) => {
    if (price === null || price === undefined || isNaN(price)) return 'N/A'
    return `$${price.toFixed(2)}`
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString()
  }

  const getSortIcon = (field: SortField) => {
    if (sortField !== field) return null
    return sortDirection === 'asc' ? (
      <ChevronUpIcon className="h-4 w-4" />
    ) : (
      <ChevronDownIcon className="h-4 w-4" />
    )
  }

  if (!coins || coins.length === 0) {
    return (
      <div className="bg-gray-800 rounded-lg p-8 text-center">
        <p className="text-gray-400">No coins found. Add your first coin to get started!</p>
      </div>
    )
  }

  const activeFiltersCount = Object.values(filters).filter(v => v !== undefined).length

  return (
    <div className="bg-gray-800 rounded-lg overflow-hidden">
      {/* Filter Indicators */}
      {activeFiltersCount > 0 && (
        <div className="px-6 py-3 bg-gray-700 border-b border-gray-600">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-300">Active filters:</span>
              {filters.is_silver === true && (
                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-900 text-yellow-300">
                  Silver Only
                </span>
              )}
              {filters.category && (
                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-900 text-blue-300">
                  {filters.category}
                </span>
              )}
              {filters.status && (
                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-900 text-green-300">
                  {filters.status}
                </span>
              )}
              {filters.source === 'ebay' && (
                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-900 text-purple-300">
                  eBay import
                </span>
              )}
              {filters.productType && (
                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-pink-900 text-pink-300">
                  {filters.productType}
                </span>
              )}
            </div>
            <button
              onClick={() => setFilters({})}
              className="text-xs text-gray-400 hover:text-white transition-colors"
            >
              Clear all filters
            </button>
          </div>
        </div>
      )}
      
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-700">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                Image
              </th>
              <th 
                className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider cursor-pointer hover:bg-gray-600 transition-colors"
                onClick={() => handleSort('title')}
              >
                <div className="flex items-center space-x-1">
                  <span>Coin Details</span>
                  {getSortIcon('title')}
                </div>
              </th>
              <th 
                className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider cursor-pointer hover:bg-gray-600 transition-colors"
                onClick={() => handleFilter('is_silver', true)}
              >
                <div className="flex items-center space-x-1">
                  <span className={filters.is_silver === true ? 'text-yellow-400' : ''}>Silver Info</span>
                  {filters.is_silver === true && <span className="text-yellow-400">●</span>}
                </div>
              </th>
              <th 
                className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider cursor-pointer hover:bg-gray-600 transition-colors"
                onClick={() => handleSort('paid_price')}
              >
                <div className="flex items-center space-x-1">
                  <span>Pricing</span>
                  {getSortIcon('paid_price')}
                </div>
              </th>
              <th 
                className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider cursor-pointer hover:bg-gray-600 transition-colors"
                onClick={() => handleSort('quantity')}
              >
                <div className="flex items-center space-x-1">
                  <span>Quantity</span>
                  {getSortIcon('quantity')}
                </div>
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                Storefront
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-700">
            {sortedCoins?.map((coin) => (
              <tr 
                key={coin.id} 
                className="hover:bg-gray-750 transition-colors cursor-pointer"
                onClick={() => onEdit(coin)}
              >
                <td className="px-6 py-4">
                  <div className="w-16 h-16 flex items-center justify-center">
                    {coin.images && coin.images.length > 0 ? (
                      <img 
                        src={coin.images[0]} 
                        alt={coin.title}
                        className="w-16 h-16 object-cover rounded-lg border border-gray-600 hover:border-yellow-500 transition-colors cursor-pointer"
                        onClick={(e) => {
                          e.stopPropagation()
                          window.open(coin.images[0], '_blank')
                        }}
                        onError={(e) => {
                          e.currentTarget.style.display = 'none'
                          const fallback = e.currentTarget.nextElementSibling as HTMLElement | null
                          if (fallback) fallback.style.display = 'flex'
                        }}
                      />
                    ) : null}
                    <div 
                      className="w-16 h-16 bg-gray-700 border border-gray-600 rounded-lg flex items-center justify-center text-gray-500 text-xs"
                      style={{ display: coin.images && coin.images.length > 0 ? 'none' : 'flex' }}
                    >
                      No Image
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <div>
                    <div className="text-sm font-medium text-white">
                      {coin.title}
                    </div>
                    <div className="text-sm text-gray-400">
                      {coin.year && `${coin.year} `}
                      {coin.denomination && `${coin.denomination} `}
                      {coin.mint_mark && `(${coin.mint_mark}) `}
                      {coin.grade && `${coin.grade}`}
                    </div>
                    {coin.sku && (
                      <div className="text-xs text-gray-500">
                        SKU: {coin.sku}
                      </div>
                    )}
                  </div>
                </td>
                <td className="px-6 py-4">
                  <div className="text-sm text-gray-300">
                    {coin.is_silver ? (
                      <>
                        <div>Silver: Yes</div>
                        {coin.silver_content_oz && (
                          <div className="text-xs text-gray-400">
                            {coin.silver_content_oz} oz
                          </div>
                        )}
                      </>
                    ) : (
                      <div className="text-gray-500">Non-silver</div>
                    )}
                  </div>
                </td>
                <td className="px-6 py-4">
                  <div className="text-sm text-gray-300">
                    <div className="text-green-400 font-medium">
                      List Price: {formatPrice(coin.computed_price)}
                    </div>
                    <div className="text-red-400 font-medium">
                      Cost: {formatPrice(coin.paid_price)}
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <div className="text-sm text-gray-300">
                    <div className="text-blue-400 font-medium">
                      Qty: {coin.quantity}
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <div className="text-sm text-gray-300">
                    <span className={`px-2 py-1 text-xs rounded ${
                      coin.status === 'active' 
                        ? 'bg-green-900 text-green-300' 
                        : coin.status === 'sold'
                        ? 'bg-red-900 text-red-300'
                        : 'bg-gray-700 text-gray-300'
                    }`}>
                      {coin.status}
                    </span>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <div className="flex items-center space-x-2" onClick={(e) => e.stopPropagation()}>
                    <button
                      onClick={() => onEdit(coin)}
                      className="text-yellow-400 hover:text-yellow-300 transition-colors"
                      title="Edit coin"
                    >
                      <PencilIcon className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => handleDelete(coin.id)}
                      disabled={deletingId === coin.id}
                      className="text-red-400 hover:text-red-300 transition-colors disabled:opacity-50"
                      title="Delete coin"
                    >
                      <TrashIcon className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => onStorefrontEdit(coin)}
                      className="text-blue-400 hover:text-blue-300 transition-colors"
                      title="Edit storefront metadata"
                    >
                      <EyeIcon className="h-4 w-4" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
