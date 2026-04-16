import { useState, useEffect } from 'react'
import { 
  XMarkIcon,
  EyeIcon,
  PencilIcon,
  TrashIcon,
  CurrencyDollarIcon,
  CalendarIcon,
  TagIcon
} from '@heroicons/react/24/outline'
import { api } from '../lib/api'
import toast from 'react-hot-toast'

interface Coin {
  id: number
  sku: string
  name: string
  year?: number
  mint_mark?: string
  condition?: string
  purchase_price?: number
  current_price?: number
  collection_id?: number
  created_at: string
  updated_at: string
}

interface CollectionInventoryProps {
  collectionId: number
  collectionName: string
  onClose: () => void
}

export default function CollectionInventory({ collectionId, collectionName, onClose }: CollectionInventoryProps) {
  const [coins, setCoins] = useState<Coin[]>([])
  const [loading, setLoading] = useState(true)
  const [totalValue, setTotalValue] = useState(0)
  const [totalCoins, setTotalCoins] = useState(0)

  useEffect(() => {
    fetchCoins()
  }, [collectionId])

  const fetchCoins = async () => {
    try {
      // For now, we'll fetch all coins and filter by collection_id
      // In a real implementation, you'd have a dedicated endpoint
      const response = await api.get('/coins/')
      const allCoins = response.data
      const collectionCoins = allCoins.filter((coin: Coin) => coin.collection_id === collectionId)
      
      setCoins(collectionCoins)
      setTotalCoins(collectionCoins.length)
      
      // Calculate total value
      const value = collectionCoins.reduce((sum: number, coin: Coin) => {
        return sum + (coin.current_price || coin.purchase_price || 0)
      }, 0)
      setTotalValue(value)
    } catch (error) {
      console.error('Error fetching coins:', error)
      toast.error('Failed to load collection inventory')
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteCoin = async (coinId: number) => {
    if (!confirm('Are you sure you want to delete this coin?')) return

    try {
      await api.delete(`/coins/${coinId}`)
      toast.success('Coin deleted successfully')
      fetchCoins()
    } catch (error) {
      console.error('Error deleting coin:', error)
      toast.error('Failed to delete coin')
    }
  }

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-gray-800 rounded-lg p-6 w-11/12 max-w-6xl h-5/6">
          <div className="flex items-center justify-center h-full">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-yellow-500"></div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-lg p-6 w-11/12 max-w-6xl h-5/6 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold text-white">
              {collectionName} - Inventory
            </h2>
            <p className="text-gray-400">
              {totalCoins} coins • Total Value: ${totalValue.toFixed(2)}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-gray-700 rounded-lg p-4">
            <div className="flex items-center">
              <TagIcon className="h-8 w-8 text-blue-500" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-400">Total Coins</p>
                <p className="text-2xl font-bold text-white">{totalCoins}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-gray-700 rounded-lg p-4">
            <div className="flex items-center">
              <CurrencyDollarIcon className="h-8 w-8 text-green-500" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-400">Total Value</p>
                <p className="text-2xl font-bold text-white">${totalValue.toFixed(2)}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-gray-700 rounded-lg p-4">
            <div className="flex items-center">
              <CurrencyDollarIcon className="h-8 w-8 text-yellow-500" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-400">Avg Price</p>
                <p className="text-2xl font-bold text-white">
                  ${totalCoins > 0 ? (totalValue / totalCoins).toFixed(2) : '0.00'}
                </p>
              </div>
            </div>
          </div>
          
          <div className="bg-gray-700 rounded-lg p-4">
            <div className="flex items-center">
              <CalendarIcon className="h-8 w-8 text-purple-500" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-400">Latest Addition</p>
                <p className="text-sm font-bold text-white">
                  {coins.length > 0 ? new Date(coins[0].created_at).toLocaleDateString() : 'N/A'}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Coins Table */}
        <div className="flex-1 overflow-hidden">
          <div className="h-full overflow-auto">
            <table className="min-w-full divide-y divide-gray-700">
              <thead className="bg-gray-700 sticky top-0">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    SKU
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Year
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Condition
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Purchase Price
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Current Price
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-gray-800 divide-y divide-gray-700">
                {coins.map((coin) => (
                  <tr key={coin.id} className="hover:bg-gray-700">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-300">
                      {coin.sku}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-white">{coin.name}</div>
                      {coin.mint_mark && (
                        <div className="text-sm text-gray-400">{coin.mint_mark}</div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                      {coin.year || 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                      {coin.condition || 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                      {coin.purchase_price ? `$${coin.purchase_price.toFixed(2)}` : 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                      {coin.current_price ? `$${coin.current_price.toFixed(2)}` : 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex space-x-2">
                        <button
                          className="text-blue-400 hover:text-blue-300"
                          title="View Details"
                        >
                          <EyeIcon className="h-4 w-4" />
                        </button>
                        <button
                          className="text-yellow-400 hover:text-yellow-300"
                          title="Edit Coin"
                        >
                          <PencilIcon className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDeleteCoin(coin.id)}
                          className="text-red-400 hover:text-red-300"
                          title="Delete Coin"
                        >
                          <TrashIcon className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            
            {coins.length === 0 && (
              <div className="text-center py-12">
                <TagIcon className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-300">No coins in this collection</h3>
                <p className="mt-1 text-sm text-gray-500">
                  Add coins to this collection to see them here.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

