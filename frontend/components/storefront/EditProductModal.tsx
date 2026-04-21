import { useEffect, useState } from 'react'
import PhotoEditor from './PhotoEditor'
import CameraCapture from './CameraCapture'

import { getAuth } from '../../lib/auth'
import { resolveImageUrl } from '../../lib/storefront'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:1270/api/v1'
function getToken() { return getAuth()?.token || 'manage-token' }

interface Product {
  id: number
  slug: string
  name: string
  metal: string
  metals?: string[]
  productType: string
  price: string
  image: string | null
  buyUrl: string | null
  quantity: number | null
  ebayQuantity?: number | null
  offerPrice?: number | null
}

interface Props {
  product: Product
  onClose: () => void
  onSaved: () => void
}

interface MetalOption { value: string; label: string; basePrice?: number; offerPrice?: number }
interface TypeOption { value: string; label: string }

type ImageStage = 'current' | 'camera' | 'uploading' | 'editing' | 'done'

const metalColors: Record<string, string> = {
  gold: 'border-amber-400 bg-amber-50 text-amber-700',
  platinum: 'border-slate-400 bg-slate-50 text-slate-700',
  silver: 'border-gray-400 bg-gray-50 text-gray-700',
}
function metalColor(value: string) {
  return metalColors[value] ?? 'border-stone-400 bg-stone-50 text-stone-700'
}

const DEFAULT_METALS: MetalOption[] = [
  { value: 'gold', label: 'Gold' },
  { value: 'platinum', label: 'Platinum' },
  { value: 'silver', label: 'Silver' },
]
const DEFAULT_TYPES: TypeOption[] = [
  { value: 'card', label: 'Card' },
  { value: 'bundle', label: 'Kit / Set' },
]

