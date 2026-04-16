import { useState, useEffect } from 'react'
import { 
  ChartBarIcon, 
  DocumentTextIcon, 
  PhotoIcon, 
  CalendarIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  MinusIcon
} from '@heroicons/react/24/outline'
import { api } from '../lib/api'

interface CollectionAnalytics {
  collection_id: number
  collection_name: string
  created_at: string
  updated_at: string
  days_since_creation: number
  days_since_update: number
  metadata_fields_count: number
  metadata_completion_percentage: number
  field_types: Record<string, number>
  required_fields_completed: number
  total_required_fields: number
  required_fields_completion_percentage: number
  images_count: number
  has_featured_image: boolean
  total_image_size: number
  average_image_size: number
  image_size_formatted: string
  description_length: number
  description_html_length: number
  has_description: boolean
  has_rich_description: boolean
  has_shopify_integration: boolean
  views: number
  searches: number
  interactions: number
  engagement_score: number
}

interface Collection {
  id: number
  name: string
  description?: string
  description_html?: string
  color: string
  icon?: string
  sort_order?: number
  shopify_collection_id?: string
  default_markup?: number
  coin_count: number
  created_at: string
  updated_at: string
  metadata_fields?: any[]
  images?: any[]
  featured_image?: any
}

interface CollectionAnalyticsProps {
  collection: Collection
}

