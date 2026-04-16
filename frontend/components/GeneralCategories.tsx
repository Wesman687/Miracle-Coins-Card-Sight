import { useState, useEffect } from 'react'
import { TagIcon, PlusIcon, TrashIcon, PencilIcon } from '@heroicons/react/24/outline'
import { api } from '../lib/api'
import toast from 'react-hot-toast'

interface GeneralCategory {
  id: number
  name: string
  description: string
  bulk_price_per_oz: number
  coin_count: number
  total_value: number
}

interface GeneralCategoriesProps {
  coinId?: number
  onCategorySelect?: (category: GeneralCategory) => void
  showAddToCategory?: boolean
}

export default function GeneralCategories({ coinId, onCategorySelect, showAddToCategory = false }: GeneralCategoriesProps) {
  const [categories, setCategories] = useState<GeneralCategory[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [showAddModal, setShowAddModal] = useState(false)
  const [editingCategory, setEditingCategory] = useState<GeneralCategory | null>(null)
  const [newCategory, setNewCategory] = useState({
    name: '',
    description: '',
    bulk_price_per_oz: 0
  })

  // Fetch categories on component mount
  useEffect(() => {
    fetchCategories()
  }, [])

  const fetchCategories = async () => {
    try {
      const response = await api.get('/categories')
      setCategories(response.data)
    } catch (error) {
      console.error('Error fetching categories:', error)
      toast.error('Failed to load categories')
    } finally {
      setIsLoading(false)
    }
  }

  const handleAddToCategory = async (categoryId: number) => {
    if (!coinId) return
    
    try {
      await api.post(`/coins/${coinId}/add-to-category`, {
        category_id: categoryId
      })
      toast.success('Coin added to category successfully!')
      fetchCategories() // Refresh to update counts
    } catch (error) {
      console.error('Error adding to category:', error)
      toast.error('Failed to add coin to category')
    }
  }

  const handleCreateCategory = async () => {
    try {
      await api.post('/categories', newCategory)
      toast.success('Category created successfully!')
      setShowAddModal(false)
      setNewCategory({ name: '', description: '', bulk_price_per_oz: 0 })
      fetchCategories()
    } catch (error) {
      console.error('Error creating category:', error)
      toast.error('Failed to create category')
    }
  }

  const handleUpdateCategory = async () => {
    if (!editingCategory) return
    
    try {
      await api.put(`/categories/${editingCategory.id}`, editingCategory)
      toast.success('Category updated successfully!')
      setEditingCategory(null)
      fetchCategories()
    } catch (error) {
      console.error('Error updating category:', error)
      toast.error('Failed to update category')
    }
  }

  const handleDeleteCategory = async (categoryId: number) => {
    if (!confirm('Are you sure you want to delete this category? This action cannot be undone.')) {
      return
    }
    
    try {
      await api.delete(`/categories/${categoryId}`)
      toast.success('Category deleted successfully!')
      fetchCategories()
    } catch (error) {
      console.error('Error deleting category:', error)
      toast.error('Failed to delete category')
    }
  }

  if (isLoading) {
    return (
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-700 rounded mb-4"></div>
          <div className="space-y-3">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-16 bg-gray-700 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-2">
          <TagIcon className="h-6 w-6 text-blue-400" />
          <h3 className="text-lg font-semibold text-white">General Categories</h3>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="bg-blue-500 hover:bg-blue-600 text-white px-3 py-2 rounded-lg flex items-center space-x-1 transition-colors"
        >
          <PlusIcon className="h-4 w-4" />
          <span>Add Category</span>
        </button>
      </div>

      <div className="space-y-4">
        {categories.map((category) => (
          <div key={category.id} className="bg-gray-700 rounded-lg p-4 border border-gray-600">
            <div className="flex items-center justify-between mb-2">
              <h4 className="font-medium text-white">{category.name}</h4>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setEditingCategory(category)}
                  className="text-gray-400 hover:text-white transition-colors"
                  title="Edit category"
                >
                  <PencilIcon className="h-4 w-4" />
                </button>
                <button
                  onClick={() => handleDeleteCategory(category.id)}
                  className="text-red-400 hover:text-red-300 transition-colors"
                  title="Delete category"
                >
                  <TrashIcon className="h-4 w-4" />
                </button>
              </div>
            </div>
            
            <p className="text-sm text-gray-300 mb-3">{category.description}</p>
            
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div>
                <span className="text-gray-400">Bulk Price:</span>
                <div className="font-medium text-yellow-400">
                  ${category.bulk_price_per_oz.toFixed(2)}/oz
                </div>
              </div>
              <div>
                <span className="text-gray-400">Coins:</span>
                <div className="font-medium text-white">{category.coin_count}</div>
              </div>
              <div>
                <span className="text-gray-400">Total Value:</span>
                <div className="font-medium text-green-400">
                  ${category.total_value.toFixed(2)}
                </div>
              </div>
            </div>

            {showAddToCategory && coinId && (
              <div className="mt-3 pt-3 border-t border-gray-600">
                <button
                  onClick={() => handleAddToCategory(category.id)}
                  className="bg-green-500 hover:bg-green-600 text-white px-3 py-1 rounded-lg text-sm font-medium transition-colors"
                >
                  Add to This Category
                </button>
              </div>
            )}
          </div>
        ))}

        {categories.length === 0 && (
          <div className="text-center py-8">
            <TagIcon className="h-12 w-12 text-gray-500 mx-auto mb-3" />
            <p className="text-gray-400">No categories created yet</p>
            <p className="text-sm text-gray-500">Create your first category to organize bulk inventory</p>
          </div>
        )}
      </div>

      {/* Add Category Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 w-96">
            <h3 className="text-lg font-semibold text-white mb-4">Create New Category</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Category Name
                </label>
                <input
                  type="text"
                  value={newCategory.name}
                  onChange={(e) => setNewCategory({ ...newCategory, name: e.target.value })}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
                  placeholder="e.g., Common Silver Coins"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Description
                </label>
                <textarea
                  value={newCategory.description}
                  onChange={(e) => setNewCategory({ ...newCategory, description: e.target.value })}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500 resize-none"
                  rows={3}
                  placeholder="Describe this category..."
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Bulk Price per Oz
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={newCategory.bulk_price_per_oz}
                  onChange={(e) => setNewCategory({ ...newCategory, bulk_price_per_oz: parseFloat(e.target.value) || 0 })}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
                  placeholder="0.00"
                />
              </div>
            </div>

            <div className="flex space-x-3 mt-6">
              <button
                onClick={handleCreateCategory}
                className="flex-1 bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg font-medium transition-colors"
              >
                Create Category
              </button>
              <button
                onClick={() => setShowAddModal(false)}
                className="px-4 py-2 bg-gray-600 hover:bg-gray-500 text-white rounded-lg transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Category Modal */}
      {editingCategory && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 w-96">
            <h3 className="text-lg font-semibold text-white mb-4">Edit Category</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Category Name
                </label>
                <input
                  type="text"
                  value={editingCategory.name}
                  onChange={(e) => setEditingCategory({ ...editingCategory, name: e.target.value })}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Description
                </label>
                <textarea
                  value={editingCategory.description}
                  onChange={(e) => setEditingCategory({ ...editingCategory, description: e.target.value })}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500 resize-none"
                  rows={3}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Bulk Price per Oz
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={editingCategory.bulk_price_per_oz}
                  onChange={(e) => setEditingCategory({ ...editingCategory, bulk_price_per_oz: parseFloat(e.target.value) || 0 })}
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
                />
              </div>
            </div>

            <div className="flex space-x-3 mt-6">
              <button
                onClick={handleUpdateCategory}
                className="flex-1 bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg font-medium transition-colors"
              >
                Update Category
              </button>
              <button
                onClick={() => setEditingCategory(null)}
                className="px-4 py-2 bg-gray-600 hover:bg-gray-500 text-white rounded-lg transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