export default function EditProductModal({ product, onClose, onSaved }: Props) {
  const [title, setTitle] = useState(product.name)
  const [selectedMetals, setSelectedMetals] = useState<string[]>(product.metals?.length ? product.metals : [product.metal || 'gold'])
  const [productType, setProductType] = useState(product.productType || 'card')
  const [price, setPrice] = useState(product.price?.replace('$', '') || '')
  const [quantity, setQuantity] = useState(product.quantity ? String(product.quantity) : '1')
  const [unlimited, setUnlimited] = useState(product.quantity === null || product.quantity === 0)
  const [ebayQuantity, setEbayQuantity] = useState(String(product.ebayQuantity || 1))
  const [offerPrice, setOfferPrice] = useState(product.offerPrice ? String(product.offerPrice) : '')

  // Standard pricing / offer toggles
  const [useStandardPrice, setUseStandardPrice] = useState(!product.price || product.price === 'Price coming soon')
  const [useStandardOffer, setUseStandardOffer] = useState(!product.offerPrice)

  const [metals, setMetals] = useState<MetalOption[]>(DEFAULT_METALS)
  const [types, setTypes] = useState<TypeOption[]>(DEFAULT_TYPES)

  const [imageStage, setImageStage] = useState<ImageStage>('current')
  const [rawSrc, setRawSrc] = useState<string | null>(null)
  const [newImageUrl, setNewImageUrl] = useState<string | null>(null)

  const [saving, setSaving] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleDelete() {
    if (!confirm(`Delete "${product.name}"? This cannot be undone.`)) return
    setDeleting(true)
    try {
      const res = await fetch(`${API}/storefront/products/${product.id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${getToken()}` },
      })
      if (!res.ok) throw new Error(`${res.status}`)
      onClose()
    } catch (e: any) {
      setError('Delete failed: ' + e.message)
      setDeleting(false)
    }
  }

  // Load options from API
  useEffect(() => {
    fetch(`${API}/storefront/options`)
      .then(r => r.json())
      .then(data => {
        if (data.metals?.length) setMetals(data.metals)
        if (data.types?.length) setTypes(data.types)
      })
      .catch(() => {})
  }, [])

  // Toggle metal in/out of selection (multi-select)
  function toggleMetal(value: string) {
    setSelectedMetals(prev => {
      if (prev.includes(value)) {
        const next = prev.filter(x => x !== value)
        return next.length > 0 ? next : prev
      }
      const next = [value, ...prev.filter(x => x !== value)]
      return next
    })
  }

  function handleFileSelect(file: File) {
    const reader = new FileReader()
    reader.onload = e => {
      setRawSrc(e.target?.result as string)
      setImageStage('editing')
    }
    reader.readAsDataURL(file)
  }

  async function handlePhotoSaved(dataUrl: string) {
    setImageStage('uploading')
    try {
      const blob = await fetch(dataUrl).then(r => r.blob())
      const form = new FormData()
      form.append('file', blob, 'product.jpg')
      const res = await fetch(`${API}/storefront/products/${product.id}/image`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${getToken()}` },
        body: form,
      })
      if (!res.ok) throw new Error('Image upload failed')
      const { url } = await res.json()
      setNewImageUrl(url)
      setImageStage('done')
    } catch (e: any) {
      setError(e.message)
      setImageStage('current')
    }
  }

  function handlePhotoCancel() {
    setRawSrc(null)
    setImageStage('current')
  }

  async function handleSubmit() {
    if (!title.trim()) { setError('Title is required.'); return }
    setSaving(true)
    setError(null)
    try {
      const primaryMetal = metals.find(m => m.value === selectedMetals[0])
      const effectivePrice = useStandardPrice
        ? (primaryMetal?.basePrice ?? null)
        : (price ? parseFloat(price) : null)
      const metalOfferPrice = primaryMetal?.offerPrice ?? null
      const effectiveOfferPrice = useStandardOffer
        ? (metalOfferPrice ?? 0)
        : (offerPrice ? parseFloat(offerPrice) : 0)
      const res = await fetch(`${API}/storefront/products/${product.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${getToken()}` },
        body: JSON.stringify({
          title: title.trim(),
          metal: selectedMetals[0],
          metals: selectedMetals,
          product_type: productType,
          price: effectivePrice,
          quantity: unlimited ? 0 : (parseInt(quantity) || 1),
          ebay_quantity: parseInt(ebayQuantity) || 1,
          offer_price: effectiveOfferPrice,
        }),
      })
      if (!res.ok) throw new Error(`Save failed (${res.status})`)
      onSaved()
      onClose()
    } catch (e: any) {
      setError(e.message || 'Something went wrong.')
    } finally {
      setSaving(false)
    }
  }

  const [ebayPublishing, setEbayPublishing] = useState(false)
  const [ebayResult, setEbayResult] = useState<{ success?: boolean; message?: string } | null>(null)

  async function publishToEbay() {
    setEbayPublishing(true)
    setEbayResult(null)
    try {
      const primaryMetal = metals.find(m => m.value === selectedMetals[0])
      const effectivePrice = useStandardPrice
        ? (primaryMetal?.basePrice ?? undefined)
        : (price ? parseFloat(price) : undefined)
      const metalOfferPrice = primaryMetal?.offerPrice ?? undefined
      const effectiveOfferPrice = useStandardOffer
        ? metalOfferPrice
        : (offerPrice ? parseFloat(offerPrice) : undefined)
      const res = await fetch(`${API}/storefront/products/${product.id}/ebay-publish`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${getToken()}` },
        body: JSON.stringify({
          price: effectivePrice,
          quantity: parseInt(ebayQuantity) || 1,
          offer_price: effectiveOfferPrice,
        }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        setEbayResult({ success: false, message: err.detail || `Error ${res.status}` })
      } else {
        const data = await res.json()
        setEbayResult({ success: true, message: data.ebay?.url ? `Listed: ${data.ebay.url}` : 'Published to eBay!' })
      }
    } catch (e: any) {
      setEbayResult({ success: false, message: e.message })
    } finally {
      setEbayPublishing(false)
    }
  }

  const currentImage = resolveImageUrl(newImageUrl || product.image)
  const primaryMetal = selectedMetals[0]
  const selectedMetal = metals.find(m => m.value === primaryMetal)

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="relative w-full max-w-2xl max-h-[95vh] overflow-y-auto rounded-2xl bg-white shadow-2xl">

        {/* Header */}
        <div className="sticky top-0 z-10 flex items-center justify-between border-b border-stone-100 bg-white px-6 py-4">
          <h2 className="text-lg font-semibold text-stone-900">Edit Product</h2>
          <button onClick={onClose} className="rounded-full p-1.5 text-stone-400 hover:bg-stone-100 transition-colors">
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="grid gap-6 p-6 lg:grid-cols-2">

          {/* Left: Photo */}
          <div>
            <label className="mb-2 block text-sm font-medium text-stone-700">Photo</label>
            {imageStage === 'current' && (
              <div className="flex flex-col gap-3">
                {currentImage ? (
                  <div className="overflow-hidden rounded-xl border border-stone-200 bg-stone-100">
                    <img src={currentImage} alt={title} className="w-full h-auto block" />
                  </div>
                ) : (
                  <div className="flex items-center justify-center rounded-xl border-2 border-dashed border-stone-200 aspect-square text-stone-300">
                    <svg className="h-10 w-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                  </div>
                )}
                <div className="flex gap-2">
                  <button
                    onClick={() => setImageStage('camera')}
                    className="flex-1 flex items-center justify-center gap-2 rounded-full border border-stone-200 py-2 text-sm text-stone-500 hover:bg-stone-50 hover:border-amber-300 hover:text-amber-600 transition-colors"
                  >
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                    Camera
                  </button>
                  <label className="flex-1 flex items-center justify-center gap-2 cursor-pointer rounded-full border border-stone-200 py-2 text-sm text-stone-500 hover:bg-stone-50 hover:border-amber-300 hover:text-amber-600 transition-colors">
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                    </svg>
                    Upload
                    <input type="file" accept="image/*" className="hidden"
                      onChange={e => e.target.files?.[0] && handleFileSelect(e.target.files[0])} />
                  </label>
                </div>
              </div>
            )}
            {imageStage === 'camera' && (
              <CameraCapture
                onCapture={handlePhotoSaved}
                onCancel={() => setImageStage('current')}
              />
            )}
            {imageStage === 'uploading' && (
              <div className="flex items-center justify-center rounded-xl border border-stone-200 aspect-square bg-stone-50">
                <div className="text-sm text-stone-400">Uploading…</div>
              </div>
            )}
            {imageStage === 'editing' && rawSrc && (
              <PhotoEditor src={rawSrc} onSave={handlePhotoSaved} onCancel={handlePhotoCancel} />
            )}
            {imageStage === 'done' && (
              <div className="flex flex-col gap-3">
                <div className="overflow-hidden rounded-xl border border-stone-200 bg-stone-100">
                  <img src={newImageUrl!} alt={title} className="w-full h-auto block" />
                </div>
                <p className="text-center text-xs text-green-600">Photo updated</p>
                <div className="flex gap-2">
                  <button
                    onClick={() => setImageStage('camera')}
                    className="flex-1 rounded-full border border-stone-200 py-2 text-sm text-stone-500 hover:bg-stone-50 transition-colors"
                  >
                    Retake
                  </button>
                  <label className="flex-1 cursor-pointer rounded-full border border-stone-200 py-2 text-center text-sm text-stone-500 hover:bg-stone-50 transition-colors">
                    Replace
                    <input type="file" accept="image/*" className="hidden"
                      onChange={e => e.target.files?.[0] && handleFileSelect(e.target.files[0])} />
                  </label>
                </div>
              </div>
            )}
          </div>

          {/* Right: Form */}
          <div className="flex flex-col gap-5">

            {/* Title */}
            <div>
              <label className="mb-1.5 block text-sm font-medium text-stone-700">Title <span className="text-red-400">*</span></label>
              <input
                type="text"
                value={title}
                onChange={e => setTitle(e.target.value)}
                className="w-full rounded-xl border border-stone-200 px-4 py-2.5 text-sm text-stone-900 focus:border-amber-400 focus:outline-none focus:ring-1 focus:ring-amber-400"
              />
            </div>

            {/* Metal */}
            <div>
              <label className="mb-2 block text-sm font-medium text-stone-700">
                Metal
                <span className="ml-1.5 text-xs font-normal text-stone-400">select all that apply</span>
              </label>
              <div className="flex flex-wrap gap-2">
                {metals.map(m => {
                  const active = selectedMetals.includes(m.value)
                  return (
                    <button
                      key={m.value}
                      type="button"
                      onClick={() => toggleMetal(m.value)}
                      className={`rounded-xl border-2 px-4 py-2 text-sm font-medium transition-colors ${
                        active
                          ? metalColor(m.value) + ' border-current'
                          : 'border-stone-200 text-stone-500 hover:border-stone-300'
                      }`}
                    >
                      {m.label}
                      {m.basePrice != null && (
                        <span className="ml-1.5 opacity-60 font-normal">${m.basePrice}</span>
                      )}
                    </button>
                  )
                })}
              </div>
              {selectedMetals.length > 1 && (
                <p className="mt-1.5 text-xs text-stone-400">
                  Primary: <span className="font-medium">{selectedMetal?.label || primaryMetal}</span> — first selected sets the main category
                </p>
              )}
              {selectedMetals.length === 1 && selectedMetal?.basePrice != null && (
                <p className="mt-1.5 text-xs text-stone-400">
                  Base price for {selectedMetal.label}: <span className="font-medium">${selectedMetal.basePrice}</span>
                  {' '}— set below to override
                </p>
              )}
            </div>

            {/* Type */}
            <div>
              <label className="mb-2 block text-sm font-medium text-stone-700">Type</label>
              <div className="flex flex-wrap gap-2">
                {types.map(t => (
                  <button
                    key={t.value}
                    type="button"
                    onClick={() => setProductType(t.value)}
                    className={`rounded-xl border-2 px-4 py-2 text-sm font-medium transition-colors ${
                      productType === t.value
                        ? 'border-amber-400 bg-amber-50 text-amber-700'
                        : 'border-stone-200 text-stone-500 hover:border-stone-300'
                    }`}
                  >
                    {t.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Price + Quantity */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <div className="mb-1.5 flex items-center justify-between">
                  <label className="text-sm font-medium text-stone-700">Price ($)</label>
                  {selectedMetal?.basePrice != null && (
                    <label className="flex items-center gap-1.5 text-xs text-stone-500 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={useStandardPrice}
                        onChange={e => setUseStandardPrice(e.target.checked)}
                        className="accent-amber-500"
                      />
                      Standard
                    </label>
                  )}
                </div>
                {useStandardPrice && selectedMetal?.basePrice != null ? (
                  <div className="flex items-center rounded-xl border border-stone-200 bg-stone-50 px-4 py-2.5 text-sm text-stone-500">
                    ${selectedMetal.basePrice.toFixed(2)}
                    <span className="ml-1.5 text-xs text-stone-400">(standard)</span>
                  </div>
                ) : (
                  <input
                    type="number" min="0" step="0.01"
                    value={price}
                    onChange={e => setPrice(e.target.value)}
                    placeholder={selectedMetal?.basePrice != null ? String(selectedMetal.basePrice) : '0.00'}
                    className="w-full rounded-xl border border-stone-200 px-4 py-2.5 text-sm text-stone-900 placeholder-stone-300 focus:border-amber-400 focus:outline-none focus:ring-1 focus:ring-amber-400"
                  />
                )}
              </div>
              <div>
                <div className="mb-1.5 flex items-center justify-between">
                  <label className="text-sm font-medium text-stone-700">Quantity</label>
                  <label className="flex items-center gap-1.5 text-xs text-stone-500 cursor-pointer">
                    <input type="checkbox" checked={unlimited} onChange={e => setUnlimited(e.target.checked)} className="accent-amber-500" />
                    Unlimited
                  </label>
                </div>
                <input
                  type="number" min="1"
                  value={unlimited ? '' : quantity}
                  disabled={unlimited}
                  onChange={e => setQuantity(e.target.value)}
                  placeholder={unlimited ? '∞' : '1'}
                  className="w-full rounded-xl border border-stone-200 px-4 py-2.5 text-sm text-stone-900 placeholder-stone-400 focus:border-amber-400 focus:outline-none focus:ring-1 focus:ring-amber-400 disabled:bg-stone-50 disabled:text-stone-400"
                />
              </div>
            </div>

            {/* Error */}
            {error && (
              <p className="rounded-xl bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-600">{error}</p>
            )}

            {/* Submit */}
            <button
              onClick={handleSubmit}
              disabled={saving || deleting}
              className="mt-auto rounded-full bg-amber-500 py-3 text-sm font-semibold text-white hover:bg-amber-600 disabled:opacity-50 transition-colors"
            >
              {saving ? 'Saving…' : 'Save Changes'}
            </button>
            <button
              onClick={handleDelete}
              disabled={saving || deleting}
              className="rounded-full border border-red-200 py-2.5 text-sm font-medium text-red-400 hover:bg-red-50 hover:border-red-400 hover:text-red-600 disabled:opacity-50 transition-colors"
            >
              {deleting ? 'Deleting…' : 'Delete this product'}
            </button>
          </div>
        </div>

        {/* eBay publish */}
        <div className="border-t border-stone-100 px-6 py-5 space-y-3">
          <div className="flex items-center justify-between gap-4 flex-wrap">
            <div>
              <div className="text-sm font-medium text-stone-700">List on eBay</div>
              <div className="text-xs text-stone-400">Publish this product to your eBay seller account</div>
              {ebayResult && (
                <div className={`mt-1.5 text-xs font-medium ${ebayResult.success ? 'text-green-600' : 'text-red-500'}`}>
                  {ebayResult.message}
                </div>
              )}
            </div>
            <button
              type="button"
              onClick={publishToEbay}
              disabled={ebayPublishing}
              className="flex-shrink-0 flex items-center gap-2 rounded-full border border-stone-300 bg-white px-4 py-2 text-sm font-medium text-stone-700 hover:border-amber-400 hover:text-amber-700 disabled:opacity-50 transition-colors"
            >
              {ebayPublishing ? (
                <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
              ) : (
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
              )}
              {ebayPublishing ? 'Publishing…' : 'Publish to eBay'}
            </button>
          </div>
          <div className="flex items-center gap-3">
            <label className="text-xs font-medium text-stone-500 w-24 flex-shrink-0">eBay Quantity</label>
            <input
              type="number" min="1"
              value={ebayQuantity}
              onChange={e => setEbayQuantity(e.target.value)}
              className="w-24 rounded-lg border border-stone-200 px-3 py-1.5 text-sm text-stone-800 focus:border-amber-400 focus:outline-none"
            />
            <span className="text-xs text-stone-400">Separate from website stock</span>
          </div>
          {(() => {
            const primaryMetal = metals.find(m => m.value === selectedMetals[0])
            const metalOfferPrice = primaryMetal?.offerPrice ?? null
            return (
              <div className="flex items-center gap-3 flex-wrap">
                <label className="text-xs font-medium text-stone-500 w-24 flex-shrink-0">Min. offer</label>
                {useStandardOffer && metalOfferPrice != null ? (
                  <div className="flex items-center rounded-lg border border-stone-200 bg-stone-50 px-3 py-1.5 text-sm text-stone-500 min-w-[6rem]">
                    ${metalOfferPrice.toFixed(2)}
                  </div>
                ) : (
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-xs text-stone-400">$</span>
                    <input
                      type="number" min="0" step="0.01"
                      value={offerPrice}
                      onChange={e => setOfferPrice(e.target.value)}
                      placeholder="—"
                      className="w-24 rounded-lg border border-stone-200 pl-6 pr-2 py-1.5 text-sm text-stone-800 placeholder-stone-300 focus:border-amber-400 focus:outline-none"
                    />
                  </div>
                )}
                {metalOfferPrice != null && (
                  <label className="flex items-center gap-1.5 text-xs text-stone-500 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={useStandardOffer}
                      onChange={e => setUseStandardOffer(e.target.checked)}
                      className="accent-amber-500"
                    />
                    Standard
                  </label>
                )}
                <span className="text-xs text-stone-400">Buyers cannot submit offers below this price</span>
              </div>
            )
          })()}
        </div>

      </div>
    </div>
  )
}
