import { useState, useRef } from 'react'
import { 
  PhotoIcon, 
  TrashIcon, 
  StarIcon, 
  ArrowUpIcon, 
  ArrowDownIcon,
  PlusIcon,
  EyeIcon,
  XMarkIcon
} from '@heroicons/react/24/outline'
import { StarIcon as StarIconSolid } from '@heroicons/react/24/solid'
import { api } from '../lib/api'
import toast from 'react-hot-toast'

interface CollectionImage {
  id: number
  collection_id: number
  image_url: string
  alt_text?: string
  caption?: string
  is_featured: boolean
  sort_order: number
  file_size?: number
  width?: number
  height?: number
  mime_type?: string
  uploaded_at: string
  updated_at: string
  file_size_formatted?: string
  dimensions_formatted?: string
}

interface ImageGalleryProps {
  collectionId?: number
  images: CollectionImage[]
  featuredImage?: CollectionImage
  onUpdate: () => void
}

export default function ImageGallery({ collectionId, images, featuredImage, onUpdate }: ImageGalleryProps) {
  const [uploading, setUploading] = useState(false)
  const [selectedImage, setSelectedImage] = useState<CollectionImage | null>(null)
  const [showUploadModal, setShowUploadModal] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files
    if (!files || files.length === 0) return

    setUploading(true)
    try {
      for (const file of Array.from(files)) {
        const formData = new FormData()
        formData.append('file', file)
        formData.append('alt_text', file.name)
        formData.append('is_featured', images.length === 0 ? 'true' : 'false')

        await api.post(`/collections/${collectionId}/images/upload`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })
      }
      
      toast.success(`${files.length} image(s) uploaded successfully`)
      onUpdate()
    } catch (error: any) {
      console.error('Error uploading images:', error)
      toast.error('Failed to upload images')
    } finally {
      setUploading(false)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  const handleDeleteImage = async (imageId: number) => {
    if (!confirm('Are you sure you want to delete this image?')) return

    try {
      await api.delete(`/collections/${collectionId}/images/${imageId}`)
      toast.success('Image deleted successfully')
      onUpdate()
    } catch (error: any) {
      console.error('Error deleting image:', error)
      toast.error('Failed to delete image')
    }
  }

  const handleSetFeatured = async (imageId: number) => {
    try {
      await api.patch(`/collections/${collectionId}/images/${imageId}/featured`)
      toast.success('Featured image updated')
      onUpdate()
    } catch (error: any) {
      console.error('Error setting featured image:', error)
      toast.error('Failed to set featured image')
    }
  }

  const handleReorderImages = async (imageId: number, direction: 'up' | 'down') => {
    const currentImage = images.find(img => img.id === imageId)
    if (!currentImage) return

    const sortedImages = [...images].sort((a, b) => a.sort_order - b.sort_order)
    const currentIndex = sortedImages.findIndex(img => img.id === imageId)
    
    if (direction === 'up' && currentIndex > 0) {
      const newOrder = sortedImages[currentIndex].sort_order
      const prevOrder = sortedImages[currentIndex - 1].sort_order
      
      // Swap sort orders
      await api.post(`/collections/${collectionId}/images/reorder`, {
        [imageId]: prevOrder,
        [sortedImages[currentIndex - 1].id]: newOrder
      })
    } else if (direction === 'down' && currentIndex < sortedImages.length - 1) {
      const newOrder = sortedImages[currentIndex].sort_order
      const nextOrder = sortedImages[currentIndex + 1].sort_order
      
      // Swap sort orders
      await api.post(`/collections/${collectionId}/images/reorder`, {
        [imageId]: nextOrder,
        [sortedImages[currentIndex + 1].id]: newOrder
      })
    }
    
    onUpdate()
  }

  const sortedImages = [...images].sort((a, b) => a.sort_order - b.sort_order)

  return (
    <div className="space-y-6">
      {/* Upload Section */}
      <div className="bg-gray-700 rounded-lg p-6 border-2 border-dashed border-gray-600">
        <div className="text-center">
          <PhotoIcon className="mx-auto h-12 w-12 text-gray-400" />
          <div className="mt-4">
            <label htmlFor="image-upload" className="cursor-pointer">
              <span className="mt-2 block text-sm font-medium text-gray-300">
                Upload Images
              </span>
              <span className="mt-1 block text-xs text-gray-400">
                PNG, JPG, GIF up to 10MB each
              </span>
            </label>
            <input
              ref={fileInputRef}
              id="image-upload"
              type="file"
              multiple
              accept="image/*"
              onChange={handleFileUpload}
              className="sr-only"
              disabled={uploading}
            />
          </div>
          <div className="mt-4">
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading}
              className="bg-blue-500 hover:bg-blue-600 disabled:bg-gray-600 text-white px-4 py-2 rounded-lg flex items-center space-x-2 mx-auto transition-colors"
            >
              <PlusIcon className="h-4 w-4" />
              <span>{uploading ? 'Uploading...' : 'Choose Files'}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Images Grid */}
      {sortedImages.length > 0 && (
        <div className="space-y-4">
          <h4 className="text-lg font-semibold text-white">Collection Images</h4>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {sortedImages.map((image, index) => (
              <div
                key={image.id}
                className="relative bg-gray-700 rounded-lg overflow-hidden group"
              >
                {/* Image */}
                <div className="aspect-square relative">
                  <img
                    src={image.image_url}
                    alt={image.alt_text || 'Collection image'}
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      const target = e.target as HTMLImageElement
                      target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjMzMzIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIxNCIgZmlsbD0iIzk5OSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPkltYWdlIE5vdCBGb3VuZDwvdGV4dD48L3N2Zz4='
                    }}
                  />
                  
                  {/* Overlay */}
                  <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-50 transition-all duration-200 flex items-center justify-center">
                    <div className="opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex space-x-2">
                      <button
                        onClick={() => setSelectedImage(image)}
                        className="p-2 bg-white bg-opacity-20 hover:bg-opacity-30 rounded-full transition-colors"
                        title="View Details"
                      >
                        <EyeIcon className="h-4 w-4 text-white" />
                      </button>
                      <button
                        onClick={() => handleDeleteImage(image.id)}
                        className="p-2 bg-red-500 bg-opacity-20 hover:bg-opacity-30 rounded-full transition-colors"
                        title="Delete Image"
                      >
                        <TrashIcon className="h-4 w-4 text-white" />
                      </button>
                    </div>
                  </div>

                  {/* Featured Badge */}
                  {image.is_featured && (
                    <div className="absolute top-2 left-2">
                      <div className="bg-yellow-500 text-black px-2 py-1 rounded-full text-xs font-semibold flex items-center space-x-1">
                        <StarIconSolid className="h-3 w-3" />
                        <span>Featured</span>
                      </div>
                    </div>
                  )}

                  {/* Sort Order */}
                  <div className="absolute top-2 right-2 bg-black bg-opacity-50 text-white px-2 py-1 rounded text-xs">
                    {image.sort_order + 1}
                  </div>
                </div>

                {/* Image Info */}
                <div className="p-3">
                  <div className="text-sm text-gray-300 truncate">
                    {image.alt_text || 'Untitled'}
                  </div>
                  {image.dimensions_formatted && (
                    <div className="text-xs text-gray-400">
                      {image.dimensions_formatted}
                    </div>
                  )}
                  {image.file_size_formatted && (
                    <div className="text-xs text-gray-400">
                      {image.file_size_formatted}
                    </div>
                  )}
                </div>

                {/* Action Buttons */}
                <div className="absolute bottom-2 left-2 right-2 flex justify-between">
                  <div className="flex space-x-1">
                    <button
                      onClick={() => handleReorderImages(image.id, 'up')}
                      disabled={index === 0}
                      className="p-1 bg-black bg-opacity-50 hover:bg-opacity-70 disabled:opacity-30 disabled:cursor-not-allowed rounded transition-colors"
                      title="Move Up"
                    >
                      <ArrowUpIcon className="h-3 w-3 text-white" />
                    </button>
                    <button
                      onClick={() => handleReorderImages(image.id, 'down')}
                      disabled={index === sortedImages.length - 1}
                      className="p-1 bg-black bg-opacity-50 hover:bg-opacity-70 disabled:opacity-30 disabled:cursor-not-allowed rounded transition-colors"
                      title="Move Down"
                    >
                      <ArrowDownIcon className="h-3 w-3 text-white" />
                    </button>
                  </div>
                  <button
                    onClick={() => handleSetFeatured(image.id)}
                    className={`p-1 rounded transition-colors ${
                      image.is_featured
                        ? 'bg-yellow-500 text-black'
                        : 'bg-black bg-opacity-50 hover:bg-opacity-70 text-white'
                    }`}
                    title={image.is_featured ? 'Remove Featured' : 'Set as Featured'}
                  >
                    <StarIcon className="h-3 w-3" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Image Details Modal */}
      {selectedImage && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white">Image Details</h3>
              <button
                onClick={() => setSelectedImage(null)}
                className="text-gray-400 hover:text-white transition-colors"
              >
                <XMarkIcon className="h-6 w-6" />
              </button>
            </div>
            
            <div className="space-y-4">
              <div className="text-center">
                <img
                  src={selectedImage.image_url}
                  alt={selectedImage.alt_text || 'Collection image'}
                  className="max-w-full max-h-96 mx-auto rounded-lg"
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Alt Text
                  </label>
                  <p className="text-white">{selectedImage.alt_text || 'None'}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Caption
                  </label>
                  <p className="text-white">{selectedImage.caption || 'None'}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Dimensions
                  </label>
                  <p className="text-white">{selectedImage.dimensions_formatted || 'Unknown'}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    File Size
                  </label>
                  <p className="text-white">{selectedImage.file_size_formatted || 'Unknown'}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Upload Date
                  </label>
                  <p className="text-white">
                    {new Date(selectedImage.uploaded_at).toLocaleDateString()}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Status
                  </label>
                  <p className="text-white">
                    {selectedImage.is_featured ? 'Featured' : 'Regular'}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

