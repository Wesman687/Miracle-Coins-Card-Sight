import { useState, useEffect, useRef } from 'react'
import { 
  XMarkIcon, 
  SparklesIcon, 
  ChatBubbleLeftRightIcon,
  ClockIcon,
  StarIcon,
  MagnifyingGlassIcon,
  BoltIcon,
  DocumentTextIcon,
  CalendarIcon,
  CurrencyDollarIcon,
  PhotoIcon,
  EyeIcon
} from '@heroicons/react/24/outline'
import { api } from '../lib/api'
import toast from 'react-hot-toast'
import SearchPresets from './SearchPresets'
import SearchHistory from './SearchHistory'
import ImageUpload from './ImageUpload'
import ImagePreview from './ImagePreview'

interface AIChatModalProps {
  isOpen: boolean
  onClose: () => void
  initialQuery?: string
  initialPreset?: string
}

interface ChatMessage {
  id: string
  type: 'user' | 'ai'
  content: string
  timestamp: Date
  preset?: string
  confidence?: number
  pricing?: {
    suggested_price: number
    melt_value: number
    confidence_score: number
    category: string
  }
  imageUrl?: string
  imageData?: {
    filename: string
    size: number
    type: string
  }
}

interface SearchPreset {
  id: string
  name: string
  description: string
  icon: React.ComponentType<any>
  color: string
  estimatedTime: string
}

const searchPresets: SearchPreset[] = [
  {
    id: 'quick_response',
    name: 'Quick Response',
    description: 'Fast pricing for auctions',
    icon: BoltIcon,
    color: 'bg-green-500',
    estimatedTime: '5-10 seconds'
  },
  {
    id: 'in_depth_analysis',
    name: 'In-Depth Analysis',
    description: 'Detailed analysis with scam detection',
    icon: MagnifyingGlassIcon,
    color: 'bg-blue-500',
    estimatedTime: '30-60 seconds'
  },
  {
    id: 'descriptions',
    name: 'Descriptions',
    description: 'Generate coin descriptions',
    icon: DocumentTextIcon,
    color: 'bg-purple-500',
    estimatedTime: '10-15 seconds'
  },
  {
    id: 'year_mintage',
    name: 'Year & Mintage',
    description: 'Historical data and rarity',
    icon: CalendarIcon,
    color: 'bg-orange-500',
    estimatedTime: '15-20 seconds'
  },
  {
    id: 'pricing_only',
    name: 'Pricing Only',
    description: 'Just the price, nothing else',
    icon: CurrencyDollarIcon,
    color: 'bg-yellow-500',
    estimatedTime: '3-5 seconds'
  },
  {
    id: 'visual_identification',
    name: 'Visual ID',
    description: 'Identify coin from image',
    icon: EyeIcon,
    color: 'bg-indigo-500',
    estimatedTime: '15-30 seconds'
  },
  {
    id: 'grade_assessment',
    name: 'Grade Assessment',
    description: 'Assess coin grade from image',
    icon: PhotoIcon,
    color: 'bg-teal-500',
    estimatedTime: '20-40 seconds'
  }
]

