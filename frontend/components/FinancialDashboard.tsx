import { useState, useEffect } from 'react'
import { useQuery } from 'react-query'
import { 
  CurrencyDollarIcon,
  ChartBarIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  CogIcon,
  PlusIcon
} from '@heroicons/react/24/outline'
import { api } from '../lib/api'

interface FinancialDashboard {
  current_period: PLStatement
  cash_flow_analysis: CashFlowAnalysis
  kpis: KPIs
  revenue_trend: TrendData[]
  profit_trend: TrendData[]
  expense_trend: TrendData[]
  financial_alerts: FinancialAlert[]
}

interface PLStatement {
  period_start: string
  period_end: string
  period_name: string
  total_revenue: number
  sales_revenue: number
  other_revenue: number
  cost_of_goods: number
  gross_profit: number
  gross_profit_margin: number
  operating_expenses: number
  operating_profit: number
  operating_margin: number
  other_expenses: number
  net_profit: number
  net_profit_margin: number
  revenue_growth: number
  profit_growth: number
  expense_ratio: number
}

interface CashFlowAnalysis {
  period_start: string
  period_end: string
  period_name: string
  operating_cash_flow: number
  sales_cash_inflow: number
  expense_cash_outflow: number
  investing_cash_flow: number
  inventory_investment: number
  equipment_investment: number
  financing_cash_flow: number
  owner_investment: number
  loan_proceeds: number
  net_cash_flow: number
  beginning_cash: number
  ending_cash: number
  operating_cash_flow_margin: number
  cash_conversion_cycle: number
}

interface KPIs {
  revenue: number
  gross_profit_margin: number
  net_profit_margin: number
  revenue_growth: number
  operating_cash_flow: number
  inventory_turnover: number
  return_on_investment: number
}

interface TrendData {
  period: string
  value: number
}

interface FinancialAlert {
  type: string
  message: string
  severity: string
}

