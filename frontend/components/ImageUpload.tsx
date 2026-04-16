import { useState, useRef, useCallback } from 'react'
import { 
  PhotoIcon, 
  XMarkIcon, 
  ArrowUpTrayIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline'
import { api } from '../lib/api'
import toast from 'react-hot-toast'

interface ImageUploadProps {
  onImageUploaded: (imageUrl: string, imageData: any) => void
  onImageRemoved: () => void
  maxFileSize?: number // in MB
  acceptedFormats?: string[]
  className?: string
}

interface UploadedImage {
  url: string
  filename: string
  size: number
  type: string
}

export default function ImageUpload({ 
  onImageUploaded, 
  onImageRemoved,
  maxFileSize = 10,
  acceptedFormats = ['jpg', 'jpeg', 'png', 'webp'],
  className = ''
}: ImageUploadProps) {
  const [isDragOver, setIsDragOver] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadedImage, setUploadedImage] = useState<UploadedImage | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const validateFile = (file: File): string | null => {
    // Check file size
    if (file.size > maxFileSize * 1024 * 1024) {
      return `File size must be less than ${maxFileSize}MB`
    }

    // Check file type
    const fileExtension = file.name.split('.').pop()?.toLowerCase()
    if (!fileExtension || !acceptedFormats.includes(fileExtension)) {
      return `File must be one of: ${acceptedFormats.join(', ')}`
    }

    return null
  }

  const handleFileUpload = useCallback(async (file: File) => {
    const validationError = validateFile(file)
    if (validationError) {
      toast.error(validationError)
      return
    }

    setIsUploading(true)
    
    try {
      // Create FormData for file upload
      const formData = new FormData()
      formData.append('file', file)

      // Upload file using AI chat upload endpoint
      const response = await api.post('/ai-chat/upload-image', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })

      const uploadedFile = response.data.data
      
      // Construct full URL for the uploaded image
      const fullImageUrl = uploadedFile.public_url.startsWith('http') 
        ? uploadedFile.public_url 
        : `http://localhost:1270${uploadedFile.public_url}`

      const imageData: UploadedImage = {
        url: fullImageUrl,
        filename: uploadedFile.filename,
        size: file.size,
        type: file.type
      }

      setUploadedImage(imageData)
      setPreviewUrl(fullImageUrl)
      onImageUploaded(fullImageUrl, imageData)
      
      toast.success('Image uploaded successfully!')

    } catch (error) {
      console.error('Image upload error:', error)
      toast.error('Failed to upload image')
    } finally {
      setIsUploading(false)
    }
  }, [maxFileSize, acceptedFormats, onImageUploaded])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
    
    const files = Array.from(e.dataTransfer.files)
    if (files.length > 0) {
      handleFileUpload(files[0])
    }
  }, [handleFileUpload])

  const handleFileInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      handleFileUpload(files[0])
    }
  }, [handleFileUpload])

  const handleRemoveImage = useCallback(() => {
    setUploadedImage(null)
    setPreviewUrl(null)
    onImageRemoved()
    
    // Clear file input
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }, [onImageRemoved])

  const handleClickUpload = useCallback(() => {
    fileInputRef.current?.click()
  }, [])

  return (
    <div className={`space-y-3 ${className}`}>
      {/* Upload Area */}
      {!uploadedImage && (
        <div
          className={`border-2 border-dashed rounded-lg p-6 text-center transition-all duration-200 cursor-pointer ${
            isDragOver
              ? 'border-yellow-500 bg-yellow-500/10'
              : 'border-gray-600 hover:border-gray-500 hover:bg-gray-800/50'
          } ${isUploading ? 'opacity-50 cursor-not-allowed' : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={handleClickUpload}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept={acceptedFormats.map(format => `.${format}`).join(',')}
            onChange={handleFileInputChange}
            className="hidden"
            disabled={isUploading}
          />
          
          <div className="flex flex-col items-center space-y-3">
            {isUploading ? (
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-yellow-500"></div>
            ) : (
              <PhotoIcon className="h-8 w-8 text-gray-400" />
            )}
            
            <div>
              <p className="text-sm text-white font-medium">
                {isUploading ? 'Uploading...' : 'Drop image here or click to upload'}
              </p>
              <p className="text-xs text-gray-400 mt-1">
                {acceptedFormats.join(', ').toUpperCase()} • Max {maxFileSize}MB
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Image Preview */}
      {uploadedImage && previewUrl && (
        <div className="relative">
          <div className="bg-gray-800 rounded-lg p-4">
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0">
                <img
                  src={previewUrl}
                  alt="Uploaded coin"
                  className="h-20 w-20 object-cover rounded-lg border border-gray-600"
                />
              </div>
              
              <div className="flex-1 min-w-0">
                <div className="flex items-center space-x-2 mb-1">
                  <PhotoIcon className="h-4 w-4 text-green-400" />
                  <span className="text-sm font-medium text-white truncate">
                    {uploadedImage.filename}
                  </span>
                </div>
                
                <div className="text-xs text-gray-400 space-y-1">
                  <div>Size: {(uploadedImage.size / 1024 / 1024).toFixed(2)} MB</div>
                  <div>Type: {uploadedImage.type}</div>
                </div>
              </div>
              
              <button
                onClick={handleRemoveImage}
                className="flex-shrink-0 p-1 text-gray-400 hover:text-red-400 transition-colors"
              >
                <XMarkIcon className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Upload Button (Alternative) */}
      {!uploadedImage && (
        <button
          onClick={handleClickUpload}
          disabled={isUploading}
          className="w-full bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded-lg flex items-center justify-center space-x-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <ArrowUpTrayIcon className="h-4 w-4" />
          <span className="text-sm font-medium">
            {isUploading ? 'Uploading...' : 'Choose Image File'}
          </span>
        </button>
      )}

      {/* Help Text */}
      <div className="text-xs text-gray-500 space-y-1">
        <div className="flex items-center space-x-1">
          <ExclamationTriangleIcon className="h-3 w-3" />
          <span>Supported formats: {acceptedFormats.join(', ').toUpperCase()}</span>
        </div>
        <div>Maximum file size: {maxFileSize}MB</div>
        <div>For best results, use clear, well-lit photos of coins</div>
      </div>
    </div>
  )
}
