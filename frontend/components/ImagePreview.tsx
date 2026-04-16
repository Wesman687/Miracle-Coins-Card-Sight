import { useState } from 'react'
import { 
  PhotoIcon, 
  XMarkIcon, 
  MagnifyingGlassPlusIcon,
  MagnifyingGlassMinusIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline'

interface ImagePreviewProps {
  imageUrl: string
  filename: string
  size: number
  type: string
  onRemove: () => void
  onReanalyze?: () => void
  className?: string
}

export default function ImagePreview({ 
  imageUrl, 
  filename, 
  size, 
  type, 
  onRemove, 
  onReanalyze,
  className = ''
}: ImagePreviewProps) {
  const [zoom, setZoom] = useState(1)
  const [isFullscreen, setIsFullscreen] = useState(false)

  const handleZoomIn = () => {
    setZoom(prev => Math.min(prev + 0.25, 3))
  }

  const handleZoomOut = () => {
    setZoom(prev => Math.max(prev - 0.25, 0.5))
  }

  const handleResetZoom = () => {
    setZoom(1)
  }

  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen)
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  return (
    <div className={`bg-gray-800 rounded-lg p-4 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          <PhotoIcon className="h-5 w-5 text-green-400" />
          <div>
            <div className="text-sm font-medium text-white truncate max-w-48">
              {filename}
            </div>
            <div className="text-xs text-gray-400">
              {formatFileSize(size)} • {type}
            </div>
          </div>
        </div>
        
        <div className="flex items-center space-x-1">
          {onReanalyze && (
            <button
              onClick={onReanalyze}
              className="p-1 text-gray-400 hover:text-blue-400 transition-colors"
              title="Re-analyze image"
            >
              <ArrowPathIcon className="h-4 w-4" />
            </button>
          )}
          <button
            onClick={onRemove}
            className="p-1 text-gray-400 hover:text-red-400 transition-colors"
            title="Remove image"
          >
            <XMarkIcon className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Image Container */}
      <div className="relative bg-gray-900 rounded-lg overflow-hidden">
        <div className="relative">
          <img
            src={imageUrl}
            alt="Coin preview"
            className="w-full h-auto max-h-64 object-contain"
            style={{ transform: `scale(${zoom})` }}
            onClick={toggleFullscreen}
          />
          
          {/* Zoom Controls */}
          <div className="absolute top-2 right-2 flex flex-col space-y-1">
            <button
              onClick={handleZoomIn}
              className="p-1 bg-gray-800/80 hover:bg-gray-700/80 text-white rounded transition-colors"
              title="Zoom in"
            >
              <MagnifyingGlassPlusIcon className="h-4 w-4" />
            </button>
            <button
              onClick={handleZoomOut}
              className="p-1 bg-gray-800/80 hover:bg-gray-700/80 text-white rounded transition-colors"
              title="Zoom out"
            >
              <MagnifyingGlassMinusIcon className="h-4 w-4" />
            </button>
            <button
              onClick={handleResetZoom}
              className="p-1 bg-gray-800/80 hover:bg-gray-700/80 text-white rounded transition-colors"
              title="Reset zoom"
            >
              <ArrowPathIcon className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Zoom Info */}
      <div className="flex items-center justify-between mt-2 text-xs text-gray-400">
        <span>Click image to view fullscreen</span>
        <span>Zoom: {Math.round(zoom * 100)}%</span>
      </div>

      {/* Fullscreen Modal */}
      {isFullscreen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-90 flex items-center justify-center z-50 p-4"
          onClick={toggleFullscreen}
        >
          <div className="relative max-w-4xl max-h-full">
            <img
              src={imageUrl}
              alt="Coin fullscreen"
              className="max-w-full max-h-full object-contain"
              onClick={(e) => e.stopPropagation()}
            />
            
            <button
              onClick={toggleFullscreen}
              className="absolute top-4 right-4 p-2 bg-gray-800/80 hover:bg-gray-700/80 text-white rounded-full transition-colors"
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

