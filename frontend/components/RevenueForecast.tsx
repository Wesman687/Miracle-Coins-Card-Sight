import { useState } from 'react'
import { useQuery } from 'react-query'
import { 
  ChartBarIcon,
  CalendarIcon,
  ArrowTrendingUpIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline'
import { api } from '../lib/api'

interface ForecastSettings {
  time_period: 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'yearly'
  forecast_horizon: number
  confidence_level: number
  include_seasonality: boolean
  include_trends: boolean
  include_external_factors: boolean
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

interface SalesForecastResponse {
  forecast_type: string
  forecast_horizon: number
  confidence_level: number
  forecast_data: ForecastData[]
  accuracy_score: number
  created_at: string
  valid_until: string
}

export default function RevenueForecast() {
  const [settings, setSettings] = useState<ForecastSettings>({
    time_period: 'monthly',
    forecast_horizon: 3,
    confidence_level: 80,
    include_seasonality: true,
    include_trends: true,
    include_external_factors: false
  })

  const [showSettings, setShowSettings] = useState(false)

  const { data: forecastData, isLoading, error, refetch } = useQuery(
    ['revenue-forecast', settings],
    () => api.post('/sales/forecast', settings),
    {
      refetchInterval: 300000, // Refresh every 5 minutes
      retry: 3,
      enabled: false, // Don't auto-fetch, require manual trigger
    }
  )

  const forecast = forecastData?.data as SalesForecastResponse

  const handleGenerateForecast = () => {
    refetch()
  }

  const updateSettings = (updates: Partial<ForecastSettings>) => {
    setSettings(prev => ({ ...prev, ...updates }))
  }

  if (isLoading) {
    return (
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-700 rounded w-1/3 mb-6"></div>
          <div className="h-64 bg-gray-700 rounded-lg mb-6"></div>
          <div className="space-y-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="h-16 bg-gray-700 rounded-lg"></div>
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
          <ArrowTrendingUpIcon className="h-6 w-6 text-yellow-500" />
          <h2 className="text-xl font-semibold text-white">Revenue Forecast</h2>
        </div>
        
        <div className="flex space-x-2">
          <button
            onClick={() => setShowSettings(!showSettings)}
            className="bg-gray-700 hover:bg-gray-600 px-3 py-2 rounded-lg flex items-center space-x-2 transition-colors"
          >
            <CalendarIcon className="h-4 w-4" />
            <span>Settings</span>
          </button>
          
          <button
            onClick={handleGenerateForecast}
            className="bg-yellow-500 hover:bg-yellow-600 text-black px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors font-medium"
          >
            <ChartBarIcon className="h-4 w-4" />
            <span>Generate Forecast</span>
          </button>
        </div>
      </div>

      {/* Forecast Settings */}
      {showSettings && (
        <div className="bg-gray-700 rounded-lg p-4 mb-6">
          <h3 className="text-lg font-semibold text-white mb-4">Forecast Settings</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Time Period
              </label>
              <select
                value={settings.time_period}
                onChange={(e) => updateSettings({ time_period: e.target.value as any })}
                className="w-full bg-gray-600 border border-gray-500 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
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
                onChange={(e) => updateSettings({ forecast_horizon: parseInt(e.target.value) })}
                className="w-full bg-gray-600 border border-gray-500 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Confidence Level: {settings.confidence_level}%
              </label>
              <input
                type="range"
                min="50"
                max="95"
                step="5"
                value={settings.confidence_level}
                onChange={(e) => updateSettings({ confidence_level: parseInt(e.target.value) })}
                className="w-full"
              />
            </div>
          </div>

          {/* Advanced Options */}
          <div className="mt-4">
            <h4 className="text-sm font-medium text-gray-300 mb-3">Advanced Options</h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={settings.include_seasonality}
                  onChange={(e) => updateSettings({ include_seasonality: e.target.checked })}
                  className="rounded border-gray-500 bg-gray-600 text-yellow-500 focus:ring-yellow-500"
                />
                <span className="text-sm text-gray-300">Include Seasonality</span>
              </label>
              
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={settings.include_trends}
                  onChange={(e) => updateSettings({ include_trends: e.target.checked })}
                  className="rounded border-gray-500 bg-gray-600 text-yellow-500 focus:ring-yellow-500"
                />
                <span className="text-sm text-gray-300">Include Trends</span>
              </label>
              
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={settings.include_external_factors}
                  onChange={(e) => updateSettings({ include_external_factors: e.target.checked })}
                  className="rounded border-gray-500 bg-gray-600 text-yellow-500 focus:ring-yellow-500"
                />
                <span className="text-sm text-gray-300">External Factors</span>
              </label>
            </div>
          </div>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4 mb-6">
          <div className="flex items-center space-x-2 text-red-400">
            <ExclamationTriangleIcon className="h-5 w-5" />
            <span className="font-medium">Forecast Generation Failed</span>
          </div>
          <p className="text-sm text-red-300 mt-1">
            Unable to generate forecast. Please check your settings and try again.
          </p>
        </div>
      )}

      {/* No Forecast State */}
      {!forecast && !isLoading && !error && (
        <div className="bg-gray-700 rounded-lg p-8 text-center">
          <ChartBarIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-white mb-2">No Forecast Available</h3>
          <p className="text-gray-400 mb-4">
            Generate a revenue forecast to see predicted sales performance
          </p>
          <button
            onClick={handleGenerateForecast}
            className="bg-yellow-500 hover:bg-yellow-600 text-black px-4 py-2 rounded-lg font-medium transition-colors"
          >
            Generate Forecast
          </button>
        </div>
      )}

      {/* Forecast Results */}
      {forecast && (
        <>
          {/* Forecast Summary */}
          <div className="bg-gray-700 rounded-lg p-4 mb-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white">Forecast Summary</h3>
              <div className="flex items-center space-x-2 text-sm text-gray-400">
                <InformationCircleIcon className="h-4 w-4" />
                <span>Accuracy: {forecast.accuracy_score?.toFixed(1) || 'N/A'}%</span>
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-yellow-400">
                  {forecast.forecast_horizon}
                </div>
                <div className="text-sm text-gray-400">Periods Ahead</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-400">
                  {forecast.confidence_level}%
                </div>
                <div className="text-sm text-gray-400">Confidence Level</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-400">
                  {forecast.forecast_type}
                </div>
                <div className="text-sm text-gray-400">Time Period</div>
              </div>
            </div>
          </div>

          {/* Forecast Chart Placeholder */}
          <div className="bg-gray-700 rounded-lg p-4 mb-6">
            <h3 className="text-lg font-semibold text-white mb-4">Revenue Forecast Chart</h3>
            <div className="h-64 bg-gray-600 rounded-lg flex items-center justify-center">
              <div className="text-center text-gray-400">
                <ChartBarIcon className="h-12 w-12 mx-auto mb-2 opacity-50" />
                <p>Chart visualization will be implemented</p>
                <p className="text-sm">Showing {forecast.forecast_data.length} forecast periods</p>
              </div>
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
                    <th className="text-left text-gray-300 py-2">Factors</th>
                  </tr>
                </thead>
                <tbody>
                  {forecast.forecast_data.map((item, index) => (
                    <tr key={index} className="border-b border-gray-600">
                      <td className="py-3 text-white font-medium">{item.period}</td>
                      <td className="py-3 text-green-400 font-medium">
                        ${item.predicted_revenue.toLocaleString()}
                      </td>
                      <td className="py-3 text-gray-300">
                        ${item.confidence_range.min.toLocaleString()} - ${item.confidence_range.max.toLocaleString()}
                      </td>
                      <td className="py-3">
                        <div className="flex items-center space-x-2">
                          <div className={`w-2 h-2 rounded-full ${
                            item.accuracy_score >= 80 ? 'bg-green-400' : 
                            item.accuracy_score >= 60 ? 'bg-yellow-400' : 'bg-red-400'
                          }`}></div>
                          <span className="text-gray-300">{item.accuracy_score?.toFixed(1) || 'N/A'}%</span>
                        </div>
                      </td>
                      <td className="py-3">
                        <div className="flex flex-wrap gap-1">
                          {item.factors.slice(0, 2).map((factor, factorIndex) => (
                            <span
                              key={factorIndex}
                              className={`px-2 py-1 rounded text-xs ${
                                factor.impact === 'positive' ? 'bg-green-500/20 text-green-400' :
                                factor.impact === 'negative' ? 'bg-red-500/20 text-red-400' :
                                'bg-gray-500/20 text-gray-400'
                              }`}
                            >
                              {factor.name}
                            </span>
                          ))}
                          {item.factors.length > 2 && (
                            <span className="px-2 py-1 rounded text-xs bg-gray-500/20 text-gray-400">
                              +{item.factors.length - 2} more
                            </span>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Forecast Metadata */}
          <div className="mt-4 text-sm text-gray-400 text-center">
            <p>Forecast generated on {new Date(forecast.created_at).toLocaleString()}</p>
            <p>Valid until {new Date(forecast.valid_until).toLocaleString()}</p>
          </div>
        </>
      )}
    </div>
  )
}


