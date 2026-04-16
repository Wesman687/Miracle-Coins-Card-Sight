import { useState, useEffect } from 'react'
import { useQuery } from 'react-query'
import { 
  CurrencyDollarIcon, 
  ChartBarIcon, 
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  ArrowPathIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline'
import { api } from '../lib/api'
import toast from 'react-hot-toast'

interface CoinPrice {
  id: number
  title: string
  year?: number
  denomination?: string
  grade?: string
  is_silver: boolean
  silver_content_oz?: number
  paid_price?: number
  computed_price?: number
  ai_suggested_price?: number
  melt_value?: number
  confidence_score?: number
  category: 'premium' | 'standard' | 'bulk'
  ai_notes?: string
  last_updated: string
  status: string
}

interface PricingDashboardProps {
  onCoinSelect?: (coin: CoinPrice) => void
}

export default function PricingDashboard({ onCoinSelect }: PricingDashboardProps) {
  const [selectedCoins, setSelectedCoins] = useState<number[]>([])
  const [showBulkActions, setShowBulkActions] = useState(false)

  // Fetch pricing data
  const { data: pricingData, isLoading, refetch } = useQuery(
    'pricing-dashboard',
    () => api.get('/pricing/dashboard'),
    {
      refetchInterval: 30000, // Refetch every 30 seconds
    }
  )

  const coins: CoinPrice[] = pricingData?.data?.coins || []
  const spotPrice = pricingData?.data?.spot_price || 0
  const lastUpdated = pricingData?.data?.last_updated || ''

  const handleSyncNow = async () => {
    try {
      await api.post('/pricing/refresh')
      toast.success('Pricing sync initiated!')
      refetch()
    } catch (error) {
      console.error('Error syncing pricing:', error)
      toast.error('Failed to sync pricing')
    }
  }

  const handleBulkUpdate = async (action: 'approve' | 'reject' | 'category') => {
    if (selectedCoins.length === 0) return

    try {
      await api.post('/pricing/bulk-update', {
        coin_ids: selectedCoins,
        action: action
      })
      toast.success(`Bulk ${action} completed!`)
      setSelectedCoins([])
      setShowBulkActions(false)
      refetch()
    } catch (error) {
      console.error('Error with bulk update:', error)
      toast.error(`Failed to ${action} coins`)
    }
  }

  const handleCoinSelect = (coinId: number) => {
    setSelectedCoins(prev => 
      prev.includes(coinId) 
        ? prev.filter(id => id !== coinId)
        : [...prev, coinId]
    )
  }

  const getStatusIcon = (coin: CoinPrice) => {
    if (coin.computed_price && coin.melt_value && coin.computed_price < coin.melt_value) {
      return <ExclamationTriangleIcon className="h-5 w-5 text-red-400" />
    }
    return <CheckCircleIcon className="h-5 w-5 text-green-400" />
  }

  const getStatusColor = (coin: CoinPrice) => {
    if (coin.computed_price && coin.melt_value && coin.computed_price < coin.melt_value) {
      return 'bg-red-500/10 border-red-500/20'
    }
    return 'bg-green-500/10 border-green-500/20'
  }

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'premium':
        return 'bg-yellow-500 text-black'
      case 'standard':
        return 'bg-blue-500 text-white'
      case 'bulk':
        return 'bg-gray-500 text-white'
      default:
        return 'bg-gray-500 text-white'
    }
  }

  const formatPrice = (price?: number | null) => {
    if (price === null || price === undefined || isNaN(price)) return 'N/A'
    return `$${price.toFixed(2)}`
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString()
  }

  if (isLoading) {
    return (
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-700 rounded mb-4"></div>
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-20 bg-gray-700 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <ChartBarIcon className="h-6 w-6 text-yellow-500" />
          <h2 className="text-xl font-semibold text-white">Pricing Dashboard</h2>
        </div>
        <div className="flex items-center space-x-3">
          <div className="text-sm text-gray-400">
            Silver Spot: <span className="text-yellow-400 font-medium">${spotPrice.toFixed(2)}</span>
          </div>
          <button
            onClick={handleSyncNow}
            className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors"
          >
            <ArrowPathIcon className="h-4 w-4" />
            <span>Sync Now</span>
          </button>
        </div>
      </div>

      {/* Bulk Actions */}
      {selectedCoins.length > 0 && (
        <div className="bg-gray-700 rounded-lg p-4 mb-6">
          <div className="flex items-center justify-between">
            <span className="text-white font-medium">
              {selectedCoins.length} coin{selectedCoins.length !== 1 ? 's' : ''} selected
            </span>
            <div className="flex space-x-2">
              <button
                onClick={() => handleBulkUpdate('approve')}
                className="bg-green-500 hover:bg-green-600 text-white px-3 py-1 rounded-lg text-sm transition-colors"
              >
                Approve All
              </button>
              <button
                onClick={() => handleBulkUpdate('reject')}
                className="bg-red-500 hover:bg-red-600 text-white px-3 py-1 rounded-lg text-sm transition-colors"
              >
                Reject All
              </button>
              <button
                onClick={() => handleBulkUpdate('category')}
                className="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded-lg text-sm transition-colors"
              >
                Move to Bulk
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Last Updated */}
      <div className="text-sm text-gray-400 mb-4">
        Last updated: {formatDate(lastUpdated)}
      </div>

      {/* Coins Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
        {coins.map((coin) => (
          <div
            key={coin.id}
            className={`rounded-lg p-4 border-2 transition-all cursor-pointer ${
              selectedCoins.includes(coin.id) 
                ? 'border-yellow-500 bg-yellow-500/10' 
                : getStatusColor(coin)
            }`}
            onClick={() => handleCoinSelect(coin.id)}
          >
            <div className="flex items-start justify-between mb-3">
              <div className="flex-1">
                <h3 className="font-medium text-white text-sm">{coin.title}</h3>
                <div className="text-xs text-gray-400">
                  {coin.year && `${coin.year} `}
                  {coin.denomination && `${coin.denomination} `}
                  {coin.grade && `${coin.grade}`}
                </div>
              </div>
              <div className="flex items-center space-x-2">
                {getStatusIcon(coin)}
                <input
                  type="checkbox"
                  checked={selectedCoins.includes(coin.id)}
                  onChange={() => handleCoinSelect(coin.id)}
                  className="rounded border-gray-600 bg-gray-700 text-yellow-500 focus:ring-yellow-500"
                />
              </div>
            </div>

            {/* Pricing Info */}
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">Paid:</span>
                <span className="text-white">{formatPrice(coin.paid_price)}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">Melt:</span>
                <span className="text-blue-400">{formatPrice(coin.melt_value)}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">AI Suggested:</span>
                <span className="text-yellow-400 font-medium">{formatPrice(coin.ai_suggested_price)}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">Current:</span>
                <span className="text-green-400 font-medium">{formatPrice(coin.computed_price)}</span>
              </div>
            </div>

            {/* Category */}
            <div className="mt-3 flex items-center justify-between">
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${getCategoryColor(coin.category)}`}>
                {coin.category.charAt(0).toUpperCase() + coin.category.slice(1)}
              </span>
              {coin.confidence_score && (
                <span className="text-xs text-gray-400">
                  {(coin.confidence_score * 100).toFixed(0)}% confidence
                </span>
              )}
            </div>

            {/* AI Notes Preview */}
            {coin.ai_notes && (
              <div className="mt-3 p-2 bg-gray-700 rounded text-xs text-gray-300">
                {coin.ai_notes.length > 100 
                  ? `${coin.ai_notes.substring(0, 100)}...` 
                  : coin.ai_notes
                }
              </div>
            )}
          </div>
        ))}
      </div>

      {coins.length === 0 && (
        <div className="text-center py-8">
          <ChartBarIcon className="h-12 w-12 text-gray-500 mx-auto mb-3" />
          <p className="text-gray-400">No coins found</p>
          <p className="text-sm text-gray-500">Add coins to see pricing data</p>
        </div>
      )}
    </div>
  )
}
