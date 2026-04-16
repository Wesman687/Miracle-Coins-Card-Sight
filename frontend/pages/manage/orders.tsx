import { useEffect, useState, useCallback } from 'react'
import PublicLayout from '../../components/storefront/PublicLayout'
import { getAuth } from '../../lib/auth'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:1270/api/v1'
function getToken() { return getAuth()?.token || '' }

type Order = {
  id: number
  external_order_id: string | null
  customer_id: number | null
  customer_email: string | null
  customer_name: string | null
  coin_id: number | null
  product_name: string | null
  qty: number
  sold_price: number | null
  channel: string
  status: string
  tracking_number: string | null
  notes: string | null
  created_at: string | null
  updated_at: string | null
}

const STATUS_COLORS: Record<string, string> = {
  paid: 'bg-green-100 text-green-700',
  shipped: 'bg-blue-100 text-blue-700',
  delivered: 'bg-purple-100 text-purple-700',
  refunded: 'bg-red-100 text-red-700',
  cancelled: 'bg-stone-100 text-stone-500',
}

const SORT_OPTIONS = [
  { value: 'date_desc', label: 'Newest first' },
  { value: 'date_asc', label: 'Oldest first' },
  { value: 'customer_asc', label: 'Customer A–Z' },
  { value: 'customer_desc', label: 'Customer Z–A' },
  { value: 'price_desc', label: 'Price high–low' },
  { value: 'price_asc', label: 'Price low–high' },
  { value: 'status_asc', label: 'Status A–Z' },
]

