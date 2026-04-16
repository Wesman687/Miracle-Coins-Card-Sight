import { ClockIcon, ExclamationTriangleIcon, ArrowUpIcon, ArrowDownIcon } from '@heroicons/react/24/outline'
import { MetalsPrice } from '../types'

interface MetalsPricesProps {
  metals_prices?: {
    silver: MetalsPrice
    gold: MetalsPrice
  }
}

export default function MetalsPrices({ metals_prices }: MetalsPricesProps) {
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount)
  }

  const formatPrice = (price: MetalsPrice) => {
    if (price.price === null) {
      return 'N/A'
    }
    return formatCurrency(price.price)
  }

  const getStatusColor = (price: MetalsPrice) => {
    if (price.price === null) {
      return 'text-red-400'
    }
    if (price.confidence >= 0.8) {
      return 'text-green-400'
    }
    if (price.confidence >= 0.6) {
      return 'text-yellow-400'
    }
    return 'text-orange-400'
  }

  // Calculate real price changes based on stored historical data
  const getPriceChanges = (metal: 'silver' | 'gold', currentPrice: number) => {
    if (!currentPrice || !metals_prices?.[metal]?.timestamp) {
      return {
        '10min': { change: 0, percent: 0 },
        '24hr': { change: 0, percent: 0 }
      }
    }

    // Get stored price history from localStorage
    const priceHistoryKey = `metals_price_history_${metal}`
    const priceHistory = JSON.parse(localStorage.getItem(priceHistoryKey) || '[]')
    
    // Store current price with timestamp
    const now = new Date()
    const currentEntry = {
      price: currentPrice,
      timestamp: now.toISOString()
    }
    
    // Add current price to history
    priceHistory.push(currentEntry)
    
    // Keep only last 48 hours of data
    const cutoffTime = new Date(now.getTime() - 48 * 60 * 60 * 1000)
    const filteredHistory = priceHistory.filter((entry: any) => 
      new Date(entry.timestamp) > cutoffTime
    )
    
    // Save updated history
    localStorage.setItem(priceHistoryKey, JSON.stringify(filteredHistory))
    
    // Calculate changes
    const changes = {
      '10min': { change: 0, percent: 0 },
      '24hr': { change: 0, percent: 0 }
    }
    
    // Calculate 10-minute change
    const tenMinutesAgo = new Date(now.getTime() - 10 * 60 * 1000)
    const tenMinEntry = filteredHistory.find((entry: any) => 
      new Date(entry.timestamp) <= tenMinutesAgo
    )
    
    if (tenMinEntry) {
      const change = currentPrice - tenMinEntry.price
      const percent = (change / tenMinEntry.price) * 100
      changes['10min'] = { change, percent }
    }
    
    // Calculate 24-hour change
    const twentyFourHoursAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000)
    const twentyFourHourEntry = filteredHistory.find((entry: any) => 
      new Date(entry.timestamp) <= twentyFourHoursAgo
    )
    
    if (twentyFourHourEntry) {
      const change = currentPrice - twentyFourHourEntry.price
      const percent = (change / twentyFourHourEntry.price) * 100
      changes['24hr'] = { change, percent }
    }
    
    return changes
  }

  const formatPriceChange = (change: number, percent: number) => {
    const isPositive = change > 0
    const color = isPositive ? 'text-green-400' : 'text-red-400'
    const Icon = isPositive ? ArrowUpIcon : ArrowDownIcon
    const sign = isPositive ? '+' : ''
    
    return (
      <div className={`flex items-center ${color}`}>
        <Icon className="h-3 w-3 mr-1" />
        <span className="text-xs">
          {sign}{formatCurrency(Math.abs(change))} ({sign}{percent.toFixed(2)}%)
        </span>
      </div>
    )
  }

  return (
    <div className="bg-gray-800 border border-gray-700 rounded-lg p-4 mb-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <ClockIcon className="h-5 w-5 text-yellow-500 mr-2" />
          <h3 className="text-lg font-semibold text-yellow-500">Live Metals Prices</h3>
        </div>
        <div className="flex items-center justify-between w-full">
          {/* Silver */}
          <div className="flex-1 flex items-center justify-between px-4 py-2 bg-gray-700 rounded-lg">
            <div className="flex flex-col">
              <div className="text-sm text-gray-400 mb-1">Silver (XAG)</div>
              {metals_prices?.silver ? (
                <>
                  <div className={`text-xl font-bold ${getStatusColor(metals_prices.silver)}`}>
                    {formatPrice(metals_prices.silver)}
                  </div>
                  <div className="text-xs text-gray-500">
                    {metals_prices.silver.source}
                    {metals_prices.silver.timestamp && (
                      <span className="ml-1">
                        • {new Date(metals_prices.silver.timestamp).toLocaleTimeString()}
                      </span>
                    )}
                  </div>
                </>
              ) : (
                <>
                  <div className="text-xl font-bold text-red-400">Loading...</div>
                  <div className="text-xs text-gray-500">Fetching data...</div>
                </>
              )}
            </div>
            
            {metals_prices?.silver?.price && (
              <div className="flex flex-col space-y-1">
                {(() => {
                  const changes = getPriceChanges('silver', metals_prices.silver.price!)
                  return (
                    <>
                      <div className="text-xs text-gray-400">10min: {formatPriceChange(changes['10min'].change, changes['10min'].percent)}</div>
                      <div className="text-xs text-gray-400">24hr: {formatPriceChange(changes['24hr'].change, changes['24hr'].percent)}</div>
                    </>
                  )
                })()}
              </div>
            )}
          </div>

          {/* Gold */}
          <div className="flex-1 flex items-center justify-between px-4 py-2 bg-gray-700 rounded-lg mx-4">
            <div className="flex flex-col">
              <div className="text-sm text-gray-400 mb-1">Gold (XAU)</div>
              {metals_prices?.gold ? (
                <>
                  <div className={`text-xl font-bold ${getStatusColor(metals_prices.gold)}`}>
                    {formatPrice(metals_prices.gold)}
                  </div>
                  <div className="text-xs text-gray-500">
                    {metals_prices.gold.source}
                    {metals_prices.gold.timestamp && (
                      <span className="ml-1">
                        • {new Date(metals_prices.gold.timestamp).toLocaleTimeString()}
                      </span>
                    )}
                  </div>
                </>
              ) : (
                <>
                  <div className="text-xl font-bold text-red-400">Loading...</div>
                  <div className="text-xs text-gray-500">Fetching data...</div>
                </>
              )}
            </div>
            
            {metals_prices?.gold?.price && (
              <div className="flex flex-col space-y-1">
                {(() => {
                  const changes = getPriceChanges('gold', metals_prices.gold.price!)
                  return (
                    <>
                      <div className="text-xs text-gray-400">10min: {formatPriceChange(changes['10min'].change, changes['10min'].percent)}</div>
                      <div className="text-xs text-gray-400">24hr: {formatPriceChange(changes['24hr'].change, changes['24hr'].percent)}</div>
                    </>
                  )
                })()}
              </div>
            )}
          </div>

          {/* Status indicator */}
          <div className="flex items-center text-xs text-gray-400 flex-shrink-0">
            {metals_prices?.silver?.price && metals_prices?.gold?.price ? (
              <div className="flex items-center">
                <div className="w-2 h-2 bg-green-400 rounded-full mr-1"></div>
                Live
              </div>
            ) : (
              <div className="flex items-center">
                <div className="w-2 h-2 bg-red-400 rounded-full mr-1"></div>
                Offline
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
