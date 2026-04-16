import { CurrencyDollarIcon, ChartBarIcon, ArrowTrendingUpIcon, CubeIcon } from '@heroicons/react/24/outline'

interface DashboardKPIsProps {
  kpis?: {
    inventory_melt_value: number
    inventory_list_value: number
    gross_profit: number
    melt_vs_list_ratio: number
    total_coins: number
    active_listings?: number
    sold_this_month?: number
  }
}

export default function DashboardKPIs({ kpis }: DashboardKPIsProps) {
  if (!kpis) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="bg-gray-800 rounded-lg p-6 animate-pulse">
            <div className="h-4 bg-gray-700 rounded mb-2"></div>
            <div className="h-8 bg-gray-700 rounded"></div>
          </div>
        ))}
      </div>
    )
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount)
  }

  const formatPercentage = (value: number) => {
    return `${(value * 100).toFixed(1)}%`
  }


  const kpiCards = [
    {
      title: 'Inventory Cost',
      value: formatCurrency(kpis.inventory_melt_value),
      icon: CurrencyDollarIcon,
      color: 'text-blue-400',
      bgColor: 'bg-blue-500/10',
    },
    {
      title: 'Inventory List Value',
      value: formatCurrency(kpis.inventory_list_value),
      icon: ChartBarIcon,
      color: 'text-green-400',
      bgColor: 'bg-green-500/10',
    },
    {
      title: 'Gross Profit',
      value: formatCurrency(kpis.gross_profit),
      icon: ArrowTrendingUpIcon,
      color: 'text-yellow-400',
      bgColor: 'bg-yellow-500/10',
    },
    {
      title: 'Melt vs List Ratio',
      value: formatPercentage(kpis.melt_vs_list_ratio),
      icon: CubeIcon,
      color: 'text-purple-400',
      bgColor: 'bg-purple-500/10',
    },
  ]

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {kpiCards.map((card, index) => (
        <div key={index} className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-400 mb-1">
                {card.title}
              </p>
              <p className="text-2xl font-bold text-white">
                {card.value}
              </p>
            </div>
            <div className={`p-3 rounded-lg ${card.bgColor}`}>
              <card.icon className={`h-6 w-6 ${card.color}`} />
            </div>
          </div>
        </div>
      ))}
      
      {/* Additional Stats */}
      <div className="col-span-full bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h3 className="text-lg font-semibold text-yellow-500 mb-4">Additional Statistics</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center">
            <p className="text-2xl font-bold text-white">{kpis.total_coins}</p>
            <p className="text-sm text-gray-400">Total Coins</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-white">{kpis.active_listings || 0}</p>
            <p className="text-sm text-gray-400">Active Listings</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-white">{kpis.sold_this_month || 0}</p>
            <p className="text-sm text-gray-400">Sold This Month</p>
          </div>
        </div>
      </div>

    </div>
  )
}
