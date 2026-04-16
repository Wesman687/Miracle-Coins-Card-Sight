import { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { XMarkIcon, MagnifyingGlassIcon } from '@heroicons/react/24/outline'
import { api } from '../lib/api'
import toast from 'react-hot-toast'
import CollectionSelector from './CollectionSelector'
import TagSelector from './TagSelector'
import ImageManager from './ImageManager'
import RichTextEditor from './RichTextEditor'

const coinSchema = z.object({
  sku: z.string().optional(),
  title: z.string().min(1, 'Title is required'),
  year: z.number().optional(),
  denomination: z.string().optional(),
  mint_mark: z.string().optional(),
  grade: z.string().optional(),
  category: z.string().optional(),
  shopify_collection_ids: z.array(z.string()).default([]),
  tags: z.array(z.string()).default([]),
  description: z.string().optional(),
  condition_notes: z.string().optional(),
  status: z.enum(['active', 'inactive']).default('active'),
  is_silver: z.boolean().default(false),
  silver_percent: z.number().optional(),
  silver_content_oz: z.number().optional(),
  paid_price: z.number().optional(),
  pricing_strategy: z.enum(['fixed_price', 'base_price_scaling']).default('fixed_price'),
  fixed_price: z.number().optional(),
  base_price: z.number().optional(),
  market_multiplier: z.number().default(1.3),
  quantity: z.number().default(1),
  additional_quantity: z.number().optional(),
  additional_cost_per_coin: z.number().optional(),
  images: z.array(z.string()).default([]),
  metadata: z.record(z.string()).optional(),
  shopify_metadata: z.record(z.any()).optional(),
  collection_ids: z.array(z.number()).default([]),
})

type CoinFormData = z.infer<typeof coinSchema> & {
  metafields?: {
    custom?: Record<string, any>
    shopify?: Record<string, any>
  }
}

interface AddCoinModalProps {
  coin?: any
  onClose: () => void
  onSuccess: () => void
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

export default function AddCoinModal({ coin, onClose, onSuccess }: AddCoinModalProps) {
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [shopifyCollections, setShopifyCollections] = useState<ShopifyCollection[]>([])
  const [existingCoins, setExistingCoins] = useState<ExistingCoin[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [showExistingCoins, setShowExistingCoins] = useState(false)
  const [selectedIndex, setSelectedIndex] = useState(-1)
  const [existingTags, setExistingTags] = useState<string[]>([])
  const [spotPrices, setSpotPrices] = useState<{silver: number, gold: number}>({silver: 25.0, gold: 2000.0})
  const [loadingSpotPrices, setLoadingSpotPrices] = useState(false)
  const [collections, setCollections] = useState<any[]>([])
  const [loadingCollections, setLoadingCollections] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
    setValue,
  } = useForm<CoinFormData>({
    resolver: zodResolver(coinSchema),
    defaultValues: coin || {
      is_silver: false,
      pricing_strategy: 'fixed_price',
      market_multiplier: 1.3,
      quantity: 1,
      shopify_collection_ids: [],
      tags: [],
      images: [],
    }
  })

  // Set fixed_price to computed_price when editing a coin
  useEffect(() => {
    if (coin && coin.computed_price) {
      setValue('fixed_price', coin.computed_price)
    }
  }, [coin, setValue])

  const isSilver = watch('is_silver')
  const pricingStrategy = watch('pricing_strategy') as 'fixed_price' | 'base_price_scaling'
  const silverPercent = watch('silver_percent')
  const silverContentOz = watch('silver_content_oz')
  const fixedPrice = watch('fixed_price')
  const basePrice = watch('base_price')
  const marketMultiplier = watch('market_multiplier')
  
  // Calculate melt value automatically
  const meltValue = isSilver && silverPercent && silverContentOz 
    ? (silverContentOz * (silverPercent / 100)) 
    : null

  // Calculate estimated list price
  const estimatedListPrice = pricingStrategy === 'fixed_price' && fixedPrice
    ? fixedPrice
    : pricingStrategy === 'base_price_scaling' && basePrice && marketMultiplier
    ? basePrice * (spotPrices.silver / 25) * marketMultiplier // Scale from $25 base spot
    : null

  // Fetch Shopify collections
  useEffect(() => {
    const fetchCollections = async () => {
      try {
        const response = await api.get('/shopify/collections')
        const collections = response.data?.collections || response.data || []
        setShopifyCollections(Array.isArray(collections) ? collections : [])
      } catch (error) {
        console.error('Error fetching Shopify collections:', error)
        // Mock data for testing
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

  // Fetch live spot prices
  useEffect(() => {
    const fetchSpotPrices = async () => {
      setLoadingSpotPrices(true)
      try {
        const response = await api.get('/pricing/dashboard-kpis')
        if (response.data && response.data.metals_prices) {
          setSpotPrices({
            silver: response.data.metals_prices.silver?.price || 25.0,
            gold: response.data.metals_prices.gold?.price || 2000.0
          })
        }
      } catch (error) {
        console.error('Error fetching spot prices:', error)
        // Keep default values
      } finally {
        setLoadingSpotPrices(false)
      }
    }
    fetchSpotPrices()
  }, [])

  // Fetch existing tags
  useEffect(() => {
    const fetchTags = async () => {
      try {
        // First try to get tags from existing coins
        const coinsResponse = await api.get('/coins?limit=1000')
        const coins = coinsResponse.data || []
        
        // Extract unique tags from existing coins
        const existingTags = new Set<string>()
        coins.forEach((coin: any) => {
          if (coin.tags && Array.isArray(coin.tags)) {
            coin.tags.forEach((tag: string) => existingTags.add(tag))
          }
        })
        
        // Add common coin tags
        const commonTags = [
          'rare', 'uncirculated', 'proof', 'graded', 'toned', 'key-date',
          'morgan', 'peace', 'kennedy', 'mercury', 'roosevelt', 'washington',
          'silver', 'gold', 'copper', 'nickel', 'bronze', 'platinum',
          'ms', 'au', 'xf', 'vf', 'f', 'vg', 'g', 'ag', 'fr', 'pr',
          'business-strike', 'proof-strike', 'special-strike'
        ]
        
        commonTags.forEach(tag => existingTags.add(tag))
        
        setExistingTags(Array.from(existingTags).sort())
      } catch (error) {
        console.error('Error fetching tags:', error)
        // Fallback to common tags
        setExistingTags([
          'rare', 'uncirculated', 'proof', 'graded', 'toned', 'key-date',
          'morgan', 'peace', 'kennedy', 'mercury', 'roosevelt', 'washington',
          'silver', 'gold', 'copper', 'nickel', 'bronze', 'platinum',
          'ms', 'au', 'xf', 'vf', 'f', 'vg', 'g', 'ag', 'fr', 'pr',
          'business-strike', 'proof-strike', 'special-strike'
        ])
      }
    }
    fetchTags()
  }, [])

  // Fetch collections
  useEffect(() => {
    const fetchCollections = async () => {
      setLoadingCollections(true)
      try {
        const response = await api.get('/collections')
        if (response.data && Array.isArray(response.data)) {
          setCollections(response.data)
        }
      } catch (error) {
        console.error('Error fetching collections:', error)
      } finally {
        setLoadingCollections(false)
      }
    }
    fetchCollections()
  }, [])

  const handleImageUpload = async (files: FileList): Promise<string[]> => {
    const uploadPromises = Array.from(files).map(async (file) => {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('collection', 'coin-images')
      formData.append('folder', 'coins/coin-images')
      
      try {
        const response = await api.post('/files/upload/image', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        })
        
        // The file upload service returns public_url directly
        return response.data?.public_url || response.data?.data?.public_url
      } catch (error) {
        console.error('Upload error:', error)
        // Fallback to placeholder for now
        return `https://via.placeholder.com/300x300/4a5568/ffffff?text=Upload+Failed`
      }
    })
    
    return Promise.all(uploadPromises)
  }

  const onSubmit = async (data: CoinFormData) => {
    setIsSubmitting(true)
    try {
      if (coin) {
        // Update existing coin
        let updateData = { ...data }
        
        // Handle quantity addition if specified
        if (data.additional_quantity && data.additional_quantity > 0 && data.additional_cost_per_coin) {
          const currentQuantity = coin.quantity
          const currentCost = coin.paid_price || 0
          const additionalQuantity = data.additional_quantity
          const additionalCost = data.additional_cost_per_coin
          
          // Calculate new total quantity
          const newQuantity = currentQuantity + additionalQuantity
          
          // Calculate new average cost
          const currentTotalCost = currentQuantity * currentCost
          const additionalTotalCost = additionalQuantity * additionalCost
          const newAverageCost = (currentTotalCost + additionalTotalCost) / newQuantity
          
          updateData.quantity = newQuantity
          updateData.paid_price = newAverageCost
          
          // Remove the additional fields from the update data
          delete updateData.additional_quantity
          delete updateData.additional_cost_per_coin
        }
        
        const response = await api.put(`/coins/${coin.id}`, updateData)
        toast.success('Coin updated successfully!')
      } else {
        // Create new coin
        const response = await api.post('/coins', data)
        toast.success('Coin added successfully!')
      }
      onSuccess()
      onClose()
    } catch (error) {
      console.error('Error saving coin:', error)
      toast.error(`Failed to ${coin ? 'update' : 'add'} coin`)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
      onClick={(e) => {
        if (e.target === e.currentTarget) {
          onClose()
        }
      }}
    >
      <div className="bg-gray-900 rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-y-auto scrollbar-hide">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-700">
          <h2 className="text-2xl font-bold text-yellow-400">
            {coin ? 'Edit Coin' : 'Add New Coin'}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-8">
          {/* Basic Information */}
          <div>
            <h3 className="text-lg font-semibold text-yellow-500 mb-4">Basic Information</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Title *
                </label>
                <input
                  {...register('title')}
                  className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
                  placeholder="e.g., 1921 Morgan Silver Dollar"
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
                  className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
                  placeholder="e.g., MOR-1921-P"
                />
              </div>
            </div>

            {/* Description Field */}
            <div className="mt-6">
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Description
              </label>
              <RichTextEditor
                value={watch('description') || ''}
                onChange={(value) => setValue('description', value)}
                placeholder="Enter coin description..."
              />
            </div>

            {/* Status Toggle */}
            <div className="mt-6">
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Status
              </label>
              <div className="flex items-center space-x-4">
                <label className="flex items-center">
                  <input
                    type="radio"
                    {...register('status')}
                    value="active"
                    defaultChecked={!coin || coin.status === 'active'}
                    className="mr-2 text-yellow-500 focus:ring-yellow-500"
                  />
                  <span className="text-white">Active (Visible on Shopify)</span>
                </label>
                <label className="flex items-center">
                  <input
                    type="radio"
                    {...register('status')}
                    value="inactive"
                    defaultChecked={coin && coin.status === 'inactive'}
                    className="mr-2 text-yellow-500 focus:ring-yellow-500"
                  />
                  <span className="text-white">Inactive (Hidden from Shopify)</span>
                </label>
              </div>
              <p className="text-xs text-gray-400 mt-1">
                Active coins will sync to Shopify when updated. Inactive coins remain local only.
              </p>
            </div>
          </div>

          {/* Silver Information */}
          <div className="border-t border-gray-700 pt-6">
            <h3 className="text-lg font-semibold text-yellow-500 mb-4">Silver Information</h3>
            
            <div className="flex items-center mb-4">
              <input
                type="checkbox"
                {...register('is_silver')}
                className="mr-2"
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
                    className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
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
                    className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
                    placeholder="0.7734"
                  />
                </div>
              </div>
            )}

            {/* Live Spot Prices Display */}
            <div className="mt-4 p-3 bg-blue-900/20 border border-blue-500/30 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-300">Live Spot Prices</span>
                {loadingSpotPrices && (
                  <span className="text-xs text-blue-400">Updating...</span>
                )}
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="text-center">
                  <div className="text-lg font-semibold text-blue-400">
                    ${spotPrices.silver.toFixed(2)}
                  </div>
                  <div className="text-xs text-gray-400">Silver (oz)</div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-semibold text-yellow-400">
                    ${spotPrices.gold.toFixed(2)}
                  </div>
                  <div className="text-xs text-gray-400">Gold (oz)</div>
                </div>
              </div>
            </div>
          </div>

          {/* Pricing */}
          <div className="border-t border-gray-700 pt-6">
            <h3 className="text-lg font-semibold text-yellow-500 mb-4">Pricing</h3>
            
            {/* Pricing Strategy Selection */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Pricing Strategy
              </label>
              <select
                {...register('pricing_strategy')}
                className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
              >
                <option value="fixed_price">Fixed Price</option>
                <option value="base_price_scaling">Base Price + Market Scaling</option>
              </select>
              <p className="text-xs text-gray-400 mt-1">
                {pricingStrategy === 'fixed_price' && 'Set a specific price that doesn\'t change'}
                {pricingStrategy === 'base_price_scaling' && 'Set a base price that scales with silver spot (e.g., $50 base scales up/down with spot)'}
              </p>
            </div>

            {/* Pricing Fields */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Paid Price - Always shown for inventory tracking */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Paid Price (Cost) *
                </label>
                <input
                  type="number"
                  step="0.01"
                  {...register('paid_price', { valueAsNumber: true })}
                  className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
                  placeholder="45.00"
                  required
                />
                <p className="text-xs text-gray-400 mt-1">
                  What you paid for this coin (for inventory tracking)
                </p>
              </div>

              {/* Fixed Price - shown only for fixed_price strategy */}
              {pricingStrategy === 'fixed_price' && (
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Fixed Price *
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    {...register('fixed_price', { valueAsNumber: true })}
                    className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
                    placeholder="75.00"
                    required
                  />
                  <p className="text-xs text-gray-400 mt-1">
                    This price will not change with market conditions
                  </p>
                </div>
              )}

              {/* Base Price - shown only for base_price_scaling strategy */}
              {pricingStrategy === 'base_price_scaling' && (
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Base Price *
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    {...register('base_price', { valueAsNumber: true })}
                    className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
                    placeholder="50.00"
                    required
                  />
                  <p className="text-xs text-gray-400 mt-1">
                    Base price that scales with silver spot (e.g., $50 at $25/oz spot)
                  </p>
                </div>
              )}

              {/* Market Multiplier - shown only for base_price_scaling strategy */}
              {pricingStrategy === 'base_price_scaling' && (
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Market Multiplier *
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    {...register('market_multiplier', { valueAsNumber: true })}
                    className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
                    placeholder="1.30"
                    required
                  />
                  <p className="text-xs text-gray-400 mt-1">
                    Multiplier for spot price scaling (e.g., 1.30 = 30% over spot)
                  </p>
                </div>
              )}
            </div>

            {/* Melt Value Display - Auto-calculated */}
            {isSilver && meltValue && (
              <div className="mt-4 p-3 bg-gray-700 rounded-lg">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-300">Melt Value:</span>
                  <span className="text-lg font-semibold text-yellow-400">
                    ${meltValue.toFixed(4)} oz
                  </span>
                </div>
                <p className="text-xs text-gray-400 mt-1">
                  Auto-calculated from silver content and percentage
                </p>
              </div>
            )}

            {/* Price Preview */}
            {estimatedListPrice && (
              <div className="mt-4 p-3 bg-green-900/20 border border-green-500/30 rounded-lg">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-300">Estimated List Price:</span>
                  <span className="text-lg font-semibold text-green-400">
                    ${estimatedListPrice.toFixed(2)}
                  </span>
                </div>
                <p className="text-xs text-gray-400 mt-1">
                  {pricingStrategy === 'base_price_scaling' && `Base price scales with silver spot ($${spotPrices.silver.toFixed(2)}/oz)`}
                  {pricingStrategy === 'fixed_price' && 'Fixed price - will not change'}
                </p>
              </div>
            )}
          </div>

          {/* Inventory */}
          <div className="border-t border-gray-700 pt-6">
            <h3 className="text-lg font-semibold text-yellow-500 mb-4">Inventory</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Quantity *
                </label>
                <input
                  type="number"
                  min="1"
                  {...register('quantity', { valueAsNumber: true })}
                  className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
                  placeholder="1"
                  required
                />
              </div>
            </div>

            {/* Quantity Addition Section - Only show when editing existing coin */}
            {coin && (
              <div className="mt-6 p-4 bg-gray-800 border border-gray-600 rounded-lg">
                <h4 className="text-md font-semibold text-yellow-400 mb-4">Add More Quantity</h4>
                <p className="text-sm text-gray-400 mb-4">
                  Add more coins of this type to your inventory. This will update the total quantity and average cost.
                </p>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Additional Quantity
                    </label>
                    <input
                      type="number"
                      min="1"
                      {...register('additional_quantity', { valueAsNumber: true })}
                      className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
                      placeholder="0"
                    />
                    <p className="text-xs text-gray-400 mt-1">Number of additional coins to add</p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Cost Per Additional Coin
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      {...register('additional_cost_per_coin', { valueAsNumber: true })}
                      className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
                      placeholder="0.00"
                    />
                    <p className="text-xs text-gray-400 mt-1">Cost per additional coin (for average calculation)</p>
                  </div>
                </div>

                <div className="mt-4 p-3 bg-gray-700 rounded-lg">
                  <p className="text-sm text-gray-300">
                    <strong>Current:</strong> {coin.quantity} coins at ${coin.paid_price?.toFixed(2) || '0.00'} each
                  </p>
                  <p className="text-sm text-gray-300 mt-1">
                    <strong>After Addition:</strong> Will calculate new average cost based on total investment
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Collections and Tags */}
          <div className="border-t border-gray-700 pt-6">
            <h3 className="text-lg font-semibold text-yellow-500 mb-4">Collections & Tags</h3>
            
            <div className="space-y-6">
              {/* Collections - Multi-select like tags */}
              <div>
                <p className="text-sm text-gray-400 mb-4">Select collections for this coin:</p>
                {loadingCollections ? (
                  <div className="bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-gray-400">
                    Loading collections...
                  </div>
                ) : (
                  <CollectionSelector
                    collections={collections}
                    selectedIds={watch('collection_ids') || []}
                    onSelectionChange={(selectedIds) => setValue('collection_ids', selectedIds)}
                    placeholder="Search collections..."
                  />
                )}
              </div>

              {/* Tags */}
              <div>
                <p className="text-sm text-gray-400 mb-4">Add tags for this coin:</p>
                <TagSelector
                  selectedTags={watch('tags') || []}
                  onTagsChange={(tags) => setValue('tags', tags)}
                  existingTags={existingTags}
                  placeholder="Add tags..."
                />
              </div>
            </div>
          </div>

          {/* Custom Metafields */}
          {coin && coin.shopify_metadata && (
            <div className="border-t border-gray-700 pt-6">
              <h3 className="text-lg font-semibold text-yellow-500 mb-4">Coin Details (Custom Metafields)</h3>
              
              <div className="space-y-6">

                {/* Custom Metafields Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Silver Content */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Silver Content
                    </label>
                    <input
                      type="number"
                      step="0.00001"
                      {...register('metafields.custom.silver_content', { valueAsNumber: true })}
                      defaultValue={coin.shopify_metadata?.product_metafields?.['custom.silver_content'] || ''}
                      className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
                      placeholder="0.7734"
                    />
                    <p className="text-xs text-gray-400 mt-1">Silver content in ounces</p>
                  </div>

                  {/* Year */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Year
                    </label>
                    <input
                      type="text"
                      {...register('metafields.custom.year')}
                      defaultValue={coin.shopify_metadata?.product_metafields?.['custom.year'] || ''}
                      className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
                      placeholder="1921"
                    />
                    <p className="text-xs text-gray-400 mt-1">Year or year range</p>
                  </div>

                  {/* Weight */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Weight
                    </label>
                    <input
                      type="text"
                      {...register('metafields.custom.weight')}
                      defaultValue={coin.shopify_metadata?.product_metafields?.['custom.weight'] || ''}
                      className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
                      placeholder="26.73 g"
                    />
                    <p className="text-xs text-gray-400 mt-1">Weight with unit</p>
                  </div>

                  {/* Diameter */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Diameter
                    </label>
                    <input
                      type="text"
                      {...register('metafields.custom.diameter')}
                      defaultValue={coin.shopify_metadata?.product_metafields?.['custom.diameter'] || ''}
                      className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
                      placeholder="38.1 mm"
                    />
                    <p className="text-xs text-gray-400 mt-1">Diameter with unit</p>
                  </div>

                  {/* Thickness */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Thickness
                    </label>
                    <input
                      type="text"
                      {...register('metafields.custom.thickness')}
                      defaultValue={coin.shopify_metadata?.product_metafields?.['custom.thickness'] || ''}
                      className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
                      placeholder="2.4 mm"
                    />
                    <p className="text-xs text-gray-400 mt-1">Thickness with unit</p>
                  </div>

                  {/* Composition */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Composition
                    </label>
                    <input
                      type="text"
                      {...register('metafields.custom.composition')}
                      defaultValue={coin.shopify_metadata?.product_metafields?.['custom.composition'] || ''}
                      className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
                      placeholder="90% Silver, 10% Copper"
                    />
                    <p className="text-xs text-gray-400 mt-1">Metal composition</p>
                  </div>

                  {/* Mintage */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Mintage
                    </label>
                    <input
                      type="text"
                      {...register('metafields.custom.mintage')}
                      defaultValue={coin.shopify_metadata?.product_metafields?.['custom.mintage'] || ''}
                      className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
                      placeholder="44,690,000"
                    />
                    <p className="text-xs text-gray-400 mt-1">Total mintage</p>
                  </div>

                  {/* Estimated Value */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Estimated Value
                    </label>
                    <input
                      type="text"
                      {...register('metafields.custom.estimated_value')}
                      defaultValue={coin.shopify_metadata?.product_metafields?.['custom.estimated_value'] || ''}
                      className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
                      placeholder="$55 – $90"
                    />
                    <p className="text-xs text-gray-400 mt-1">Estimated value range</p>
                  </div>

                  {/* Rarity */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Rarity
                    </label>
                    <select
                      {...register('metafields.custom.rarity')}
                      defaultValue={coin.shopify_metadata?.product_metafields?.['custom.rarity'] || ''}
                      className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
                    >
                      <option value="">Select rarity</option>
                      <option value="Common">Common</option>
                      <option value="Uncommon">Uncommon</option>
                      <option value="Rare">Rare</option>
                      <option value="Very Rare">Very Rare</option>
                      <option value="Key Date">Key Date</option>
                    </select>
                    <p className="text-xs text-gray-400 mt-1">Rarity level</p>
                  </div>

                  {/* Mint Mark */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Mint Mark
                    </label>
                    <input
                      type="text"
                      {...register('metafields.custom.mint_mark')}
                      defaultValue={coin.shopify_metadata?.product_metafields?.['custom.mint_mark'] || ''}
                      className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
                      placeholder="D, S, P, CC"
                    />
                    <p className="text-xs text-gray-400 mt-1">Mint marks (comma separated)</p>
                  </div>

                  {/* Grade */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Grade
                    </label>
                    <input
                      type="text"
                      {...register('metafields.custom.grade')}
                      defaultValue={coin.shopify_metadata?.product_metafields?.['custom.grade'] || ''}
                      className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
                      placeholder="MS-65, AU-50"
                    />
                    <p className="text-xs text-gray-400 mt-1">Grades (comma separated)</p>
                  </div>

                  {/* Condition Notes */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Condition Notes
                    </label>
                    <textarea
                      {...register('metafields.custom.condition_notes')}
                      defaultValue={coin.shopify_metadata?.product_metafields?.['custom.condition_notes'] || ''}
                      className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
                      rows={3}
                      placeholder="Circulated with minor wear"
                    />
                    <p className="text-xs text-gray-400 mt-1">Detailed condition description</p>
                  </div>

                  {/* Obverse Design */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Obverse Design
                    </label>
                    <textarea
                      {...register('metafields.custom.obverse_design')}
                      defaultValue={coin.shopify_metadata?.product_metafields?.['custom.obverse_design'] || ''}
                      className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
                      rows={2}
                      placeholder="Description of obverse design"
                    />
                    <p className="text-xs text-gray-400 mt-1">Obverse (heads) design description</p>
                  </div>

                  {/* Reverse Design */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Reverse Design
                    </label>
                    <textarea
                      {...register('metafields.custom.reverse_design')}
                      defaultValue={coin.shopify_metadata?.product_metafields?.['custom.reverse_design'] || ''}
                      className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
                      rows={2}
                      placeholder="Description of reverse design"
                    />
                    <p className="text-xs text-gray-400 mt-1">Reverse (tails) design description</p>
                  </div>

                  {/* Origin Country */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Origin Country
                    </label>
                    <input
                      type="text"
                      {...register('metafields.custom.origin_country')}
                      defaultValue={coin.shopify_metadata?.product_metafields?.['custom.origin_country'] || ''}
                      className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
                      placeholder="United States"
                    />
                    <p className="text-xs text-gray-400 mt-1">Country of origin</p>
                  </div>

                  {/* Variety */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Variety
                    </label>
                    <input
                      type="text"
                      {...register('metafields.custom.variety')}
                      defaultValue={coin.shopify_metadata?.product_metafields?.['custom.variety'] || ''}
                      className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
                      placeholder="Variety description"
                    />
                    <p className="text-xs text-gray-400 mt-1">Coin variety or type</p>
                  </div>

                  {/* Privy Mark */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Privy Mark
                    </label>
                    <input
                      type="text"
                      {...register('metafields.custom.privy_mark')}
                      defaultValue={coin.shopify_metadata?.product_metafields?.['custom.privy_mark'] || ''}
                      className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
                      placeholder="Privy mark description"
                    />
                    <p className="text-xs text-gray-400 mt-1">Special privy marks</p>
                  </div>
                </div>

                        {/* Shopify Standard Metafields */}
                        <div className="mt-6">
                          <h4 className="text-md font-semibold text-green-400 mb-4">Shopify Standard Metafields</h4>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {/* Condition */}
                            <div>
                              <label className="block text-sm font-medium text-gray-300 mb-2">
                                Condition
                              </label>
                              <select
                                {...register('metafields.shopify.condition')}
                                defaultValue={coin.shopify_metadata?.product_metafields?.['shopify.condition'] || ''}
                                className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
                              >
                                <option value="">Select condition</option>
                                <option value="Mint">Mint</option>
                                <option value="Uncirculated">Uncirculated</option>
                                <option value="Circulated">Circulated</option>
                                <option value="Proof">Proof</option>
                                <option value="Brilliant Uncirculated">Brilliant Uncirculated</option>
                              </select>
                              <p className="text-xs text-gray-400 mt-1">Coin condition</p>
                            </div>

                            {/* Country */}
                            <div>
                              <label className="block text-sm font-medium text-gray-300 mb-2">
                                Country
                              </label>
                              <input
                                type="text"
                                {...register('metafields.shopify.country')}
                                defaultValue={coin.shopify_metadata?.product_metafields?.['shopify.country'] || ''}
                                className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
                                placeholder="United States"
                              />
                              <p className="text-xs text-gray-400 mt-1">Country of origin</p>
                            </div>

                            {/* Coin Material */}
                            <div>
                              <label className="block text-sm font-medium text-gray-300 mb-2">
                                Coin Material
                              </label>
                              <select
                                {...register('metafields.shopify.coin-material')}
                                defaultValue={coin.shopify_metadata?.product_metafields?.['shopify.coin-material'] || ''}
                                className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
                              >
                                <option value="">Select material</option>
                                <option value="Silver">Silver</option>
                                <option value="Gold">Gold</option>
                                <option value="Bronze">Bronze</option>
                                <option value="Copper">Copper</option>
                                <option value="Nickel">Nickel</option>
                                <option value="Platinum">Platinum</option>
                                <option value="Palladium">Palladium</option>
                              </select>
                              <p className="text-xs text-gray-400 mt-1">Primary metal</p>
                            </div>

                            {/* Denomination */}
                            <div>
                              <label className="block text-sm font-medium text-gray-300 mb-2">
                                Denomination
                              </label>
                              <input
                                type="text"
                                {...register('metafields.shopify.denomination')}
                                defaultValue={coin.shopify_metadata?.product_metafields?.['shopify.denomination'] || ''}
                                className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
                                placeholder="$1, 50¢, 10¢"
                              />
                              <p className="text-xs text-gray-400 mt-1">Face value</p>
                            </div>

                            {/* Color Pattern */}
                            <div>
                              <label className="block text-sm font-medium text-gray-300 mb-2">
                                Color Pattern
                              </label>
                              <input
                                type="text"
                                {...register('metafields.shopify.color-pattern')}
                                defaultValue={coin.shopify_metadata?.product_metafields?.['shopify.color-pattern'] || ''}
                                className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
                                placeholder="Silver, Gold, Bronze"
                              />
                              <p className="text-xs text-gray-400 mt-1">Color or pattern</p>
                            </div>

                            {/* Bullion Form */}
                            <div>
                              <label className="block text-sm font-medium text-gray-300 mb-2">
                                Bullion Form
                              </label>
                              <select
                                {...register('metafields.shopify.bullion-form')}
                                defaultValue={coin.shopify_metadata?.product_metafields?.['shopify.bullion-form'] || ''}
                                className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
                              >
                                <option value="">Select form</option>
                                <option value="Rounds">Rounds</option>
                                <option value="Bars">Bars</option>
                                <option value="Coins">Coins</option>
                                <option value="Medallions">Medallions</option>
                              </select>
                              <p className="text-xs text-gray-400 mt-1">Bullion form type</p>
                            </div>

                            {/* Theme */}
                            <div>
                              <label className="block text-sm font-medium text-gray-300 mb-2">
                                Theme
                              </label>
                              <input
                                type="text"
                                {...register('metafields.shopify.theme')}
                                defaultValue={coin.shopify_metadata?.product_metafields?.['shopify.theme'] || ''}
                                className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
                                placeholder="Historical, Commemorative, Investment"
                              />
                              <p className="text-xs text-gray-400 mt-1">Coin theme</p>
                            </div>
                          </div>
                        </div>

                {/* Basic Shopify Info (collapsed by default) */}
                <details className="bg-gray-800 border border-gray-600 rounded-lg p-4">
                  <summary className="text-sm font-medium text-gray-300 cursor-pointer hover:text-white">
                    Basic Shopify Information
                  </summary>
                  <div className="mt-4 space-y-2 text-sm text-gray-400">
                    <div><strong>Shopify ID:</strong> {coin.shopify_metadata.shopify_id}</div>
                    <div><strong>Handle:</strong> {coin.shopify_metadata.handle}</div>
                    <div><strong>Vendor:</strong> {coin.shopify_metadata.vendor}</div>
                    <div><strong>Product Type:</strong> {coin.shopify_metadata.product_type}</div>
                    <div><strong>Status:</strong> {coin.shopify_metadata.status}</div>
                    <div><strong>Created:</strong> {coin.shopify_metadata.created_at}</div>
                    <div><strong>Updated:</strong> {coin.shopify_metadata.updated_at}</div>
                    {coin.shopify_metadata.published_at && (
                      <div><strong>Published:</strong> {coin.shopify_metadata.published_at}</div>
                    )}
                  </div>
                </details>
              </div>
            </div>
          )}

          {/* Images */}
          <div className="border-t border-gray-700 pt-6">
            <h3 className="text-lg font-semibold text-yellow-500 mb-4">Images</h3>
            <ImageManager
              images={watch('images') || []}
              onImagesChange={(images) => setValue('images', images)}
              onUpload={handleImageUpload}
            />
          </div>

          {/* Description */}
          <div className="border-t border-gray-700 pt-6">
            <RichTextEditor
              value={watch('description') || ''}
              onChange={(value) => setValue('description', value)}
              placeholder="Enter detailed description..."
            />
          </div>


          {/* Condition Notes */}
          <div className="border-t border-gray-700 pt-6">
            <h3 className="text-lg font-semibold text-yellow-500 mb-4">Condition & Notes</h3>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Condition Notes
              </label>
              <textarea
                {...register('condition_notes')}
                rows={3}
                className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
                placeholder="Any additional notes about the coin's condition..."
              />
            </div>
          </div>

          {/* Submit Buttons */}
          <div className="border-t border-gray-700 pt-6 flex justify-end space-x-4">
            <button
              type="button"
              onClick={onClose}
              className="px-6 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-6 py-2 bg-yellow-500 hover:bg-yellow-600 disabled:bg-gray-600 text-black font-medium rounded-lg transition-colors"
            >
              {isSubmitting ? (coin ? 'Saving...' : 'Adding...') : (coin ? 'Save Coin' : 'Add Coin')}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}