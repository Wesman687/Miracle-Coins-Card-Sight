import { useState } from 'react'
import AdvancedSearch from '../components/AdvancedSearch'
import { 
  MagnifyingGlassIcon,
  PlusIcon,
  ArrowPathIcon,
  ArrowLeftIcon
} from '@heroicons/react/24/outline'

export default function SearchPage() {
  const [showSavedSearches, setShowSavedSearches] = useState(false)

  return (
    <div className="min-h-screen bg-gray-900">
      {/* Header */}
      <div className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => window.history.back()}
                className="flex items-center space-x-2 text-gray-400 hover:text-white transition-colors"
              >
                <ArrowLeftIcon className="h-5 w-5" />
                <span className="text-sm font-medium">Back</span>
              </button>
              <div className="h-6 w-px bg-gray-600"></div>
              <MagnifyingGlassIcon className="h-8 w-8 text-yellow-500" />
              <h1 className="text-2xl font-bold text-white">Advanced Search</h1>
            </div>
            
            <div className="flex items-center space-x-4">
              <button className="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors">
                <ArrowPathIcon className="h-4 w-4" />
                <span>Refresh</span>
              </button>
              <button 
                onClick={() => setShowSavedSearches(true)}
                className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors font-medium"
              >
                <PlusIcon className="h-4 w-4" />
                <span>Saved Searches</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <AdvancedSearch />
      </div>

      {/* Saved Searches Modal */}
      {showSavedSearches && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 w-full max-w-md">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white">Saved Searches</h3>
              <button
                onClick={() => setShowSavedSearches(false)}
                className="text-gray-400 hover:text-white"
              >
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            <div className="space-y-3">
              <div className="bg-gray-700 rounded-lg p-3">
                <div className="text-white font-medium">Silver Coins</div>
                <div className="text-sm text-gray-400">is_silver: true</div>
                <div className="text-xs text-gray-500 mt-1">Created 2 days ago</div>
              </div>
              
              <div className="bg-gray-700 rounded-lg p-3">
                <div className="text-white font-medium">High Value Items</div>
                <div className="text-sm text-gray-400">min_price: 100</div>
                <div className="text-xs text-gray-500 mt-1">Created 1 week ago</div>
              </div>
              
              <div className="bg-gray-700 rounded-lg p-3">
                <div className="text-white font-medium">Recent Additions</div>
                <div className="text-sm text-gray-400">created_after: 2024-01-01</div>
                <div className="text-xs text-gray-500 mt-1">Created 3 days ago</div>
              </div>
            </div>
            
            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowSavedSearches(false)}
                className="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded-lg transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}


