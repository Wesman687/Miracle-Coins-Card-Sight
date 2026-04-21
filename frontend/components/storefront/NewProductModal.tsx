import { useRef, useState } from 'react'
import PhotoEditor from './PhotoEditor'
import CameraCapture from './CameraCapture'

import { getAuth } from '../../lib/auth'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:1270/api/v1'
function getToken() { return getAuth()?.token || 'manage-token' }

interface Props {
  onClose: () => void
  onSaved: () => void
}

type ImageStage = 'empty' | 'camera' | 'editing' | 'done'

const METALS = [
  { value: 'gold', label: 'Gold', color: 'border-amber-400 bg-amber-50 text-amber-700' },
  { value: 'platinum', label: 'Platinum', color: 'border-slate-400 bg-slate-50 text-slate-700' },
  { value: 'silver', label: 'Silver', color: 'border-gray-400 bg-gray-50 text-gray-700' },
]

const TYPES = [
  { value: 'card', label: 'Card' },
  { value: 'bundle', label: 'Kit / Set' },
]

const WEIGHT_DEFAULTS: Record<string, string> = {
  gold: '1/4 grain gold',
  platinum: '1/4 grain platinum',
  silver: '1 grain silver',
}

export default function NewProductModal({ onClose, onSaved }: Props) {
  // Form state
  const [title, setTitle] = useState('')
  const [selectedMetals, setSelectedMetals] = useState<string[]>(['gold'])
  const [productType, setProductType] = useState('card')
  const [price, setPrice] = useState('')
  const [weightLabel, setWeightLabel] = useState('1/4 grain gold')
  const [description, setDescription] = useState('')
  const [quantity, setQuantity] = useState('1')
  const [unlimited, setUnlimited] = useState(false)
  const [ebayQuantity, setEbayQuantity] = useState('1')

  // Image state
  const [imageStage, setImageStage] = useState<ImageStage>('empty')
  const [rawSrc, setRawSrc] = useState<string | null>(null)
  const [finalImage, setFinalImage] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)


  // eBay listing option
  const [listOnEbay, setListOnEbay] = useState(false)
  const [ebayStatus, setEbayStatus] = useState<string | null>(null)
  const [offerPrice, setOfferPrice] = useState('')

  // AI description
  const [generatingDesc, setGeneratingDesc] = useState(false)

  async function generateDescription() {
    setGeneratingDesc(true)
    try {
      const res = await fetch(`${API}/storefront/generate-description`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${getToken()}` },
        body: JSON.stringify({ title, metal: selectedMetals[0], product_type: productType, instructions: description }),
      })
      if (!res.ok) throw new Error('Failed')
      const data = await res.json()
      setDescription(data.description)
    } catch { alert('AI description failed — check that OPENAI_API_KEY is set.') }
    finally { setGeneratingDesc(false) }
  }

  // Submission
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // ── Metal toggle (multi-select) ───────────────────────────────────────────
  function toggleMetal(m: string) {
    setSelectedMetals(prev => {
      if (prev.includes(m)) {
        const next = prev.filter(x => x !== m)
        return next.length > 0 ? next : prev // must keep at least one
      }
      const next = [...prev, m]
      // Auto-fill weight label when it's the only selection
      if (next.length === 1) setWeightLabel(WEIGHT_DEFAULTS[m] ?? '')
      return next
    })
  }


  // ── File upload ───────────────────────────────────────────────────────────
  function handleFileSelect(file: File) {
    const reader = new FileReader()
    reader.onload = e => {
      setRawSrc(e.target?.result as string)
      setImageStage('editing')
    }
    reader.readAsDataURL(file)
  }

  // ── Photo editor callbacks ────────────────────────────────────────────────
  function handlePhotoSaved(dataUrl: string) {
    setFinalImage(dataUrl)
    setImageStage('done')
  }

  function handlePhotoCancel() {
    setRawSrc(null)
    setImageStage('empty')
  }

  function changePhoto() {
    setFinalImage(null)
    setRawSrc(null)
    setImageStage('empty')
  }

  // ── Submit ────────────────────────────────────────────────────────────────
  async function handleSubmit() {
    if (!title.trim()) { setError('Title is required.'); return }
    setSaving(true)
    setError(null)

    try {
      let imageUrls: string[] = []

      // Upload image if we have one
      if (finalImage) {
        const blob = await fetch(finalImage).then(r => r.blob())
        const form = new FormData()
        form.append('file', blob, 'product.jpg')
        const uploadRes = await fetch(`${API}/storefront/upload-image`, {
          method: 'POST',
          headers: { Authorization: `Bearer ${getToken()}` },
          body: form,
        })
        if (!uploadRes.ok) throw new Error('Image upload failed')
        const { url } = await uploadRes.json()
        imageUrls = [url]
      }

      // Create product
      const res = await fetch(`${API}/storefront/products`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${getToken()}` },
        body: JSON.stringify({
          title: title.trim(),
          metal: selectedMetals[0],
          metals: selectedMetals,
          product_type: productType,
          price: price ? parseFloat(price) : null,
          description: description.trim(),
          weight_label: weightLabel.trim(),
          quantity: unlimited ? 0 : (parseInt(quantity) || 1),
          ebay_quantity: listOnEbay ? (parseInt(ebayQuantity) || 1) : undefined,
          image_urls: imageUrls,
        }),
      })
      if (!res.ok) throw new Error(`Save failed (${res.status})`)
      const created = await res.json()

      // Optionally publish to eBay
      if (listOnEbay && created.id) {
        setEbayStatus('Listing on eBay…')
        try {
          const ebayRes = await fetch(`${API}/storefront/products/${created.id}/ebay-publish`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${getToken()}` },
            body: JSON.stringify({
              price: price ? parseFloat(price) : undefined,
              quantity: parseInt(ebayQuantity) || 1,
              offer_price: offerPrice ? parseFloat(offerPrice) : undefined,
            }),
          })
          if (!ebayRes.ok) {
            const err = await ebayRes.json().catch(() => ({}))
            alert(`Product saved! eBay listing failed: ${err.detail || ebayRes.status}`)
            onSaved(); onClose(); return
          }
          setEbayStatus('Listed on eBay!')
        } catch (e: any) {
          alert(`Product saved! eBay listing failed: ${e.message}`)
          onSaved(); onClose(); return
        }
      }

      onSaved()
      onClose()
    } catch (e: any) {
      setError(e.message || 'Something went wrong.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="relative w-full max-w-3xl max-h-[95vh] overflow-y-auto rounded-2xl bg-white shadow-2xl">

        {/* Header */}
        <div className="sticky top-0 z-10 flex items-center justify-between border-b border-stone-100 bg-white px-6 py-4">
          <h2 className="text-lg font-semibold text-stone-900">New Product</h2>
          <button onClick={onClose} className="rounded-full p-1.5 text-stone-400 hover:bg-stone-100 transition-colors">
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="grid gap-6 p-6 lg:grid-cols-2">

          {/* ── Left: Image ───────────────────────────────────────────────── */}
          <div>
            <label className="mb-2 block text-sm font-medium text-stone-700">Photo</label>

            {/* Empty state */}
            {imageStage === 'empty' && (
              <div className="flex flex-col gap-3 rounded-xl border-2 border-dashed border-stone-200 p-8 text-center">
                <p className="text-sm text-stone-400">Add a photo for this product</p>
                <div className="flex justify-center gap-3">
                  <button
                    onClick={() => setImageStage('camera')}
                    className="flex items-center gap-2 rounded-full border border-stone-300 px-5 py-2.5 text-sm text-stone-600 hover:border-amber-400 hover:text-amber-600 transition-colors"
                  >
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                    Camera
                  </button>
                  <label className="flex cursor-pointer items-center gap-2 rounded-full border border-stone-300 px-5 py-2.5 text-sm text-stone-600 hover:border-amber-400 hover:text-amber-600 transition-colors">
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                    </svg>
                    Upload
                    <input
                      ref={fileInputRef}
                      type="file" accept="image/*" className="hidden"
                      onChange={e => e.target.files?.[0] && handleFileSelect(e.target.files[0])}
                    />
                  </label>
                </div>
              </div>
            )}

            {/* Camera */}
            {imageStage === 'camera' && (
              <CameraCapture
                onCapture={dataUrl => { setFinalImage(dataUrl); setImageStage('done') }}
                onCancel={() => setImageStage('empty')}
              />
            )}

            {/* Photo editor */}
            {imageStage === 'editing' && rawSrc && (
              <PhotoEditor
                src={rawSrc}
                onSave={handlePhotoSaved}
                onCancel={handlePhotoCancel}
              />
            )}

            {/* Final preview */}
            {imageStage === 'done' && finalImage && (
              <div className="flex flex-col gap-3">
                <div className="overflow-hidden rounded-xl border border-stone-200 bg-stone-100">
                  <img src={finalImage} alt="Product" className="w-full h-auto block" />
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => setImageStage('camera')}
                    className="flex-1 rounded-full border border-stone-200 py-2 text-sm text-stone-500 hover:bg-stone-50 transition-colors"
                  >
                    Retake
                  </button>
                  <button
                    onClick={changePhoto}
                    className="flex-1 rounded-full border border-stone-200 py-2 text-sm text-stone-500 hover:bg-stone-50 transition-colors"
                  >
                    Replace
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* ── Right: Form ───────────────────────────────────────────────── */}
          <div className="flex flex-col gap-5">

            {/* Title */}
            <div>
              <label className="mb-1.5 block text-sm font-medium text-stone-700">Title <span className="text-red-400">*</span></label>
              <input
                type="text"
                value={title}
                onChange={e => setTitle(e.target.value)}
                placeholder="e.g. 1/4 Grain Gold Card — Eagle"
                className="w-full rounded-xl border border-stone-200 px-4 py-2.5 text-sm text-stone-900 placeholder-stone-300 focus:border-amber-400 focus:outline-none focus:ring-1 focus:ring-amber-400"
              />
            </div>

            {/* Metal */}
            <div>
              <label className="mb-2 block text-sm font-medium text-stone-700">
                Metal
                <span className="ml-1.5 text-xs font-normal text-stone-400">select all that apply</span>
              </label>
              <div className="flex gap-2">
                {METALS.map(m => {
                  const active = selectedMetals.includes(m.value)
                  return (
                    <button
                      key={m.value}
                      type="button"
                      onClick={() => toggleMetal(m.value)}
                      className={`flex-1 rounded-xl border-2 py-2 text-sm font-medium transition-colors ${
                        active ? m.color + ' border-current' : 'border-stone-200 text-stone-500 hover:border-stone-300'
                      }`}
                    >
                      {m.label}
                    </button>
                  )
                })}
              </div>
              {selectedMetals.length > 1 && (
                <p className="mt-1.5 text-xs text-stone-400">Primary: {selectedMetals[0].charAt(0).toUpperCase() + selectedMetals[0].slice(1)}</p>
              )}
            </div>

            {/* Type */}
            <div>
              <label className="mb-2 block text-sm font-medium text-stone-700">Type</label>
              <div className="flex gap-2">
                {TYPES.map(t => (
                  <button
                    key={t.value}
                    onClick={() => setProductType(t.value)}
                    className={`flex-1 rounded-xl border-2 py-2 text-sm font-medium transition-colors ${
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
                <label className="mb-1.5 block text-sm font-medium text-stone-700">Price ($)</label>
                <input
                  type="number" min="0" step="0.01"
                  value={price}
                  onChange={e => setPrice(e.target.value)}
                  placeholder="14.00"
                  className="w-full rounded-xl border border-stone-200 px-4 py-2.5 text-sm text-stone-900 placeholder-stone-300 focus:border-amber-400 focus:outline-none focus:ring-1 focus:ring-amber-400"
                />
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

            {/* Weight label */}
            <div>
              <label className="mb-1.5 block text-sm font-medium text-stone-700">Weight Label</label>
              <input
                type="text"
                value={weightLabel}
                onChange={e => setWeightLabel(e.target.value)}
                placeholder="e.g. 1/4 grain gold"
                className="w-full rounded-xl border border-stone-200 px-4 py-2.5 text-sm text-stone-900 placeholder-stone-300 focus:border-amber-400 focus:outline-none focus:ring-1 focus:ring-amber-400"
              />
            </div>

            {/* Description */}
            <div>
              <div className="mb-1.5 flex items-center justify-between">
                <label className="text-sm font-medium text-stone-700">Description <span className="text-stone-400 font-normal">(optional)</span></label>
                <button
                  type="button"
                  onClick={generateDescription}
                  disabled={generatingDesc}
                  className="flex items-center gap-1.5 rounded-full border border-stone-200 px-3 py-1 text-xs text-stone-500 hover:border-amber-400 hover:text-amber-600 disabled:opacity-50 transition-colors"
                >
                  {generatingDesc ? (
                    <svg className="h-3 w-3 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
                  ) : (
                    <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
                  )}
                  {generatingDesc ? 'Writing…' : 'AI write'}
                </button>
              </div>
              <textarea
                rows={3}
                value={description}
                onChange={e => setDescription(e.target.value)}
                placeholder="Leave blank for AI to write from the title, or type notes/instructions first…"
                className="w-full resize-none rounded-xl border border-stone-200 px-4 py-2.5 text-sm text-stone-900 placeholder-stone-300 focus:border-amber-400 focus:outline-none focus:ring-1 focus:ring-amber-400"
              />
            </div>

            {/* eBay toggle */}
            <div className="rounded-xl border border-stone-200 bg-stone-50 overflow-hidden">
              <label className="flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-stone-100 transition-colors">
                <input
                  type="checkbox"
                  checked={listOnEbay}
                  onChange={e => setListOnEbay(e.target.checked)}
                  className="h-4 w-4 rounded border-stone-300 accent-amber-500"
                />
                <div>
                  <div className="text-sm font-medium text-stone-700">Also list on eBay</div>
                  <div className="text-xs text-stone-400">Publishes this product to your eBay seller account after saving</div>
                </div>
              </label>
              {listOnEbay && (
                <div className="px-4 pb-3 border-t border-stone-200 pt-3 space-y-3">
                  <div>
                    <label className="mb-1.5 block text-xs font-medium text-stone-600">eBay Quantity</label>
                    <input
                      type="number" min="1"
                      value={ebayQuantity}
                      onChange={e => setEbayQuantity(e.target.value)}
                      className="w-32 rounded-lg border border-stone-300 px-3 py-2 text-sm text-stone-900 focus:border-amber-400 focus:outline-none"
                    />
                    <p className="mt-1 text-xs text-stone-400">Separate from website stock — how many to list on eBay</p>
                  </div>
                  <div>
                    <label className="mb-1.5 block text-xs font-medium text-stone-600">Best Offer Auto-Accept Price ($) <span className="text-stone-400 font-normal">optional</span></label>
                    <input
                      type="number" min="0" step="0.01"
                      value={offerPrice}
                      onChange={e => setOfferPrice(e.target.value)}
                      placeholder="e.g. 12.00"
                      className="w-40 rounded-lg border border-stone-300 px-3 py-2 text-sm text-stone-900 focus:border-amber-400 focus:outline-none"
                    />
                    <p className="mt-1 text-xs text-stone-400">eBay will auto-accept offers at or above this price</p>
                  </div>
                </div>
              )}
            </div>

            {/* Error */}
            {error && (
              <p className="rounded-xl bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-600">{error}</p>
            )}
            {ebayStatus && (
              <p className={`rounded-xl border px-4 py-3 text-sm ${ebayStatus.startsWith('eBay error') ? 'border-red-200 bg-red-50 text-red-600' : 'border-green-200 bg-green-50 text-green-700'}`}>
                {ebayStatus}
              </p>
            )}

            {/* Submit */}
            <button
              onClick={handleSubmit}
              disabled={saving}
              className="mt-auto rounded-full bg-amber-500 py-3 text-sm font-semibold text-white hover:bg-amber-600 disabled:opacity-50 transition-colors"
            >
              {saving ? (ebayStatus || 'Saving…') : 'Save Product'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