export default function FinancialDashboard() {
  const [selectedPeriod, setSelectedPeriod] = useState<'monthly' | 'quarterly' | 'yearly'>('monthly')
  const [activeTab, setActiveTab] = useState<'overview' | 'p-l' | 'cash-flow' | 'pricing'>('overview')

  const { data: dashboardData, isLoading, error, refetch } = useQuery(
    ['financial-dashboard', selectedPeriod],
    () => api.get(`/financial/dashboard?period=${selectedPeriod}`),
    {
      refetchInterval: 300000, // Refresh every 5 minutes
      retry: 3,
    }
  )

  const dashboard = dashboardData?.data

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
          <p>Failed to load financial dashboard</p>
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
          <CurrencyDollarIcon className="h-6 w-6 text-yellow-500" />
          <h2 className="text-xl font-semibold text-white">Financial Dashboard</h2>
        </div>
        
        <div className="flex space-x-2">
          {['monthly', 'quarterly', 'yearly'].map((period) => (
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
          onClick={() => setActiveTab('p-l')}
          className={`pb-2 px-1 border-b-2 font-medium text-sm transition-colors ${
            activeTab === 'p-l'
              ? 'border-yellow-500 text-yellow-400'
              : 'border-transparent text-gray-400 hover:text-gray-300'
          }`}
        >
          P&L Statement
        </button>
        <button
          onClick={() => setActiveTab('cash-flow')}
          className={`pb-2 px-1 border-b-2 font-medium text-sm transition-colors ${
            activeTab === 'cash-flow'
              ? 'border-yellow-500 text-yellow-400'
              : 'border-transparent text-gray-400 hover:text-gray-300'
          }`}
        >
          Cash Flow
        </button>
        <button
          onClick={() => setActiveTab('pricing')}
          className={`pb-2 px-1 border-b-2 font-medium text-sm transition-colors ${
            activeTab === 'pricing'
              ? 'border-yellow-500 text-yellow-400'
              : 'border-transparent text-gray-400 hover:text-gray-300'
          }`}
        >
          Pricing Strategies
        </button>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && <OverviewTab dashboard={dashboard} />}
      {activeTab === 'p-l' && <PLTab plStatement={dashboard?.current_period} />}
      {activeTab === 'cash-flow' && <CashFlowTab cashFlow={dashboard?.cash_flow_analysis} />}
      {activeTab === 'pricing' && <PricingTab />}
    </div>
  )
}

// Overview Tab Component
function OverviewTab({ dashboard }) {
  return (
    <>
      {/* Financial Alerts */}
      {dashboard?.financial_alerts?.length > 0 && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-white mb-4">Financial Alerts</h3>
          <div className="space-y-2">
            {dashboard.financial_alerts.map((alert, index) => (
              <div
                key={index}
                className={`p-3 rounded-lg border ${
                  alert.severity === 'high' ? 'bg-red-500/10 border-red-500/20 text-red-400' :
                  alert.severity === 'medium' ? 'bg-yellow-500/10 border-yellow-500/20 text-yellow-400' :
                  'bg-green-500/10 border-green-500/20 text-green-400'
                }`}
              >
                <div className="flex items-center space-x-2">
                  {alert.severity === 'high' ? (
                    <ExclamationTriangleIcon className="h-5 w-5" />
                  ) : (
                    <CheckCircleIcon className="h-5 w-5" />
                  )}
                  <span className="font-medium">{alert.message}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Key Performance Indicators */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <KPICard
          title="Revenue"
          value={`$${dashboard?.kpis?.revenue?.toLocaleString() || '0'}`}
          change={dashboard?.current_period?.revenue_growth}
          icon={CurrencyDollarIcon}
          color="text-green-400"
          bgColor="bg-green-500/10"
        />
        
        <KPICard
          title="Gross Profit Margin"
          value={`${dashboard?.kpis?.gross_profit_margin?.toFixed(1) || '0'}%`}
          change={null}
          icon={ChartBarIcon}
          color="text-blue-400"
          bgColor="bg-blue-500/10"
        />
        
        <KPICard
          title="Net Profit Margin"
          value={`${dashboard?.kpis?.net_profit_margin?.toFixed(1) || '0'}%`}
          change={null}
          icon={ArrowTrendingUpIcon}
          color="text-yellow-400"
          bgColor="bg-yellow-500/10"
        />
        
        <KPICard
          title="Operating Cash Flow"
          value={`$${dashboard?.kpis?.operating_cash_flow?.toLocaleString() || '0'}`}
          change={null}
          icon={CurrencyDollarIcon}
          color="text-purple-400"
          bgColor="bg-purple-500/10"
        />
      </div>

      {/* Secondary KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <KPICard
          title="Inventory Turnover"
          value={`${dashboard?.kpis?.inventory_turnover?.toFixed(1) || '0'}x`}
          change={null}
          icon={ArrowTrendingUpIcon}
          color="text-blue-400"
          bgColor="bg-blue-500/10"
        />
        
        <KPICard
          title="Return on Investment"
          value={`${dashboard?.kpis?.return_on_investment?.toFixed(1) || '0'}%`}
          change={null}
          icon={ChartBarIcon}
          color="text-green-400"
          bgColor="bg-green-500/10"
        />
        
        <KPICard
          title="Cash Conversion Cycle"
          value={`${dashboard?.cash_flow_analysis?.cash_conversion_cycle || '0'} days`}
          change={null}
          icon={ArrowTrendingDownIcon}
          color="text-yellow-400"
          bgColor="bg-yellow-500/10"
        />
      </div>

      {/* Trends */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <TrendChart title="Revenue Trend" data={dashboard?.revenue_trend} color="text-green-400" />
        <TrendChart title="Profit Trend" data={dashboard?.profit_trend} color="text-blue-400" />
        <TrendChart title="Expense Trend" data={dashboard?.expense_trend} color="text-red-400" />
      </div>
    </>
  )
}

// P&L Statement Tab Component
function PLTab({ plStatement }) {
  if (!plStatement) {
    return (
      <div className="text-center text-gray-400 py-8">
        <ChartBarIcon className="h-12 w-12 mx-auto mb-4 opacity-50" />
        <p>No P&L data available</p>
      </div>
    )
  }

  return (
    <div className="bg-gray-700 rounded-lg p-6 border border-gray-600">
      <h3 className="text-lg font-semibold text-white mb-6">
        P&L Statement - {plStatement.period_name}
      </h3>
      
      <div className="space-y-4">
        {/* Revenue Section */}
        <div className="border-b border-gray-600 pb-4">
          <h4 className="text-md font-semibold text-green-400 mb-3">Revenue</h4>
          <div className="space-y-2 ml-4">
            <div className="flex justify-between">
              <span className="text-gray-300">Sales Revenue</span>
              <span className="text-white font-medium">${plStatement.sales_revenue.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-300">Other Revenue</span>
              <span className="text-white font-medium">${plStatement.other_revenue.toLocaleString()}</span>
            </div>
            <div className="flex justify-between border-t border-gray-600 pt-2">
              <span className="text-white font-semibold">Total Revenue</span>
              <span className="text-green-400 font-bold">${plStatement.total_revenue.toLocaleString()}</span>
            </div>
          </div>
        </div>

        {/* Cost of Goods Section */}
        <div className="border-b border-gray-600 pb-4">
          <h4 className="text-md font-semibold text-red-400 mb-3">Cost of Goods Sold</h4>
          <div className="space-y-2 ml-4">
            <div className="flex justify-between">
              <span className="text-gray-300">Cost of Goods</span>
              <span className="text-white font-medium">${plStatement.cost_of_goods.toLocaleString()}</span>
            </div>
            <div className="flex justify-between border-t border-gray-600 pt-2">
              <span className="text-white font-semibold">Gross Profit</span>
              <span className="text-green-400 font-bold">${plStatement.gross_profit.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-300">Gross Profit Margin</span>
              <span className="text-green-400 font-medium">{plStatement.gross_profit_margin.toFixed(1)}%</span>
            </div>
          </div>
        </div>

        {/* Operating Expenses Section */}
        <div className="border-b border-gray-600 pb-4">
          <h4 className="text-md font-semibold text-yellow-400 mb-3">Operating Expenses</h4>
          <div className="space-y-2 ml-4">
            <div className="flex justify-between">
              <span className="text-gray-300">Operating Expenses</span>
              <span className="text-white font-medium">${plStatement.operating_expenses.toLocaleString()}</span>
            </div>
            <div className="flex justify-between border-t border-gray-600 pt-2">
              <span className="text-white font-semibold">Operating Profit</span>
              <span className="text-blue-400 font-bold">${plStatement.operating_profit.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-300">Operating Margin</span>
              <span className="text-blue-400 font-medium">{plStatement.operating_margin.toFixed(1)}%</span>
            </div>
          </div>
        </div>

        {/* Other Expenses Section */}
        <div className="border-b border-gray-600 pb-4">
          <h4 className="text-md font-semibold text-red-400 mb-3">Other Expenses</h4>
          <div className="space-y-2 ml-4">
            <div className="flex justify-between">
              <span className="text-gray-300">Other Expenses</span>
              <span className="text-white font-medium">${plStatement.other_expenses.toLocaleString()}</span>
            </div>
          </div>
        </div>

        {/* Net Profit Section */}
        <div>
          <h4 className="text-md font-semibold text-green-400 mb-3">Net Profit</h4>
          <div className="space-y-2 ml-4">
            <div className="flex justify-between border-t border-gray-600 pt-2">
              <span className="text-white font-semibold">Net Profit</span>
              <span className="text-green-400 font-bold text-xl">${plStatement.net_profit.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-300">Net Profit Margin</span>
              <span className="text-green-400 font-medium">{plStatement.net_profit_margin.toFixed(1)}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-300">Expense Ratio</span>
              <span className="text-red-400 font-medium">{plStatement.expense_ratio.toFixed(1)}%</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// Cash Flow Tab Component
function CashFlowTab({ cashFlow }) {
  if (!cashFlow) {
    return (
      <div className="text-center text-gray-400 py-8">
        <CurrencyDollarIcon className="h-12 w-12 mx-auto mb-4 opacity-50" />
        <p>No cash flow data available</p>
      </div>
    )
  }

  return (
    <div className="bg-gray-700 rounded-lg p-6 border border-gray-600">
      <h3 className="text-lg font-semibold text-white mb-6">
        Cash Flow Analysis - {cashFlow.period_name}
      </h3>
      
      <div className="space-y-6">
        {/* Operating Activities */}
        <div>
          <h4 className="text-md font-semibold text-green-400 mb-3">Operating Activities</h4>
          <div className="space-y-2 ml-4">
            <div className="flex justify-between">
              <span className="text-gray-300">Sales Cash Inflow</span>
              <span className="text-green-400 font-medium">${cashFlow.sales_cash_inflow.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-300">Expense Cash Outflow</span>
              <span className="text-red-400 font-medium">-${cashFlow.expense_cash_outflow.toLocaleString()}</span>
            </div>
            <div className="flex justify-between border-t border-gray-600 pt-2">
              <span className="text-white font-semibold">Operating Cash Flow</span>
              <span className={`font-bold ${cashFlow.operating_cash_flow >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                ${cashFlow.operating_cash_flow.toLocaleString()}
              </span>
            </div>
          </div>
        </div>

        {/* Investing Activities */}
        <div>
          <h4 className="text-md font-semibold text-blue-400 mb-3">Investing Activities</h4>
          <div className="space-y-2 ml-4">
            <div className="flex justify-between">
              <span className="text-gray-300">Inventory Investment</span>
              <span className="text-red-400 font-medium">-${cashFlow.inventory_investment.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-300">Equipment Investment</span>
              <span className="text-red-400 font-medium">-${cashFlow.equipment_investment.toLocaleString()}</span>
            </div>
            <div className="flex justify-between border-t border-gray-600 pt-2">
              <span className="text-white font-semibold">Investing Cash Flow</span>
              <span className={`font-bold ${cashFlow.investing_cash_flow >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                ${cashFlow.investing_cash_flow.toLocaleString()}
              </span>
            </div>
          </div>
        </div>

        {/* Financing Activities */}
        <div>
          <h4 className="text-md font-semibold text-purple-400 mb-3">Financing Activities</h4>
          <div className="space-y-2 ml-4">
            <div className="flex justify-between">
              <span className="text-gray-300">Owner Investment</span>
              <span className="text-green-400 font-medium">${cashFlow.owner_investment.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-300">Loan Proceeds</span>
              <span className="text-green-400 font-medium">${cashFlow.loan_proceeds.toLocaleString()}</span>
            </div>
            <div className="flex justify-between border-t border-gray-600 pt-2">
              <span className="text-white font-semibold">Financing Cash Flow</span>
              <span className={`font-bold ${cashFlow.financing_cash_flow >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                ${cashFlow.financing_cash_flow.toLocaleString()}
              </span>
            </div>
          </div>
        </div>

        {/* Net Cash Flow */}
        <div className="border-t border-gray-600 pt-6">
          <h4 className="text-md font-semibold text-yellow-400 mb-3">Net Cash Flow</h4>
          <div className="space-y-2 ml-4">
            <div className="flex justify-between">
              <span className="text-gray-300">Beginning Cash</span>
              <span className="text-white font-medium">${cashFlow.beginning_cash.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-300">Net Cash Flow</span>
              <span className={`font-bold ${cashFlow.net_cash_flow >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                ${cashFlow.net_cash_flow.toLocaleString()}
              </span>
            </div>
            <div className="flex justify-between border-t border-gray-600 pt-2">
              <span className="text-white font-semibold">Ending Cash</span>
              <span className="text-green-400 font-bold text-xl">${cashFlow.ending_cash.toLocaleString()}</span>
            </div>
          </div>
        </div>

        {/* Cash Flow Ratios */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-gray-600 rounded-lg p-4">
            <div className="text-sm text-gray-300 mb-1">Operating Cash Flow Margin</div>
            <div className="text-lg font-bold text-green-400">{cashFlow.operating_cash_flow_margin.toFixed(1)}%</div>
          </div>
          <div className="bg-gray-600 rounded-lg p-4">
            <div className="text-sm text-gray-300 mb-1">Cash Conversion Cycle</div>
            <div className="text-lg font-bold text-blue-400">{cashFlow.cash_conversion_cycle} days</div>
          </div>
        </div>
      </div>
    </div>
  )
}

// Pricing Strategies Tab Component
function PricingTab() {
  return (
    <div className="bg-gray-700 rounded-lg p-6 border border-gray-600">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-white">Pricing Strategies</h3>
        <button className="bg-yellow-500 hover:bg-yellow-600 text-black px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors font-medium">
          <PlusIcon className="h-4 w-4" />
          <span>New Strategy</span>
        </button>
      </div>
      
      <div className="text-center text-gray-400 py-8">
        <CogIcon className="h-12 w-12 mx-auto mb-4 opacity-50" />
        <p>Pricing strategies management</p>
        <p className="text-sm">Create and manage dynamic pricing strategies</p>
      </div>
    </div>
  )
}

// Supporting Components
function KPICard({ title, value, change, icon: Icon, color, bgColor }) {
  return (
    <div className="bg-gray-700 rounded-lg p-4 border border-gray-600">
      <div className="flex items-center justify-between mb-2">
        <div className={`p-2 rounded-lg ${bgColor}`}>
          <Icon className={`h-5 w-5 ${color}`} />
        </div>
        {change !== null && (
          <div className={`text-sm flex items-center space-x-1 ${
            change >= 0 ? 'text-green-400' : 'text-red-400'
          }`}>
            {change >= 0 ? (
              <ArrowTrendingUpIcon className="h-4 w-4" />
            ) : (
              <ArrowTrendingDownIcon className="h-4 w-4" />
            )}
            <span>{change > 0 ? '+' : ''}{change?.toFixed(1)}%</span>
          </div>
        )}
      </div>
      <div className="text-2xl font-bold text-white mb-1">{value}</div>
      <div className="text-sm text-gray-400">{title}</div>
    </div>
  )
}

function TrendChart({ title, data, color }) {
  if (!data || data.length === 0) {
    return (
      <div className="bg-gray-700 rounded-lg p-4 border border-gray-600">
        <h4 className="text-md font-semibold text-white mb-4">{title}</h4>
        <div className="text-center text-gray-400 py-4">
          <ChartBarIcon className="h-8 w-8 mx-auto mb-2 opacity-50" />
          <p>No data available</p>
        </div>
      </div>
    )
  }

  const maxValue = Math.max(...data.map(d => d.value))
  
  return (
    <div className="bg-gray-700 rounded-lg p-4 border border-gray-600">
      <h4 className="text-md font-semibold text-white mb-4">{title}</h4>
      <div className="space-y-2">
        {data.map((item, index) => (
          <div key={index} className="flex items-center justify-between">
            <span className="text-gray-300 text-sm">{item.period}</span>
            <div className="flex items-center space-x-2">
              <div className="w-20 bg-gray-600 rounded-full h-2">
                <div 
                  className={`h-2 rounded-full ${color.replace('text-', 'bg-')}`}
                  style={{ width: `${(item.value / maxValue) * 100}%` }}
                ></div>
              </div>
              <span className="text-white text-sm font-medium">${item.value.toLocaleString()}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}


