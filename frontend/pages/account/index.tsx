import Link from 'next/link'
import { useRouter } from 'next/router'
import { useEffect, useState } from 'react'
import PublicLayout from '../../components/storefront/PublicLayout'
import { getAuth, clearAuth, authHeaders, AuthUser, getCustomerId } from '../../lib/auth'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:1270/api/v1'

interface Order {
  id: number
  order_id: string
  product: string
  qty: number
  total: number | null
  channel: string
  status: string
  date: string
}

interface Profile {
  name: string | null
  phone: string | null
  address_line1: string | null
  address_line2: string | null
  city: string | null
  state_province: string | null
  zip_code: string | null
  country: string | null
}

const STATUS_LABELS: Record<string, { label: string; color: string }> = {
  paid:      { label: 'Paid',      color: 'text-green-700 bg-green-50 border-green-200' },
  inquiry:   { label: 'Pending',   color: 'text-amber-700 bg-amber-50 border-amber-200' },
  shipped:   { label: 'Shipped',   color: 'text-blue-700 bg-blue-50 border-blue-200' },
  delivered: { label: 'Delivered', color: 'text-green-700 bg-green-50 border-green-200' },
  cancelled: { label: 'Cancelled', color: 'text-red-700 bg-red-50 border-red-200' },
  refunded:  { label: 'Refunded',  color: 'text-stone-600 bg-stone-50 border-stone-200' },
}

function formatPhone(raw: string): string {
  const digits = raw.replace(/\D/g, '').slice(0, 10)
  if (digits.length <= 3) return digits
  if (digits.length <= 6) return `(${digits.slice(0, 3)}) ${digits.slice(3)}`
  return `(${digits.slice(0, 3)}) ${digits.slice(3, 6)}-${digits.slice(6)}`
}

