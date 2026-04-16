import Link from 'next/link'
import { useEffect, useState } from 'react'
import PublicLayout from '../../components/storefront/PublicLayout'
import { getAuth } from '../../lib/auth'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:1270/api/v1'
function getToken() { return getAuth()?.token || 'manage-token' }

interface MetalOption  { value: string; label: string; basePrice?: number }
interface TypeOption   { value: string; label: string }
interface DiscountTier { minTotal: number; pct: number }

const DEFAULT_METALS: MetalOption[] = [
  { value: 'gold',     label: 'Gold' },
  { value: 'platinum', label: 'Platinum' },
  { value: 'silver',   label: 'Silver' },
]
const DEFAULT_TYPES: TypeOption[] = [
  { value: 'card',   label: 'Card' },
  { value: 'bundle', label: 'Kit / Set' },
]

export default function CatalogOptionsPage() {
  const [metals,    setMetals]    = useState<MetalOption[]>(DEFAULT_METALS)
  const [types,     setTypes]     = useState<TypeOption[]>(DEFAULT_TYPES)
  const [discounts, setDiscounts] = useState<DiscountTier[]>([])
  const [saving,    setSaving]    = useState(false)
  const [saved,     setSaved]     = useState(false)

  const [metalEdits,    setMetalEdits]    = useState<Record<string, { label: string; basePrice: string }>>({})
  const [newMetalLabel, setNewMetalLabel] = useState('')
  const [newMetalPrice, setNewMetalPrice] = useState('')
  const [newTypeLabel,  setNewTypeLabel]  = useState('')

  // Discount edit state (controlled inputs, parallel to discounts)
  const [discountEdits, setDiscountEdits] = useState<{ minTotal: string; pct: string }[]>([])

  // New discount form
  const [newMin, setNewMin] = useState('')
  const [newPct, setNewPct] = useState('')

  useEffect(() => {
    fetch(`${API}/storefront/options`)
      .then(r => r.json())
      .then(data => {
        if (data.metals?.length)    setMetals(data.metals)
        if (data.types?.length)     setTypes(data.types)
        if (data.discounts?.length) setDiscounts(data.discounts)
      })
      .catch(() => {})
  }, [])

  useEffect(() => {
    const edits: Record<string, { label: string; basePrice: string }> = {}
    metals.forEach(m => {
      edits[m.value] = {
        label:     metalEdits[m.value]?.label     || m.label,
        basePrice: metalEdits[m.value]?.basePrice || (m.basePrice != null ? String(m.basePrice) : ''),
      }
    })
    setMetalEdits(edits)
  }, [metals])

  // Keep discountEdits in sync when discounts array changes (add/remove)
  useEffect(() => {
    setDiscountEdits(discounts.map((d, i) => ({
      minTotal: discountEdits[i]?.minTotal || String(d.minTotal),
      pct:      discountEdits[i]?.pct      || String(d.pct),
    })))
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [discounts])

  async function persist(nextMetals: MetalOption[], nextTypes: TypeOption[], nextDiscounts: DiscountTier[]) {
    setSaving(true); setSaved(false)
    try {
      await fetch(`${API}/storefront/options`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${getToken()}` },
        body: JSON.stringify({ metals: nextMetals, types: nextTypes, discounts: nextDiscounts }),
      })
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } catch {}
    setSaving(false)
  }

  // ── Metals ────────────────────────────────────────────────────────────────

  function saveMetalEdits() {
    const next = metals.map(m => ({
      ...m,
      label:     metalEdits[m.value]?.label     || m.label,
      basePrice: metalEdits[m.value]?.basePrice ? parseFloat(metalEdits[m.value].basePrice) : m.basePrice,
    }))
    setMetals(next)
    persist(next, types, discounts)
  }

  function addMetal() {
    const label = newMetalLabel.trim(); if (!label) return
    const value = label.toLowerCase().replace(/\s+/g, '-')
    if (metals.some(m => m.value === value)) return
    const next = [...metals, { value, label, basePrice: newMetalPrice ? parseFloat(newMetalPrice) : undefined }]
    setMetals(next); persist(next, types, discounts)
    setNewMetalLabel(''); setNewMetalPrice('')
  }

  function removeMetal(value: string) {
    const next = metals.filter(m => m.value !== value)
    setMetals(next); persist(next, types, discounts)
  }

  // ── Types ─────────────────────────────────────────────────────────────────

  function addType() {
    const label = newTypeLabel.trim(); if (!label) return
    const value = label.toLowerCase().replace(/\s+/g, '-')
    if (types.some(t => t.value === value)) return
    const next = [...types, { value, label }]
    setTypes(next); persist(metals, next, discounts)
    setNewTypeLabel('')
  }

  function removeType(value: string) {
    const next = types.filter(t => t.value !== value)
    setTypes(next); persist(metals, next, discounts)
  }

  // ── Discounts ─────────────────────────────────────────────────────────────

  function saveDiscountEdits() {
    const next = discountEdits
      .map(e => ({ minTotal: parseFloat(e.minTotal), pct: parseFloat(e.pct) }))
      .filter(d => !isNaN(d.minTotal) && !isNaN(d.pct) && d.minTotal > 0 && d.pct > 0 && d.pct < 100)
      .sort((a, b) => a.minTotal - b.minTotal)
    setDiscounts(next)
    persist(metals, types, next)
  }

  function addDiscount() {
    const minTotal = parseFloat(newMin)
    const pct      = parseFloat(newPct)
    if (!minTotal || !pct || minTotal <= 0 || pct <= 0 || pct >= 100) return
    const next = [...discounts.filter(d => d.minTotal !== minTotal), { minTotal, pct }]
      .sort((a, b) => a.minTotal - b.minTotal)
    setDiscounts(next); persist(metals, types, next)
    setNewMin(''); setNewPct('')
  }

  function removeDiscount(minTotal: number) {
    const next = discounts.filter(d => d.minTotal !== minTotal)
    setDiscounts(next); persist(metals, types, next)
  }

  return (
    <PublicLayout title="Catalog Settings — Miracle Coins">
      <main className="mx-auto max-w-3xl px-4 py-10 sm:px-6 lg:px-8 space-y-8">

        <div className="flex items-center gap-4 flex-wrap">
          <Link href="/manage" className="text-sm text-stone-400 no-underline hover:text-stone-600">← Back to Manage</Link>
          <h1 className="text-2xl font-bold text-stone-900">Catalog Settings</h1>
          {saved && <span className="text-sm font-medium text-green-600">Saved!</span>}
        </div>

        {/* ── Order Discounts ──────────────────────────────────────────────── */}
        <section className="rounded-2xl border border-stone-200 bg-white p-6">
          <h2 className="mb-1 text-base font-semibold text-stone-900">Order Discounts</h2>
          <p className="mb-5 text-sm text-stone-400">
            Automatically discount the total order when a customer's cart reaches a spending threshold.
            Applied at checkout via Stripe — works across any mix of products.
          </p>

          {discounts.length === 0 ? (
            <p className="mb-5 text-sm text-stone-300">No discounts set yet.</p>
          ) : (
            <div className="mb-4 space-y-2">
              {discounts.map((d, i) => (
                <div key={i} className="flex items-center gap-3 rounded-xl border border-stone-200 bg-stone-50 px-4 py-3">
                  <div className="flex items-center gap-1.5 flex-1">
                    <span className="text-sm text-stone-500">Spend</span>
                    <div className="flex items-center rounded-lg border border-stone-200 bg-white overflow-hidden w-28">
                      <span className="pl-2 text-sm text-stone-400">$</span>
                      <input
                        type="number" min="1" step="1"
                        value={discountEdits[i]?.minTotal ?? ''}
                        onChange={e => setDiscountEdits(prev => prev.map((x, j) => j === i ? { ...x, minTotal: e.target.value } : x))}
                        className="w-full px-2 py-1.5 text-sm bg-transparent focus:outline-none"
                      />
                    </div>
                    <span className="text-sm text-stone-500">or more →</span>
                    <div className="flex items-center rounded-lg border border-stone-200 bg-white overflow-hidden w-24">
                      <input
                        type="number" min="1" max="99" step="0.5"
                        value={discountEdits[i]?.pct ?? ''}
                        onChange={e => setDiscountEdits(prev => prev.map((x, j) => j === i ? { ...x, pct: e.target.value } : x))}
                        className="w-full px-2 py-1.5 text-sm bg-transparent focus:outline-none text-right"
                      />
                      <span className="pr-2 text-sm text-stone-400">%</span>
                    </div>
                    <span className="text-sm font-medium text-green-700">off</span>
                  </div>
                  <button onClick={() => removeDiscount(d.minTotal)} className="text-stone-300 hover:text-red-400 transition-colors flex-shrink-0">
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              ))}
              <button onClick={saveDiscountEdits} disabled={saving} className="rounded-full bg-amber-500 px-5 py-2 text-sm font-medium text-white hover:bg-amber-600 disabled:opacity-50 transition-colors">
                {saving ? 'Saving…' : 'Save changes'}
              </button>
            </div>
          )}

          {/* Add discount */}
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm text-stone-500">Spend</span>
            <div className="flex items-center rounded-xl border border-stone-200 bg-stone-50 overflow-hidden w-28">
              <span className="pl-3 text-sm text-stone-400">$</span>
              <input
                type="number" min="1" step="1"
                value={newMin}
                onChange={e => setNewMin(e.target.value)}
                placeholder="50"
                className="w-full px-2 py-2 text-sm bg-transparent focus:outline-none"
              />
            </div>
            <span className="text-sm text-stone-500">or more →</span>
            <div className="flex items-center rounded-xl border border-stone-200 bg-stone-50 overflow-hidden w-24">
              <input
                type="number" min="1" max="99" step="0.5"
                value={newPct}
                onChange={e => setNewPct(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && addDiscount()}
                placeholder="10"
                className="w-full px-2 py-2 text-sm bg-transparent focus:outline-none text-right"
              />
              <span className="pr-2 text-sm text-stone-400">%</span>
            </div>
            <span className="text-sm text-stone-500">off</span>
            <button
              onClick={addDiscount}
              className="rounded-xl bg-amber-500 px-4 py-2 text-sm font-medium text-white hover:bg-amber-600 transition-colors"
            >
              Add
            </button>
          </div>
          <p className="mt-2 text-xs text-stone-400">e.g. Spend $100 or more → 10% off the entire order</p>
        </section>

        {/* ── Metal Types ──────────────────────────────────────────────────── */}
        <section className="rounded-2xl border border-stone-200 bg-white p-6">
          <h2 className="mb-1 text-base font-semibold text-stone-900">Metal Types</h2>
          <p className="mb-5 text-sm text-stone-400">Set a base price per metal — products default to this when the metal is selected in the editor.</p>

          <div className="space-y-3 mb-5">
            {metals.map(m => (
              <div key={m.value} className="flex items-center gap-3 rounded-xl border border-stone-200 bg-stone-50 p-3">
                <input
                  type="text"
                  value={metalEdits[m.value]?.label ?? m.label}
                  onChange={e => setMetalEdits(prev => ({ ...prev, [m.value]: { ...prev[m.value], label: e.target.value } }))}
                  className="flex-1 rounded-lg border border-stone-200 bg-white px-3 py-1.5 text-sm focus:border-amber-400 focus:outline-none focus:ring-1 focus:ring-amber-400"
                />
                <div className="flex items-center rounded-lg border border-stone-200 bg-white overflow-hidden w-28">
                  <span className="pl-3 text-sm text-stone-400">$</span>
                  <input
                    type="number" min="0" step="0.01"
                    value={metalEdits[m.value]?.basePrice ?? ''}
                    onChange={e => setMetalEdits(prev => ({ ...prev, [m.value]: { ...prev[m.value], basePrice: e.target.value } }))}
                    placeholder="Base price"
                    className="w-full px-2 py-1.5 text-sm focus:outline-none"
                  />
                </div>
                <button onClick={() => removeMetal(m.value)} className="text-stone-300 hover:bg-red-50 hover:text-red-400 rounded-lg p-1.5 transition-colors">
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            ))}
          </div>

          <button onClick={saveMetalEdits} disabled={saving} className="mb-6 rounded-full bg-amber-500 px-5 py-2 text-sm font-medium text-white hover:bg-amber-600 disabled:opacity-50 transition-colors">
            {saving ? 'Saving…' : 'Save changes'}
          </button>

          <div className="border-t border-stone-100 pt-5">
            <p className="mb-3 text-xs font-medium text-stone-500 uppercase tracking-wider">Add a new metal type</p>
            <div className="flex gap-2">
              <input type="text" value={newMetalLabel} onChange={e => setNewMetalLabel(e.target.value)} placeholder="Label (e.g. Rose Gold)"
                className="flex-1 rounded-xl border border-stone-200 px-3 py-2 text-sm focus:border-amber-400 focus:outline-none focus:ring-1 focus:ring-amber-400" />
              <div className="flex items-center rounded-xl border border-stone-200 bg-white overflow-hidden w-28">
                <span className="pl-3 text-sm text-stone-400">$</span>
                <input type="number" min="0" step="0.01" value={newMetalPrice} onChange={e => setNewMetalPrice(e.target.value)} placeholder="Price"
                  className="w-full px-2 py-2 text-sm focus:outline-none" />
              </div>
              <button onClick={addMetal} className="rounded-xl bg-stone-800 px-4 py-2 text-sm font-medium text-white hover:bg-stone-700 transition-colors">Add</button>
            </div>
          </div>
        </section>

        {/* ── Product Types ────────────────────────────────────────────────── */}
        <section className="rounded-2xl border border-stone-200 bg-white p-6">
          <h2 className="mb-1 text-base font-semibold text-stone-900">Product Types</h2>
          <p className="mb-5 text-sm text-stone-400">Categories that appear in filters and on product cards.</p>

          <div className="flex flex-wrap gap-2 mb-5">
            {types.map(t => (
              <div key={t.value} className="flex items-center gap-1.5 rounded-full border border-stone-200 bg-stone-50 pl-4 pr-2 py-1.5">
                <span className="text-sm text-stone-700">{t.label}</span>
                <button onClick={() => removeType(t.value)} className="rounded-full p-0.5 text-stone-300 hover:bg-red-50 hover:text-red-400 transition-colors">
                  <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            ))}
          </div>

          <div className="flex gap-2">
            <input type="text" value={newTypeLabel} onChange={e => setNewTypeLabel(e.target.value)} onKeyDown={e => e.key === 'Enter' && addType()} placeholder="New type (e.g. Coin, Bar)"
              className="flex-1 rounded-xl border border-stone-200 px-3 py-2 text-sm focus:border-amber-400 focus:outline-none focus:ring-1 focus:ring-amber-400" />
            <button onClick={addType} className="rounded-xl bg-stone-800 px-4 py-2 text-sm font-medium text-white hover:bg-stone-700 transition-colors">Add</button>
          </div>
        </section>

      </main>
    </PublicLayout>
  )
}
