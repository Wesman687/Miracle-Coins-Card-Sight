import { useEffect, useState } from 'react'
import { XMarkIcon } from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'
import { api } from '../lib/api'

interface CoinRecord {
  id: number
  title: string
  description?: string
  shopify_metadata?: {
    storefront?: {
      name?: string
      metal?: 'gold' | 'platinum' | 'silver'
      weightLabel?: string
      description?: string
      badge?: string
      design?: string
      productType?: 'card' | 'bundle'
      features?: string[]
      audience?: string[]
      featured?: boolean
      hidden?: boolean
    }
    ebay?: {
      url?: string
    }
  }
}

export default function StorefrontMetadataModal({
  coin,
  onClose,
  onSuccess,
}: {
  coin: CoinRecord
  onClose: () => void
  onSuccess: () => void
}) {
  const storefront = coin.shopify_metadata?.storefront || {}
  const [form, setForm] = useState({
    name: storefront.name || coin.title || '',
    metal: storefront.metal || 'gold',
    weightLabel: storefront.weightLabel || '',
    description: storefront.description || coin.description || '',
    badge: storefront.badge || '',
    design: storefront.design || coin.title || '',
    productType: storefront.productType || 'card',
    features: (storefront.features || []).join('\n'),
    audience: (storefront.audience || []).join('\n'),
    featured: Boolean(storefront.featured),
    hidden: Boolean(storefront.hidden),
  })
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    document.body.style.overflow = 'hidden'
    return () => {
      document.body.style.overflow = 'unset'
    }
  }, [])

  const updateField = (key: string, value: string | boolean) => {
    setForm((prev) => ({ ...prev, [key]: value }))
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      await api.put(`/storefront/products/${coin.id}/metadata`, {
        ...form,
        features: form.features.split('\n').map((item) => item.trim()).filter(Boolean),
        audience: form.audience.split('\n').map((item) => item.trim()).filter(Boolean),
      })
      toast.success('Storefront metadata updated')
      onSuccess()
    } catch (error) {
      console.error(error)
      toast.error('Failed to update storefront metadata')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
      <div className="max-h-[90vh] w-full max-w-4xl overflow-y-auto rounded-2xl border border-white/10 bg-gray-900 shadow-2xl">
        <div className="sticky top-0 flex items-center justify-between border-b border-white/10 bg-gray-900 px-6 py-4">
          <div>
            <h2 className="text-xl font-semibold text-white">Edit storefront metadata</h2>
            <p className="text-sm text-gray-400">Clean up how this imported product appears on the website.</p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-white">
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        <div className="grid gap-6 p-6 lg:grid-cols-2">
          <div className="space-y-4">
            <label className="block">
              <span className="mb-1 block text-sm text-gray-300">Storefront name</span>
              <input value={form.name} onChange={(e) => updateField('name', e.target.value)} className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-white" />
            </label>
            <label className="block">
              <span className="mb-1 block text-sm text-gray-300">Metal</span>
              <select value={form.metal} onChange={(e) => updateField('metal', e.target.value)} className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-white">
                <option value="gold">Gold</option>
                <option value="platinum">Platinum</option>
                <option value="silver">Silver</option>
              </select>
            </label>
            <label className="block">
              <span className="mb-1 block text-sm text-gray-300">Product type</span>
              <select value={form.productType} onChange={(e) => updateField('productType', e.target.value)} className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-white">
                <option value="card">Card</option>
                <option value="bundle">Bundle</option>
              </select>
            </label>
            <label className="block">
              <span className="mb-1 block text-sm text-gray-300">Weight label</span>
              <input value={form.weightLabel} onChange={(e) => updateField('weightLabel', e.target.value)} className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-white" />
            </label>
            <label className="block">
              <span className="mb-1 block text-sm text-gray-300">Badge</span>
              <input value={form.badge} onChange={(e) => updateField('badge', e.target.value)} className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-white" />
            </label>
            <label className="block">
              <span className="mb-1 block text-sm text-gray-300">Design label</span>
              <input value={form.design} onChange={(e) => updateField('design', e.target.value)} className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-white" />
            </label>
          </div>

          <div className="space-y-4">
            <label className="block">
              <span className="mb-1 block text-sm text-gray-300">Description</span>
              <textarea value={form.description} onChange={(e) => updateField('description', e.target.value)} rows={5} className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-white" />
            </label>
            <label className="block">
              <span className="mb-1 block text-sm text-gray-300">Features (one per line)</span>
              <textarea value={form.features} onChange={(e) => updateField('features', e.target.value)} rows={5} className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-white" />
            </label>
            <label className="block">
              <span className="mb-1 block text-sm text-gray-300">Audience (one per line)</span>
              <textarea value={form.audience} onChange={(e) => updateField('audience', e.target.value)} rows={4} className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-white" />
            </label>
            <div className="grid grid-cols-2 gap-4 rounded-xl border border-white/10 bg-gray-800/60 p-4">
              <label className="flex items-center gap-3 text-sm text-gray-300">
                <input type="checkbox" checked={form.featured} onChange={(e) => updateField('featured', e.target.checked)} />
                Featured on storefront
              </label>
              <label className="flex items-center gap-3 text-sm text-gray-300">
                <input type="checkbox" checked={form.hidden} onChange={(e) => updateField('hidden', e.target.checked)} />
                Hidden from storefront
              </label>
            </div>
            {coin.shopify_metadata?.ebay?.url && (
              <a href={coin.shopify_metadata.ebay.url} target="_blank" rel="noreferrer" className="inline-flex text-sm text-blue-400 no-underline hover:text-blue-300">
                Open linked eBay listing →
              </a>
            )}
          </div>
        </div>

        <div className="flex justify-end gap-3 border-t border-white/10 px-6 py-4">
          <button onClick={onClose} className="rounded-lg border border-gray-700 px-4 py-2 text-gray-300">Cancel</button>
          <button onClick={handleSave} disabled={saving} className="rounded-lg bg-yellow-500 px-4 py-2 font-medium text-black disabled:opacity-60">
            {saving ? 'Saving...' : 'Save storefront metadata'}
          </button>
        </div>
      </div>
    </div>
  )
}
