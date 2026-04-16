# 🎨 Frontend Implementation Plan
## Miracle Coins CoinSync Pro - Detailed Frontend Development

---

## 📋 **Frontend Architecture Overview**

### **Technology Stack:**
- **Framework**: Next.js 14.2.33 with TypeScript
- **Styling**: Tailwind CSS with custom design system
- **State Management**: React Query + Zustand
- **UI Components**: Headless UI + Custom components
- **Mobile**: Responsive design with PWA capabilities
- **Performance**: Virtual scrolling, lazy loading, memoization

### **Design System:**
- **Theme**: Black/Gold professional theme
- **Typography**: Inter font family
- **Spacing**: Consistent 4px grid system
- **Colors**: Miracle Gold (#FFD700), Miracle Black (#000000)
- **Components**: Modular, reusable, accessible

---

## 🎯 **Phase 1: Sales Dashboard & Revenue Forecasting (Weeks 1-2)**

### **1.1 Enhanced Sales Dashboard Component**

#### **File: `components/SalesDashboard.tsx`**
```typescript
import { useState, useEffect } from 'react'
import { useQuery } from 'react-query'
import { 
  ChartBarIcon, 
  CurrencyDollarIcon,
  TrendingUpIcon,
  ShoppingCartIcon,
  UsersIcon
} from '@heroicons/react/24/outline'
import { api } from '../lib/api'

interface SalesMetrics {
  total_sales: number
  sales_by_channel: ChannelSales[]
  top_selling_coins: Coin[]
  profit_per_coin: number
  sales_velocity: number
  revenue_forecast: ForecastData[]
  period_comparison: PeriodComparison
}

interface ChannelSales {
  channel: 'shopify' | 'in_store' | 'auction' | 'direct'
  sales_count: number
  revenue: number
  profit: number
  percentage: number
}

interface ForecastData {
  period: string
  predicted_revenue: number
  confidence_range: { min: number; max: number }
  factors: ForecastFactor[]
}

interface PeriodComparison {
  current_period: number
  previous_period: number
  change_percentage: number
  trend: 'up' | 'down' | 'stable'
}

export default function SalesDashboard() {
  const [selectedPeriod, setSelectedPeriod] = useState<'daily' | 'weekly' | 'monthly'>('daily')
  const [selectedChannel, setSelectedChannel] = useState<string>('all')

  const { data: salesData, isLoading } = useQuery(
    ['sales-dashboard', selectedPeriod, selectedChannel],
    () => api.get(`/sales/dashboard?period=${selectedPeriod}&channel=${selectedChannel}`),
    {
      refetchInterval: 30000, // Refresh every 30 seconds
    }
  )

  const metrics = salesData?.data

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <ChartBarIcon className="h-6 w-6 text-yellow-500" />
          <h2 className="text-xl font-semibold text-white">Sales Dashboard</h2>
        </div>
        
        {/* Period Selector */}
        <div className="flex space-x-2">
          {['daily', 'weekly', 'monthly'].map((period) => (
            <button
              key={period}
              onClick={() => setSelectedPeriod(period as any)}
              className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
                selectedPeriod === period
                  ? 'bg-yellow-500 text-black'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              {period.charAt(0).toUpperCase() + period.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <MetricCard
          title="Total Sales"
          value={`$${metrics?.total_sales?.toLocaleString() || '0'}`}
          icon={CurrencyDollarIcon}
          color="text-green-400"
          bgColor="bg-green-500/10"
          trend={metrics?.period_comparison?.trend}
          change={metrics?.period_comparison?.change_percentage}
        />
        
        <MetricCard
          title="Sales Velocity"
          value={`${metrics?.sales_velocity || 0} coins/day`}
          icon={TrendingUpIcon}
          color="text-blue-400"
          bgColor="bg-blue-500/10"
        />
        
        <MetricCard
          title="Profit per Coin"
          value={`$${metrics?.profit_per_coin?.toFixed(2) || '0.00'}`}
          icon={ChartBarIcon}
          color="text-yellow-400"
          bgColor="bg-yellow-500/10"
        />
        
        <MetricCard
          title="Active Channels"
          value={`${metrics?.sales_by_channel?.length || 0}`}
          icon={ShoppingCartIcon}
          color="text-purple-400"
          bgColor="bg-purple-500/10"
        />
      </div>

      {/* Sales by Channel */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChannelBreakdown channels={metrics?.sales_by_channel || []} />
        <TopSellingCoins coins={metrics?.top_selling_coins || []} />
      </div>
    </div>
  )
}

// Supporting Components
function MetricCard({ title, value, icon: Icon, color, bgColor, trend, change }) {
  return (
    <div className="bg-gray-700 rounded-lg p-4 border border-gray-600">
      <div className="flex items-center justify-between mb-2">
        <div className={`p-2 rounded-lg ${bgColor}`}>
          <Icon className={`h-5 w-5 ${color}`} />
        </div>
        {trend && (
          <div className={`text-sm ${trend === 'up' ? 'text-green-400' : trend === 'down' ? 'text-red-400' : 'text-gray-400'}`}>
            {change > 0 ? '+' : ''}{change?.toFixed(1)}%
          </div>
        )}
      </div>
      <div className="text-2xl font-bold text-white mb-1">{value}</div>
      <div className="text-sm text-gray-400">{title}</div>
    </div>
  )
}

function ChannelBreakdown({ channels }) {
  return (
    <div className="bg-gray-700 rounded-lg p-4 border border-gray-600">
      <h3 className="text-lg font-semibold text-white mb-4">Sales by Channel</h3>
      <div className="space-y-3">
        {channels.map((channel) => (
          <div key={channel.channel} className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-3 h-3 rounded-full bg-yellow-400"></div>
              <span className="text-white capitalize">{channel.channel.replace('_', ' ')}</span>
            </div>
            <div className="text-right">
              <div className="text-white font-medium">${channel.revenue.toLocaleString()}</div>
              <div className="text-sm text-gray-400">{channel.sales_count} sales</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function TopSellingCoins({ coins }) {
  return (
    <div className="bg-gray-700 rounded-lg p-4 border border-gray-600">
      <h3 className="text-lg font-semibold text-white mb-4">Top Selling Coins</h3>
      <div className="space-y-3">
        {coins.slice(0, 5).map((coin, index) => (
          <div key={coin.id} className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-6 h-6 rounded-full bg-yellow-500 flex items-center justify-center text-black text-xs font-bold">
                {index + 1}
              </div>
              <span className="text-white text-sm">{coin.title}</span>
            </div>
            <div className="text-right">
              <div className="text-white font-medium">${coin.total_sales.toLocaleString()}</div>
              <div className="text-sm text-gray-400">{coin.sales_count} sold</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
```

### **1.2 Revenue Forecasting Component**

#### **File: `components/RevenueForecast.tsx`**
```typescript
import { useState } from 'react'
import { useQuery } from 'react-query'
import { 
  ChartBarIcon,
  CalendarIcon,
  TrendingUpIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline'
import { api } from '../lib/api'

interface ForecastSettings {
  time_period: 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'yearly'
  forecast_horizon: number
  confidence_level: number
  include_seasonality: boolean
  include_trends: boolean
}

interface ForecastData {
  period: string
  predicted_revenue: number
  confidence_range: { min: number; max: number }
  factors: ForecastFactor[]
  accuracy_score: number
}

interface ForecastFactor {
  name: string
  impact: 'positive' | 'negative' | 'neutral'
  weight: number
  description: string
}

export default function RevenueForecast() {
  const [settings, setSettings] = useState<ForecastSettings>({
    time_period: 'monthly',
    forecast_horizon: 3,
    confidence_level: 80,
    include_seasonality: true,
    include_trends: true
  })

  const { data: forecastData, isLoading } = useQuery(
    ['revenue-forecast', settings],
    () => api.post('/sales/forecast', settings),
    {
      refetchInterval: 300000, // Refresh every 5 minutes
    }
  )

  const forecast = forecastData?.data

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <TrendingUpIcon className="h-6 w-6 text-yellow-500" />
          <h2 className="text-xl font-semibold text-white">Revenue Forecast</h2>
        </div>
        
        <button
          onClick={() => {/* Open settings modal */}}
          className="bg-gray-700 hover:bg-gray-600 px-3 py-2 rounded-lg flex items-center space-x-2 transition-colors"
        >
          <CalendarIcon className="h-4 w-4" />
          <span>Settings</span>
        </button>
      </div>

      {/* Forecast Settings */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">
            Time Period
          </label>
          <select
            value={settings.time_period}
            onChange={(e) => setSettings({...settings, time_period: e.target.value as any})}
            className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
          >
            <option value="daily">Daily</option>
            <option value="weekly">Weekly</option>
            <option value="monthly">Monthly</option>
            <option value="quarterly">Quarterly</option>
            <option value="yearly">Yearly</option>
          </select>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">
            Forecast Horizon
          </label>
          <input
            type="number"
            min="1"
            max="12"
            value={settings.forecast_horizon}
            onChange={(e) => setSettings({...settings, forecast_horizon: parseInt(e.target.value)})}
            className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">
            Confidence Level
          </label>
          <input
            type="range"
            min="50"
            max="95"
            step="5"
            value={settings.confidence_level}
            onChange={(e) => setSettings({...settings, confidence_level: parseInt(e.target.value)})}
            className="w-full"
          />
          <div className="text-sm text-gray-400 text-center">{settings.confidence_level}%</div>
        </div>
      </div>

      {/* Forecast Chart */}
      <div className="bg-gray-700 rounded-lg p-4 mb-6">
        <h3 className="text-lg font-semibold text-white mb-4">Revenue Forecast</h3>
        {/* Chart component would go here */}
        <div className="h-64 bg-gray-600 rounded-lg flex items-center justify-center">
          <span className="text-gray-400">Chart visualization will be implemented</span>
        </div>
      </div>

      {/* Forecast Data Table */}
      <div className="bg-gray-700 rounded-lg p-4">
        <h3 className="text-lg font-semibold text-white mb-4">Forecast Details</h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-600">
                <th className="text-left text-gray-300 py-2">Period</th>
                <th className="text-left text-gray-300 py-2">Predicted Revenue</th>
                <th className="text-left text-gray-300 py-2">Confidence Range</th>
                <th className="text-left text-gray-300 py-2">Accuracy</th>
              </tr>
            </thead>
            <tbody>
              {forecast?.forecast_data?.map((item, index) => (
                <tr key={index} className="border-b border-gray-600">
                  <td className="py-2 text-white">{item.period}</td>
                  <td className="py-2 text-green-400 font-medium">
                    ${item.predicted_revenue.toLocaleString()}
                  </td>
                  <td className="py-2 text-gray-300">
                    ${item.confidence_range.min.toLocaleString()} - ${item.confidence_range.max.toLocaleString()}
                  </td>
                  <td className="py-2">
                    <div className="flex items-center space-x-2">
                      <div className={`w-2 h-2 rounded-full ${
                        item.accuracy_score >= 80 ? 'bg-green-400' : 
                        item.accuracy_score >= 60 ? 'bg-yellow-400' : 'bg-red-400'
                      }`}></div>
                      <span className="text-gray-300">{item.accuracy_score}%</span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
```

---

## 🎯 **Phase 2: Advanced Inventory Management (Weeks 3-4)**

### **2.1 Inventory Manager Component**

#### **File: `components/InventoryManager.tsx`**
```typescript
import { useState } from 'react'
import { useQuery } from 'react-query'
import { 
  CubeIcon,
  ExclamationTriangleIcon,
  TrendingUpIcon,
  MapPinIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline'
import { api } from '../lib/api'

interface InventoryMetrics {
  total_coins: number
  total_value: number
  dead_stock_count: number
  dead_stock_value: number
  profit_margin_analysis: MarginAnalysis[]
  location_breakdown: LocationInventory[]
  turnover_analysis: TurnoverAnalysis
}

interface LocationInventory {
  location_id: string
  location_name: string
  coin_count: number
  total_value: number
  profit_margin: number
  last_updated: string
}

interface MarginAnalysis {
  category: string
  average_margin: number
  min_margin: number
  max_margin: number
  coin_count: number
  total_value: number
}

interface TurnoverAnalysis {
  fast_moving: Coin[]
  slow_moving: Coin[]
  dead_stock: Coin[]
  turnover_rate: number
}

export default function InventoryManager() {
  const [selectedLocation, setSelectedLocation] = useState<string>('all')
  const [selectedCategory, setSelectedCategory] = useState<string>('all')

  const { data: inventoryData, isLoading } = useQuery(
    ['inventory-metrics', selectedLocation, selectedCategory],
    () => api.get(`/inventory/metrics?location=${selectedLocation}&category=${selectedCategory}`),
    {
      refetchInterval: 60000, // Refresh every minute
    }
  )

  const metrics = inventoryData?.data

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <CubeIcon className="h-6 w-6 text-yellow-500" />
          <h2 className="text-xl font-semibold text-white">Inventory Management</h2>
        </div>
        
        <div className="flex space-x-3">
          <select
            value={selectedLocation}
            onChange={(e) => setSelectedLocation(e.target.value)}
            className="bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
          >
            <option value="all">All Locations</option>
            <option value="main">Main Store</option>
            <option value="warehouse">Warehouse</option>
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
      </div>

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
          value={`${metrics?.turnover_analysis?.turnover_rate?.toFixed(1) || '0'}x`}
          subtitle="per year"
          icon={TrendingUpIcon}
          color="text-green-400"
          bgColor="bg-green-500/10"
        />
        
        <MetricCard
          title="Avg Profit Margin"
          value={`${metrics?.profit_margin_analysis?.[0]?.average_margin?.toFixed(1) || '0'}%`}
          subtitle="across all items"
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

      {/* Turnover Analysis */}
      <TurnoverAnalysis turnover={metrics?.turnover_analysis} />
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

function TurnoverAnalysis({ turnover }) {
  return (
    <div className="bg-gray-700 rounded-lg p-4 border border-gray-600">
      <h3 className="text-lg font-semibold text-white mb-4">Turnover Analysis</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <h4 className="text-green-400 font-medium mb-2">Fast Moving</h4>
          <div className="space-y-1">
            {turnover?.fast_moving?.slice(0, 3).map((coin) => (
              <div key={coin.id} className="text-sm text-gray-300">
                {coin.title} - {coin.sales_count} sold
              </div>
            ))}
          </div>
        </div>
        
        <div>
          <h4 className="text-yellow-400 font-medium mb-2">Slow Moving</h4>
          <div className="space-y-1">
            {turnover?.slow_moving?.slice(0, 3).map((coin) => (
              <div key={coin.id} className="text-sm text-gray-300">
                {coin.title} - {coin.days_since_sale} days
              </div>
            ))}
          </div>
        </div>
        
        <div>
          <h4 className="text-red-400 font-medium mb-2">Dead Stock</h4>
          <div className="space-y-1">
            {turnover?.dead_stock?.slice(0, 3).map((coin) => (
              <div key={coin.id} className="text-sm text-gray-300">
                {coin.title} - {coin.days_since_sale} days
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
```

---

## 🎯 **Phase 3: Advanced Search & Bulk Operations (Weeks 5-6)**

### **3.1 Advanced Search Component**

#### **File: `components/AdvancedSearch.tsx`**
```typescript
import { useState, useEffect } from 'react'
import { useQuery } from 'react-query'
import { 
  MagnifyingGlassIcon,
  FunnelIcon,
  XMarkIcon,
  ClockIcon
} from '@heroicons/react/24/outline'
import { api } from '../lib/api'

interface SearchCriteria {
  title?: string
  year_range?: { min: number; max: number }
  denomination?: string[]
  grade?: string[]
  mint_mark?: string[]
  is_silver?: boolean
  silver_content_range?: { min: number; max: number }
  price_range?: { min: number; max: number }
  profit_margin_range?: { min: number; max: number }
  category?: ('premium' | 'standard' | 'bulk')[]
  location?: string[]
  status?: string[]
  date_added_range?: { start: string; end: string }
}

interface SearchResult {
  coins: Coin[]
  total_count: number
  facets: SearchFacets
  execution_time: number
}

interface SearchFacets {
  denominations: FacetItem[]
  grades: FacetItem[]
  mint_marks: FacetItem[]
  categories: FacetItem[]
  locations: FacetItem[]
  years: FacetRange
  prices: FacetRange
}

interface FacetItem {
  value: string
  count: number
}

interface FacetRange {
  min: number
  max: number
  distribution: { value: number; count: number }[]
}

export default function AdvancedSearch() {
  const [searchCriteria, setSearchCriteria] = useState<SearchCriteria>({})
  const [showFilters, setShowFilters] = useState(false)
  const [searchHistory, setSearchHistory] = useState<string[]>([])

  const { data: searchResults, isLoading } = useQuery(
    ['advanced-search', searchCriteria],
    () => api.post('/search/advanced', searchCriteria),
    {
      enabled: Object.keys(searchCriteria).length > 0,
    }
  )

  const { data: facets } = useQuery(
    'search-facets',
    () => api.get('/search/facets')
  )

  const handleSearch = (criteria: SearchCriteria) => {
    setSearchCriteria(criteria)
    // Add to search history
    const searchString = JSON.stringify(criteria)
    if (!searchHistory.includes(searchString)) {
      setSearchHistory(prev => [searchString, ...prev.slice(0, 9)])
    }
  }

  const clearFilters = () => {
    setSearchCriteria({})
  }

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      {/* Search Header */}
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
            onClick={clearFilters}
            className="bg-red-500 hover:bg-red-600 px-3 py-2 rounded-lg flex items-center space-x-2 transition-colors"
          >
            <XMarkIcon className="h-4 w-4" />
            <span>Clear</span>
          </button>
        </div>
      </div>

      {/* Quick Search Bar */}
      <div className="mb-6">
        <div className="relative">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search coins by title, year, denomination..."
            className="w-full bg-gray-700 border border-gray-600 rounded-lg pl-10 pr-4 py-3 text-white placeholder-gray-400 focus:outline-none focus:border-yellow-500"
            onChange={(e) => {
              if (e.target.value) {
                handleSearch({ ...searchCriteria, title: e.target.value })
              }
            }}
          />
        </div>
      </div>

      {/* Search History */}
      {searchHistory.length > 0 && (
        <div className="mb-6">
          <h3 className="text-sm font-medium text-gray-300 mb-2 flex items-center">
            <ClockIcon className="h-4 w-4 mr-2" />
            Recent Searches
          </h3>
          <div className="flex flex-wrap gap-2">
            {searchHistory.slice(0, 5).map((search, index) => (
              <button
                key={index}
                onClick={() => setSearchCriteria(JSON.parse(search))}
                className="bg-gray-700 hover:bg-gray-600 px-3 py-1 rounded-lg text-sm text-gray-300 transition-colors"
              >
                {JSON.parse(search).title || 'Custom Search'}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Advanced Filters */}
      {showFilters && (
        <SearchFilters
          criteria={searchCriteria}
          facets={facets?.data}
          onCriteriaChange={handleSearch}
        />
      )}

      {/* Search Results */}
      <SearchResults
        results={searchResults?.data}
        isLoading={isLoading}
        onCoinSelect={(coin) => {/* Handle coin selection */}}
      />
    </div>
  )
}

// Search Filters Component
function SearchFilters({ criteria, facets, onCriteriaChange }) {
  const [localCriteria, setLocalCriteria] = useState(criteria)

  const updateCriteria = (updates: Partial<SearchCriteria>) => {
    const newCriteria = { ...localCriteria, ...updates }
    setLocalCriteria(newCriteria)
    onCriteriaChange(newCriteria)
  }

  return (
    <div className="bg-gray-700 rounded-lg p-4 mb-6">
      <h3 className="text-lg font-semibold text-white mb-4">Advanced Filters</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Year Range */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">Year Range</label>
          <div className="flex space-x-2">
            <input
              type="number"
              placeholder="Min"
              value={localCriteria.year_range?.min || ''}
              onChange={(e) => updateCriteria({
                year_range: {
                  min: parseInt(e.target.value) || undefined,
                  max: localCriteria.year_range?.max
                }
              })}
              className="flex-1 bg-gray-600 border border-gray-500 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
            />
            <input
              type="number"
              placeholder="Max"
              value={localCriteria.year_range?.max || ''}
              onChange={(e) => updateCriteria({
                year_range: {
                  min: localCriteria.year_range?.min,
                  max: parseInt(e.target.value) || undefined
                }
              })}
              className="flex-1 bg-gray-600 border border-gray-500 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
            />
          </div>
        </div>

        {/* Price Range */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">Price Range</label>
          <div className="flex space-x-2">
            <input
              type="number"
              placeholder="Min $"
              value={localCriteria.price_range?.min || ''}
              onChange={(e) => updateCriteria({
                price_range: {
                  min: parseFloat(e.target.value) || undefined,
                  max: localCriteria.price_range?.max
                }
              })}
              className="flex-1 bg-gray-600 border border-gray-500 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
            />
            <input
              type="number"
              placeholder="Max $"
              value={localCriteria.price_range?.max || ''}
              onChange={(e) => updateCriteria({
                price_range: {
                  min: localCriteria.price_range?.min,
                  max: parseFloat(e.target.value) || undefined
                }
              })}
              className="flex-1 bg-gray-600 border border-gray-500 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
            />
          </div>
        </div>

        {/* Silver Content */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">Silver Content (oz)</label>
          <div className="flex space-x-2">
            <input
              type="number"
              step="0.001"
              placeholder="Min"
              value={localCriteria.silver_content_range?.min || ''}
              onChange={(e) => updateCriteria({
                silver_content_range: {
                  min: parseFloat(e.target.value) || undefined,
                  max: localCriteria.silver_content_range?.max
                }
              })}
              className="flex-1 bg-gray-600 border border-gray-500 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
            />
            <input
              type="number"
              step="0.001"
              placeholder="Max"
              value={localCriteria.silver_content_range?.max || ''}
              onChange={(e) => updateCriteria({
                silver_content_range: {
                  min: localCriteria.silver_content_range?.min,
                  max: parseFloat(e.target.value) || undefined
                }
              })}
              className="flex-1 bg-gray-600 border border-gray-500 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
            />
          </div>
        </div>

        {/* Denominations */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">Denominations</label>
          <div className="space-y-2 max-h-32 overflow-y-auto">
            {facets?.denominations?.map((denom) => (
              <label key={denom.value} className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={localCriteria.denomination?.includes(denom.value) || false}
                  onChange={(e) => {
                    const denominations = localCriteria.denomination || []
                    if (e.target.checked) {
                      updateCriteria({ denomination: [...denominations, denom.value] })
                    } else {
                      updateCriteria({ denomination: denominations.filter(d => d !== denom.value) })
                    }
                  }}
                  className="rounded border-gray-500 bg-gray-600 text-yellow-500 focus:ring-yellow-500"
                />
                <span className="text-sm text-gray-300">
                  {denom.value} ({denom.count})
                </span>
              </label>
            ))}
          </div>
        </div>

        {/* Categories */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">Categories</label>
          <div className="space-y-2">
            {['premium', 'standard', 'bulk'].map((category) => (
              <label key={category} className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={localCriteria.category?.includes(category as any) || false}
                  onChange={(e) => {
                    const categories = localCriteria.category || []
                    if (e.target.checked) {
                      updateCriteria({ category: [...categories, category as any] })
                    } else {
                      updateCriteria({ category: categories.filter(c => c !== category) })
                    }
                  }}
                  className="rounded border-gray-500 bg-gray-600 text-yellow-500 focus:ring-yellow-500"
                />
                <span className="text-sm text-gray-300 capitalize">{category}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Silver Only Toggle */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">Silver Only</label>
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={localCriteria.is_silver || false}
              onChange={(e) => updateCriteria({ is_silver: e.target.checked })}
              className="rounded border-gray-500 bg-gray-600 text-yellow-500 focus:ring-yellow-500"
            />
            <span className="text-sm text-gray-300">Show only silver coins</span>
          </label>
        </div>
      </div>
    </div>
  )
}

// Search Results Component
function SearchResults({ results, isLoading, onCoinSelect }) {
  if (isLoading) {
    return (
      <div className="bg-gray-700 rounded-lg p-8 text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-yellow-500 mx-auto"></div>
        <p className="mt-2 text-gray-400">Searching...</p>
      </div>
    )
  }

  if (!results) {
    return (
      <div className="bg-gray-700 rounded-lg p-8 text-center">
        <p className="text-gray-400">Enter search criteria to find coins</p>
      </div>
    )
  }

  return (
    <div className="bg-gray-700 rounded-lg p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">
          Search Results ({results.total_count.toLocaleString()})
        </h3>
        <div className="text-sm text-gray-400">
          Found in {results.execution_time}ms
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {results.coins.map((coin) => (
          <div
            key={coin.id}
            onClick={() => onCoinSelect(coin)}
            className="bg-gray-600 rounded-lg p-4 cursor-pointer hover:bg-gray-500 transition-colors"
          >
            <h4 className="font-medium text-white mb-2">{coin.title}</h4>
            <div className="space-y-1 text-sm text-gray-300">
              <div>{coin.year} {coin.denomination}</div>
              <div>Grade: {coin.grade}</div>
              <div className="text-yellow-400 font-medium">
                ${coin.computed_price?.toFixed(2) || 'N/A'}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
```

This comprehensive frontend implementation plan provides the foundation for all the features you requested. Each component is designed to be modular, performant, and maintainable while following your business requirements and design preferences.

Would you like me to continue with the remaining phases (Bulk Operations, Alert System, Shopify Integration, and Mobile Optimization) or would you prefer to focus on implementing these first components?


