import { Editor } from '@tinymce/tinymce-react'
import { useState } from 'react'

interface RichTextEditorProps {
  value: string
  onChange: (value: string) => void
  placeholder?: string
}

export default function RichTextEditor({ value, onChange, placeholder = "Enter description..." }: RichTextEditorProps) {
  const [isPreview, setIsPreview] = useState(false)
  const [apiKeyError, setApiKeyError] = useState(false)

  const handleEditorChange = (content: string) => {
    onChange(content)
  }

  const handleEditorError = (error: any) => {
    console.error('TinyMCE error:', error)
    setApiKeyError(true)
  }

  return (
    <div className="space-y-3">
      {/* Toolbar */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <span className="text-sm font-medium text-gray-300">Description</span>
          <button
            type="button"
            onClick={() => setIsPreview(!isPreview)}
            className="text-xs px-2 py-1 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded transition-colors"
          >
            {isPreview ? 'Edit' : 'Preview'}
          </button>
        </div>
        <span className="text-xs text-gray-500">
          Rich text editor with live preview
        </span>
      </div>

      {/* API Key Error Message */}
      {apiKeyError && (
        <div className="bg-yellow-900 border border-yellow-600 rounded-lg p-3">
          <p className="text-yellow-200 text-sm">
            <strong>TinyMCE API Key Issue:</strong> Please check your NEXT_PUBLIC_TINY_API_KEY in .env.local
            <br />
            Get a free API key from: <a href="https://www.tiny.cloud/auth/signup/" target="_blank" rel="noopener noreferrer" className="underline">https://www.tiny.cloud/auth/signup/</a>
          </p>
        </div>
      )}

      {/* Editor */}
      {!isPreview ? (
        <div className="border border-gray-600 rounded-lg overflow-hidden">
          <Editor
            apiKey={process.env.NEXT_PUBLIC_TINY_API_KEY}
            value={value}
            onEditorChange={handleEditorChange}
            onError={handleEditorError}
            init={{
              height: 300,
              menubar: false,
              plugins: [
                'advlist', 'autolink', 'lists', 'link', 'image', 'charmap', 'preview',
                'anchor', 'searchreplace', 'visualblocks', 'code', 'fullscreen',
                'insertdatetime', 'media', 'table', 'help', 'wordcount'
              ],
              toolbar: 'undo redo | blocks | ' +
                'bold italic forecolor | alignleft aligncenter ' +
                'alignright alignjustify | bullist numlist outdent indent | ' +
                'removeformat | help',
              content_style: 'body { font-family: -apple-system, BlinkMacSystemFont, San Francisco, Segoe UI, Roboto, Helvetica Neue, sans-serif; font-size: 14px; }',
              placeholder: placeholder,
              skin: 'oxide-dark',
              content_css: 'dark',
              branding: false,
              statusbar: false,
            }}
          />
        </div>
      ) : (
        <div className="border border-gray-600 rounded-lg p-4 bg-gray-800 min-h-[300px]">
          <div 
            className="prose prose-invert max-w-none"
            dangerouslySetInnerHTML={{ __html: value || '<p class="text-gray-500 italic">No description entered</p>' }}
          />
        </div>
      )}
    </div>
  )
}
