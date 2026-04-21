import { useEffect, useRef, useState } from 'react'
import { useCart } from '../../lib/cart'
import { isAdmin as checkAdmin } from '../../lib/auth'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:1270/api/v1'
const FRONTEND_BASE = process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:8100'

interface DiscountTier { minTotal: number; pct: number }

interface Props {
  open: boolean
  onClose: () => void
}

export default function CartDrawer({ open, onClose }: Props) {
  const { items, count, total, removeItem, updateQty, clearCart } = useCart()
  const [discounts, setDiscounts]     = useState<DiscountTier[]>([])
  const [inquiryMode, setInquiryMode] = useState(false)
  const [admin, setAdmin]             = useState(false)
  const loadedRef = useRef(false)

  // Inquiry form state
  const [inquiryName,  setInquiryName]  = useState('')
  const [inquiryEmail, setInquiryEmail] = useState('')
  const [inquiryPhone, setInquiryPhone] = useState('')
  const [inquiryNote,  setInquiryNote]  = useState('')
  const [inquirySent,  setInquirySent]  = useState(false)
  const [inquiryError, setInquiryError] = useState('')
  const [submitting,   setSubmitting]   = useState(false)

  useEffect(() => { setAdmin(checkAdmin()) }, [])

  useEffect(() => {
    if (loadedRef.current) return
    loadedRef.current = true
    fetch(`${API}/storefront/options`)
      .then(r => r.json())
      .then(data => {
        if (data.discounts?.length) setDiscounts(data.discounts)
        if (typeof data.inquiry_mode === 'boolean') setInquiryMode(data.inquiry_mode)
      })
      .catch(() => {})
  }, [])

  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [onClose])

  useEffect(() => {
    document.body.style.overflow = open ? 'hidden' : ''
    return () => { document.body.style.overflow = '' }
  }, [open])

  async function handleInquiry() {
    if (!inquiryName.trim() || !inquiryEmail.trim()) {
      setInquiryError('Please enter your name and email.')
      return
    }
    setSubmitting(true)
    setInquiryError('')
    try {
      const res = await fetch(`${API}/storefront/checkout/inquiry`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          items: items.map(i => ({ product_id: i.productId, qty: i.qty })),
          name: inquiryName.trim(),
          email: inquiryEmail.trim(),
          phone: inquiryPhone.trim() || null,
          note: inquiryNote.trim() || null,
        }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        setInquiryError(err.detail || 'Something went wrong. Please try again.')
        return
      }
      setInquirySent(true)
      clearCart()
    } catch {
      setInquiryError('Could not send request. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  async function handleCheckout() {
    try {
      const res = await fetch(`${API}/storefront/checkout/session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          items: items.map(i => ({ product_id: i.productId, qty: i.qty })),
          success_url: `${FRONTEND_BASE}/checkout/success?session_id={CHECKOUT_SESSION_ID}`,
          cancel_url: `${FRONTEND_BASE}/checkout/cancel`,
        }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        alert(err.detail || 'Checkout failed. Please try again.')
        return
      }
      const { url } = await res.json()
      window.location.href = url
    } catch {
      alert('Could not connect to checkout. Please try again.')
    }
  }

  return (
    <>
      {/* Backdrop */}
      <div
        className={`fixed inset-0 bg-black/60 transition-opacity duration-300 ${open ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}
        style={{ zIndex: 9998 }}
        onClick={onClose}
      />

      {/* Drawer */}
      <div
        className={`fixed top-0 right-0 h-screen w-96 max-w-full bg-white flex flex-col border-l-2 border-stone-200 transition-transform duration-300 ease-in-out ${open ? 'translate-x-0' : 'translate-x-full'}`}
        style={{ zIndex: 9999, boxShadow: '-12px 0 48px rgba(0,0,0,0.35)' }}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-stone-200 bg-white px-6 py-5">
          <div className="flex items-center gap-3">
            <h2 className="text-lg font-bold text-stone-900">Your Cart</h2>
            {count > 0 && (
              <span className="rounded-full bg-amber-500 px-2.5 py-0.5 text-xs font-bold text-white">
                {count}
              </span>
            )}
          </div>
          <button
            onClick={onClose}
            className="rounded-full p-2 text-stone-400 hover:bg-stone-100 hover:text-stone-600 transition-colors"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Items */}
        <div className="min-h-0 flex-1 overflow-y-auto bg-stone-50 px-6 py-5">
          {items.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full gap-4 text-stone-400">
              <svg className="h-14 w-14 opacity-25" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
              <p className="text-sm font-medium">Your cart is empty</p>
            </div>
          ) : (
            <ul className="space-y-3">
              {items.map(item => (
                <li key={item.productId} className="flex gap-4 rounded-2xl border border-stone-200 bg-white p-4 shadow-sm">
                  {/* Image */}
                  <div className="h-20 w-20 flex-shrink-0 overflow-hidden rounded-xl border border-stone-100 bg-stone-50">
                    {item.image
                      ? <img src={item.image} alt={item.name} className="h-full w-full object-cover" />
                      : <div className="flex h-full w-full items-center justify-center text-stone-300 text-xs">No img</div>
                    }
                  </div>

                  {/* Info */}
                  <div className="flex min-w-0 flex-1 flex-col gap-2">
                    <div className="flex items-start justify-between gap-2">
                      <p className="text-sm font-semibold text-stone-900 leading-snug line-clamp-2">{item.name}</p>
                      <button
                        onClick={() => removeItem(item.productId)}
                        className="flex-shrink-0 rounded-full p-1 text-stone-300 hover:bg-red-50 hover:text-red-400 transition-colors"
                      >
                        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>
                    <p className="text-xs text-stone-400 capitalize">{item.metal}</p>
                    <div className="flex items-center justify-between gap-2">
                      {/* Qty controls */}
                      <div className="flex items-center overflow-hidden rounded-lg border border-stone-200 bg-stone-50">
                        <button
                          onClick={() => updateQty(item.productId, item.qty - 1)}
                          className="px-2.5 py-1.5 text-stone-500 hover:bg-stone-100 text-sm font-medium transition-colors"
                        >−</button>
                        <span className="min-w-[2rem] px-1 py-1.5 text-center text-sm font-medium text-stone-800">{item.qty}</span>
                        <button
                          onClick={() => updateQty(item.productId, item.qty + 1)}
                          className="px-2.5 py-1.5 text-stone-500 hover:bg-stone-100 text-sm font-medium transition-colors"
                        >+</button>
                      </div>
                      <span className="text-sm font-bold text-stone-900">
                        ${(item.priceValue * item.qty).toFixed(2)}
                      </span>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Footer */}
        {(items.length > 0 || inquirySent) && (
          <div className="border-t border-stone-200 bg-white px-6 py-5 space-y-4">

            {inquirySent ? (
              <div className="flex flex-col items-center gap-3 py-4 text-center">
                <div className="rounded-full bg-green-100 p-3">
                  <svg className="h-6 w-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <p className="text-base font-semibold text-stone-900">Request sent!</p>
                <p className="text-sm text-stone-500">We&apos;ll reach out shortly to arrange your order.</p>
                <button onClick={onClose} className="mt-1 rounded-full bg-amber-500 px-6 py-2.5 text-sm font-bold text-white hover:bg-amber-600 transition-colors">
                  Close
                </button>
              </div>
            ) : inquiryMode && !admin ? (
              <>
                {/* Inquiry form */}
                <div className="flex items-center justify-between">
                  <span className="text-sm text-stone-500">Subtotal ({count} item{count !== 1 ? 's' : ''})</span>
                  <span className="text-xl font-bold text-stone-900">${total.toFixed(2)}</span>
                </div>
                <p className="text-xs text-stone-400 -mt-2">Leave your details and we&apos;ll be in touch to complete the order.</p>
                <div className="space-y-2">
                  <input
                    type="text" placeholder="Your name *" value={inquiryName}
                    onChange={e => setInquiryName(e.target.value)}
                    className="w-full rounded-xl border border-stone-200 px-3 py-2.5 text-sm focus:border-amber-400 focus:outline-none focus:ring-1 focus:ring-amber-400"
                  />
                  <input
                    type="email" placeholder="Email address *" value={inquiryEmail}
                    onChange={e => setInquiryEmail(e.target.value)}
                    className="w-full rounded-xl border border-stone-200 px-3 py-2.5 text-sm focus:border-amber-400 focus:outline-none focus:ring-1 focus:ring-amber-400"
                  />
                  <input
                    type="tel" placeholder="Phone (optional)" value={inquiryPhone}
                    onChange={e => setInquiryPhone(e.target.value)}
                    className="w-full rounded-xl border border-stone-200 px-3 py-2.5 text-sm focus:border-amber-400 focus:outline-none focus:ring-1 focus:ring-amber-400"
                  />
                  <textarea
                    placeholder="Any notes? (optional)" value={inquiryNote}
                    onChange={e => setInquiryNote(e.target.value)} rows={2}
                    className="w-full rounded-xl border border-stone-200 px-3 py-2.5 text-sm focus:border-amber-400 focus:outline-none focus:ring-1 focus:ring-amber-400 resize-none"
                  />
                </div>
                {inquiryError && <p className="text-xs text-red-500">{inquiryError}</p>}
                <button
                  onClick={handleInquiry} disabled={submitting}
                  className="w-full rounded-full bg-amber-500 py-3.5 text-sm font-bold text-white hover:bg-amber-600 active:bg-amber-700 transition-colors shadow-md disabled:opacity-60"
                >
                  {submitting ? 'Sending…' : 'Send Order Request →'}
                </button>
                <button onClick={clearCart} className="w-full text-center text-xs text-stone-400 hover:text-red-400 transition-colors">
                  Clear cart
                </button>
              </>
            ) : (
              <>
                {/* Discount progress banner */}
                {(() => {
                  if (!discounts.length) return null
                  const sorted = [...discounts].sort((a, b) => a.minTotal - b.minTotal)
                  const applied = [...sorted].reverse().find(d => total >= d.minTotal)
                  const next = sorted.find(d => total < d.minTotal)
                  if (applied) {
                    const savings = (total * applied.pct / 100)
                    return (
                      <div className="rounded-xl bg-green-50 border border-green-200 px-4 py-3 text-center">
                        <p className="text-sm font-semibold text-green-700">{applied.pct}% discount applied at checkout</p>
                        <p className="text-xs text-green-600 mt-0.5">You save ~${savings.toFixed(2)} on this order</p>
                      </div>
                    )
                  }
                  if (next) {
                    const needed = (next.minTotal - total).toFixed(2)
                    return (
                      <div className="rounded-xl bg-amber-50 border border-amber-200 px-4 py-3 text-center">
                        <p className="text-sm font-medium text-amber-700">
                          Spend <span className="font-bold">${needed}</span> more for <span className="font-bold">{next.pct}% off</span> your order
                        </p>
                      </div>
                    )
                  }
                  return null
                })()}
                <div className="flex items-center justify-between">
                  <span className="text-sm text-stone-500">Subtotal ({count} item{count !== 1 ? 's' : ''})</span>
                  <span className="text-xl font-bold text-stone-900">${total.toFixed(2)}</span>
                </div>
                <button
                  onClick={handleCheckout}
                  className="w-full rounded-full bg-amber-500 py-3.5 text-sm font-bold text-white hover:bg-amber-600 active:bg-amber-700 transition-colors shadow-md"
                >
                  Checkout with Stripe →
                </button>
                <button
                  onClick={clearCart}
                  className="w-full text-center text-xs text-stone-400 hover:text-red-400 transition-colors"
                >
                  Clear cart
                </button>
              </>
            )}
          </div>
        )}
      </div>
    </>
  )
}
