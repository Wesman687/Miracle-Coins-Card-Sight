import { useState } from 'react'
import PhotoCaptureEditor from './PhotoCaptureEditor'
import { XMarkIcon, PhotoIcon, ArrowsUpDownIcon } from '@heroicons/react/24/outline'
import { DndProvider, useDrag, useDrop } from 'react-dnd'
import { HTML5Backend } from 'react-dnd-html5-backend'

interface ImageItem {
  id: string
  url: string
  filename: string
}

interface ImageManagerProps {
  images: string[]
  onImagesChange: (images: string[]) => void
  onUpload?: (files: FileList) => Promise<string[]>
}

interface DraggableImageProps {
  image: ImageItem
  index: number
  onRemove: (id: string) => void
  onMove: (dragIndex: number, hoverIndex: number) => void
}

const DraggableImage = ({ image, index, onRemove, onMove }: DraggableImageProps) => {
  const [{ isDragging }, drag] = useDrag({
    type: 'image',
    item: { index },
    collect: (monitor) => ({
      isDragging: monitor.isDragging(),
    }),
  })

  const [, drop] = useDrop({
    accept: 'image',
    hover: (draggedItem: { index: number }) => {
      if (draggedItem.index !== index) {
        onMove(draggedItem.index, index)
        draggedItem.index = index
      }
    },
  })

  return (
    <div
      ref={(node) => {
        drag(node)
        drop(node)
      }}
      className={`relative group cursor-move ${isDragging ? 'opacity-50' : ''}`}
    >
      <div className="relative w-24 h-24 bg-gray-700 rounded-lg overflow-hidden border-2 border-gray-600 hover:border-yellow-500 transition-colors">
        <img
          src={image.url}
          alt={image.filename}
          className="w-full h-full object-cover"
          onClick={() => window.open(image.url, '_blank')}
        />
        
        {/* Remove button */}
        <button
          type="button"
          onClick={() => onRemove(image.id)}
          className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 hover:bg-red-600 text-white rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
        >
          <XMarkIcon className="h-4 w-4" />
        </button>

        {/* Drag indicator */}
        <div className="absolute bottom-1 right-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <ArrowsUpDownIcon className="h-4 w-4 text-white bg-black/50 rounded" />
        </div>
      </div>
    </div>
  )
}

export default function ImageManager({ images, onImagesChange, onUpload }: ImageManagerProps) {
  const [isUploading, setIsUploading] = useState(false)
  const [showEditor, setShowEditor] = useState(false)

  const imageItems: ImageItem[] = images.map((url, index) => ({
    id: `img-${index}`,
    url,
    filename: `image-${index + 1}`,
  }))

  const handleRemove = (id: string) => {
    const index = imageItems.findIndex(img => img.id === id)
    if (index !== -1) {
      const newImages = [...images]
      newImages.splice(index, 1)
      onImagesChange(newImages)
    }
  }

  const handleMove = (dragIndex: number, hoverIndex: number) => {
    const newImages = [...images]
    const draggedImage = newImages[dragIndex]
    newImages.splice(dragIndex, 1)
    newImages.splice(hoverIndex, 0, draggedImage)
    onImagesChange(newImages)
  }

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files
    if (!files || !onUpload) return

    setIsUploading(true)
    try {
      const uploadedUrls = await onUpload(files)
      onImagesChange([...images, ...uploadedUrls])
    } catch (error) {
      console.error('Upload failed:', error)
    } finally {
      setIsUploading(false)
      // Reset input
      event.target.value = ''
    }
  }

  return (
    <DndProvider backend={HTML5Backend}>
      <div className="space-y-4">
        {/* Upload Area */}
        <div className="border-2 border-dashed border-gray-600 rounded-lg p-6 text-center hover:border-yellow-500 transition-colors">
          <input
            type="file"
            multiple
            accept="image/*"
            onChange={handleFileUpload}
            disabled={isUploading}
            className="hidden"
            id="image-upload"
          />
          <label
            htmlFor="image-upload"
            className="cursor-pointer flex flex-col items-center space-y-2"
          >
            <PhotoIcon className="h-8 w-8 text-gray-400" />
            <span className="text-gray-400">
              {isUploading ? 'Uploading...' : 'Click to upload images or drag and drop'}
            </span>
            <span className="text-xs text-gray-500">
              PNG, JPG, WEBP up to 10MB each
            </span>
          </label>
          {onUpload && (
            <button
              type="button"
              onClick={() => setShowEditor(true)}
              className="mt-4 rounded-lg border border-white/15 px-4 py-2 text-sm text-white hover:border-yellow-500 hover:text-yellow-300"
            >
              Take photo / crop / adjust
            </button>
          )}
        </div>

        {/* Image Grid */}
        {imageItems.length > 0 && (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-medium text-gray-300">
                Images ({imageItems.length})
              </h4>
              <span className="text-xs text-gray-500">
                Drag to reorder • Click to view • Hover for options
              </span>
            </div>
            
            <div className="grid grid-cols-4 gap-3">
              {imageItems.map((image, index) => (
                <DraggableImage
                  key={image.id}
                  image={image}
                  index={index}
                  onRemove={handleRemove}
                  onMove={handleMove}
                />
              ))}
            </div>
          </div>
        )}
      </div>
      {showEditor && onUpload && (
        <PhotoCaptureEditor
          onClose={() => setShowEditor(false)}
          onAddImages={async (files) => {
            const dt = new DataTransfer()
            files.forEach((file) => dt.items.add(file))
            const uploadedUrls = await onUpload(dt.files)
            onImagesChange([...images, ...uploadedUrls])
          }}
        />
      )}
    </DndProvider>
  )
}
