import { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { XMarkIcon, TagIcon } from '@heroicons/react/24/outline'
import { api } from '../lib/api'
import toast from 'react-hot-toast'
import RichTextEditor from './RichTextEditor'

const collectionSchema = z.object({
  name: z.string().min(1, 'Name is required').max(100, 'Name too long'),
  description: z.string().optional(),
  description_html: z.string().optional(),
  shopify_collection_id: z.string().optional(),
  color: z.string().regex(/^#[0-9A-Fa-f]{6}$/, 'Invalid hex color'),
  icon: z.string().optional(),
  image_url: z.string().optional()
})

type CollectionFormData = z.infer<typeof collectionSchema>

interface Collection {
  id: number
  name: string
  description?: string
  description_html?: string
  shopify_collection_id?: string
  color: string
  icon?: string
  image_url?: string
  coin_count: number
  total_value?: number
  average_price?: number
  created_at: string
  updated_at: string
}

interface CollectionModalProps {
  collection?: Collection | null
  onClose: () => void
  onSuccess: () => void
}

const colorOptions = [
  { name: 'Blue', value: '#3b82f6' },
  { name: 'Green', value: '#10b981' },
  { name: 'Purple', value: '#8b5cf6' },
  { name: 'Red', value: '#ef4444' },
  { name: 'Orange', value: '#f97316' },
  { name: 'Pink', value: '#ec4899' },
  { name: 'Indigo', value: '#6366f1' },
  { name: 'Teal', value: '#14b8a6' },
  { name: 'Gold', value: '#f59e0b' },
  { name: 'Silver', value: '#c0c0c0' }
]


export default function CollectionModal({ collection, onClose, onSuccess }: CollectionModalProps) {
  const [loading, setLoading] = useState(false)
  const isEditing = !!collection

  const {
    register,
    handleSubmit,
    formState: { errors },
    setValue,
    watch
  } = useForm<CollectionFormData>({
    resolver: zodResolver(collectionSchema),
    defaultValues: {
      name: collection?.name || '',
      description: collection?.description || '',
      description_html: collection?.description_html || '',
      shopify_collection_id: collection?.shopify_collection_id || '',
      color: collection?.color || '#3b82f6',
      icon: collection?.icon || '',
      image_url: collection?.image_url || ''
    }
  })

  const selectedColor = watch('color')

  const onSubmit = async (data: CollectionFormData) => {
    setLoading(true)
    try {
      if (isEditing) {
        await api.put(`/collections/${collection.id}`, data)
        toast.success('Collection updated successfully')
      } else {
        await api.post('/collections', data)
        toast.success('Collection created successfully')
      }
      onSuccess()
      onClose()
    } catch (error: any) {
      console.error('Error saving collection:', error)
      const message = error.response?.data?.detail || 'Failed to save collection'
      toast.error(message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-500 rounded-lg">
              <TagIcon className="h-6 w-6 text-white" />
            </div>
            <h2 className="text-xl font-bold text-white">
              {isEditing ? 'Edit Collection' : 'Create New Collection'}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          {/* Basic Information */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-white">Basic Information</h3>
            
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Collection Name *
              </label>
              <input
                {...register('name')}
                type="text"
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
                placeholder="e.g., Morgan Silver Dollars"
              />
              {errors.name && (
                <p className="mt-1 text-sm text-red-400">{errors.name.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Description
              </label>
              <RichTextEditor
                value={watch('description_html') || ''}
                onChange={(value) => setValue('description_html', value)}
                placeholder="Enter collection description..."
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Shopify Collection ID
              </label>
              <input
                {...register('shopify_collection_id')}
                type="text"
                readOnly
                className="w-full bg-gray-600 border border-gray-500 rounded-lg px-3 py-2 text-gray-300 cursor-not-allowed"
                placeholder="Set automatically by Shopify"
              />
              <p className="mt-1 text-xs text-gray-400">
                This field is managed by Shopify and cannot be edited manually.
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Collection Image
              </label>
              <div className="space-y-4">
                {/* Current Image Display */}
                {watch('image_url') && (
                  <div className="relative inline-block">
                    <img 
                      src={watch('image_url')} 
                      alt="Collection image"
                      className="w-32 h-32 rounded-lg object-cover border border-gray-600"
                      onError={(e) => {
                        e.currentTarget.style.display = 'none';
                        const fallback = e.currentTarget.nextElementSibling as HTMLElement | null
                          if (fallback) fallback.style.display = 'flex';
                      }}
                    />
                    <div className="w-32 h-32 bg-gray-600 rounded-lg flex items-center justify-center hidden">
                      <svg className="h-8 w-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                    </div>
                    <button
                      type="button"
                      onClick={() => setValue('image_url', '')}
                      className="absolute -top-2 -right-2 bg-red-500 hover:bg-red-600 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm"
                    >
                      ×
                    </button>
                  </div>
                )}
                
                {/* Image URL Input */}
                <div>
                  <input
                    {...register('image_url')}
                    type="url"
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
                    placeholder="Enter image URL..."
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Appearance */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-white">Appearance</h3>
            
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Color
              </label>
              <div className="grid grid-cols-5 gap-2">
                {colorOptions.map((color) => (
                  <button
                    key={color.value}
                    type="button"
                    onClick={() => setValue('color', color.value)}
                    className={`w-12 h-12 rounded-lg border-2 transition-all ${
                      selectedColor === color.value
                        ? 'border-white scale-110'
                        : 'border-gray-600 hover:border-gray-400'
                    }`}
                    style={{ backgroundColor: color.value }}
                    title={color.name}
                  />
                ))}
              </div>
              <input
                {...register('color')}
                type="text"
                className="mt-2 w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
                placeholder="#3b82f6"
              />
              {errors.color && (
                <p className="mt-1 text-sm text-red-400">{errors.color.message}</p>
              )}
            </div>
          </div>


          {/* Preview */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-white">Preview</h3>
            <div className="bg-gray-700 rounded-lg p-4">
              <div className="flex items-center space-x-3">
                <div 
                  className="w-4 h-4 rounded-full"
                  style={{ backgroundColor: selectedColor }}
                ></div>
                <span className="text-white font-medium">
                  {watch('name') || 'Collection Name'}
                </span>
                <span className="px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
                  Active
                </span>
              </div>
              {watch('description_html') && (
                <div 
                  className="mt-2 text-sm text-gray-400 prose prose-invert max-w-none"
                  dangerouslySetInnerHTML={{ __html: watch('description_html') }}
                />
              )}
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end space-x-3 pt-6 border-t border-gray-700">
            <button
              type="button"
              onClick={onClose}
              className="bg-gray-700 hover:bg-gray-600 text-white px-6 py-2 rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="bg-blue-500 hover:bg-blue-600 text-white px-6 py-2 rounded-lg transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Saving...' : (isEditing ? 'Update Collection' : 'Create Collection')}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
