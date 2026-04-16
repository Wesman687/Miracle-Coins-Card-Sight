import { useState, useEffect } from 'react'
import { useQuery } from 'react-query'
import { 
  CubeIcon,
  ExclamationTriangleIcon,
  ArrowTrendingUpIcon,
  MapPinIcon,
  ChartBarIcon,
  PlusIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline'
import { api } from '../lib/api'

interface InventoryMetrics {
  total_coins: number
  total_value: number
  dead_stock_count: number
  dead_stock_value: number
  turnover_rate: number
  location_breakdown: LocationInventory[]
  category_breakdown: CategoryBreakdown[]
  profit_margin_analysis: MarginAnalysis[]
  average_value_per_coin: number
  dead_stock_percentage: number
}

interface LocationInventory {
  location_id: number
  location_name: string
  coin_count: number
  total_value: number
  profit_margin: number
  last_updated: string
}

interface CategoryBreakdown {
  category: string
  coin_count: number
  total_value: number
}

interface MarginAnalysis {
  category: string
  average_margin: number
  min_margin: number
  max_margin: number
  coin_count: number
  total_value: number
}

interface DeadStockItem {
  id: number
  coin_id: number
  coin_title: string
  coin_value: number
  coin_category: string
  days_since_last_sale: number
  days_since_added: number
  profit_margin: number
  category: string
}

interface TurnoverData {
  fast_moving: TurnoverItem[]
  slow_moving: TurnoverItem[]
  dead_stock: TurnoverItem[]
}

interface TurnoverItem {
  id: number
  coin_id: number
  coin_title: string
  coin_value: number
  days_since_last_sale: number
  sales_count: number
  total_revenue: number
  sales_velocity: number
  profit_margin: number
  turnover_category: string
}

export default function InventoryManager() {
  const [selectedLocation, setSelectedLocation] = useState<string>('all')
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  const [activeTab, setActiveTab] = useState<'overview' | 'dead-stock' | 'turnover'>('overview')

  const { data: inventoryData, isLoading, error, refetch } = useQuery(
    ['inventory-metrics', selectedLocation, selectedCategory],
    () => api.get(`/inventory/metrics?location=${selectedLocation}&category=${selectedCategory}`),
    {
      refetchInterval: 60000, // Refresh every minute
      retry: 3,
    }
  )

  const { data: deadStockData } = useQuery(
    ['dead-stock-analysis'],
    () => api.get('/inventory/dead-stock'),
    {
      refetchInterval: 300000, // Refresh every 5 minutes
    }
  )

  const { data: turnoverData } = useQuery(
    ['turnover-analysis'],
    () => api.get('/inventory/turnover-analysis'),
    {
      refetchInterval: 300000, // Refresh every 5 minutes
    }
  )

  const metrics = inventoryData?.data
  const deadStock = deadStockData?.data || []
  const turnover = turnoverData?.data || { fast_moving: [], slow_moving: [], dead_stock: [] }

  if (isLoading) {
    return (
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-700 rounded w-1/4 mb-6"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="bg-gray-700 rounded-lg p-4">
                <div className="h-4 bg-gray-600 rounded w-1/2 mb-2"></div>
                <div className="h-8 bg-gray-600 rounded w-3/4 mb-1"></div>
                <div className="h-3 bg-gray-600 rounded w-1/3"></div>
              </div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="text-center text-red-400">
          <p>Failed to load inventory data</p>
          <p className="text-sm text-gray-400 mt-1">Please try refreshing the page</p>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <CubeIcon className="h-6 w-6 text-yellow-500" />
          <h2 className="text-xl font-semibold text-white">Inventory Management</h2>
        </div>
        
        <div className="flex space-x-3">
          <button
            onClick={() => refetch()}
            className="bg-gray-700 hover:bg-gray-600 px-3 py-2 rounded-lg flex items-center space-x-2 transition-colors"
          >
            <ArrowPathIcon className="h-4 w-4" />
            <span>Refresh</span>
          </button>
          
          <button className="bg-yellow-500 hover:bg-yellow-600 text-black px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors font-medium">
            <PlusIcon className="h-4 w-4" />
            <span>Add Location</span>
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex space-x-4 mb-6">
        <select
          value={selectedLocation}
          onChange={(e) => setSelectedLocation(e.target.value)}
          className="bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
        >
          <option value="all">All Locations</option>
          <option value="Main Store">Main Store</option>
          <option value="Warehouse">Warehouse</option>
          <option value="Vault">Vault</option>
        </select>
        
        <select
          value={selectedCategory}
          onChange={(e) => setSelectedCategory(e.target.value)}
          className="bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
        >
          <option value="all">All Categories</option>
          <option value="premium">Premium</option>
          <option value="standard">Standard</option>
          <option value="bulk">Bulk</option>
        </select>
      </div>

      {/* Navigation Tabs */}
      <div className="flex space-x-4 mb-6 border-b border-gray-600">
        <button
          onClick={() => setActiveTab('overview')}
          className={`pb-2 px-1 border-b-2 font-medium text-sm transition-colors ${
            activeTab === 'overview'
              ? 'border-yellow-500 text-yellow-400'
              : 'border-transparent text-gray-400 hover:text-gray-300'
          }`}
        >
          Overview
        </button>
        <button
          onClick={() => setActiveTab('dead-stock')}
          className={`pb-2 px-1 border-b-2 font-medium text-sm transition-colors ${
            activeTab === 'dead-stock'
              ? 'border-yellow-500 text-yellow-400'
              : 'border-transparent text-gray-400 hover:text-gray-300'
          }`}
        >
          Dead Stock Analysis
        </button>
        <button
          onClick={() => setActiveTab('turnover')}
          className={`pb-2 px-1 border-b-2 font-medium text-sm transition-colors ${
            activeTab === 'turnover'
              ? 'border-yellow-500 text-yellow-400'
              : 'border-transparent text-gray-400 hover:text-gray-300'
          }`}
        >
          Turnover Analysis
        </button>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && <OverviewTab metrics={metrics} />}
      {activeTab === 'dead-stock' && <DeadStockTab deadStock={deadStock} />}
      {activeTab === 'turnover' && <TurnoverTab turnover={turnover} />}
    </div>
  )
}

// Overview Tab Component
function OverviewTab({ metrics }) {
  return (
    <>
      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <MetricCard
          title="Total Inventory"
          value={metrics?.total_coins?.toLocaleString() || '0'}
          subtitle={`$${metrics?.total_value?.toLocaleString() || '0'}`}
          icon={CubeIcon}
          color="text-blue-400"
          bgColor="bg-blue-500/10"
        />
        
        <MetricCard
          title="Dead Stock"
          value={metrics?.dead_stock_count?.toLocaleString() || '0'}
          subtitle={`$${metrics?.dead_stock_value?.toLocaleString() || '0'}`}
          icon={ExclamationTriangleIcon}
          color="text-red-400"
          bgColor="bg-red-500/10"
        />
        
        <MetricCard
          title="Turnover Rate"
          value={`${metrics?.turnover_rate?.toFixed(1) || '0'}x`}
          subtitle="per year"
          icon={ArrowTrendingUpIcon}
          color="text-green-400"
          bgColor="bg-green-500/10"
        />
        
        <MetricCard
          title="Avg Value/Coin"
          value={`$${metrics?.average_value_per_coin?.toFixed(2) || '0.00'}`}
          subtitle="per coin"
          icon={ChartBarIcon}
          color="text-yellow-400"
          bgColor="bg-yellow-500/10"
        />
      </div>

      {/* Location Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <LocationBreakdown locations={metrics?.location_breakdown || []} />
        <MarginAnalysis margins={metrics?.profit_margin_analysis || []} />
      </div>

      {/* Category Breakdown */}
      <div className="bg-gray-700 rounded-lg p-4 border border-gray-600">
        <h3 className="text-lg font-semibold text-white mb-4">Category Breakdown</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {metrics?.category_breakdown?.map((category) => (
            <div key={category.category} className="bg-gray-600 rounded-lg p-3">
              <div className="text-sm text-gray-300 mb-1 capitalize">{category.category}</div>
              <div className="text-lg font-bold text-white">{category.coin_count}</div>
              <div className="text-sm text-gray-400">coins</div>
              <div className="text-sm text-yellow-400">${category.total_value.toLocaleString()}</div>
            </div>
          ))}
        </div>
      </div>
    </>
  )
}

// Dead Stock Tab Component
function DeadStockTab({ deadStock }) {
  return (
    <div className="bg-gray-700 rounded-lg p-4 border border-gray-600">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">Dead Stock Analysis</h3>
        <div className="text-sm text-gray-400">
          {deadStock.length} items identified
        </div>
      </div>
      
      <div className="space-y-3">
        {deadStock.slice(0, 10).map((item) => (
          <div key={item.id} className="bg-gray-600 rounded-lg p-3">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium text-white">{item.coin_title}</div>
                <div className="text-sm text-gray-400">{item.coin_category}</div>
              </div>
              <div className="text-right">
                <div className="text-yellow-400 font-medium">${item.coin_value.toFixed(2)}</div>
                <div className="text-sm text-gray-400">
                  {item.days_since_last_sale ? `${item.days_since_last_sale} days` : 'No sales'}
                </div>
              </div>
            </div>
            <div className="mt-2 flex items-center space-x-4 text-xs text-gray-400">
              <span>Added: {item.days_since_added} days ago</span>
              {item.profit_margin && (
                <span>Margin: {item.profit_margin.toFixed(1)}%</span>
              )}
            </div>
          </div>
        ))}
      </div>
      
      {deadStock.length === 0 && (
        <div className="text-center text-gray-400 py-8">
          <CubeIcon className="h-12 w-12 mx-auto mb-4 opacity-50" />
          <p>No dead stock identified</p>
          <p className="text-sm">All inventory is moving well!</p>
        </div>
      )}
    </div>
  )
}

// Turnover Tab Component
function TurnoverTab({ turnover }) {
  return (
    <div className="space-y-6">
      {/* Fast Moving */}
      <div className="bg-gray-700 rounded-lg p-4 border border-gray-600">
        <h3 className="text-lg font-semibold text-green-400 mb-4">Fast Moving Items</h3>
        <div className="space-y-2">
          {turnover.fast_moving.slice(0, 5).map((item) => (
            <div key={item.id} className="bg-gray-600 rounded-lg p-3">
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium text-white">{item.coin_title}</div>
                  <div className="text-sm text-gray-400">{item.sales_count} sales</div>
                </div>
                <div className="text-right">
                  <div className="text-green-400 font-medium">${item.total_revenue.toFixed(2)}</div>
                  <div className="text-sm text-gray-400">{item.sales_velocity.toFixed(2)}/day</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Slow Moving */}
      <div className="bg-gray-700 rounded-lg p-4 border border-gray-600">
        <h3 className="text-lg font-semibold text-yellow-400 mb-4">Slow Moving Items</h3>
        <div className="space-y-2">
          {turnover.slow_moving.slice(0, 5).map((item) => (
            <div key={item.id} className="bg-gray-600 rounded-lg p-3">
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium text-white">{item.coin_title}</div>
                  <div className="text-sm text-gray-400">{item.sales_count} sales</div>
                </div>
                <div className="text-right">
                  <div className="text-yellow-400 font-medium">${item.total_revenue.toFixed(2)}</div>
                  <div className="text-sm text-gray-400">{item.sales_velocity.toFixed(2)}/day</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Dead Stock */}
      <div className="bg-gray-700 rounded-lg p-4 border border-gray-600">
        <h3 className="text-lg font-semibold text-red-400 mb-4">Dead Stock Items</h3>
        <div className="space-y-2">
          {turnover.dead_stock.slice(0, 5).map((item) => (
            <div key={item.id} className="bg-gray-600 rounded-lg p-3">
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium text-white">{item.coin_title}</div>
                  <div className="text-sm text-gray-400">{item.sales_count} sales</div>
                </div>
                <div className="text-right">
                  <div className="text-red-400 font-medium">${item.total_revenue.toFixed(2)}</div>
                  <div className="text-sm text-gray-400">{item.sales_velocity.toFixed(2)}/day</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

// Supporting Components
function MetricCard({ title, value, subtitle, icon: Icon, color, bgColor }) {
  return (
    <div className="bg-gray-700 rounded-lg p-4 border border-gray-600">
      <div className="flex items-center justify-between mb-2">
        <div className={`p-2 rounded-lg ${bgColor}`}>
          <Icon className={`h-5 w-5 ${color}`} />
        </div>
      </div>
      <div className="text-2xl font-bold text-white mb-1">{value}</div>
      <div className="text-sm text-gray-400 mb-1">{title}</div>
      {subtitle && <div className="text-xs text-gray-500">{subtitle}</div>}
    </div>
  )
}

function LocationBreakdown({ locations }) {
  return (
    <div className="bg-gray-700 rounded-lg p-4 border border-gray-600">
      <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
        <MapPinIcon className="h-5 w-5 mr-2 text-blue-400" />
        Location Breakdown
      </h3>
      <div className="space-y-3">
        {locations.map((location) => (
          <div key={location.location_id} className="flex items-center justify-between">
            <div>
              <div className="text-white font-medium">{location.location_name}</div>
              <div className="text-sm text-gray-400">{location.coin_count} coins</div>
            </div>
            <div className="text-right">
              <div className="text-green-400 font-medium">${location.total_value.toLocaleString()}</div>
              <div className="text-sm text-gray-400">{location.profit_margin.toFixed(1)}% margin</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function MarginAnalysis({ margins }) {
  return (
    <div className="bg-gray-700 rounded-lg p-4 border border-gray-600">
      <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
        <ChartBarIcon className="h-5 w-5 mr-2 text-yellow-400" />
        Profit Margin Analysis
      </h3>
      <div className="space-y-3">
        {margins.map((margin) => (
          <div key={margin.category} className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-white capitalize">{margin.category}</span>
              <span className="text-yellow-400 font-medium">{margin.average_margin.toFixed(1)}%</span>
            </div>
            <div className="w-full bg-gray-600 rounded-full h-2">
              <div 
                className="bg-yellow-400 h-2 rounded-full"
                style={{ width: `${Math.min(margin.average_margin, 100)}%` }}
              ></div>
            </div>
            <div className="text-xs text-gray-400">
              {margin.coin_count} coins • ${margin.total_value.toLocaleString()}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}


