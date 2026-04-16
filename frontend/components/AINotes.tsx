import { useState, useEffect } from 'react'
import { DocumentTextIcon, PencilIcon, CheckIcon, XMarkIcon } from '@heroicons/react/24/outline'
import { api } from '../lib/api'
import toast from 'react-hot-toast'

interface AINotesProps {
  coinId: number
  initialNotes?: string
  onNotesUpdate?: (notes: string) => void
}

export default function AINotes({ coinId, initialNotes = '', onNotesUpdate }: AINotesProps) {
  const [notes, setNotes] = useState(initialNotes)
  const [isEditing, setIsEditing] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [tempNotes, setTempNotes] = useState(initialNotes)

  useEffect(() => {
    setNotes(initialNotes)
    setTempNotes(initialNotes)
  }, [initialNotes])

  const handleSave = async () => {
    setIsLoading(true)
    try {
      await api.put(`/coins/${coinId}`, {
        ai_notes: tempNotes
      })
      
      setNotes(tempNotes)
      setIsEditing(false)
      onNotesUpdate?.(tempNotes)
      toast.success('AI notes updated successfully!')
    } catch (error) {
      console.error('Error updating notes:', error)
      toast.error('Failed to update AI notes')
    } finally {
      setIsLoading(false)
    }
  }

  const handleCancel = () => {
    setTempNotes(notes)
    setIsEditing(false)
  }

  const handleEdit = () => {
    setTempNotes(notes)
    setIsEditing(true)
  }

  return (
    <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          <DocumentTextIcon className="h-5 w-5 text-green-400" />
          <h3 className="font-medium text-white">AI Notes</h3>
        </div>
        {!isEditing && (
          <button
            onClick={handleEdit}
            className="text-gray-400 hover:text-white transition-colors"
            title="Edit notes"
          >
            <PencilIcon className="h-4 w-4" />
          </button>
        )}
      </div>

      {isEditing ? (
        <div className="space-y-3">
          <textarea
            value={tempNotes}
            onChange={(e) => setTempNotes(e.target.value)}
            placeholder="Enter AI notes about this coin..."
            className="w-full h-32 bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white placeholder-gray-400 focus:outline-none focus:border-yellow-500 resize-none"
          />
          <div className="flex space-x-2">
            <button
              onClick={handleSave}
              disabled={isLoading}
              className="flex items-center space-x-1 bg-green-500 hover:bg-green-600 text-white px-3 py-1 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
            >
              <CheckIcon className="h-4 w-4" />
              <span>{isLoading ? 'Saving...' : 'Save'}</span>
            </button>
            <button
              onClick={handleCancel}
              disabled={isLoading}
              className="flex items-center space-x-1 bg-gray-600 hover:bg-gray-500 text-white px-3 py-1 rounded-lg text-sm font-medium transition-colors"
            >
              <XMarkIcon className="h-4 w-4" />
              <span>Cancel</span>
            </button>
          </div>
        </div>
      ) : (
        <div className="min-h-[100px]">
          {notes ? (
            <div className="text-sm text-gray-300 whitespace-pre-wrap">
              {notes}
            </div>
          ) : (
            <div className="text-sm text-gray-500 italic">
              No AI notes available. Click edit to add notes about this coin.
            </div>
          )}
        </div>
      )}
    </div>
  )
}


