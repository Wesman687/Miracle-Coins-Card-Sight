import { useState } from 'react'
import InventoryManager from '../components/InventoryManager'
import { 
  CubeIcon,
  PlusIcon,
  ArrowPathIcon,
  ArrowLeftIcon
} from '@heroicons/react/24/outline'

export default function InventoryPage() {
  const [showAddLocation, setShowAddLocation] = useState(false)

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
              <CubeIcon className="h-8 w-8 text-yellow-500" />
              <h1 className="text-2xl font-bold text-white">Inventory Management</h1>
            </div>
            
            <div className="flex items-center space-x-4">
              <button className="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors">
                <ArrowPathIcon className="h-4 w-4" />
                <span>Sync Inventory</span>
              </button>
              <button 
                onClick={() => setShowAddLocation(true)}
                className="bg-yellow-500 hover:bg-yellow-600 text-black px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors font-medium"
              >
                <PlusIcon className="h-4 w-4" />
                <span>Add Location</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <InventoryManager />
      </div>

      {/* Add Location Modal */}
      {showAddLocation && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold text-white mb-4">Add New Location</h3>
            
            <form className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Location Name
                </label>
                <input
                  type="text"
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
                  placeholder="e.g., Display Case 1"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Location Type
                </label>
                <select className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500">
                  <option value="store">Store</option>
                  <option value="warehouse">Warehouse</option>
                  <option value="vault">Vault</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Address (Optional)
                </label>
                <textarea
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
                  rows={3}
                  placeholder="Physical address or description"
                />
              </div>
            </form>
            
            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowAddLocation(false)}
                className="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button className="bg-yellow-500 hover:bg-yellow-600 text-black px-4 py-2 rounded-lg transition-colors font-medium">
                Add Location
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}


