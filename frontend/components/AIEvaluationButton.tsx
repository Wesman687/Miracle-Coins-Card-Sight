import { useState } from 'react'
import { SparklesIcon, CurrencyDollarIcon, TagIcon, DocumentTextIcon } from '@heroicons/react/24/outline'
import { api } from '../lib/api'
import toast from 'react-hot-toast'

interface AIEvaluationButtonProps {
  coinId: number
  coinData: {
    title: string
    year?: number
    denomination?: string
    grade?: string
    is_silver: boolean
    silver_content_oz?: number
  }
  onEvaluationComplete: (result: AIEvaluationResult) => void
}

interface AIEvaluationResult {
  suggested_price: number
  confidence_score: number
  category: 'premium' | 'standard' | 'bulk'
  ai_notes: string
  market_analysis: string
  melt_value: number
  retail_multiplier: number
}

export default function AIEvaluationButton({ coinId, coinData, onEvaluationComplete }: AIEvaluationButtonProps) {
  const [isEvaluating, setIsEvaluating] = useState(false)
  const [showResults, setShowResults] = useState(false)
  const [evaluationResult, setEvaluationResult] = useState<AIEvaluationResult | null>(null)

  const handleAIEvaluation = async () => {
    setIsEvaluating(true)
    try {
      const response = await api.post('/ai-evaluation/evaluate', {
        coin_id: coinId,
        coin_data: coinData
      })
      
      const result = response.data
      setEvaluationResult(result)
      setShowResults(true)
      onEvaluationComplete(result)
      
      toast.success('AI evaluation completed!')
    } catch (error) {
      console.error('AI evaluation error:', error)
      toast.error('Failed to evaluate coin with AI')
    } finally {
      setIsEvaluating(false)
    }
  }

  const handleApplySuggestion = async () => {
    if (!evaluationResult) return
    
    try {
      await api.put(`/coins/${coinId}`, {
        computed_price: evaluationResult.suggested_price,
        ai_notes: evaluationResult.ai_notes,
        category: evaluationResult.category,
        confidence_score: evaluationResult.confidence_score
      })
      
      toast.success('AI suggestion applied successfully!')
      setShowResults(false)
    } catch (error) {
      console.error('Error applying suggestion:', error)
      toast.error('Failed to apply AI suggestion')
    }
  }

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'premium':
        return 'bg-yellow-500 text-black'
      case 'standard':
        return 'bg-blue-500 text-white'
      case 'bulk':
        return 'bg-gray-500 text-white'
      default:
        return 'bg-gray-500 text-white'
    }
  }

  const getConfidenceColor = (score: number) => {
    if (score >= 0.8) return 'text-green-400'
    if (score >= 0.6) return 'text-yellow-400'
    return 'text-red-400'
  }

  return (
    <div className="relative">
      <button
        onClick={handleAIEvaluation}
        disabled={isEvaluating}
        className="bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600 text-white px-4 py-2 rounded-lg flex items-center space-x-2 transition-all shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <SparklesIcon className="h-5 w-5" />
        <span>{isEvaluating ? 'Evaluating...' : 'AI Evaluate'}</span>
      </button>

      {showResults && evaluationResult && (
        <div className="absolute top-full left-0 mt-2 w-96 bg-gray-800 border border-gray-700 rounded-lg shadow-xl z-50 p-4">
          <div className="space-y-4">
            {/* Header */}
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-yellow-500">AI Evaluation Results</h3>
              <button
                onClick={() => setShowResults(false)}
                className="text-gray-400 hover:text-white"
              >
                ×
              </button>
            </div>

            {/* Suggested Price */}
            <div className="bg-gray-700 rounded-lg p-3">
              <div className="flex items-center space-x-2 mb-2">
                <CurrencyDollarIcon className="h-5 w-5 text-yellow-400" />
                <span className="font-medium text-white">Suggested Price</span>
              </div>
              <div className="text-2xl font-bold text-yellow-400">
                ${evaluationResult.suggested_price?.toFixed(2) || '0.00'}
              </div>
              <div className="text-sm text-gray-400">
                Melt Value: ${evaluationResult.melt_value?.toFixed(2) || '0.00'} 
                (×{evaluationResult.retail_multiplier?.toFixed(1) || '0.0'})
              </div>
            </div>

            {/* Category */}
            <div className="bg-gray-700 rounded-lg p-3">
              <div className="flex items-center space-x-2 mb-2">
                <TagIcon className="h-5 w-5 text-blue-400" />
                <span className="font-medium text-white">Category</span>
              </div>
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${getCategoryColor(evaluationResult.category)}`}>
                {evaluationResult.category.charAt(0).toUpperCase() + evaluationResult.category.slice(1)}
              </span>
            </div>

            {/* Confidence Score */}
            <div className="bg-gray-700 rounded-lg p-3">
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium text-white">Confidence Score</span>
                <span className={`font-bold ${getConfidenceColor(evaluationResult.confidence_score)}`}>
                  {(evaluationResult.confidence_score * 100).toFixed(0)}%
                </span>
              </div>
              <div className="w-full bg-gray-600 rounded-full h-2">
                <div 
                  className={`h-2 rounded-full ${evaluationResult.confidence_score >= 0.8 ? 'bg-green-400' : evaluationResult.confidence_score >= 0.6 ? 'bg-yellow-400' : 'bg-red-400'}`}
                  style={{ width: `${evaluationResult.confidence_score * 100}%` }}
                ></div>
              </div>
            </div>

            {/* AI Notes */}
            <div className="bg-gray-700 rounded-lg p-3">
              <div className="flex items-center space-x-2 mb-2">
                <DocumentTextIcon className="h-5 w-5 text-green-400" />
                <span className="font-medium text-white">AI Notes</span>
              </div>
              <p className="text-sm text-gray-300">{evaluationResult.ai_notes}</p>
            </div>

            {/* Market Analysis */}
            <div className="bg-gray-700 rounded-lg p-3">
              <div className="font-medium text-white mb-2">Market Analysis</div>
              <p className="text-sm text-gray-300">{evaluationResult.market_analysis}</p>
            </div>

            {/* Actions */}
            <div className="flex space-x-2">
              <button
                onClick={handleApplySuggestion}
                className="flex-1 bg-yellow-500 hover:bg-yellow-600 text-black px-4 py-2 rounded-lg font-medium transition-colors"
              >
                Apply Suggestion
              </button>
              <button
                onClick={() => setShowResults(false)}
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


