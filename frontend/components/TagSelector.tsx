import { useState, useEffect, useRef } from 'react'
import { MagnifyingGlassIcon, XMarkIcon, ChevronDownIcon } from '@heroicons/react/24/outline'

interface TagSelectorProps {
  selectedTags: string[]
  onTagsChange: (tags: string[]) => void
  existingTags?: string[]
  placeholder?: string
}

export default function TagSelector({ 
  selectedTags, 
  onTagsChange, 
  existingTags = [],
  placeholder = "Add tags..." 
}: TagSelectorProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [highlightedIndex, setHighlightedIndex] = useState(-1)
  const inputRef = useRef<HTMLInputElement>(null)
  const dropdownRef = useRef<HTMLDivElement>(null)

  // Filter existing tags based on search term
  const filteredTags = existingTags
    .filter(tag => 
      tag.toLowerCase().includes(searchTerm.toLowerCase()) &&
      !selectedTags.includes(tag)
    )
    .slice(0, 10) // Limit to 10 suggestions

  const handleAddTag = (tag: string) => {
    if (!selectedTags.includes(tag)) {
      onTagsChange([...selectedTags, tag])
    }
    setSearchTerm('')
    setIsOpen(false)
  }

  const handleRemoveTag = (tagToRemove: string) => {
    onTagsChange(selectedTags.filter(tag => tag !== tagToRemove))
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen) return

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        setHighlightedIndex(prev => 
          prev < filteredTags.length - 1 ? prev + 1 : 0
        )
        break
      case 'ArrowUp':
        e.preventDefault()
        setHighlightedIndex(prev => 
          prev > 0 ? prev - 1 : filteredTags.length - 1
        )
        break
      case 'Enter':
        e.preventDefault()
        if (highlightedIndex >= 0 && highlightedIndex < filteredTags.length) {
          handleAddTag(filteredTags[highlightedIndex])
        } else if (searchTerm.trim() && !selectedTags.includes(searchTerm.trim())) {
          // Add new tag if not in suggestions
          handleAddTag(searchTerm.trim())
        }
        break
      case 'Escape':
        setIsOpen(false)
        setHighlightedIndex(-1)
        break
    }
  }

  const handleInputFocus = () => {
    setIsOpen(true)
    setHighlightedIndex(-1)
  }

  const handleInputBlur = (e: React.FocusEvent) => {
    // Don't close if clicking on dropdown
    if (dropdownRef.current?.contains(e.relatedTarget as Node)) {
      return
    }
    setIsOpen(false)
    setHighlightedIndex(-1)
  }

  return (
    <div className="relative">
      {/* Selected Tags Bubbles */}
      <div className="flex flex-wrap gap-2 mb-3">
        {selectedTags.map(tag => (
          <div
            key={tag}
            className="inline-flex items-center px-3 py-1 bg-blue-500/20 text-blue-300 rounded-full text-sm border border-blue-500/30"
          >
            <span className="mr-2">{tag}</span>
            <button
              type="button"
              onClick={() => handleRemoveTag(tag)}
              className="hover:text-blue-200 transition-colors"
            >
              <XMarkIcon className="h-3 w-3" />
            </button>
          </div>
        ))}
      </div>

      {/* Search Input */}
      <div className="relative">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
        </div>
        <input
          ref={inputRef}
          type="text"
          placeholder={placeholder}
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          onFocus={handleInputFocus}
          onBlur={handleInputBlur}
          onKeyDown={handleKeyDown}
          className="block w-full pl-10 pr-10 py-2 border border-gray-600 rounded-lg bg-gray-800 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
        />
        <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
          <ChevronDownIcon className={`h-5 w-5 text-gray-400 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} />
        </div>
      </div>

      {/* Dropdown */}
      {isOpen && (
        <div
          ref={dropdownRef}
          className="absolute z-50 w-full mt-1 bg-gray-800 border border-gray-600 rounded-lg shadow-xl max-h-60 overflow-y-auto"
        >
          {filteredTags.length > 0 ? (
            filteredTags.map((tag, index) => {
              const isHighlighted = index === highlightedIndex
              
              return (
                <div
                  key={tag}
                  className={`px-4 py-3 cursor-pointer transition-colors ${
                    isHighlighted 
                      ? 'bg-gray-700' 
                      : 'hover:bg-gray-700'
                  }`}
                  onClick={() => handleAddTag(tag)}
                  onMouseEnter={() => setHighlightedIndex(index)}
                >
                  <div className="text-gray-300 font-medium">{tag}</div>
                </div>
              )
            })
          ) : searchTerm.trim() ? (
            <div 
              className="px-4 py-3 cursor-pointer hover:bg-gray-700 transition-colors"
              onClick={() => handleAddTag(searchTerm.trim())}
            >
              <div className="text-blue-300 font-medium">
                Add "{searchTerm.trim()}" as new tag
              </div>
            </div>
          ) : (
            <div className="px-4 py-3 text-gray-500 text-sm">
              No tags available
            </div>
          )}
        </div>
      )}
    </div>
  )
}
