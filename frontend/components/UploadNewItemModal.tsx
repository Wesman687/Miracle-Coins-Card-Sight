import { useState, useRef, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { 
  XMarkIcon, 
  PhotoIcon, 
  SparklesIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  MagnifyingGlassIcon
} from '@heroicons/react/24/outline'
import { api } from '../lib/api'
import toast from 'react-hot-toast'

const coinSchema = z.object({
  sku: z.string().optional(),
  title: z.string().min(1, 'Title is required'),
  year: z.number().optional(),
  denomination: z.string().optional(),
  mint_mark: z.string().optional(),
  grade: z.string().optional(),
  category: z.string().optional(),
  shopify_collection_ids: z.array(z.string()).default([]),
  description: z.string().optional(),
  condition_notes: z.string().optional(),
  is_silver: z.boolean().default(false),
  silver_percent: z.number().optional(),
  silver_content_oz: z.number().optional(),
  paid_price: z.number().optional(),
  price_strategy: z.enum(['paid_price_multiplier', 'silver_spot_multiplier', 'gold_spot_multiplier', 'fixed_price', 'entry_based']).default('paid_price_multiplier'),
  price_multiplier: z.number().default(1.5),
  base_from_entry: z.boolean().default(true),
  entry_spot: z.number().optional(),
  entry_melt: z.number().optional(),
  override_price: z.boolean().default(false),
  override_value: z.number().optional(),
  fixed_price: z.number().optional(), // For hardcoded pricing
  quantity: z.number().default(1),
  status: z.string().default('active'),
  add_to_existing: z.boolean().default(false),
  existing_coin_id: z.number().optional(),
})

type CoinFormData = z.infer<typeof coinSchema>

interface AIEvaluation {
  suggested_price: number
  confidence_score: number
  selling_recommendation: string
  reasoning: string
  market_analysis: any
}

interface ShopifyCollection {
  id: string
  title: string
  handle: string
}

interface ExistingCoin {
  id: number
  title: string
  category: string
  quantity: number
}

interface UploadNewItemModalProps {
  onClose: () => void
  onSuccess: () => void
}

export default function UploadNewItemModal({ onClose, onSuccess }: UploadNewItemModalProps) {
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isEvaluating, setIsEvaluating] = useState(false)
  const [images, setImages] = useState<File[]>([])
  const [uploadedImages, setUploadedImages] = useState<Array<{file: File, url: string, fileKey: string}>>([])
  const [uploadProgress, setUploadProgress] = useState<{[key: number]: number}>({})
  const [isUploading, setIsUploading] = useState(false)
  const [aiEvaluation, setAiEvaluation] = useState<AIEvaluation | null>(null)
  const [showAiResults, setShowAiResults] = useState(false)
  const [shopifyCollections, setShopifyCollections] = useState<ShopifyCollection[]>([])
  const [existingCoins, setExistingCoins] = useState<ExistingCoin[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [showExistingCoins, setShowExistingCoins] = useState(false)
  const [selectedIndex, setSelectedIndex] = useState(-1)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
    setValue,
    getValues
  } = useForm<CoinFormData>({
    resolver: zodResolver(coinSchema),
    defaultValues: {
      is_silver: false,
      price_strategy: 'paid_price_multiplier',
      price_multiplier: 1.5,
      base_from_entry: true,
      override_price: false,
      quantity: 1,
      status: 'active',
      add_to_existing: false,
      shopify_collection_ids: [],
    }
  })

  const isSilver = watch('is_silver')
  const overridePrice = watch('override_price')
  const addToExisting = watch('add_to_existing')

  const handleImageUpload = (files: FileList) => {
    const newImages = Array.from(files).filter(file => 
      file.type.startsWith('image/') && images.length + Array.from(files).length <= 10
    )
    
    if (newImages.length !== Array.from(files).length) {
      toast.error('Only image files are allowed (max 10 images)')
    }
    
    setImages(prev => [...prev, ...newImages])
  }

  const removeImage = (index: number) => {
    setImages(prev => prev.filter((_, i) => i !== index))
    setUploadedImages(prev => prev.filter((_, i) => i !== index))
    setUploadProgress(prev => {
      const newProgress = { ...prev }
      delete newProgress[index]
      return newProgress
    })
  }

  const uploadImageToFileServer = async (file: File, collection: string, sku?: string): Promise<{url: string, fileKey: string} | null> => {
    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('collection', collection)
      if (sku) formData.append('sku', sku)

      const response = await api.post('/files/upload/image', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          const progress = Math.round((progressEvent.loaded * 100) / (progressEvent.total || 1))
          setUploadProgress(prev => ({ ...prev, [images.indexOf(file)]: progress }))
        }
      })

      if (response.data.success) {
        return {
          url: response.data.data.public_url,
          fileKey: response.data.data.file_key
        }
      }
      return null
    } catch (error) {
      console.error('Error uploading image:', error)
      toast.error(`Failed to upload ${file.name}`)
      return null
    }
  }

  const uploadAllImages = async (collection: string, sku?: string): Promise<Array<{file: File, url: string, fileKey: string}>> => {
    setIsUploading(true)
    const uploadedFiles: Array<{file: File, url: string, fileKey: string}> = []

    for (let i = 0; i < images.length; i++) {
      const file = images[i]
      const result = await uploadImageToFileServer(file, collection, sku)
      
      if (result) {
        uploadedFiles.push({
          file,
          url: result.url,
          fileKey: result.fileKey
        })
        toast.success(`Uploaded ${file.name}`)
      }
    }

    setIsUploading(false)
    return uploadedFiles
  }

  // Fetch Shopify collections
  useEffect(() => {
    const fetchCollections = async () => {
      try {
        const response = await api.get('/shopify/collections')
        setShopifyCollections(response.data)
      } catch (error) {
        console.error('Error fetching Shopify collections:', error)
        // Mock data for now
        setShopifyCollections([
          { id: '1', title: 'Morgan Silver Dollars', handle: 'morgan-silver-dollars' },
          { id: '2', title: 'Kennedy Half Dollars', handle: 'kennedy-half-dollars' },
          { id: '3', title: 'Mercury Dimes', handle: 'mercury-dimes' },
          { id: '4', title: 'Silver Eagles', handle: 'silver-eagles' },
          { id: '5', title: 'General Silver', handle: 'general-silver' },
        ])
      }
    }
    fetchCollections()
  }, [])

  // Search existing coins
  const searchExistingCoins = async (query: string) => {
    if (query.length < 1) {
      setExistingCoins([])
      setShowExistingCoins(false)
      setSelectedIndex(-1)
      return
    }
    
    try {
      const response = await api.get(`/coins/search?q=${encodeURIComponent(query)}&limit=10`)
      setExistingCoins(response.data)
      setShowExistingCoins(true)
      setSelectedIndex(-1)
    } catch (error) {
      console.error('Error searching coins:', error)
      // Mock data for testing
      const mockResults = [
        { id: 1, title: 'Mercury Dimes General', category: 'Mercury Dimes', quantity: 50 },
        { id: 2, title: 'Morgan Silver Dollars', category: 'Morgan Dollars', quantity: 25 },
        { id: 3, title: 'Kennedy Half Dollars', category: 'Kennedy Halves', quantity: 100 },
      ].filter(coin => 
        coin.title.toLowerCase().includes(query.toLowerCase()) ||
        coin.category.toLowerCase().includes(query.toLowerCase())
      )
      setExistingCoins(mockResults)
      setShowExistingCoins(mockResults.length > 0)
      setSelectedIndex(-1)
    }
  }

  const selectExistingCoin = (existingCoin: ExistingCoin) => {
    setValue('existing_coin_id', existingCoin.id)
    setValue('title', existingCoin.title)
    setValue('category', existingCoin.category)
    setSearchQuery(existingCoin.title)
    setShowExistingCoins(false)
    setSelectedIndex(-1)
    
    // Auto-fill metadata fields based on category
    if (existingCoin.category.toLowerCase().includes('mercury')) {
      setValue('denomination', '10 Cents')
      setValue('year', 1943) // Common year for Mercury dimes
      setValue('is_silver', true)
      setValue('silver_percent', 90.0)
      setValue('silver_content_oz', 0.0723)
      // Auto-select relevant collections
      const mercuryCollections = shopifyCollections.filter(c => 
        c.title.toLowerCase().includes('mercury') || 
        c.title.toLowerCase().includes('dime')
      )
      setValue('shopify_collection_ids', mercuryCollections.map(c => c.id))
    } else if (existingCoin.category.toLowerCase().includes('morgan')) {
      setValue('denomination', '$1')
      setValue('year', 1921) // Common year for Morgan dollars
      setValue('is_silver', true)
      setValue('silver_percent', 90.0)
      setValue('silver_content_oz', 0.7734)
      // Auto-select relevant collections
      const morganCollections = shopifyCollections.filter(c => 
        c.title.toLowerCase().includes('morgan') || 
        c.title.toLowerCase().includes('dollar')
      )
      setValue('shopify_collection_ids', morganCollections.map(c => c.id))
    } else if (existingCoin.category.toLowerCase().includes('kennedy')) {
      setValue('denomination', '50 Cents')
      setValue('year', 1964) // Common year for Kennedy halves
      setValue('is_silver', true)
      setValue('silver_percent', 90.0)
      setValue('silver_content_oz', 0.3617)
      // Auto-select relevant collections
      const kennedyCollections = shopifyCollections.filter(c => 
        c.title.toLowerCase().includes('kennedy') || 
        c.title.toLowerCase().includes('half')
      )
      setValue('shopify_collection_ids', kennedyCollections.map(c => c.id))
    }
  }

  const handleCollectionToggle = (collectionId: string) => {
    const currentCollections = watch('shopify_collection_ids') || []
    const newCollections = currentCollections.includes(collectionId)
      ? currentCollections.filter(id => id !== collectionId)
      : [...currentCollections, collectionId]
    setValue('shopify_collection_ids', newCollections)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!showExistingCoins || existingCoins.length === 0) return

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        setSelectedIndex(prev => 
          prev < existingCoins.length - 1 ? prev + 1 : 0
        )
        break
      case 'ArrowUp':
        e.preventDefault()
        setSelectedIndex(prev => 
          prev > 0 ? prev - 1 : existingCoins.length - 1
        )
        break
      case 'Enter':
        e.preventDefault()
        if (selectedIndex >= 0 && selectedIndex < existingCoins.length) {
          selectExistingCoin(existingCoins[selectedIndex])
        }
        break
      case 'Escape':
        setShowExistingCoins(false)
        setSelectedIndex(-1)
        break
    }
  }

  const evaluateWithAI = async () => {
    setIsEvaluating(true)
    try {
      const formData = getValues()
      
      // Create FormData for file upload
      const uploadData = new FormData()
      images.forEach((image, index) => {
        uploadData.append('images', image)
      })
      
      // Add coin data as JSON
      uploadData.append('coin_data', JSON.stringify(formData))
      
      const response = await api.post('/ai/evaluate-with-images', uploadData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      
      setAiEvaluation(response.data)
      setShowAiResults(true)
      toast.success('AI evaluation completed!')
      
    } catch (error) {
      toast.error('AI evaluation failed')
      console.error('Error evaluating with AI:', error)
    } finally {
      setIsEvaluating(false)
    }
  }

  const applyAiSuggestion = () => {
    if (aiEvaluation) {
      setValue('override_price', true)
      setValue('override_value', aiEvaluation.suggested_price)
      setShowAiResults(false)
      toast.success('AI suggestion applied to form!')
    }
  }

  const onSubmit = async (data: CoinFormData) => {
    setIsSubmitting(true)
    try {
      if (data.add_to_existing && data.existing_coin_id) {
        // Add to existing coin inventory
        await api.post(`/coins/${data.existing_coin_id}/add-inventory`, {
          quantity: data.quantity,
          paid_price: data.paid_price,
          condition_notes: data.condition_notes
        })
        toast.success(`Added ${data.quantity} coins to existing inventory!`)
      } else {
        // Upload images first if any
        let uploadedImageData: Array<{file: File, url: string, fileKey: string}> = []
        
        if (images.length > 0) {
          // Determine collection name from category or use default
          const collection = data.category || 'general'
          uploadedImageData = await uploadAllImages(collection, data.sku)
          
          if (uploadedImageData.length === 0) {
            toast.error('Failed to upload images. Please try again.')
            return
          }
        }
        
        // Create new coin with image data
        const coinData = {
          ...data,
          images: uploadedImageData.map(img => ({
            url: img.url,
            file_key: img.fileKey,
            filename: img.file.name,
            mime_type: img.file.type,
            size: img.file.size
          }))
        }
        
        const coinResponse = await api.post('/coins', coinData)
        toast.success('Coin created successfully!')
      }
      
      onSuccess()
    } catch (error) {
      toast.error('Failed to save coin')
      console.error('Error saving coin:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  const getConfidenceColor = (score: number) => {
    if (score >= 0.8) return 'text-green-400'
    if (score >= 0.6) return 'text-yellow-400'
    return 'text-red-400'
  }

  const getConfidenceIcon = (score: number) => {
    if (score >= 0.8) return <CheckCircleIcon className="h-5 w-5 text-green-400" />
    if (score >= 0.6) return <ExclamationTriangleIcon className="h-5 w-5 text-yellow-400" />
    return <InformationCircleIcon className="h-5 w-5 text-red-400" />
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 rounded-lg w-full max-w-6xl max-h-[95vh] overflow-y-auto">
        <div className="sticky top-0 bg-gray-900 border-b border-gray-700 px-6 py-4">
          <div className="flex justify-between items-center">
            <h2 className="text-2xl font-bold text-yellow-500 flex items-center">
              <SparklesIcon className="h-6 w-6 mr-2" />
              Upload New Coin
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-white transition-colors"
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>
        </div>

        <div className="p-6">
          {!showAiResults ? (
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-8">
              {/* Add to Existing vs New Coin */}
              <div className="bg-gray-800 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-yellow-500 mb-4">Add Method</h3>
                
                <div className="flex items-center space-x-6 mb-4">
                  <label className="flex items-center">
                    <input
                      type="radio"
                      {...register('add_to_existing')}
                      value="false"
                      className="mr-2"
                    />
                    <span className="text-gray-300">Create New Coin</span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="radio"
                      {...register('add_to_existing')}
                      value="true"
                      className="mr-2"
                    />
                    <span className="text-gray-300">Add to Existing Inventory</span>
                  </label>
                </div>

                {addToExisting && (
                  <div className="mt-4">
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Search Existing Coins
                    </label>
                    <div className="relative">
                      <input
                        type="text"
                        value={searchQuery}
                        onChange={(e) => {
                          setSearchQuery(e.target.value)
                          searchExistingCoins(e.target.value)
                        }}
                        onKeyDown={handleKeyDown}
                        className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
                        placeholder="Search for existing coins..."
                      />
                      <MagnifyingGlassIcon className="h-5 w-5 text-gray-400 absolute right-3 top-2.5" />
                      
                      {showExistingCoins && existingCoins.length > 0 && (
                        <div className="absolute z-10 w-full bg-gray-800 border border-gray-600 rounded-lg mt-1 max-h-60 overflow-y-auto">
                          {existingCoins.map((existingCoin, index) => (
                            <div
                              key={existingCoin.id}
                              onClick={() => selectExistingCoin(existingCoin)}
                              className={`p-3 cursor-pointer border-b border-gray-700 last:border-b-0 transition-colors ${
                                index === selectedIndex 
                                  ? 'bg-yellow-500 bg-opacity-20 border-yellow-500' 
                                  : 'hover:bg-gray-700'
                              }`}
                            >
                              <div className="font-medium text-white">{existingCoin.title}</div>
                              <div className="text-sm text-gray-400">
                                {existingCoin.category} • Qty: {existingCoin.quantity}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* Basic Information */}
              <div className="bg-gray-800 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-yellow-500 mb-4">Basic Information</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Title *
                    </label>
                    <input
                      {...register('title')}
                      className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
                      placeholder="e.g., 1921 Morgan Silver Dollar"
                      disabled={addToExisting}
                    />
                    {errors.title && (
                      <p className="text-red-400 text-sm mt-1">{errors.title.message}</p>
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      SKU
                    </label>
                    <input
                      {...register('sku')}
                      className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
                      placeholder="e.g., MORGAN-1921-MS65"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Year
                    </label>
                    <input
                      type="number"
                      {...register('year', { valueAsNumber: true })}
                      className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
                      placeholder="1921"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Denomination
                    </label>
                    <input
                      {...register('denomination')}
                      className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
                      placeholder="e.g., $1"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Mint Mark
                    </label>
                    <input
                      {...register('mint_mark')}
                      className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
                      placeholder="e.g., S, D, CC"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Grade
                    </label>
                    <input
                      {...register('grade')}
                      className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
                      placeholder="e.g., MS65, AU58"
                    />
                  </div>
                </div>
              </div>

              {/* Shopify Collection */}
              <div className="bg-gray-800 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-yellow-500 mb-4">Shopify Collections</h3>
                
                <div className="space-y-3">
                  <p className="text-sm text-gray-400 mb-4">Select one or more collections for this coin:</p>
                  {shopifyCollections.map((collection) => (
                    <label key={collection.id} className="flex items-center space-x-3 cursor-pointer hover:bg-gray-700 p-2 rounded-lg transition-colors">
                      <input
                        type="checkbox"
                        checked={(watch('shopify_collection_ids') || []).includes(collection.id)}
                        onChange={() => handleCollectionToggle(collection.id)}
                        className="w-4 h-4 text-yellow-500 bg-gray-700 border-gray-600 rounded focus:ring-yellow-500 focus:ring-2"
                      />
                      <span className="text-gray-300 font-medium">{collection.title}</span>
                      <span className="text-xs text-gray-500">({collection.handle})</span>
                    </label>
                  ))}
                  
                  {shopifyCollections.length === 0 && (
                    <p className="text-gray-500 text-sm italic">No collections available. Check your Shopify connection.</p>
                  )}
                </div>
              </div>

              {/* Silver Information */}
              <div className="bg-gray-800 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-yellow-500 mb-4">Silver Information</h3>
                
                <div className="flex items-center mb-4">
                  <input
                    type="checkbox"
                    {...register('is_silver')}
                    className="mr-2 w-4 h-4 text-yellow-500 bg-gray-700 border-gray-600 rounded focus:ring-yellow-500"
                  />
                  <label className="text-gray-300">This is a silver coin</label>
                </div>

                {isSilver && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        Silver Percentage
                      </label>
                      <input
                        type="number"
                        step="0.0001"
                        {...register('silver_percent', { valueAsNumber: true })}
                        className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
                        placeholder="0.900"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        Silver Content (oz)
                      </label>
                      <input
                        type="number"
                        step="0.0001"
                        {...register('silver_content_oz', { valueAsNumber: true })}
                        className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
                        placeholder="0.7734"
                      />
                    </div>
                  </div>
                )}
              </div>

              {/* Pricing */}
              <div className="bg-gray-800 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-yellow-500 mb-4">Pricing</h3>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Paid Price
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      {...register('paid_price', { valueAsNumber: true })}
                      className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
                      placeholder="45.00"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Price Multiplier
                    </label>
                    <input
                      type="number"
                      step="0.001"
                      {...register('price_multiplier', { valueAsNumber: true })}
                      className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
                      placeholder="1.300"
                    />
                  </div>
                </div>
              </div>

              {/* Images */}
              <div className="bg-gray-800 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-yellow-500 mb-4">Images</h3>
                
                <div className="border-2 border-dashed border-gray-600 rounded-lg p-8 text-center">
                  <PhotoIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-400 mb-4">Upload coin images (will be auto-formatted)</p>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    multiple
                    onChange={(e) => e.target.files && handleImageUpload(e.target.files)}
                    className="hidden"
                  />
                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    className="bg-yellow-500 hover:bg-yellow-600 text-black px-6 py-2 rounded-lg transition-colors"
                  >
                    Choose Images
                  </button>
                  <p className="text-sm text-gray-500 mt-2">Max 10 images</p>
                </div>

                {images.length > 0 && (
                  <div className="mt-6">
                    <h4 className="text-sm font-medium text-gray-300 mb-3">Selected Images ({images.length})</h4>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      {images.map((image, index) => (
                        <div key={index} className="relative group">
                          <img
                            src={URL.createObjectURL(image)}
                            alt={`Preview ${index + 1}`}
                            className="w-full h-24 object-cover rounded-lg"
                          />
                          <button
                            type="button"
                            onClick={() => removeImage(index)}
                            className="absolute top-1 right-1 bg-red-500 text-white rounded-full p-1 opacity-0 group-hover:opacity-100 transition-opacity"
                          >
                            <XMarkIcon className="h-3 w-3" />
                          </button>
                          
                          {/* Upload Progress */}
                          {uploadProgress[index] !== undefined && (
                            <div className="absolute bottom-0 left-0 right-0 bg-black bg-opacity-50 rounded-b-lg">
                              <div className="h-1 bg-gray-600 rounded-full">
                                <div 
                                  className="h-1 bg-yellow-500 rounded-full transition-all duration-300"
                                  style={{ width: `${uploadProgress[index]}%` }}
                                ></div>
                              </div>
                              <p className="text-xs text-white text-center py-1">
                                {uploadProgress[index]}%
                              </p>
                            </div>
                          )}
                          
                          {/* Upload Status */}
                          {uploadedImages[index] && (
                            <div className="absolute top-1 left-1 bg-green-500 text-white rounded-full p-1">
                              <CheckCircleIcon className="h-3 w-3" />
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                    
                    {/* Upload Status */}
                    {isUploading && (
                      <div className="mt-4 p-3 bg-blue-900 bg-opacity-50 rounded-lg">
                        <div className="flex items-center space-x-2">
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-400"></div>
                          <span className="text-blue-400 text-sm">Uploading images to file server...</span>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* AI Evaluation */}
              <div className="bg-gradient-to-r from-purple-900 to-blue-900 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-yellow-500 mb-4 flex items-center">
                  <SparklesIcon className="h-5 w-5 mr-2" />
                  AI-Powered Evaluation
                </h3>
                <p className="text-gray-300 mb-4">
                  Get AI suggestions for pricing and selling strategy based on coin analysis.
                </p>
                
                <button
                  type="button"
                  onClick={evaluateWithAI}
                  disabled={isEvaluating || !getValues('title')}
                  className="bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600 text-white px-6 py-3 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
                >
                  {isEvaluating ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      <span>Evaluating...</span>
                    </>
                  ) : (
                    <>
                      <SparklesIcon className="h-4 w-4" />
                      <span>Evaluate with AI</span>
                    </>
                  )}
                </button>
              </div>

              {/* Form Actions */}
              <div className="flex justify-end space-x-4 pt-6 border-t border-gray-700">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-6 py-2 border border-gray-600 text-gray-300 rounded-lg hover:bg-gray-800 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-6 py-2 bg-yellow-500 hover:bg-yellow-600 text-black rounded-lg transition-colors disabled:opacity-50 flex items-center space-x-2"
                >
                  {isSubmitting ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-black"></div>
                      <span>Saving...</span>
                    </>
                  ) : (
                    <span>
                      {addToExisting ? 'Add to Inventory' : 'Create Coin'}
                    </span>
                  )}
                </button>
              </div>
            </form>
          ) : (
            /* AI Results */
            <div className="space-y-6">
              <div className="bg-gradient-to-r from-green-900 to-blue-900 rounded-lg p-6">
                <h3 className="text-xl font-bold text-yellow-500 mb-4 flex items-center">
                  <SparklesIcon className="h-6 w-6 mr-2" />
                  AI Evaluation Results
                </h3>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="bg-gray-800 rounded-lg p-4">
                    <h4 className="text-lg font-semibold text-green-400 mb-2">Suggested Price</h4>
                    <p className="text-3xl font-bold text-white">${aiEvaluation?.suggested_price?.toFixed(2) || '0.00'}</p>
                    <div className="flex items-center mt-2">
                      {getConfidenceIcon(aiEvaluation?.confidence_score || 0)}
                      <span className={`ml-2 text-sm ${getConfidenceColor(aiEvaluation?.confidence_score || 0)}`}>
                        {(aiEvaluation?.confidence_score || 0) * 100}% confidence
                      </span>
                    </div>
                  </div>
                  
                  <div className="bg-gray-800 rounded-lg p-4">
                    <h4 className="text-lg font-semibold text-blue-400 mb-2">Selling Recommendation</h4>
                    <p className="text-xl font-semibold text-white capitalize">
                      {aiEvaluation?.selling_recommendation}
                    </p>
                    <p className="text-sm text-gray-400 mt-1">
                      Based on market analysis
                    </p>
                  </div>
                </div>
                
                <div className="mt-6 bg-gray-800 rounded-lg p-4">
                  <h4 className="text-lg font-semibold text-yellow-400 mb-2">AI Reasoning</h4>
                  <p className="text-gray-300 leading-relaxed">
                    {aiEvaluation?.reasoning}
                  </p>
                </div>
              </div>
              
              <div className="flex justify-end space-x-4">
                <button
                  onClick={() => setShowAiResults(false)}
                  className="px-6 py-2 border border-gray-600 text-gray-300 rounded-lg hover:bg-gray-800 transition-colors"
                >
                  Back to Form
                </button>
                <button
                  onClick={applyAiSuggestion}
                  className="px-6 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg transition-colors"
                >
                  Apply Suggestion
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}


