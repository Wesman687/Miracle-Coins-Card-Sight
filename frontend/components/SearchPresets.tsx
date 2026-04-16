import { StarIcon, EyeIcon, PhotoIcon } from '@heroicons/react/24/outline'

interface SearchPreset {
  id: string
  name: string
  description: string
  icon: React.ComponentType<any>
  color: string
  estimatedTime: string
}

interface SearchPresetsProps {
  presets: SearchPreset[]
  selectedPreset: string
  onPresetSelect: (presetId: string) => void
}

export default function SearchPresets({ presets, selectedPreset, onPresetSelect }: SearchPresetsProps) {
  return (
    <div className="space-y-3">
      <div className="flex items-center space-x-2">
        <StarIcon className="h-5 w-5 text-yellow-500" />
        <h3 className="text-sm font-medium text-white">Search Presets</h3>
      </div>
      
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        {presets.map((preset) => {
          const IconComponent = preset.icon
          const isSelected = selectedPreset === preset.id
          
          return (
            <button
              key={preset.id}
              onClick={() => onPresetSelect(preset.id)}
              className={`p-3 rounded-lg border-2 transition-all duration-200 ${
                isSelected
                  ? 'border-yellow-500 bg-yellow-500/10'
                  : 'border-gray-600 bg-gray-800 hover:border-gray-500 hover:bg-gray-700'
              }`}
            >
              <div className="flex flex-col items-center space-y-2">
                <div className={`p-2 rounded-lg ${preset.color}`}>
                  <IconComponent className="h-5 w-5 text-white" />
                </div>
                <div className="text-center">
                  <div className={`text-sm font-medium ${
                    isSelected ? 'text-yellow-400' : 'text-white'
                  }`}>
                    {preset.name}
                  </div>
                  <div className="text-xs text-gray-400 mt-1">
                    {preset.description}
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    ~{preset.estimatedTime}
                  </div>
                </div>
              </div>
            </button>
          )
        })}
      </div>
      
      <div className="text-xs text-gray-500 mt-2">
        💡 <strong>Quick Response:</strong> Fast pricing for auctions • 
        <strong> In-Depth:</strong> Detailed analysis with scam detection • 
        <strong> Descriptions:</strong> Generate coin descriptions • 
        <strong> Year & Mintage:</strong> Historical data and rarity • 
        <strong> Pricing Only:</strong> Just the price, nothing else
      </div>
    </div>
  )
}