export default function CollectionAnalytics({ collection }: CollectionAnalyticsProps) {
  const [analytics, setAnalytics] = useState<CollectionAnalytics | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadAnalytics()
  }, [collection.id])

  const loadAnalytics = async () => {
    try {
      const response = await api.get(`/collections/${collection.id}/analytics`)
      setAnalytics(response.data)
    } catch (error) {
      console.error('Error loading analytics:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-yellow-500"></div>
      </div>
    )
  }

  if (!analytics) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-400">Analytics data not available</p>
      </div>
    )
  }

  const StatCard = ({ title, value, icon: Icon, trend, trendValue }: {
    title: string
    value: string | number
    icon: any
    trend?: 'up' | 'down' | 'neutral'
    trendValue?: string
  }) => {
    const getTrendIcon = () => {
      switch (trend) {
        case 'up':
          return <ArrowTrendingUpIcon className="h-4 w-4 text-green-400" />
        case 'down':
          return <ArrowTrendingDownIcon className="h-4 w-4 text-red-400" />
        default:
          return <MinusIcon className="h-4 w-4 text-gray-400" />
      }
    }

    return (
      <div className="bg-gray-700 rounded-lg p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-500 rounded-lg">
              <Icon className="h-5 w-5 text-white" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-300">{title}</p>
              <p className="text-2xl font-bold text-white">{value}</p>
            </div>
          </div>
          {trend && trendValue && (
            <div className="flex items-center space-x-1">
              {getTrendIcon()}
              <span className="text-sm text-gray-400">{trendValue}</span>
            </div>
          )}
        </div>
      </div>
    )
  }

  const ProgressBar = ({ label, value, max, color = 'blue' }: {
    label: string
    value: number
    max: number
    color?: 'blue' | 'green' | 'yellow' | 'red'
  }) => {
    const percentage = max > 0 ? (value / max) * 100 : 0
    const colorClasses = {
      blue: 'bg-blue-500',
      green: 'bg-green-500',
      yellow: 'bg-yellow-500',
      red: 'bg-red-500'
    }

    return (
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-gray-300">{label}</span>
          <span className="text-white">{value}/{max} ({percentage.toFixed(1)}%)</span>
        </div>
        <div className="w-full bg-gray-600 rounded-full h-2">
          <div
            className={`h-2 rounded-full ${colorClasses[color]}`}
            style={{ width: `${Math.min(percentage, 100)}%` }}
          ></div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Overview Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Metadata Fields"
          value={analytics.metadata_fields_count}
          icon={DocumentTextIcon}
        />
        <StatCard
          title="Images"
          value={analytics.images_count}
          icon={PhotoIcon}
        />
        <StatCard
          title="Days Active"
          value={analytics.days_since_creation}
          icon={CalendarIcon}
        />
        <StatCard
          title="Engagement Score"
          value={analytics.engagement_score}
          icon={ChartBarIcon}
        />
      </div>

      {/* Metadata Analytics */}
      <div className="bg-gray-700 rounded-lg p-6">
        <h4 className="text-lg font-semibold text-white mb-4">Metadata Analytics</h4>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-4">
            <ProgressBar
              label="Metadata Completion"
              value={analytics.metadata_completion_percentage}
              max={100}
              color="blue"
            />
            <ProgressBar
              label="Required Fields"
              value={analytics.required_fields_completed}
              max={analytics.total_required_fields}
              color="green"
            />
          </div>
          
          <div>
            <h5 className="text-sm font-medium text-gray-300 mb-3">Field Types</h5>
            <div className="space-y-2">
              {Object.entries(analytics.field_types).map(([type, count]) => (
                <div key={type} className="flex justify-between text-sm">
                  <span className="text-gray-300 capitalize">{type}</span>
                  <span className="text-white">{count}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Image Analytics */}
      <div className="bg-gray-700 rounded-lg p-6">
        <h4 className="text-lg font-semibold text-white mb-4">Image Analytics</h4>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-white">{analytics.images_count}</div>
            <div className="text-sm text-gray-400">Total Images</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-white">
              {analytics.has_featured_image ? 'Yes' : 'No'}
            </div>
            <div className="text-sm text-gray-400">Featured Image</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-white">{analytics.image_size_formatted}</div>
            <div className="text-sm text-gray-400">Total Size</div>
          </div>
        </div>
      </div>

      {/* Content Analytics */}
      <div className="bg-gray-700 rounded-lg p-6">
        <h4 className="text-lg font-semibold text-white mb-4">Content Analytics</h4>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-white">{analytics.description_length}</div>
            <div className="text-sm text-gray-400">Description Length</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-white">{analytics.description_html_length}</div>
            <div className="text-sm text-gray-400">Rich Text Length</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-white">
              {analytics.has_rich_description ? 'Yes' : 'No'}
            </div>
            <div className="text-sm text-gray-400">Rich Description</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-white">
              {analytics.has_shopify_integration ? 'Yes' : 'No'}
            </div>
            <div className="text-sm text-gray-400">Shopify Integration</div>
          </div>
        </div>
      </div>

      {/* Activity Timeline */}
      <div className="bg-gray-700 rounded-lg p-6">
        <h4 className="text-lg font-semibold text-white mb-4">Activity Timeline</h4>
        
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-green-500 rounded-lg">
                <CalendarIcon className="h-4 w-4 text-white" />
              </div>
              <div>
                <p className="text-sm font-medium text-gray-300">Created</p>
                <p className="text-white">
                  {new Date(analytics.created_at).toLocaleDateString()} 
                  ({analytics.days_since_creation} days ago)
                </p>
              </div>
            </div>
          </div>
          
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-blue-500 rounded-lg">
                <CalendarIcon className="h-4 w-4 text-white" />
              </div>
              <div>
                <p className="text-sm font-medium text-gray-300">Last Updated</p>
                <p className="text-white">
                  {new Date(analytics.updated_at).toLocaleDateString()} 
                  ({analytics.days_since_update} days ago)
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Engagement Metrics */}
      <div className="bg-gray-700 rounded-lg p-6">
        <h4 className="text-lg font-semibold text-white mb-4">Engagement Metrics</h4>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-white">{analytics.views}</div>
            <div className="text-sm text-gray-400">Views</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-white">{analytics.searches}</div>
            <div className="text-sm text-gray-400">Searches</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-white">{analytics.interactions}</div>
            <div className="text-sm text-gray-400">Interactions</div>
          </div>
        </div>
      </div>
    </div>
  )
}

