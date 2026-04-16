import { useState, useEffect, useRef } from 'react'
import { MagnifyingGlassIcon, XMarkIcon, ChevronDownIcon } from '@heroicons/react/24/outline'

interface Collection {
  id: number
  name: string
  description?: string
  coin_count?: number
}

interface CollectionSelectorProps {
  collections: Collection[]
  selectedIds: number[]
  onSelectionChange: (selectedIds: number[]) => void
  placeholder?: string
}

export default function CollectionSelector({ 
  collections, 
  selectedIds, 
  onSelectionChange, 
  placeholder = "Search collections..." 
}: CollectionSelectorProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [highlightedIndex, setHighlightedIndex] = useState(-1)
  const inputRef = useRef<HTMLInputElement>(null)
  const dropdownRef = useRef<HTMLDivElement>(null)

  // Filter collections based on search term
  const filteredCollections = collections.filter(collection =>
    collection.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (collection.description && collection.description.toLowerCase().includes(searchTerm.toLowerCase()))
  )

  // Get selected collections
  const selectedCollections = collections.filter(c => selectedIds.includes(c.id))

  const handleToggleCollection = (collectionId: number) => {
    const newSelection = selectedIds.includes(collectionId)
      ? selectedIds.filter(id => id !== collectionId)
      : [...selectedIds, collectionId]
    onSelectionChange(newSelection)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen) return

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        setHighlightedIndex(prev => 
          prev < filteredCollections.length - 1 ? prev + 1 : 0
        )
        break
      case 'ArrowUp':
        e.preventDefault()
        setHighlightedIndex(prev => 
          prev > 0 ? prev - 1 : filteredCollections.length - 1
        )
        break
      case 'Enter':
        e.preventDefault()
        if (highlightedIndex >= 0 && highlightedIndex < filteredCollections.length) {
          handleToggleCollection(filteredCollections[highlightedIndex].id)
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

  const removeCollection = (collectionId: number) => {
    onSelectionChange(selectedIds.filter(id => id !== collectionId))
  }

  return (
    <div className="relative">
      {/* Selected Collections Bubbles */}
      <div className="flex flex-wrap gap-2 mb-3">
        {selectedCollections.map(collection => (
          <div
            key={collection.id}
            className="inline-flex items-center px-3 py-1 bg-yellow-500/20 text-yellow-300 rounded-full text-sm border border-yellow-500/30"
          >
            <span className="mr-2">{collection.name}</span>
            <button
              type="button"
              onClick={() => removeCollection(collection.id)}
              className="hover:text-yellow-200 transition-colors"
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
          className="block w-full pl-10 pr-10 py-2 border border-gray-600 rounded-lg bg-gray-800 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-yellow-500 focus:border-transparent transition-all duration-200"
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
          {filteredCollections.length > 0 ? (
            filteredCollections.map((collection, index) => {
              const isSelected = selectedIds.includes(collection.id)
              const isHighlighted = index === highlightedIndex
              
              return (
                <div
                  key={collection.id}
                  className={`px-4 py-3 cursor-pointer transition-colors ${
                    isHighlighted 
                      ? 'bg-gray-700' 
                      : 'hover:bg-gray-700'
                  } ${isSelected ? 'bg-yellow-500/10' : ''}`}
                  onClick={() => handleToggleCollection(collection.id)}
                  onMouseEnter={() => setHighlightedIndex(index)}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className={`font-medium ${isSelected ? 'text-yellow-300' : 'text-gray-300'}`}>
                        {collection.name}
                      </div>
                    </div>
                    {isSelected && (
                      <div className="text-yellow-400 text-sm">✓</div>
                    )}
                  </div>
                </div>
              )
            })
          ) : (
            <div className="px-4 py-3 text-gray-500 text-sm">
              {searchTerm ? 'No collections found' : 'No collections available'}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
