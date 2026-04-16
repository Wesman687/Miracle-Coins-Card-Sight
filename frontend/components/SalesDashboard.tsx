import { useState, useEffect } from 'react'
import { useQuery } from 'react-query'
import { 
  ChartBarIcon, 
  CurrencyDollarIcon,
  ArrowTrendingUpIcon,
  ShoppingCartIcon,
  UsersIcon,
  ClockIcon
} from '@heroicons/react/24/outline'
import { api } from '../lib/api'
import { Coin } from '../types'

interface SalesMetrics {
  total_sales: number
  sales_by_channel: ChannelSales[]
  top_selling_coins: Coin[]
  profit_per_coin: number
  sales_velocity: number
  revenue_forecast: ForecastData[]
  period_comparison: PeriodComparison
  total_profit: number
  sales_count: number
  unique_customers: number
  average_sale_value: number
  profit_margin_percentage: number
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

interface ForecastFactor {
  name: string
  impact: 'positive' | 'negative' | 'neutral'
  weight: number
  description: string
}

export default function SalesDashboard() {
  const [selectedPeriod, setSelectedPeriod] = useState<'daily' | 'weekly' | 'monthly'>('daily')
  const [selectedChannel, setSelectedChannel] = useState<string>('all')

  const { data: salesData, isLoading, error } = useQuery(
    ['sales-dashboard', selectedPeriod, selectedChannel],
    () => api.get(`/sales/dashboard?period=${selectedPeriod}&channel=${selectedChannel}`),
    {
      refetchInterval: 30000, // Refresh every 30 seconds
      retry: 3,
    }
  )

  const metrics = salesData?.data

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
          <p>Failed to load sales dashboard</p>
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
          value={`${metrics?.sales_velocity?.toFixed(1) || '0'} coins/day`}
          icon={ArrowTrendingUpIcon}
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

      {/* Secondary Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <MetricCard
          title="Total Profit"
          value={`$${metrics?.total_profit?.toLocaleString() || '0'}`}
          icon={CurrencyDollarIcon}
          color="text-green-400"
          bgColor="bg-green-500/10"
        />
        
        <MetricCard
          title="Sales Count"
          value={`${metrics?.sales_count?.toLocaleString() || '0'}`}
          icon={ShoppingCartIcon}
          color="text-blue-400"
          bgColor="bg-blue-500/10"
        />
        
        <MetricCard
          title="Unique Customers"
          value={`${metrics?.unique_customers?.toLocaleString() || '0'}`}
          icon={UsersIcon}
          color="text-purple-400"
          bgColor="bg-purple-500/10"
        />
        
        <MetricCard
          title="Avg Sale Value"
          value={`$${metrics?.average_sale_value?.toFixed(2) || '0.00'}`}
          icon={ChartBarIcon}
          color="text-yellow-400"
          bgColor="bg-yellow-500/10"
        />
      </div>

      {/* Sales by Channel */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <ChannelBreakdown channels={metrics?.sales_by_channel || []} />
        <TopSellingCoins coins={metrics?.top_selling_coins || []} />
      </div>

      {/* Profit Margin Analysis */}
      <div className="bg-gray-700 rounded-lg p-4 border border-gray-600">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
          <ChartBarIcon className="h-5 w-5 mr-2 text-yellow-400" />
          Profit Margin Analysis
        </h3>
        <div className="flex items-center justify-between">
          <div>
            <div className="text-2xl font-bold text-yellow-400">
              {metrics?.profit_margin_percentage?.toFixed(1) || '0'}%
            </div>
            <div className="text-sm text-gray-400">Overall Profit Margin</div>
          </div>
          <div className="text-right">
            <div className="text-sm text-gray-300">Target: 50-60%</div>
            <div className={`text-sm ${
              (metrics?.profit_margin_percentage || 0) >= 50 ? 'text-green-400' : 'text-red-400'
            }`}>
              {(metrics?.profit_margin_percentage || 0) >= 50 ? 'Above Target' : 'Below Target'}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// Supporting Components
function MetricCard({ title, value, icon: Icon, color, bgColor, trend, change }: {
  title: string
  value: string
  icon: any
  color: string
  bgColor: string
  trend?: string
  change?: number
}) {
  return (
    <div className="bg-gray-700 rounded-lg p-4 border border-gray-600">
      <div className="flex items-center justify-between mb-2">
        <div className={`p-2 rounded-lg ${bgColor}`}>
          <Icon className={`h-5 w-5 ${color}`} />
        </div>
        {trend && (
          <div className={`text-sm flex items-center space-x-1 ${
            trend === 'up' ? 'text-green-400' : trend === 'down' ? 'text-red-400' : 'text-gray-400'
          }`}>
            <ArrowTrendingUpIcon className={`h-4 w-4 ${
              trend === 'down' ? 'rotate-180' : ''
            }`} />
            <span>{change > 0 ? '+' : ''}{change?.toFixed(1)}%</span>
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
      
      {/* Channel Performance Chart */}
      <div className="mt-4">
        <div className="text-sm text-gray-400 mb-2">Channel Performance</div>
        <div className="space-y-2">
          {channels.map((channel) => (
            <div key={channel.channel} className="flex items-center space-x-2">
              <div className="w-16 text-xs text-gray-300 capitalize">
                {channel.channel.replace('_', ' ')}
              </div>
              <div className="flex-1 bg-gray-600 rounded-full h-2">
                <div 
                  className="bg-yellow-400 h-2 rounded-full"
                  style={{ width: `${channel.percentage}%` }}
                ></div>
              </div>
              <div className="w-12 text-xs text-gray-300 text-right">
                {channel.percentage.toFixed(1)}%
              </div>
            </div>
          ))}
        </div>
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
      
      {coins.length === 0 && (
        <div className="text-center text-gray-400 py-4">
          <ShoppingCartIcon className="h-8 w-8 mx-auto mb-2 opacity-50" />
          <p>No sales data available</p>
        </div>
      )}
    </div>
  )
}


