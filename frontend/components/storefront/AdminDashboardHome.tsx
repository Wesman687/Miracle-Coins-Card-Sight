import { useState, useEffect } from 'react'
import { useQuery } from 'react-query'
import {
  ChartBarIcon,
  CurrencyDollarIcon,
  SparklesIcon,
  ClipboardDocumentListIcon,
  CubeIcon,
  MagnifyingGlassIcon,
  BellIcon,
  TagIcon,
  ChatBubbleLeftRightIcon,
  ArrowPathIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline'
import DashboardKPIs from '../DashboardKPIs'
import CoinTable from '../CoinTable'
import AddCoinModal from '../AddCoinModal'
import UploadNewItemModal from '../UploadNewItemModal'
import AIChatModal from '../AIChatModal'
import MetalsPrices from '../MetalsPrices'
import StorefrontMetadataModal from '../StorefrontMetadataModal'
import { api } from '../../lib/api'

export default function AdminDashboardHome() {
  const [showAddModal, setShowAddModal] = useState(false)
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [showAIChatModal, setShowAIChatModal] = useState(false)
  const [selectedCoin, setSelectedCoin] = useState(null)
  const [selectedStorefrontCoin, setSelectedStorefrontCoin] = useState(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [debouncedSearchTerm, setDebouncedSearchTerm] = useState('')

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearchTerm(searchTerm)
    }, 300)

    return () => clearTimeout(timer)
  }, [searchTerm])

  const { data: kpis, isLoading: kpisLoading } = useQuery(
    'dashboard-kpis',
    () => api.get('/pricing/dashboard-kpis'),
    { refetchInterval: 600000 }
  )

  const { data: coins, isLoading: coinsLoading, refetch: refetchCoins } = useQuery(
    ['coins', debouncedSearchTerm],
    () => api.get(`/coins?limit=100${debouncedSearchTerm ? `&search=${encodeURIComponent(debouncedSearchTerm)}` : ''}`),
    { refetchInterval: 60000 }
  )

  return (
    <div className="min-h-screen bg-black text-white">
      <header className="bg-gradient-to-r from-gray-900 via-gray-800 to-gray-900 border-b-2 border-yellow-500 shadow-xl">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center space-x-4">
              <div className="bg-gradient-to-r from-yellow-400 to-yellow-600 rounded-lg p-2 mr-3">
                <CurrencyDollarIcon className="h-8 w-8 text-black" />
              </div>
              <div>
                <h1 className="text-3xl font-bold bg-gradient-to-r from-yellow-400 to-yellow-600 bg-clip-text text-transparent">
                  Miracle Coins
                </h1>
                <p className="text-sm text-gray-400 font-medium">Product Catalog Admin</p>
              </div>
            </div>

            <div className="flex items-center space-x-3">
              <button onClick={() => setShowUploadModal(true)} className="bg-gradient-to-r from-yellow-500 to-yellow-600 text-black px-6 py-3 rounded-xl flex items-center space-x-2 font-medium">
                <SparklesIcon className="h-5 w-5" />
                <span>Add / Upload Product</span>
              </button>
            </div>
          </div>

          <nav className="pb-4">
            <div className="flex items-center justify-center space-x-1">
            </div>
          </nav>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <MetalsPrices metals_prices={kpis?.data?.metals_prices} />

        <div className="mb-8">
          <h2 className="text-xl font-semibold mb-4 flex items-center">
            <ChartBarIcon className="h-6 w-6 mr-2 text-yellow-500" />
            Dashboard Overview
          </h2>
          {kpisLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="bg-gray-800 rounded-lg p-6 animate-pulse">
                  <div className="h-4 bg-gray-700 rounded mb-2"></div>
                  <div className="h-8 bg-gray-700 rounded"></div>
                </div>
              ))}
            </div>
          ) : (
            <DashboardKPIs kpis={kpis?.data} />
          )}
        </div>

        <div className="mb-8">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold flex items-center">
              <CurrencyDollarIcon className="h-6 w-6 mr-2 text-yellow-500" />
              Product Catalog
            </h2>
          </div>

          <div className="mb-6">
            <div className="relative max-w-md">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
              </div>
              <input
                type="text"
                placeholder="Search products by title..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="block w-full pl-10 pr-10 py-3 border border-gray-600 rounded-lg bg-gray-800 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-yellow-500 focus:border-transparent"
              />
              {searchTerm && (
                <button onClick={() => setSearchTerm('')} className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-white">
                  <XMarkIcon className="h-5 w-5" />
                </button>
              )}
            </div>
          </div>

          {coinsLoading ? (
            <div className="bg-gray-800 rounded-lg p-8 text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-yellow-500 mx-auto"></div>
              <p className="mt-2 text-gray-400">Loading products...</p>
            </div>
          ) : (
            <CoinTable coins={coins?.data || []} onEdit={setSelectedCoin} onStorefrontEdit={setSelectedStorefrontCoin} onRefresh={refetchCoins} />
          )}
        </div>
      </main>

      {showAIChatModal && <AIChatModal isOpen={showAIChatModal} onClose={() => setShowAIChatModal(false)} />}
      {showUploadModal && <UploadNewItemModal onClose={() => setShowUploadModal(false)} onSuccess={() => { setShowUploadModal(false); refetchCoins() }} />}
      {showAddModal && <AddCoinModal onClose={() => setShowAddModal(false)} onSuccess={() => { setShowAddModal(false); refetchCoins() }} />}
      {selectedCoin && <AddCoinModal coin={selectedCoin} onClose={() => setSelectedCoin(null)} onSuccess={() => { setSelectedCoin(null); refetchCoins() }} />}
      {selectedStorefrontCoin && <StorefrontMetadataModal coin={selectedStorefrontCoin} onClose={() => setSelectedStorefrontCoin(null)} onSuccess={() => { setSelectedStorefrontCoin(null); refetchCoins() }} />}
    </div>
  )
}
