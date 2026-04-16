import { useState } from 'react'
import { UseFormRegister, UseFormSetValue, UseFormWatch, FieldErrors } from 'react-hook-form'
import { TrashIcon, Cog6ToothIcon, ChevronDownIcon, ChevronRightIcon } from '@heroicons/react/24/outline'

interface MetadataField {
  id?: number
  field_name: string
  field_type: 'text' | 'textarea' | 'number' | 'date' | 'boolean' | 'select'
  field_value?: string
  field_options?: string[]
  field_label?: string
  field_description?: string
  is_required: boolean
  is_searchable: boolean
  sort_order: number
}

interface MetadataFieldEditorProps {
  index: number
  field: MetadataField
  register: UseFormRegister<any>
  setValue: UseFormSetValue<any>
  watch: UseFormWatch<any>
  errors: FieldErrors<any>
  onRemove: () => void
}

const fieldTypeOptions = [
  { value: 'text', label: 'Text' },
  { value: 'textarea', label: 'Text Area' },
  { value: 'number', label: 'Number' },
  { value: 'date', label: 'Date' },
  { value: 'boolean', label: 'Boolean' },
  { value: 'select', label: 'Select' }
]

export default function MetadataFieldEditor({
  index,
  field,
  register,
  setValue,
  watch,
  errors,
  onRemove
}: MetadataFieldEditorProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [newOption, setNewOption] = useState('')
  
  const fieldType = watch(`metadata_fields.${index}.field_type`)
  const fieldOptions = watch(`metadata_fields.${index}.field_options`) || []

  const addOption = () => {
    if (newOption.trim()) {
      const currentOptions = fieldOptions || []
      setValue(`metadata_fields.${index}.field_options`, [...currentOptions, newOption.trim()])
      setNewOption('')
    }
  }

  const removeOption = (optionIndex: number) => {
    const currentOptions = fieldOptions || []
    setValue(`metadata_fields.${index}.field_options`, currentOptions.filter((_, i) => i !== optionIndex))
  }

  const renderFieldInput = () => {
    const fieldName = `metadata_fields.${index}.field_value`
    
    switch (fieldType) {
      case 'textarea':
        return (
          <textarea
            {...register(fieldName)}
            rows={3}
            className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
            placeholder="Enter field value..."
          />
        )
      
      case 'number':
        return (
          <input
            {...register(fieldName)}
            type="number"
            className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
            placeholder="Enter number..."
          />
        )
      
      case 'date':
        return (
          <input
            {...register(fieldName)}
            type="date"
            className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
          />
        )
      
      case 'boolean':
        return (
          <select
            {...register(fieldName)}
            className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
          >
            <option value="">Select...</option>
            <option value="true">True</option>
            <option value="false">False</option>
          </select>
        )
      
      case 'select':
        return (
          <select
            {...register(fieldName)}
            className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
          >
            <option value="">Select an option...</option>
            {fieldOptions.map((option: string, optionIndex: number) => (
              <option key={optionIndex} value={option}>
                {option}
              </option>
            ))}
          </select>
        )
      
      default:
        return (
          <input
            {...register(fieldName)}
            type="text"
            className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
            placeholder="Enter field value..."
          />
        )
    }
  }

  return (
    <div className="bg-gray-700 rounded-lg p-4 border border-gray-600">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <button
            type="button"
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-gray-400 hover:text-white transition-colors"
          >
            {isExpanded ? (
              <ChevronDownIcon className="h-5 w-5" />
            ) : (
              <ChevronRightIcon className="h-5 w-5" />
            )}
          </button>
          <div className="flex items-center space-x-2">
            <Cog6ToothIcon className="h-5 w-5 text-gray-400" />
            <span className="text-white font-medium">
              {watch(`metadata_fields.${index}.field_name`) || `Field ${index + 1}`}
            </span>
            <span className="text-xs bg-gray-600 text-gray-300 px-2 py-1 rounded">
              {fieldTypeOptions.find(opt => opt.value === fieldType)?.label || fieldType}
            </span>
          </div>
        </div>
        <button
          type="button"
          onClick={onRemove}
          className="text-red-400 hover:text-red-300 transition-colors"
        >
          <TrashIcon className="h-5 w-5" />
        </button>
      </div>

      {/* Basic Fields */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Field Name *
          </label>
          <input
            {...register(`metadata_fields.${index}.field_name`)}
            type="text"
            className="w-full bg-gray-600 border border-gray-500 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
            placeholder="e.g., year_range"
          />
          {errors.metadata_fields?.[index]?.field_name && (
            <p className="mt-1 text-sm text-red-400">
              {errors.metadata_fields[index]?.field_name?.message}
            </p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Field Type *
          </label>
          <select
            {...register(`metadata_fields.${index}.field_type`)}
            className="w-full bg-gray-600 border border-gray-500 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
          >
            {fieldTypeOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Expanded Fields */}
      {isExpanded && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Display Label
              </label>
              <input
                {...register(`metadata_fields.${index}.field_label`)}
                type="text"
                className="w-full bg-gray-600 border border-gray-500 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
                placeholder="e.g., Year Range"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Sort Order
              </label>
              <input
                {...register(`metadata_fields.${index}.sort_order`, { valueAsNumber: true })}
                type="number"
                min="0"
                className="w-full bg-gray-600 border border-gray-500 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Description
            </label>
            <textarea
              {...register(`metadata_fields.${index}.field_description`)}
              rows={2}
              className="w-full bg-gray-600 border border-gray-500 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
              placeholder="Help text for this field..."
            />
          </div>

          {/* Select Options */}
          {fieldType === 'select' && (
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Options
              </label>
              <div className="space-y-2">
                {fieldOptions.map((option: string, optionIndex: number) => (
                  <div key={optionIndex} className="flex items-center space-x-2">
                    <span className="flex-1 bg-gray-600 border border-gray-500 rounded-lg px-3 py-2 text-white">
                      {option}
                    </span>
                    <button
                      type="button"
                      onClick={() => removeOption(optionIndex)}
                      className="text-red-400 hover:text-red-300 transition-colors"
                    >
                      <TrashIcon className="h-4 w-4" />
                    </button>
                  </div>
                ))}
                <div className="flex items-center space-x-2">
                  <input
                    type="text"
                    value={newOption}
                    onChange={(e) => setNewOption(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addOption())}
                    className="flex-1 bg-gray-600 border border-gray-500 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-yellow-500"
                    placeholder="Add new option..."
                  />
                  <button
                    type="button"
                    onClick={addOption}
                    className="bg-blue-500 hover:bg-blue-600 text-white px-3 py-2 rounded-lg transition-colors"
                  >
                    Add
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Checkboxes */}
          <div className="flex space-x-6">
            <label className="flex items-center space-x-2">
              <input
                {...register(`metadata_fields.${index}.is_required`)}
                type="checkbox"
                className="w-4 h-4 text-yellow-500 bg-gray-600 border-gray-500 rounded focus:ring-yellow-500 focus:ring-2"
              />
              <span className="text-sm text-gray-300">Required</span>
            </label>
            <label className="flex items-center space-x-2">
              <input
                {...register(`metadata_fields.${index}.is_searchable`)}
                type="checkbox"
                className="w-4 h-4 text-yellow-500 bg-gray-600 border-gray-500 rounded focus:ring-yellow-500 focus:ring-2"
              />
              <span className="text-sm text-gray-300">Searchable</span>
            </label>
          </div>
        </div>
      )}

      {/* Field Value Input */}
      <div className="mt-4">
        <label className="block text-sm font-medium text-gray-300 mb-2">
          Field Value
        </label>
        {renderFieldInput()}
      </div>
    </div>
  )
}