export default function AccountPage() {
  const router = useRouter()
  const [auth, setAuth] = useState<AuthUser | null>(null)
  const [mounted, setMounted] = useState(false)
  const [orders, setOrders] = useState<Order[]>([])
  const [loadingOrders, setLoadingOrders] = useState(false)

  // Contact info state
  const [profile, setProfile] = useState<Profile | null>(null)
  const [editingContact, setEditingContact] = useState(false)
  const [editName, setEditName] = useState('')
  const [editPhone, setEditPhone] = useState('')
  const [editAddr1, setEditAddr1] = useState('')
  const [editAddr2, setEditAddr2] = useState('')
  const [editCity, setEditCity] = useState('')
  const [editState, setEditState] = useState('')
  const [editZip, setEditZip] = useState('')
  const [editCountry, setEditCountry] = useState('United States')
  const [savingContact, setSavingContact] = useState(false)
  const [contactError, setContactError] = useState('')

  useEffect(() => {
    const a = getAuth()
    setAuth(a)
    setMounted(true)
    if (!a) { router.replace('/account/login'); return }
    const cid = getCustomerId(a)
    if (cid) {
      setLoadingOrders(true)
      fetch(`${API}/auth/customer/orders/${cid}`, {
        headers: { Authorization: `Bearer ${a.token}` },
      })
        .then(r => r.json())
        .then(d => setOrders(d.orders || []))
        .catch(() => {})
        .finally(() => setLoadingOrders(false))

      // Fetch contact profile
      fetch(`${API}/auth/customer/profile/${cid}`, {
        headers: { Authorization: `Bearer ${a.token}` },
      })
        .then(r => r.ok ? r.json() : null)
        .then(data => { if (data) setProfile(data) })
        .catch(() => {})
    }
  }, [])

  function startEdit() {
    if (!profile) return
    setEditName(profile.name || auth?.name || '')
    setEditPhone(profile.phone || '')
    setEditAddr1(profile.address_line1 || '')
    setEditAddr2(profile.address_line2 || '')
    setEditCity(profile.city || '')
    setEditState(profile.state_province || '')
    setEditZip(profile.zip_code || '')
    setEditCountry(profile.country || 'United States')
    setContactError('')
    setEditingContact(true)
  }

  async function saveContact() {
    const cid = auth ? getCustomerId(auth) : undefined
    if (!cid) return
    setSavingContact(true)
    setContactError('')
    try {
      const res = await fetch(`${API}/auth/customer/profile/${cid}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json', ...authHeaders() },
        body: JSON.stringify({
          name: editName.trim() || null,
          phone: editPhone.trim() || null,
          address_line1: editAddr1.trim() || null,
          address_line2: editAddr2.trim() || null,
          city: editCity.trim() || null,
          state_province: editState.trim() || null,
          zip_code: editZip.trim() || null,
          country: editCountry.trim() || null,
        }),
      })
      if (!res.ok) {
        setContactError('Failed to save. Please try again.')
        return
      }
      setProfile({
        name: editName.trim() || null,
        phone: editPhone.trim() || null,
        address_line1: editAddr1.trim() || null,
        address_line2: editAddr2.trim() || null,
        city: editCity.trim() || null,
        state_province: editState.trim() || null,
        zip_code: editZip.trim() || null,
        country: editCountry.trim() || null,
      })
      setEditingContact(false)
    } catch {
      setContactError('Could not connect. Please try again.')
    } finally {
      setSavingContact(false)
    }
  }

  function handleLogout() {
    clearAuth()
    router.push('/shop')
  }

  if (!mounted) return null

  const hasAddress = !!(profile?.address_line1 || profile?.city)
  const hasPhone = !!profile?.phone

  return (
    <PublicLayout title="My Account — Miracle Coins">
      <main className="mx-auto max-w-3xl px-4 py-10 sm:px-6 lg:px-8">
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-stone-900">My Account</h1>
            <p className="mt-1 text-sm text-stone-500">{auth?.email}</p>
          </div>
          <button
            onClick={handleLogout}
            className="rounded-full border border-stone-300 px-4 py-2 text-sm text-stone-600 hover:border-red-300 hover:text-red-500 transition-colors"
          >
            Sign out
          </button>
        </div>

        {/* Welcome card */}
        <div className="mb-8 rounded-2xl border border-amber-100 bg-amber-50 px-6 py-5">
          <p className="font-medium text-amber-800">Welcome back{auth?.name ? `, ${auth.name}` : ''}!</p>
          <p className="mt-1 text-sm text-amber-700">Browse your order history below or continue shopping.</p>
          <Link
            href="/shop"
            className="mt-3 inline-flex rounded-full bg-amber-500 px-5 py-2 text-sm font-semibold text-white no-underline hover:bg-amber-600 transition-colors"
          >
            Browse shop
          </Link>
        </div>

        {/* Contact Information */}
        <div className="mb-8 rounded-2xl border border-stone-200 bg-white overflow-hidden">
          <div className="flex items-center justify-between border-b border-stone-100 bg-stone-50 px-6 py-4">
            <h2 className="text-base font-semibold text-stone-900">Contact Information</h2>
            {!editingContact && (
              <button
                onClick={startEdit}
                className="rounded-full border border-stone-200 px-3 py-1.5 text-xs font-medium text-stone-600 hover:border-amber-300 hover:text-amber-600 transition-colors"
              >
                Edit
              </button>
            )}
          </div>

          {editingContact ? (
            <div className="px-6 py-5 space-y-4">
              <div>
                <label className="mb-1 block text-xs font-medium text-stone-500">Full Name</label>
                <input
                  type="text" value={editName}
                  onChange={e => setEditName(e.target.value)}
                  placeholder="Your name"
                  className="w-full rounded-xl border border-stone-200 px-3 py-2.5 text-sm focus:border-amber-400 focus:outline-none focus:ring-1 focus:ring-amber-400"
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-stone-500">Phone Number</label>
                <input
                  type="tel" value={editPhone}
                  onChange={e => setEditPhone(formatPhone(e.target.value))}
                  placeholder="(555) 000-0000"
                  className="w-full rounded-xl border border-stone-200 px-3 py-2.5 text-sm focus:border-amber-400 focus:outline-none focus:ring-1 focus:ring-amber-400"
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-stone-500">Address Line 1</label>
                <input
                  type="text" value={editAddr1}
                  onChange={e => setEditAddr1(e.target.value)}
                  placeholder="123 Main St"
                  className="w-full rounded-xl border border-stone-200 px-3 py-2.5 text-sm focus:border-amber-400 focus:outline-none focus:ring-1 focus:ring-amber-400"
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-stone-500">Address Line 2 <span className="text-stone-400">(optional)</span></label>
                <input
                  type="text" value={editAddr2}
                  onChange={e => setEditAddr2(e.target.value)}
                  placeholder="Apt, Suite, etc."
                  className="w-full rounded-xl border border-stone-200 px-3 py-2.5 text-sm focus:border-amber-400 focus:outline-none focus:ring-1 focus:ring-amber-400"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="mb-1 block text-xs font-medium text-stone-500">City</label>
                  <input
                    type="text" value={editCity}
                    onChange={e => setEditCity(e.target.value)}
                    placeholder="City"
                    className="w-full rounded-xl border border-stone-200 px-3 py-2.5 text-sm focus:border-amber-400 focus:outline-none focus:ring-1 focus:ring-amber-400"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs font-medium text-stone-500">State / Province</label>
                  <input
                    type="text" value={editState}
                    onChange={e => setEditState(e.target.value)}
                    placeholder="State"
                    className="w-full rounded-xl border border-stone-200 px-3 py-2.5 text-sm focus:border-amber-400 focus:outline-none focus:ring-1 focus:ring-amber-400"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="mb-1 block text-xs font-medium text-stone-500">ZIP / Postal Code</label>
                  <input
                    type="text" value={editZip}
                    onChange={e => setEditZip(e.target.value)}
                    placeholder="ZIP"
                    className="w-full rounded-xl border border-stone-200 px-3 py-2.5 text-sm focus:border-amber-400 focus:outline-none focus:ring-1 focus:ring-amber-400"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs font-medium text-stone-500">Country</label>
                  <input
                    type="text" value={editCountry}
                    onChange={e => setEditCountry(e.target.value)}
                    placeholder="United States"
                    className="w-full rounded-xl border border-stone-200 px-3 py-2.5 text-sm focus:border-amber-400 focus:outline-none focus:ring-1 focus:ring-amber-400"
                  />
                </div>
              </div>
              {contactError && <p className="text-xs text-red-500">{contactError}</p>}
              <div className="flex gap-3 pt-1">
                <button
                  onClick={saveContact} disabled={savingContact}
                  className="flex-1 rounded-full bg-amber-500 py-2.5 text-sm font-bold text-white hover:bg-amber-600 transition-colors disabled:opacity-60"
                >
                  {savingContact ? 'Saving…' : 'Save Changes'}
                </button>
                <button
                  onClick={() => setEditingContact(false)}
                  className="rounded-full border border-stone-200 px-5 py-2.5 text-sm text-stone-600 hover:bg-stone-50 transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <div className="px-6 py-5">
              {(!profile || (!hasPhone && !hasAddress && !profile?.name)) ? (
                <div className="flex items-center justify-between">
                  <p className="text-sm text-stone-400">No contact info saved yet.</p>
                  <button
                    onClick={startEdit}
                    className="rounded-full bg-amber-500 px-4 py-2 text-xs font-bold text-white hover:bg-amber-600 transition-colors"
                  >
                    Add Info
                  </button>
                </div>
              ) : (
                <div className="space-y-3">
                  <div className="flex items-start gap-3">
                    <span className="w-20 flex-shrink-0 text-xs font-medium text-stone-400 pt-0.5">Name</span>
                    <span className="text-sm text-stone-800">{profile?.name || auth?.name || <span className="text-stone-400 italic">Not set</span>}</span>
                  </div>
                  <div className="flex items-start gap-3">
                    <span className="w-20 flex-shrink-0 text-xs font-medium text-stone-400 pt-0.5">Phone</span>
                    <span className="text-sm text-stone-800">
                      {profile?.phone || <span className="text-stone-400 italic">Not set</span>}
                    </span>
                  </div>
                  <div className="flex items-start gap-3">
                    <span className="w-20 flex-shrink-0 text-xs font-medium text-stone-400 pt-0.5">Address</span>
                    <div className="text-sm text-stone-800">
                      {hasAddress ? (
                        <>
                          {profile?.address_line1 && <div>{profile.address_line1}</div>}
                          {profile?.address_line2 && <div>{profile.address_line2}</div>}
                          <div>
                            {[profile?.city, profile?.state_province].filter(Boolean).join(', ')}
                            {profile?.zip_code ? ` ${profile.zip_code}` : ''}
                          </div>
                          {profile?.country && profile.country !== 'United States' && <div>{profile.country}</div>}
                        </>
                      ) : (
                        <span className="text-stone-400 italic">Not set</span>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Order history */}
        <div>
          <h2 className="mb-4 text-lg font-semibold text-stone-900">Order History</h2>
          {loadingOrders ? (
            <div className="py-12 text-center text-sm text-stone-400">Loading orders…</div>
          ) : orders.length === 0 ? (
            <div className="rounded-2xl border border-stone-200 bg-white py-12 text-center text-sm text-stone-400">
              No orders yet.{' '}
              <Link href="/shop" className="text-amber-600 hover:underline">Start shopping →</Link>
            </div>
          ) : (
            <div className="space-y-3">
              {/* Group by order_id */}
              {Object.entries(
                orders.reduce((acc, o) => {
                  const key = o.order_id || String(o.id)
                  if (!acc[key]) acc[key] = []
                  acc[key].push(o)
                  return acc
                }, {} as Record<string, Order[]>)
              ).map(([orderId, items]) => {
                const first = items[0]
                const orderTotal = items.reduce((s, i) => s + (i.total || 0), 0)
                const statusInfo = STATUS_LABELS[first.status] || { label: first.status, color: 'text-stone-600 bg-stone-50 border-stone-200' }
                return (
                  <div key={orderId} className="rounded-2xl border border-stone-200 bg-white overflow-hidden">
                    <div className="flex items-center justify-between border-b border-stone-100 bg-stone-50 px-5 py-3">
                      <div className="flex items-center gap-3">
                        <span className="text-xs text-stone-400 font-mono">{orderId}</span>
                        <span className={`rounded-full border px-2.5 py-0.5 text-xs font-medium ${statusInfo.color}`}>
                          {statusInfo.label}
                        </span>
                        {first.channel === 'inquiry' && (
                          <span className="rounded-full border border-stone-200 bg-white px-2.5 py-0.5 text-xs text-stone-500">Order request</span>
                        )}
                      </div>
                      <span className="text-xs text-stone-400">
                        {first.date ? new Date(first.date).toLocaleDateString() : '—'}
                      </span>
                    </div>
                    <div className="divide-y divide-stone-100">
                      {items.map(item => (
                        <div key={item.id} className="flex items-center justify-between px-5 py-3">
                          <div>
                            <p className="text-sm font-medium text-stone-800">{item.product || '—'}</p>
                            <p className="text-xs text-stone-400">Qty: {item.qty}</p>
                          </div>
                          <span className="text-sm font-semibold text-stone-900">
                            {item.total != null ? `$${item.total.toFixed(2)}` : '—'}
                          </span>
                        </div>
                      ))}
                    </div>
                    {items.length > 1 && (
                      <div className="flex justify-end border-t border-stone-100 px-5 py-2">
                        <span className="text-sm font-bold text-stone-900">Total: ${orderTotal.toFixed(2)}</span>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </main>
    </PublicLayout>
  )
}
