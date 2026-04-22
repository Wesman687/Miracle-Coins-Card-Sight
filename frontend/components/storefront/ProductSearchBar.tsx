interface Props {
  value: string
  onChange: (v: string) => void
  onSubmit?: () => void
  placeholder?: string
  activeTag?: string | null
  tags?: string[]
  onTagClick?: (tag: string) => void
  onTagClear?: () => void
  className?: string
}

export default function ProductSearchBar({
  value,
  onChange,
  onSubmit,
  placeholder = 'Search products…',
  activeTag = null,
  tags = [],
  onTagClick,
  onTagClear,
  className = '',
}: Props) {
  return (
    <div className={className}>
      <form
        onSubmit={e => { e.preventDefault(); onSubmit?.() }}
        className="relative max-w-sm"
      >
        <svg className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-stone-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-4.35-4.35M17 11A6 6 0 115 11a6 6 0 0112 0z" />
        </svg>
        <input
          type="text"
          value={value}
          onChange={e => onChange(e.target.value)}
          placeholder={placeholder}
          className="w-full rounded-full border border-stone-200 bg-white pl-9 pr-4 py-2.5 text-sm text-stone-800 placeholder-stone-400 focus:border-amber-400 focus:outline-none focus:ring-1 focus:ring-amber-400 shadow-sm"
        />
        {value && (
          <button
            type="button"
            onClick={() => onChange('')}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-stone-400 hover:text-stone-600"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </form>

      {tags.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-2">
          {tags.slice(0, 12).map(tag => (
            <button
              key={tag}
              type="button"
              onClick={() => onTagClick?.(tag)}
              className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
                activeTag === tag
                  ? 'bg-amber-500 text-white'
                  : 'bg-stone-100 text-stone-600 hover:bg-stone-200'
              }`}
            >
              {tag}
            </button>
          ))}
          {activeTag && onTagClear && (
            <button
              type="button"
              onClick={onTagClear}
              className="rounded-full px-3 py-1 text-xs text-stone-400 hover:text-red-400 transition-colors"
            >
              Clear filter
            </button>
          )}
        </div>
      )}
    </div>
  )
}
