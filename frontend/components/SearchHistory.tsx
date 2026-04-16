import { useState, useEffect } from 'react'
import { useQuery } from 'react-query'
import { 
  ClockIcon, 
  StarIcon, 
  TrashIcon,
  MagnifyingGlassIcon
} from '@heroicons/react/24/outline'
import { api } from '../lib/api'
import toast from 'react-hot-toast'

interface SearchHistoryItem {
  id: string
  query: string
  preset: string
  response: string
  confidence: number
  timestamp: string
  is_favorite: boolean
}

interface SearchHistoryProps {
  onQuickSearch: (query: string, preset: string) => void
}

export default function SearchHistory({ onQuickSearch }: SearchHistoryProps) {
  const [favoritesOnly, setFavoritesOnly] = useState(false)

  // Fetch search history
  const { data: historyData, isLoading, refetch } = useQuery(
    'search-history',
    () => api.get('/ai-chat/history'),
    {
      refetchInterval: 30000, // Refetch every 30 seconds
    }
  )

  const historyItems: SearchHistoryItem[] = historyData?.data?.history || []

  const filteredHistory = favoritesOnly 
    ? historyItems.filter(item => item.is_favorite)
    : historyItems

  const handleToggleFavorite = async (itemId: string, currentStatus: boolean) => {
    try {
      await api.put(`/ai-chat/history/${itemId}/favorite`, {
        is_favorite: !currentStatus
      })
      toast.success(currentStatus ? 'Removed from favorites' : 'Added to favorites')
      refetch()
    } catch (error) {
      console.error('Error toggling favorite:', error)
      toast.error('Failed to update favorite status')
    }
  }

  const handleDeleteHistory = async (itemId: string) => {
    try {
      await api.delete(`/ai-chat/history/${itemId}`)
      toast.success('Search deleted')
      refetch()
    } catch (error) {
      console.error('Error deleting history:', error)
      toast.error('Failed to delete search')
    }
  }

  const handleClearAllHistory = async () => {
    try {
      await api.delete('/ai-chat/history/clear')
      toast.success('All search history cleared')
      refetch()
    } catch (error) {
      console.error('Error clearing history:', error)
      toast.error('Failed to clear history')
    }
  }

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60)
    
    if (diffInHours < 1) {
      return 'Just now'
    } else if (diffInHours < 24) {
      return `${Math.floor(diffInHours)}h ago`
    } else {
      return date.toLocaleDateString()
    }
  }

  const getPresetName = (preset: string) => {
    const presetNames: Record<string, string> = {
      'quick_response': 'Quick Response',
      'in_depth_analysis': 'In-Depth Analysis',
      'descriptions': 'Descriptions',
      'year_mintage': 'Year & Mintage',
      'pricing_only': 'Pricing Only'
    }
    return presetNames[preset] || preset
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-400'
    if (confidence >= 0.6) return 'text-yellow-400'
    return 'text-red-400'
  }

  if (isLoading) {
    return (
      <div className="p-4">
        <div className="animate-pulse space-y-3">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="bg-gray-700 rounded-lg p-3">
              <div className="h-4 bg-gray-600 rounded mb-2"></div>
              <div className="h-3 bg-gray-600 rounded w-2/3"></div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-700">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2">
            <ClockIcon className="h-5 w-5 text-gray-400" />
            <h3 className="text-sm font-medium text-white">Search History</h3>
          </div>
          <button
            onClick={handleClearAllHistory}
            className="text-xs text-gray-400 hover:text-red-400 transition-colors"
          >
            Clear All
          </button>
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setFavoritesOnly(!favoritesOnly)}
            className={`px-3 py-1 rounded-lg text-xs transition-colors ${
              favoritesOnly
                ? 'bg-yellow-500 text-black'
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            <StarIcon className="h-3 w-3 inline mr-1" />
            Favorites Only
          </button>
        </div>
      </div>

      {/* History List */}
      <div className="flex-1 overflow-y-auto p-4">
        {filteredHistory.length === 0 ? (
          <div className="text-center py-8">
            <ClockIcon className="h-8 w-8 text-gray-500 mx-auto mb-2" />
            <p className="text-sm text-gray-400">
              {favoritesOnly ? 'No favorite searches yet' : 'No search history yet'}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              Start searching to see your history here
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {filteredHistory.map((item) => (
              <div
                key={item.id}
                className="bg-gray-800 rounded-lg p-3 hover:bg-gray-700 transition-colors"
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-1">
                      <span className="text-xs text-gray-400">
                        {getPresetName(item.preset)}
                      </span>
                      <span className={`text-xs ${getConfidenceColor(item.confidence)}`}>
                        {Math.round(item.confidence * 100)}%
                      </span>
                    </div>
                    <p className="text-sm text-white font-medium mb-1">
                      {item.query}
                    </p>
                    <p className="text-xs text-gray-400 line-clamp-2">
                      {item.response}
                    </p>
                  </div>
                  
                  <div className="flex items-center space-x-1 ml-2">
                    <button
                      onClick={() => handleToggleFavorite(item.id, item.is_favorite)}
                      className={`p-1 rounded transition-colors ${
                        item.is_favorite
                          ? 'text-yellow-400 hover:text-yellow-300'
                          : 'text-gray-400 hover:text-yellow-400'
                      }`}
                    >
                      <StarIcon className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => handleDeleteHistory(item.id)}
                      className="p-1 rounded text-gray-400 hover:text-red-400 transition-colors"
                    >
                      <TrashIcon className="h-4 w-4" />
                    </button>
                  </div>
                </div>
                
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-500">
                    {formatTimestamp(item.timestamp)}
                  </span>
                  <button
                    onClick={() => onQuickSearch(item.query, item.preset)}
                    className="text-xs text-yellow-400 hover:text-yellow-300 transition-colors flex items-center space-x-1"
                  >
                    <MagnifyingGlassIcon className="h-3 w-3" />
                    <span>Search Again</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-700">
        <div className="text-xs text-gray-500 text-center">
          {filteredHistory.length} {favoritesOnly ? 'favorite' : 'total'} searches
        </div>
      </div>
    </div>
  )
}

