import Link from 'next/link'
import { useEffect, useState } from 'react'
import PublicLayout from '../../components/storefront/PublicLayout'
import { getAuth } from '../../lib/auth'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:1270/api/v1'
function getToken() { return getAuth()?.token || 'manage-token' }

interface MetalOption  { value: string; label: string; basePrice?: number; offerPrice?: number }
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

  const [metalEdits,    setMetalEdits]    = useState<Record<string, { label: string; basePrice: string; offerPrice: string }>>({})
  const [newMetalLabel, setNewMetalLabel] = useState('')
  const [newMetalPrice, setNewMetalPrice] = useState('')
  const [newMetalOffer, setNewMetalOffer] = useState('')
  const [newTypeLabel,  setNewTypeLabel]  = useState('')

  const [discountEdits, setDiscountEdits] = useState<{ minTotal: string; pct: string }[]>([])
  const [newMin, setNewMin] = useState('')
  const [newPct, setNewPct] = useState('')

  const [testMode, setTestMode]       = useState(false)
  const [inquiryMode, setInquiryMode] = useState(false)

  useEffect(() => {
    fetch(`${API}/storefront/options`)
      .then(r => r.json())
      .then(data => {
        if (data.metals?.length)    setMetals(data.metals)
        if (data.types?.length)     setTypes(data.types)
        if (data.discounts?.length) setDiscounts(data.discounts)
        if (typeof data.test_mode === 'boolean') setTestMode(data.test_mode)
        if (typeof data.inquiry_mode === 'boolean') setInquiryMode(data.inquiry_mode)
      })
      .catch(() => {})
  }, [])

  useEffect(() => {
    const edits: Record<string, { label: string; basePrice: string; offerPrice: string }> = {}
    metals.forEach(m => {
      edits[m.value] = {
        label:      metalEdits[m.value]?.label      || m.label,
        basePrice:  metalEdits[m.value]?.basePrice  || (m.basePrice  != null ? String(m.basePrice)  : ''),
        offerPrice: metalEdits[m.value]?.offerPrice || (m.offerPrice != null ? String(m.offerPrice) : ''),
      }
    })
    setMetalEdits(edits)
  }, [metals])

  useEffect(() => {
    setDiscountEdits(discounts.map((d, i) => ({
      minTotal: discountEdits[i]?.minTotal || String(d.minTotal),
      pct:      discountEdits[i]?.pct      || String(d.pct),
    })))
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [discounts])

  async function persist(
    nextMetals: MetalOption[], nextTypes: TypeOption[], nextDiscounts: DiscountTier[],
    nextTestMode?: boolean, nextInquiryMode?: boolean,
  ) {
    setSaving(true); setSaved(false)
    try {
      await fetch(`${API}/storefront/options`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${getToken()}` },
        body: JSON.stringify({
          metals: nextMetals, types: nextTypes, discounts: nextDiscounts,
          test_mode: nextTestMode ?? testMode,
          inquiry_mode: nextInquiryMode ?? inquiryMode,
        }),
      })
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } catch {}
    setSaving(false)
  }

  async function toggleTestMode() {
    const next = !testMode
    setTestMode(next)
    await persist(metals, types, discounts, next)
  }

  async function toggleInquiryMode() {
    const next = !inquiryMode
    setInquiryMode(next)
    await persist(metals, types, discounts, undefined, next)
  }

  function saveMetalEdits() {
    const next = metals.map(m => ({
      ...m,
      label:      metalEdits[m.value]?.label      || m.label,
      basePrice:  metalEdits[m.value]?.basePrice  ? parseFloat(metalEdits[m.value].basePrice)  : m.basePrice,
      offerPrice: metalEdits[m.value]?.offerPrice ? parseFloat(metalEdits[m.value].offerPrice) : m.offerPrice,
    }))
    setMetals(next)
    persist(next, types, discounts)
  }

  function addMetal() {
    const label = newMetalLabel.trim(); if (!label) return
    const value = label.toLowerCase().replace(/\s+/g, '-')
    if (metals.some(m => m.value === value)) return
    const next = [...metals, {
      value, label,
      basePrice:  newMetalPrice ? parseFloat(newMetalPrice) : undefined,
      offerPrice: newMetalOffer ? parseFloat(newMetalOffer) : undefined,
    }]
    setMetals(next); persist(next, types, discounts)
    setNewMetalLabel(''); setNewMetalPrice(''); setNewMetalOffer('')
  }

  function removeMetal(value: string) {
    const next = metals.filter(m => m.value !== value)
    setMetals(next); persist(next, types, discounts)
  }

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

          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm text-stone-500">Spend</span>
            <div className="flex items-center rounded-xl border border-stone-200 bg-stone-50 overflow-hidden w-28">
              <span className="pl-3 text-sm text-stone-400">$</span>
              <input type="number" min="1" step="1" value={newMin} onChange={e => setNewMin(e.target.value)} placeholder="50"
                className="w-full px-2 py-2 text-sm bg-transparent focus:outline-none" />
            </div>
            <span className="text-sm text-stone-500">or more →</span>
            <div className="flex items-center rounded-xl border border-stone-200 bg-stone-50 overflow-hidden w-24">
              <input type="number" min="1" max="99" step="0.5" value={newPct} onChange={e => setNewPct(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && addDiscount()} placeholder="10"
                className="w-full px-2 py-2 text-sm bg-transparent focus:outline-none text-right" />
              <span className="pr-2 text-sm text-stone-400">%</span>
            </div>
            <span className="text-sm text-stone-500">off</span>
            <button onClick={addDiscount} className="rounded-xl bg-amber-500 px-4 py-2 text-sm font-medium text-white hover:bg-amber-600 transition-colors">Add</button>
          </div>
          <p className="mt-2 text-xs text-stone-400">e.g. Spend $100 or more → 10% off the entire order</p>
        </section>

        {/* ── Metal Types ──────────────────────────────────────────────────── */}
        <section className="rounded-2xl border border-stone-200 bg-white p-6">
          <h2 className="mb-1 text-base font-semibold text-stone-900">Metal Types</h2>
          <p className="mb-1 text-sm text-stone-400">Set pricing defaults per metal. New products will use these automatically.</p>
          <div className="mb-4 grid grid-cols-3 gap-2 text-xs font-medium text-stone-400 uppercase tracking-wider px-3">
            <span>Metal</span>
            <span>Price</span>
            <span>Min. Offer (eBay)</span>
          </div>

          <div className="space-y-2 mb-5">
            {metals.map(m => (
              <div key={m.value} className="grid grid-cols-3 gap-2 items-center rounded-xl border border-stone-200 bg-stone-50 p-3">
                <input
                  type="text"
                  value={metalEdits[m.value]?.label ?? m.label}
                  onChange={e => setMetalEdits(prev => ({ ...prev, [m.value]: { ...prev[m.value], label: e.target.value } }))}
                  className="rounded-lg border border-stone-200 bg-white px-3 py-1.5 text-sm focus:border-amber-400 focus:outline-none focus:ring-1 focus:ring-amber-400"
                />
                <div className="flex items-center rounded-lg border border-stone-200 bg-white overflow-hidden">
                  <span className="pl-3 text-sm text-stone-400">$</span>
                  <input
                    type="number" min="0" step="0.01"
                    value={metalEdits[m.value]?.basePrice ?? ''}
                    onChange={e => setMetalEdits(prev => ({ ...prev, [m.value]: { ...prev[m.value], basePrice: e.target.value } }))}
                    placeholder="—"
                    className="w-full px-2 py-1.5 text-sm focus:outline-none"
                  />
                </div>
                <div className="flex items-center gap-2">
                  <div className="flex items-center rounded-lg border border-stone-200 bg-white overflow-hidden flex-1">
                    <span className="pl-3 text-sm text-stone-400">$</span>
                    <input
                      type="number" min="0" step="0.01"
                      value={metalEdits[m.value]?.offerPrice ?? ''}
                      onChange={e => setMetalEdits(prev => ({ ...prev, [m.value]: { ...prev[m.value], offerPrice: e.target.value } }))}
                      placeholder="—"
                      className="w-full px-2 py-1.5 text-sm focus:outline-none"
                    />
                  </div>
                  <button onClick={() => removeMetal(m.value)} className="text-stone-300 hover:text-red-400 rounded-lg p-1 transition-colors flex-shrink-0">
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </div>
            ))}
          </div>

          <button onClick={saveMetalEdits} disabled={saving} className="mb-6 rounded-full bg-amber-500 px-5 py-2 text-sm font-medium text-white hover:bg-amber-600 disabled:opacity-50 transition-colors">
            {saving ? 'Saving…' : 'Save changes'}
          </button>

          <div className="border-t border-stone-100 pt-5">
            <p className="mb-3 text-xs font-medium text-stone-500 uppercase tracking-wider">Add a new metal type</p>
            <div className="flex gap-2 flex-wrap">
              <input type="text" value={newMetalLabel} onChange={e => setNewMetalLabel(e.target.value)} placeholder="Label (e.g. Rose Gold)"
                className="flex-1 min-w-32 rounded-xl border border-stone-200 px-3 py-2 text-sm focus:border-amber-400 focus:outline-none focus:ring-1 focus:ring-amber-400" />
              <div className="flex items-center rounded-xl border border-stone-200 bg-white overflow-hidden w-28">
                <span className="pl-3 text-sm text-stone-400">$</span>
                <input type="number" min="0" step="0.01" value={newMetalPrice} onChange={e => setNewMetalPrice(e.target.value)} placeholder="Price"
                  className="w-full px-2 py-2 text-sm focus:outline-none" />
              </div>
              <div className="flex items-center rounded-xl border border-stone-200 bg-white overflow-hidden w-32">
                <span className="pl-3 text-sm text-stone-400">$</span>
                <input type="number" min="0" step="0.01" value={newMetalOffer} onChange={e => setNewMetalOffer(e.target.value)} placeholder="Min. offer"
                  className="w-full px-2 py-2 text-sm focus:outline-none" />
              </div>
              <button onClick={addMetal} className="rounded-xl bg-stone-800 px-4 py-2 text-sm font-medium text-white hover:bg-stone-700 transition-colors">Add</button>
            </div>
          </div>
        </section>

        {/* ── Developer / Test Mode ───────────────────────────────────────── */}
        <section className="rounded-2xl border border-stone-200 bg-white p-6">
          <h2 className="mb-1 text-base font-semibold text-stone-900">Developer Settings</h2>
          <p className="mb-5 text-sm text-stone-400">Use test Stripe keys to run through the checkout flow without charging real cards.</p>

          <div className="flex items-center justify-between rounded-xl border border-stone-200 bg-stone-50 px-4 py-3">
            <div>
              <p className="text-sm font-medium text-stone-800">Stripe Test Mode</p>
              <p className="text-xs text-stone-400 mt-0.5">
                {testMode
                  ? 'Active — checkout uses STRIPE_TEST_SECRET_KEY. Use card 4242 4242 4242 4242.'
                  : 'Inactive — checkout uses live Stripe keys.'}
              </p>
            </div>
            <button
              onClick={toggleTestMode}
              disabled={saving}
              className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none disabled:opacity-50 ${testMode ? 'bg-amber-500' : 'bg-stone-300'}`}
            >
              <span className={`pointer-events-none inline-block h-5 w-5 rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${testMode ? 'translate-x-5' : 'translate-x-0'}`} />
            </button>
          </div>

          {testMode && (
            <div className="mt-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3">
              <p className="text-sm font-semibold text-amber-800">Test mode is ON</p>
              <p className="text-xs text-amber-700 mt-1">Real payments are disabled. Use Stripe test card: <span className="font-mono font-semibold">4242 4242 4242 4242</span>, any future expiry, any CVC.</p>
            </div>
          )}

          <div className="mt-3 flex items-center justify-between rounded-xl border border-stone-200 bg-stone-50 px-4 py-3">
            <div>
              <p className="text-sm font-medium text-stone-800">Inquiry Mode</p>
              <p className="text-xs text-stone-400 mt-0.5">
                {inquiryMode
                  ? 'Active — customers submit order requests instead of paying. You receive a Discord notification.'
                  : 'Inactive — customers pay through Stripe normally.'}
              </p>
            </div>
            <button
              onClick={toggleInquiryMode}
              disabled={saving}
              className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none disabled:opacity-50 ${inquiryMode ? 'bg-amber-500' : 'bg-stone-300'}`}
            >
              <span className={`pointer-events-none inline-block h-5 w-5 rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${inquiryMode ? 'translate-x-5' : 'translate-x-0'}`} />
            </button>
          </div>

          {inquiryMode && (
            <div className="mt-3 rounded-xl border border-blue-200 bg-blue-50 px-4 py-3">
              <p className="text-sm font-semibold text-blue-800">Inquiry mode is ON</p>
              <p className="text-xs text-blue-700 mt-1">Customers will see a contact form at checkout instead of Stripe. You&apos;ll get a Discord message with their cart and contact info. Admins still use Stripe.</p>
            </div>
          )}
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