export default function OrdersPage() {
  const [orders, setOrders] = useState<Order[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [sort, setSort] = useState('date_desc')
  const [statusFilter, setStatusFilter] = useState('')
  const [search, setSearch] = useState('')
  const [searchInput, setSearchInput] = useState('')
  const [expandedId, setExpandedId] = useState<number | null>(null)
  const [trackingEdits, setTrackingEdits] = useState<Record<number, string>>({})
  const [notesEdits, setNotesEdits] = useState<Record<number, string>>({})
  const [savingId, setSavingId] = useState<number | null>(null)

  const loadOrders = useCallback(async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams({ sort, limit: '200', offset: '0' })
      if (statusFilter) params.set('status', statusFilter)
      if (search) params.set('search', search)
      const res = await fetch(`${API}/storefront/admin/orders?${params}`, {
        headers: { Authorization: `Bearer ${getToken()}` },
      })
      if (!res.ok) throw new Error('Failed to load orders')
      const data = await res.json()
      setOrders(data.orders || [])
      setTotal(data.total || 0)
    } catch (e: any) {
      alert('Error loading orders: ' + e.message)
    } finally {
      setLoading(false)
    }
  }, [sort, statusFilter, search])

  useEffect(() => { loadOrders() }, [loadOrders])

  async function saveTracking(order: Order) {
    setSavingId(order.id)
    try {
      const tracking = trackingEdits[order.id] ?? (order.tracking_number || '')
      const notes = notesEdits[order.id] ?? (order.notes || '')
      const res = await fetch(`${API}/storefront/admin/orders/${order.id}/tracking`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${getToken()}` },
        body: JSON.stringify({ tracking_number: tracking, notes }),
      })
      if (!res.ok) throw new Error('Save failed')
      await loadOrders()
      setExpandedId(null)
    } catch (e: any) {
      alert('Error: ' + e.message)
    } finally {
      setSavingId(null)
    }
  }

  async function updateStatus(orderId: number, status: string) {
    try {
      const res = await fetch(`${API}/storefront/admin/orders/${orderId}/status?status=${encodeURIComponent(status)}`, {
        method: 'PATCH',
        headers: { Authorization: `Bearer ${getToken()}` },
      })
      if (!res.ok) throw new Error(`${res.status}`)
      await loadOrders()
    } catch (e: any) {
      alert('Failed to update status: ' + e.message)
    }
  }

  function fmtDate(iso: string | null) {
    if (!iso) return '—'
    return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' })
  }

  return (
    <PublicLayout title="Orders — Miracle Coins">
      <main className="mx-auto max-w-6xl px-4 py-10 sm:px-6 lg:px-8 space-y-6">

        {/* Header */}
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div>
            <h1 className="text-2xl font-bold text-stone-800">Orders</h1>
            <p className="text-sm text-stone-500 mt-0.5">{total} total</p>
          </div>
          <a
            href="/manage"
            className="text-sm text-stone-500 hover:text-amber-600 transition-colors"
          >
            ← Back to products
          </a>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap gap-3 items-center">
          <form
            onSubmit={e => { e.preventDefault(); setSearch(searchInput) }}
            className="flex gap-2"
          >
            <input
              type="text"
              value={searchInput}
              onChange={e => setSearchInput(e.target.value)}
              placeholder="Search email, name, product…"
              className="rounded-lg border border-stone-300 px-3 py-2 text-sm text-stone-800 focus:border-amber-400 focus:outline-none w-56"
            />
            <button
              type="submit"
              className="rounded-lg bg-amber-500 px-4 py-2 text-sm font-medium text-white hover:bg-amber-600 transition-colors"
            >
              Search
            </button>
            {search && (
              <button
                type="button"
                onClick={() => { setSearch(''); setSearchInput('') }}
                className="rounded-lg border border-stone-300 px-3 py-2 text-sm text-stone-500 hover:border-amber-400 transition-colors"
              >
                Clear
              </button>
            )}
          </form>

          <select
            value={statusFilter}
            onChange={e => setStatusFilter(e.target.value)}
            className="rounded-lg border border-stone-300 px-3 py-2 text-sm text-stone-700 focus:border-amber-400 focus:outline-none"
          >
            <option value="">All statuses</option>
            <option value="paid">Paid</option>
            <option value="shipped">Shipped</option>
            <option value="delivered">Delivered</option>
            <option value="refunded">Refunded</option>
            <option value="cancelled">Cancelled</option>
          </select>

          <select
            value={sort}
            onChange={e => setSort(e.target.value)}
            className="rounded-lg border border-stone-300 px-3 py-2 text-sm text-stone-700 focus:border-amber-400 focus:outline-none"
          >
            {SORT_OPTIONS.map(o => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </select>
        </div>

        {/* Table */}
        {loading ? (
          <div className="space-y-2">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="animate-pulse h-16 rounded-xl bg-stone-100" />
            ))}
          </div>
        ) : orders.length === 0 ? (
          <div className="rounded-xl border border-stone-200 bg-white p-12 text-center text-stone-400">
            No orders found.
          </div>
        ) : (
          <div className="rounded-xl border border-stone-200 bg-white overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-stone-50 border-b border-stone-200">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-stone-500 uppercase tracking-wider">Date</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-stone-500 uppercase tracking-wider">Customer</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-stone-500 uppercase tracking-wider">Product</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-stone-500 uppercase tracking-wider">Total</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-stone-500 uppercase tracking-wider">Status</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-stone-500 uppercase tracking-wider">Tracking</th>
                  <th className="px-4 py-3" />
                </tr>
              </thead>
              <tbody className="divide-y divide-stone-100">
                {orders.map(order => (
                  <>
                    <tr
                      key={order.id}
                      className="hover:bg-stone-50 transition-colors cursor-pointer"
                      onClick={() => setExpandedId(expandedId === order.id ? null : order.id)}
                    >
                      <td className="px-4 py-3 text-stone-500 whitespace-nowrap">{fmtDate(order.created_at)}</td>
                      <td className="px-4 py-3">
                        <div className="font-medium text-stone-800">{order.customer_name || '—'}</div>
                        <div className="text-xs text-stone-400">{order.customer_email || '—'}</div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="text-stone-700">{order.product_name || '—'}</div>
                        <div className="text-xs text-stone-400">qty {order.qty}</div>
                      </td>
                      <td className="px-4 py-3 font-medium text-stone-800">
                        {order.sold_price != null ? `$${order.sold_price.toFixed(2)}` : '—'}
                      </td>
                      <td className="px-4 py-3">
                        <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_COLORS[order.status] || 'bg-stone-100 text-stone-500'}`}>
                          {order.status}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-stone-500">
                        {order.tracking_number
                          ? <span className="font-mono text-xs text-blue-600">{order.tracking_number}</span>
                          : <span className="text-stone-300">—</span>}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <svg
                          className={`h-4 w-4 text-stone-400 inline transition-transform ${expandedId === order.id ? 'rotate-180' : ''}`}
                          fill="none" viewBox="0 0 24 24" stroke="currentColor"
                        >
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                      </td>
                    </tr>

                    {expandedId === order.id && (
                      <tr key={`${order.id}-detail`}>
                        <td colSpan={7} className="px-6 py-5 bg-stone-50 border-b border-stone-200">
                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 max-w-2xl">

                            {/* Order details */}
                            <div className="space-y-2 text-sm">
                              <h3 className="font-semibold text-stone-700">Order Details</h3>
                              <div className="text-stone-500">
                                <span className="text-stone-400">Stripe ID: </span>
                                <span className="font-mono text-xs">{order.external_order_id || '—'}</span>
                              </div>
                              <div className="text-stone-500">
                                <span className="text-stone-400">Channel: </span>{order.channel}
                              </div>
                              <div className="text-stone-500">
                                <span className="text-stone-400">Updated: </span>{fmtDate(order.updated_at)}
                              </div>
                              <div className="mt-3">
                                <label className="block text-xs font-medium text-stone-500 mb-1">Status</label>
                                <select
                                  value={order.status}
                                  onChange={e => updateStatus(order.id, e.target.value)}
                                  onClick={e => e.stopPropagation()}
                                  className="rounded-lg border border-stone-300 px-3 py-1.5 text-sm text-stone-700 focus:border-amber-400 focus:outline-none"
                                >
                                  <option value="paid">Paid</option>
                                  <option value="shipped">Shipped</option>
                                  <option value="delivered">Delivered</option>
                                  <option value="refunded">Refunded</option>
                                  <option value="cancelled">Cancelled</option>
                                </select>
                              </div>
                            </div>

                            {/* Tracking + notes */}
                            <div className="space-y-3 text-sm">
                              <h3 className="font-semibold text-stone-700">Tracking</h3>
                              <div>
                                <label className="block text-xs font-medium text-stone-500 mb-1">Tracking Number</label>
                                <input
                                  type="text"
                                  value={trackingEdits[order.id] ?? (order.tracking_number || '')}
                                  onChange={e => setTrackingEdits(prev => ({ ...prev, [order.id]: e.target.value }))}
                                  onClick={e => e.stopPropagation()}
                                  placeholder="Enter tracking number…"
                                  className="w-full rounded-lg border border-stone-300 px-3 py-2 text-sm text-stone-800 font-mono focus:border-amber-400 focus:outline-none"
                                />
                              </div>
                              <div>
                                <label className="block text-xs font-medium text-stone-500 mb-1">Notes</label>
                                <textarea
                                  value={notesEdits[order.id] ?? (order.notes || '')}
                                  onChange={e => setNotesEdits(prev => ({ ...prev, [order.id]: e.target.value }))}
                                  onClick={e => e.stopPropagation()}
                                  rows={2}
                                  placeholder="Internal notes…"
                                  className="w-full rounded-lg border border-stone-300 px-3 py-2 text-sm text-stone-800 focus:border-amber-400 focus:outline-none resize-none"
                                />
                              </div>
                              <button
                                onClick={e => { e.stopPropagation(); saveTracking(order) }}
                                disabled={savingId === order.id}
                                className="rounded-lg bg-amber-500 px-4 py-2 text-sm font-medium text-white hover:bg-amber-600 disabled:opacity-50 transition-colors"
                              >
                                {savingId === order.id ? 'Saving…' : 'Save'}
                              </button>
                            </div>

                          </div>
                        </td>
                      </tr>
                    )}
                  </>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </PublicLayout>
  )
}
