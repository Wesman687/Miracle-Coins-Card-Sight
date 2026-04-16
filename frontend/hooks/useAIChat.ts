import { useState, useCallback } from 'react'
import { api } from '../lib/api'
import toast from 'react-hot-toast'

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
}

interface AIChatResponse {
  response: string
  confidence_score: number
  pricing?: {
    suggested_price: number
    melt_value: number
    confidence_score: number
    category: string
  }
  cached: boolean
  search_time_ms: number
}

interface UseAIChatOptions {
  onError?: (error: Error) => void
  onSuccess?: (response: AIChatResponse) => void
}

export function useAIChat(options: UseAIChatOptions = {}) {
  const [isLoading, setIsLoading] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>([])

  const sendMessage = useCallback(async (
    query: string,
    preset: string = 'quick_response',
    context: ChatMessage[] = []
  ): Promise<AIChatResponse | null> => {
    setIsLoading(true)
    
    try {
      const response = await api.post('/ai-chat/search', {
        query,
        preset,
        context: context.slice(-5) // Send last 5 messages for context
      })

      const aiResponse: AIChatResponse = response.data
      
      // Add user message
      const userMessage: ChatMessage = {
        id: Date.now().toString(),
        type: 'user',
        content: query,
        timestamp: new Date(),
        preset
      }

      // Add AI response
      const aiMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        content: aiResponse.response,
        timestamp: new Date(),
        preset,
        confidence: aiResponse.confidence_score,
        pricing: aiResponse.pricing
      }

      setMessages(prev => [...prev, userMessage, aiMessage])

      // Save to search history
      try {
        await api.post('/ai-chat/history', {
          query,
          preset,
          response: aiResponse.response,
          confidence: aiResponse.confidence_score
        })
      } catch (historyError) {
        console.warn('Failed to save to history:', historyError)
        // Don't show error toast for history save failures
      }

      options.onSuccess?.(aiResponse)
      return aiResponse

    } catch (error) {
      console.error('AI chat error:', error)
      const errorMessage = error instanceof Error ? error.message : 'Failed to get AI response'
      
      // Add error message
      const errorChatMessage: ChatMessage = {
        id: Date.now().toString(),
        type: 'ai',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date(),
        preset
      }

      setMessages(prev => [...prev, errorChatMessage])
      
      options.onError?.(error instanceof Error ? error : new Error(errorMessage))
      toast.error(errorMessage)
      return null
    } finally {
      setIsLoading(false)
    }
  }, [options])

  const clearMessages = useCallback(() => {
    setMessages([])
  }, [])

  const getQuickPricing = useCallback(async (coinDescription: string): Promise<AIChatResponse | null> => {
    return sendMessage(coinDescription, 'quick_response')
  }, [sendMessage])

  const getDetailedAnalysis = useCallback(async (coinDescription: string): Promise<AIChatResponse | null> => {
    return sendMessage(coinDescription, 'in_depth_analysis')
  }, [sendMessage])

  const getPricingOnly = useCallback(async (coinDescription: string): Promise<AIChatResponse | null> => {
    return sendMessage(coinDescription, 'pricing_only')
  }, [sendMessage])

  const getCoinDescription = useCallback(async (coinDescription: string): Promise<AIChatResponse | null> => {
    return sendMessage(coinDescription, 'descriptions')
  }, [sendMessage])

  const getYearMintageInfo = useCallback(async (coinDescription: string): Promise<AIChatResponse | null> => {
    return sendMessage(coinDescription, 'year_mintage')
  }, [sendMessage])

  return {
    messages,
    isLoading,
    sendMessage,
    clearMessages,
    getQuickPricing,
    getDetailedAnalysis,
    getPricingOnly,
    getCoinDescription,
    getYearMintageInfo
  }
}

export default useAIChat

