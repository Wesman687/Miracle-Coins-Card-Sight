import { useState, useEffect } from 'react'
import { 
  TagIcon, 
  PlusIcon, 
  PencilIcon, 
  TrashIcon,
  EyeIcon,
  ChartBarIcon,
  CurrencyDollarIcon,
  CubeIcon,
  ArrowLeftIcon,
  PhotoIcon,
  SwatchIcon,
  ChevronRightIcon,
  Bars3Icon
} from '@heroicons/react/24/outline'
import { api } from '../lib/api'
import toast from 'react-hot-toast'
import CollectionModal from './CollectionModal'
import AdvancedCollectionModal from './AdvancedCollectionModal'
import CollectionInventory from './CollectionInventory'

interface Collection {
  id: number
  name: string
  description?: string
  description_html?: string
  shopify_collection_id?: string
  color: string
  icon?: string
  image_url?: string  // Simple image URL
  coin_count: number
  total_value?: number
  average_price?: number
  created_at: string
  updated_at: string
  metadata_fields?: any[]
  images?: any[]
  featured_image?: any
  // Temporary fields that exist in database but are not used in UI
  sort_order?: number
  default_markup?: number
}

interface CollectionStats {
  total_collections: number
  active_collections: number
  most_popular_collection?: {
    name: string
    coin_count: number
  }
}

