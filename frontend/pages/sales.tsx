import { useState } from 'react'
import SalesDashboard from '../components/SalesDashboard'
import RevenueForecast from '../components/RevenueForecast'
import { 
  ChartBarIcon,
  ArrowTrendingUpIcon,
  PlusIcon,
  ArrowLeftIcon
} from '@heroicons/react/24/outline'

export default function SalesPage() {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'forecast'>('dashboard')

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
              <ChartBarIcon className="h-8 w-8 text-yellow-500" />
              <h1 className="text-2xl font-bold text-white">Sales Management</h1>
            </div>
            
            <div className="flex items-center space-x-4">
              <button className="bg-yellow-500 hover:bg-yellow-600 text-black px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors font-medium">
                <PlusIcon className="h-4 w-4" />
                <span>Record Sale</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-8">
            <button
              onClick={() => setActiveTab('dashboard')}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'dashboard'
                  ? 'border-yellow-500 text-yellow-400'
                  : 'border-transparent text-gray-400 hover:text-gray-300 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center space-x-2">
                <ChartBarIcon className="h-4 w-4" />
                <span>Sales Dashboard</span>
              </div>
            </button>
            
            <button
              onClick={() => setActiveTab('forecast')}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'forecast'
                  ? 'border-yellow-500 text-yellow-400'
                  : 'border-transparent text-gray-400 hover:text-gray-300 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center space-x-2">
                <ArrowTrendingUpIcon className="h-4 w-4" />
                <span>Revenue Forecast</span>
              </div>
            </button>
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'dashboard' && <SalesDashboard />}
        {activeTab === 'forecast' && <RevenueForecast />}
      </div>
    </div>
  )
}