export default function AIChatModal({ isOpen, onClose, initialQuery = '', initialPreset = 'quick_response' }: AIChatModalProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputValue, setInputValue] = useState(initialQuery)
  const [selectedPreset, setSelectedPreset] = useState(initialPreset)
  const [isLoading, setIsLoading] = useState(false)
  const [showHistory, setShowHistory] = useState(false)
  const [uploadedImage, setUploadedImage] = useState<{url: string, data: any} | null>(null)
  const [showPresets, setShowPresets] = useState(false)
  const [showImageUpload, setShowImageUpload] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    if (isOpen && initialQuery) {
      handleSendMessage()
    }
  }, [isOpen])

  const handleSendMessage = async () => {
    if ((!inputValue.trim() && !uploadedImage) || isLoading) return

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: inputValue || (uploadedImage ? 'Analyze this coin image' : ''),
      timestamp: new Date(),
      preset: selectedPreset,
      imageUrl: uploadedImage?.url,
      imageData: uploadedImage?.data
    }

    setMessages(prev => [...prev, userMessage])
    setInputValue('')
    setIsLoading(true)

    try {
      const requestData: any = {
        query: inputValue || (uploadedImage ? 'Analyze this coin image' : ''),
        preset: selectedPreset,
        context: messages.slice(-5) // Send last 5 messages for context
      }

      // Add image data if present
      if (uploadedImage) {
        requestData.image_url = uploadedImage.url
        requestData.image_analysis = true
      }

      const response = await api.post('/ai-chat/search', requestData)

      const aiMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        content: response.data.response,
        timestamp: new Date(),
        preset: selectedPreset,
        confidence: response.data.confidence_score,
        pricing: response.data.pricing
      }

      setMessages(prev => [...prev, aiMessage])
      
      // Save to search history
      await api.post('/ai-chat/history', {
        query: inputValue || (uploadedImage ? 'Analyze this coin image' : ''),
        preset: selectedPreset,
        response: response.data.response,
        confidence: response.data.confidence_score,
        image_url: uploadedImage?.url
      })

    } catch (error) {
      console.error('AI chat error:', error)
      toast.error('Failed to get AI response')
      
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date(),
        preset: selectedPreset
      }
      
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const handlePresetSelect = (presetId: string) => {
    setSelectedPreset(presetId)
  }

  const handleQuickSearch = (query: string, preset: string) => {
    setInputValue(query)
    setSelectedPreset(preset)
    handleSendMessage()
  }

  const handleImageUploaded = (imageUrl: string, imageData: any) => {
    setUploadedImage({ url: imageUrl, data: imageData })
  }

  const handleImageRemoved = () => {
    setUploadedImage(null)
  }

  const formatMessage = (message: ChatMessage) => {
    if (message.type === 'user') {
      return (
        <div className="flex justify-end mb-4">
          <div className="bg-yellow-500 text-black rounded-lg p-3 max-w-xs lg:max-w-md">
            {message.imageUrl && (
              <div className="mb-2">
                <img
                  src={message.imageUrl}
                  alt="Uploaded coin"
                  className="w-full h-auto rounded border border-gray-600"
                />
              </div>
            )}
            <p className="text-sm">{message.content}</p>
            <div className="text-xs text-gray-600 mt-1">
              {message.timestamp.toLocaleTimeString()}
            </div>
          </div>
        </div>
      )
    }

    return (
      <div className="flex justify-start mb-4">
        <div className="bg-gray-700 rounded-lg p-4 max-w-xs lg:max-w-md">
          <div className="flex items-center space-x-2 mb-2">
            <SparklesIcon className="h-4 w-4 text-purple-400" />
            <span className="text-xs text-gray-400">
              {searchPresets.find(p => p.id === message.preset)?.name}
            </span>
            {message.confidence && (
              <span className="text-xs text-gray-400">
                ({Math.round(message.confidence * 100)}% confidence)
              </span>
            )}
          </div>
          
          <p className="text-sm text-white mb-3">{message.content}</p>
          
          {message.pricing && (
            <div className="bg-gray-600 rounded p-3 mb-3">
              <div className="text-xs text-gray-400 mb-2">Pricing Analysis:</div>
              <div className="space-y-1">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-300">Suggested Price:</span>
                  <span className="text-yellow-400 font-medium">
                    ${message.pricing.suggested_price?.toFixed(2)}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-300">Melt Value:</span>
                  <span className="text-blue-400">
                    ${message.pricing.melt_value?.toFixed(2)}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-300">Category:</span>
                  <span className="text-green-400 capitalize">
                    {message.pricing.category}
                  </span>
                </div>
              </div>
            </div>
          )}
          
          <div className="text-xs text-gray-500">
            {message.timestamp.toLocaleTimeString()}
          </div>
        </div>
      </div>
    )
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 rounded-xl shadow-2xl w-full max-w-4xl h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-700">
          <div className="flex items-center space-x-3">
            <div className="bg-gradient-to-r from-purple-500 to-blue-500 rounded-lg p-2">
              <ChatBubbleLeftRightIcon className="h-6 w-6 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-white">AI Coin Pricing Assistant</h2>
              <p className="text-sm text-gray-400">Get instant pricing and analysis</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setShowHistory(!showHistory)}
              className="bg-gray-700 hover:bg-gray-600 text-white px-3 py-2 rounded-lg flex items-center space-x-2 transition-colors"
            >
              <ClockIcon className="h-4 w-4" />
              <span className="text-sm">History</span>
            </button>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-white transition-colors"
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 flex overflow-hidden">
          {/* Main Chat Area */}
          <div className="flex-1 flex flex-col">
            {/* Presets - Collapsible */}
            <div className="border-b border-gray-700">
              <button
                onClick={() => setShowPresets(!showPresets)}
                className="w-full p-4 flex items-center justify-between hover:bg-gray-800 transition-colors"
              >
                <div className="flex items-center space-x-2">
                  <BoltIcon className="h-5 w-5 text-yellow-500" />
                  <span className="text-white font-medium">Search Presets</span>
                </div>
                <div className={`transform transition-transform ${showPresets ? 'rotate-180' : ''}`}>
                  <svg className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
              </button>
              {showPresets && (
                <div className="p-4 pt-0">
                  <SearchPresets
                    presets={searchPresets}
                    selectedPreset={selectedPreset}
                    onPresetSelect={handlePresetSelect}
                  />
                </div>
              )}
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4">
              {messages.length === 0 && (
                <div className="text-center py-8">
                  <SparklesIcon className="h-12 w-12 text-gray-500 mx-auto mb-3" />
                  <h3 className="text-lg font-medium text-white mb-2">Welcome to AI Pricing Assistant</h3>
                  <p className="text-gray-400 mb-4">Ask me about any coin for instant pricing and analysis</p>
                  <div className="space-y-2">
                    <p className="text-sm text-gray-500">Try asking:</p>
                    <div className="space-y-1">
                      <button
                        onClick={() => handleQuickSearch("1921 Morgan Silver Dollar MS65", "quick_response")}
                        className="text-yellow-400 hover:text-yellow-300 text-sm block"
                      >
                        "1921 Morgan Silver Dollar MS65"
                      </button>
                      <button
                        onClick={() => handleQuickSearch("What's a 1964 Kennedy Half Dollar worth?", "pricing_only")}
                        className="text-yellow-400 hover:text-yellow-300 text-sm block"
                      >
                        "What's a 1964 Kennedy Half Dollar worth?"
                      </button>
                    </div>
                  </div>
                </div>
              )}
              
              {messages.map(message => (
                <div key={message.id}>
                  {formatMessage(message)}
                </div>
              ))}
              
              {isLoading && (
                <div className="flex justify-start mb-4">
                  <div className="bg-gray-700 rounded-lg p-4">
                    <div className="flex items-center space-x-2">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-purple-400"></div>
                      <span className="text-sm text-gray-400">AI is thinking...</span>
                    </div>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="border-t border-gray-700">
              {/* Image Upload Section - Collapsible */}
              {!uploadedImage && (
                <div className="border-b border-gray-700">
                  <button
                    onClick={() => setShowImageUpload(!showImageUpload)}
                    className="w-full p-4 flex items-center justify-between hover:bg-gray-800 transition-colors"
                  >
                    <div className="flex items-center space-x-2">
                      <PhotoIcon className="h-5 w-5 text-blue-500" />
                      <span className="text-white font-medium">Upload Image</span>
                    </div>
                    <div className={`transform transition-transform ${showImageUpload ? 'rotate-180' : ''}`}>
                      <svg className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    </div>
                  </button>
                  {showImageUpload && (
                    <div className="p-4 pt-0">
                      <ImageUpload
                        onImageUploaded={handleImageUploaded}
                        onImageRemoved={handleImageRemoved}
                        maxFileSize={10}
                        acceptedFormats={['jpg', 'jpeg', 'png', 'webp']}
                      />
                    </div>
                  )}
                </div>
              )}

              {/* Image Preview */}
              {uploadedImage && (
                <div className="p-4 border-b border-gray-700">
                  <ImagePreview
                    imageUrl={uploadedImage.url}
                    filename={uploadedImage.data.filename}
                    size={uploadedImage.data.size}
                    type={uploadedImage.data.type}
                    onRemove={handleImageRemoved}
                    onReanalyze={() => handleSendMessage()}
                  />
                </div>
              )}

              {/* Text Input */}
              <div className="p-4">
                <div className="flex space-x-3">
                <div className="flex-1">
                  <textarea
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder={uploadedImage ? "Add additional details about the coin..." : "Describe the coin you want to price or upload an image..."}
                    className="w-full bg-gray-800 border border-gray-600 rounded-lg px-4 py-3 text-white placeholder-gray-400 focus:outline-none focus:border-yellow-500 resize-none"
                    rows={2}
                    disabled={isLoading}
                  />
                </div>
                <button
                  onClick={handleSendMessage}
                  disabled={(!inputValue.trim() && !uploadedImage) || isLoading}
                  className="bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600 text-white px-6 py-3 rounded-lg flex items-center space-x-2 transition-all shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <SparklesIcon className="h-5 w-5" />
                  <span>Send</span>
                </button>
                </div>
              </div>
            </div>
          </div>

          {/* History Sidebar */}
          {showHistory && (
            <div className="w-80 border-l border-gray-700">
              <SearchHistory onQuickSearch={handleQuickSearch} />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