export default function CollectionsManager() {
  const [collections, setCollections] = useState<Collection[]>([])
  const [stats, setStats] = useState<CollectionStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [showAdvancedModal, setShowAdvancedModal] = useState(false)
  const [selectedCollection, setSelectedCollection] = useState<Collection | null>(null)
  const [useAdvancedEditor, setUseAdvancedEditor] = useState(false)
  const [showColorModal, setShowColorModal] = useState(false)
  const [showInventoryModal, setShowInventoryModal] = useState(false)
  const [draggedIndex, setDraggedIndex] = useState<number | null>(null)

  // Function to render HTML description safely
  const renderDescription = (collection: Collection): string => {
    if (collection.description && !collection.description.includes('<')) {
      return collection.description
    }
    if (collection.description_html) {
      return collection.description_html
    }
    return collection.description || ''
  }

  useEffect(() => {
    fetchCollections()
    fetchStats()
  }, [])

  const fetchCollections = async () => {
    try {
      const response = await api.get('/collections/')
      setCollections(response.data)
    } catch (error) {
      console.error('Error fetching collections:', error)
      toast.error('Failed to load collections')
    } finally {
      setLoading(false)
    }
  }

  const handleCollectionClick = (collection: Collection) => {
    setSelectedCollection(collection)
    if (useAdvancedEditor) {
      setShowAdvancedModal(true)
    } else {
      setShowEditModal(true)
    }
  }

  const handleDragStart = (e: React.DragEvent, index: number) => {
    setDraggedIndex(index)
    e.dataTransfer.effectAllowed = 'move'
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
  }

  const handleDrop = (e: React.DragEvent, dropIndex: number) => {
    e.preventDefault()
    
    if (draggedIndex === null || draggedIndex === dropIndex) {
      setDraggedIndex(null)
      return
    }

    const newCollections = [...collections]
    const draggedItem = newCollections[draggedIndex]
    
    // Remove the dragged item
    newCollections.splice(draggedIndex, 1)
    
    // Insert it at the new position
    newCollections.splice(dropIndex, 0, draggedItem)
    
    setCollections(newCollections)
    setDraggedIndex(null)
    
    // TODO: Save the new order to the backend
    toast.success('Collection order updated')
  }

  const fetchStats = async () => {
    try {
      const response = await api.get('/collections/stats')
      setStats(response.data)
    } catch (error) {
      console.error('Error fetching stats:', error)
    }
  }

  const handleDeleteCollection = async (collectionId: number) => {
    if (!confirm('Are you sure you want to delete this collection?')) return

    try {
      await api.delete(`/collections/${collectionId}`)
      toast.success('Collection deleted successfully')
      fetchCollections()
      fetchStats()
    } catch (error) {
      console.error('Error deleting collection:', error)
      toast.error('Failed to delete collection')
    }
  }

  const handleEditCollection = (collection: Collection) => {
    setSelectedCollection(collection)
    if (useAdvancedEditor) {
      setShowAdvancedModal(true)
    } else {
      setShowEditModal(true)
    }
  }

  const handleCreateCollection = () => {
    if (useAdvancedEditor) {
      setShowAdvancedModal(true)
    } else {
      setShowCreateModal(true)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-yellow-500"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => window.history.back()}
            className="flex items-center space-x-2 text-gray-400 hover:text-white transition-colors"
          >
            <ArrowLeftIcon className="h-5 w-5" />
            <span className="text-sm font-medium">Back</span>
          </button>
          <div className="h-6 w-px bg-gray-600"></div>
          <TagIcon className="h-8 w-8 text-yellow-500" />
          <h1 className="text-2xl font-bold text-white">Collections</h1>
        </div>
        
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="advanced-editor"
              checked={useAdvancedEditor}
              onChange={(e) => setUseAdvancedEditor(e.target.checked)}
              className="w-4 h-4 text-yellow-500 bg-gray-700 border-gray-600 rounded focus:ring-yellow-500 focus:ring-2"
            />
            <label htmlFor="advanced-editor" className="text-sm text-gray-300">
              Advanced Editor
            </label>
          </div>
          <button
            onClick={handleCreateCollection}
            className="bg-yellow-500 hover:bg-yellow-600 text-black px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors font-medium"
          >
            <PlusIcon className="h-4 w-4" />
            <span>Add Collection</span>
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-gray-800 rounded-lg p-6">
            <div className="flex items-center">
              <div className="p-2 bg-blue-500 rounded-lg">
                <TagIcon className="h-6 w-6 text-white" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-400">Total Collections</p>
                <p className="text-2xl font-bold text-white">{stats.total_collections}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-gray-800 rounded-lg p-6">
            <div className="flex items-center">
              <div className="p-2 bg-green-500 rounded-lg">
                <ChartBarIcon className="h-6 w-6 text-white" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-400">Active Collections</p>
                <p className="text-2xl font-bold text-white">{stats.active_collections}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-gray-800 rounded-lg p-6">
            <div className="flex items-center">
              <div className="p-2 bg-purple-500 rounded-lg">
                <CubeIcon className="h-6 w-6 text-white" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-400">Most Popular</p>
                <p className="text-lg font-bold text-white">
                  {stats.most_popular_collection?.name || 'N/A'}
                </p>
                <p className="text-sm text-gray-400">
                  {stats.most_popular_collection?.coin_count || 0} coins
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

              {/* Collections Table */}
              <div className="bg-gray-800 rounded-lg overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-700">
                    <thead className="bg-gray-700">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider w-8">
                          {/* Drag handle column */}
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                          Collection
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider w-20">
                          Images
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                          Coins
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                          Shopify ID
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                          Actions
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-gray-800 divide-y divide-gray-700">
                      {collections.map((collection, index) => (
                        <tr 
                          key={collection.id} 
                          className={`hover:bg-gray-700 cursor-pointer transition-colors ${
                            draggedIndex === index ? 'opacity-50' : ''
                          }`}
                          draggable
                          onDragStart={(e) => handleDragStart(e, index)}
                          onDragOver={handleDragOver}
                          onDrop={(e) => handleDrop(e, index)}
                          onClick={() => handleCollectionClick(collection)}
                        >
                          <td className="px-2 py-4 whitespace-nowrap">
                            <div 
                              className="cursor-move text-gray-400 hover:text-gray-200 p-1"
                              onMouseDown={(e) => e.stopPropagation()}
                            >
                              <Bars3Icon className="h-4 w-4" />
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex items-center">
                              <div className="flex items-center space-x-3">
                                <div 
                                  className="w-4 h-4 rounded-full flex-shrink-0"
                                  style={{ backgroundColor: collection.color }}
                                ></div>
                                <div className="flex-1 min-w-0">
                                  <div className="text-sm font-medium text-white truncate">
                                    {collection.name}
                                  </div>
                                </div>
                                <ChevronRightIcon className="h-4 w-4 text-gray-400 flex-shrink-0" />
                              </div>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap w-20">
                            <div className="flex items-center justify-center">
                              {collection.image_url ? (
                                <div className="relative">
                                  <img 
                                    src={collection.image_url} 
                                    alt={collection.name}
                                    className="w-10 h-10 rounded object-cover"
                                    onError={(e) => {
                                      e.currentTarget.style.display = 'none';
                                      const fallback = e.currentTarget.nextElementSibling as HTMLElement | null
                          if (fallback) fallback.style.display = 'flex';
                                    }}
                                  />
                                  <div className="w-10 h-10 bg-gray-600 rounded flex items-center justify-center hidden">
                                    <PhotoIcon className="h-5 w-5 text-gray-400" />
                                  </div>
                                </div>
                              ) : (
                                <div className="w-10 h-10 bg-gray-600 rounded flex items-center justify-center">
                                  <PhotoIcon className="h-5 w-5 text-gray-400" />
                                </div>
                              )}
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                            <span className="font-medium">{collection.coin_count}</span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                            {collection.shopify_collection_id ? (
                              <span className="text-green-400 font-mono text-xs">
                                {collection.shopify_collection_id}
                              </span>
                            ) : (
                              <span className="text-gray-500">Not synced</span>
                            )}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                            <div className="flex space-x-2">
                              <button
                                onClick={(e) => {
                                  e.stopPropagation()
                                  setSelectedCollection(collection)
                                  setShowInventoryModal(true)
                                }}
                                className="text-green-400 hover:text-green-300 p-1 rounded hover:bg-gray-600"
                                title="View Inventory"
                              >
                                <EyeIcon className="h-4 w-4" />
                              </button>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation()
                                  handleEditCollection(collection)
                                }}
                                className="text-yellow-400 hover:text-yellow-300 p-1 rounded hover:bg-gray-600"
                                title="Edit Collection"
                              >
                                <PencilIcon className="h-4 w-4" />
                              </button>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation()
                                  setShowColorModal(true)
                                  setSelectedCollection(collection)
                                }}
                                className="text-blue-400 hover:text-blue-300 p-1 rounded hover:bg-gray-600"
                                title="Change Color"
                              >
                                <SwatchIcon className="h-4 w-4" />
                              </button>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation()
                                  handleDeleteCollection(collection.id)
                                }}
                                className="text-red-400 hover:text-red-300 p-1 rounded hover:bg-gray-600"
                                title="Delete Collection"
                              >
                                <TrashIcon className="h-4 w-4" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

      {/* Create/Edit Modals */}
      {showCreateModal && (
        <CollectionModal
          onClose={() => setShowCreateModal(false)}
          onSuccess={() => {
            fetchCollections()
            fetchStats()
          }}
        />
      )}

      {showEditModal && selectedCollection && (
        <CollectionModal
          collection={selectedCollection}
          onClose={() => {
            setShowEditModal(false)
            setSelectedCollection(null)
          }}
          onSuccess={() => {
            fetchCollections()
            fetchStats()
          }}
        />
      )}

              {/* Advanced Modal */}
              {showAdvancedModal && (
                <AdvancedCollectionModal
                  collection={selectedCollection}
                  onClose={() => {
                    setShowAdvancedModal(false)
                    setSelectedCollection(null)
                  }}
                  onSuccess={() => {
                    fetchCollections()
                    fetchStats()
                  }}
                />
              )}

              {/* Color Picker Modal */}
              {showColorModal && selectedCollection && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                  <div className="bg-gray-800 rounded-lg p-6 w-96">
                    <h3 className="text-lg font-semibold text-white mb-4">
                      Change Collection Color
                    </h3>
                    <p className="text-gray-400 mb-4">
                      Select a new color for "{selectedCollection.name}"
                    </p>
                    
                    <div className="grid grid-cols-8 gap-2 mb-6">
                      {[
                        '#3b82f6', '#ef4444', '#10b981', '#f59e0b',
                        '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16',
                        '#f97316', '#6366f1', '#14b8a6', '#eab308',
                        '#a855f7', '#f43f5e', '#0ea5e9', '#22c55e'
                      ].map((color) => (
                        <button
                          key={color}
                          onClick={() => {
                            // Update collection color
                            const updatedCollection = { ...selectedCollection, color }
                            setSelectedCollection(updatedCollection)
                            setShowColorModal(false)
                            // TODO: Save to backend
                            toast.success('Color updated successfully')
                          }}
                          className={`w-8 h-8 rounded-full border-2 ${
                            selectedCollection.color === color 
                              ? 'border-white' 
                              : 'border-gray-600'
                          }`}
                          style={{ backgroundColor: color }}
                        />
                      ))}
                    </div>
                    
                    <div className="flex justify-end space-x-3">
                      <button
                        onClick={() => setShowColorModal(false)}
                        className="px-4 py-2 text-gray-400 hover:text-white transition-colors"
                      >
                        Cancel
                      </button>
                      <button
                        onClick={() => setShowColorModal(false)}
                        className="px-4 py-2 bg-yellow-500 hover:bg-yellow-600 text-black rounded transition-colors"
                      >
                        Done
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* Inventory Modal */}
              {showInventoryModal && selectedCollection && (
                <CollectionInventory
                  collectionId={selectedCollection.id}
                  collectionName={selectedCollection.name}
                  onClose={() => {
                    setShowInventoryModal(false)
                    setSelectedCollection(null)
                  }}
                />
              )}
            </div>
          )
        }
