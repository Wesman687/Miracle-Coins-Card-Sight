import { useEffect, useState, useCallback } from 'react'
import PublicLayout from '../../components/storefront/PublicLayout'
import { getAuth } from '../../lib/auth'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:1270/api/v1'
function getToken() { return getAuth()?.token || '' }

type OrderRow = {
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

type OrderGroup = {
  key: string
  rows: OrderRow[]
  customer_name: string | null
  customer_email: string | null
  channel: string
  status: string
  total: number
  created_at: string | null
  tracking_number: string | null
  notes: string | null
}

const STATUS_COLORS: Record<string, string> = {
  paid:      'bg-green-100 text-green-700',
  shipped:   'bg-blue-100 text-blue-700',
  delivered: 'bg-purple-100 text-purple-700',
  refunded:  'bg-red-100 text-red-700',
  cancelled: 'bg-stone-100 text-stone-500',
  inquiry:   'bg-amber-100 text-amber-700',
}

const SORT_OPTIONS = [
  { value: 'date_desc',     label: 'Newest first' },
  { value: 'date_asc',      label: 'Oldest first' },
  { value: 'customer_asc',  label: 'Customer A–Z' },
  { value: 'customer_desc', label: 'Customer Z–A' },
  { value: 'price_desc',    label: 'Price high–low' },
  { value: 'price_asc',     label: 'Price low–high' },
  { value: 'status_asc',    label: 'Status A–Z' },
]

function groupOrders(rows: OrderRow[]): OrderGroup[] {
  const map = new Map<string, OrderRow[]>()
  for (const r of rows) {
    const key = r.external_order_id || String(r.id)
    if (!map.has(key)) map.set(key, [])
    map.get(key)!.push(r)
  }
  return Array.from(map.entries()).map(([key, rows]) => {
    const first = rows[0]
    return {
      key,
      rows,
      customer_name: first.customer_name,
      customer_email: first.customer_email,
      channel: first.channel,
      status: first.status,
      total: rows.reduce((s, r) => s + (r.sold_price || 0), 0),
      created_at: first.created_at,
      tracking_number: first.tracking_number,
      notes: first.notes,
    }
  })
}

export default function OrdersPage() {
  const [rows,         setRows]         = useState<OrderRow[]>([])
  const [total,        setTotal]        = useState(0)
  const [loading,      setLoading]      = useState(true)
  const [sort,         setSort]         = useState('date_desc')
  const [statusFilter, setStatusFilter] = useState('')
  const [search,       setSearch]       = useState('')
  const [searchInput,  setSearchInput]  = useState('')
  const [expandedKey,  setExpandedKey]  = useState<string | null>(null)
  const [trackingEdit, setTrackingEdit] = useState<Record<string, string>>({})
  const [notesEdit,    setNotesEdit]    = useState<Record<string, string>>({})
  const [savingKey,    setSavingKey]    = useState<string | null>(null)
  const [deletingKey,  setDeletingKey]  = useState<string | null>(null)
  const [selected,     setSelected]     = useState<Set<string>>(new Set())
  const [bulkDeleting, setBulkDeleting] = useState(false)

  const loadOrders = useCallback(async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams({ sort, limit: '500', offset: '0' })
      if (statusFilter) params.set('status', statusFilter)
      if (search) params.set('search', search)
      const res = await fetch(`${API}/storefront/admin/orders?${params}`, {
        headers: { Authorization: `Bearer ${getToken()}` },
      })
      if (!res.ok) throw new Error('Failed to load orders')
      const data = await res.json()
      setRows(data.orders || [])
      setTotal(data.total || 0)
    } catch (e: any) {
      alert('Error loading orders: ' + e.message)
    } finally {
      setLoading(false)
    }
  }, [sort, statusFilter, search])

  useEffect(() => { loadOrders() }, [loadOrders])

  const groups = groupOrders(rows)

  async function saveTracking(group: OrderGroup) {
    setSavingKey(group.key)
    try {
      const tracking = trackingEdit[group.key] ?? (group.tracking_number || '')
      const notes    = notesEdit[group.key]    ?? (group.notes || '')
      // Apply to all rows in the group
      for (const row of group.rows) {
        await fetch(`${API}/storefront/admin/orders/${row.id}/tracking`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${getToken()}` },
          body: JSON.stringify({ tracking_number: tracking, notes }),
        })
      }
      await loadOrders()
      setExpandedKey(null)
    } catch (e: any) {
      alert('Error: ' + e.message)
    } finally {
      setSavingKey(null)
    }
  }

  async function updateStatus(group: OrderGroup, status: string) {
    try {
      for (const row of group.rows) {
        await fetch(`${API}/storefront/admin/orders/${row.id}/status?status=${encodeURIComponent(status)}`, {
          method: 'PATCH',
          headers: { Authorization: `Bearer ${getToken()}` },
        })
      }
      await loadOrders()
    } catch (e: any) {
      alert('Failed to update status: ' + e.message)
    }
  }

  async function deleteGroup(group: OrderGroup) {
    if (!confirm(`Delete order ${group.key}? This cannot be undone.`)) return
    setDeletingKey(group.key)
    try {
      await fetch(`${API}/storefront/admin/orders/group/${encodeURIComponent(group.key)}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${getToken()}` },
      })
      await loadOrders()
    } catch (e: any) {
      alert('Failed to delete: ' + e.message)
    } finally {
      setDeletingKey(null)
    }
  }

  async function bulkDelete() {
    if (selected.size === 0) return
    if (!confirm(`Delete ${selected.size} order${selected.size !== 1 ? 's' : ''}? This cannot be undone.`)) return
    setBulkDeleting(true)
    try {
      await Promise.all([...selected].map(key =>
        fetch(`${API}/storefront/admin/orders/group/${encodeURIComponent(key)}`, {
          method: 'DELETE',
          headers: { Authorization: `Bearer ${getToken()}` },
        })
      ))
      setSelected(new Set())
      await loadOrders()
    } catch (e: any) {
      alert('Bulk delete failed: ' + e.message)
    } finally {
      setBulkDeleting(false)
    }
  }

  function toggleSelect(key: string) {
    setSelected(prev => {
      const next = new Set(prev)
      next.has(key) ? next.delete(key) : next.add(key)
      return next
    })
  }

  function toggleSelectAll() {
    setSelected(prev => prev.size === groups.length ? new Set() : new Set(groups.map(g => g.key)))
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
            <p className="text-sm text-stone-500 mt-0.5">{groups.length} orders ({total} line items)</p>
          </div>
          <div className="flex items-center gap-3">
            {selected.size > 0 && (
              <button
                onClick={bulkDelete}
                disabled={bulkDeleting}
                className="rounded-full bg-red-500 px-4 py-2 text-sm font-medium text-white hover:bg-red-600 disabled:opacity-50 transition-colors"
              >
                {bulkDeleting ? 'Deleting…' : `Delete ${selected.size} selected`}
              </button>
            )}
            <a href="/manage" className="text-sm text-stone-500 hover:text-amber-600 transition-colors">
              ← Back to products
            </a>
          </div>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap gap-3 items-center">
          <form onSubmit={e => { e.preventDefault(); setSearch(searchInput) }} className="flex gap-2">
            <input
              type="text" value={searchInput} onChange={e => setSearchInput(e.target.value)}
              placeholder="Search email, name, product…"
              className="rounded-lg border border-stone-300 px-3 py-2 text-sm text-stone-800 focus:border-amber-400 focus:outline-none w-56"
            />
            <button type="submit" className="rounded-lg bg-amber-500 px-4 py-2 text-sm font-medium text-white hover:bg-amber-600 transition-colors">
              Search
            </button>
            {search && (
              <button type="button" onClick={() => { setSearch(''); setSearchInput('') }}
                className="rounded-lg border border-stone-300 px-3 py-2 text-sm text-stone-500 hover:border-amber-400 transition-colors">
                Clear
              </button>
            )}
          </form>

          <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)}
            className="rounded-lg border border-stone-300 px-3 py-2 text-sm text-stone-700 focus:border-amber-400 focus:outline-none">
            <option value="">All statuses</option>
            <option value="inquiry">Inquiry (pending)</option>
            <option value="paid">Paid</option>
            <option value="shipped">Shipped</option>
            <option value="delivered">Delivered</option>
            <option value="refunded">Refunded</option>
            <option value="cancelled">Cancelled</option>
          </select>

          <select value={sort} onChange={e => setSort(e.target.value)}
            className="rounded-lg border border-stone-300 px-3 py-2 text-sm text-stone-700 focus:border-amber-400 focus:outline-none">
            {SORT_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
        </div>

        {/* Groups */}
        {loading ? (
          <div className="space-y-2">
            {[...Array(5)].map((_, i) => <div key={i} className="animate-pulse h-16 rounded-xl bg-stone-100" />)}
          </div>
        ) : groups.length === 0 ? (
          <div className="rounded-xl border border-stone-200 bg-white p-12 text-center text-stone-400">No orders found.</div>
        ) : (
          <div className="space-y-2">
            {/* Select-all row */}
            <div className="flex items-center gap-3 px-2 py-1">
              <input
                type="checkbox"
                checked={groups.length > 0 && selected.size === groups.length}
                onChange={toggleSelectAll}
                className="h-4 w-4 rounded border-stone-300 text-amber-500 focus:ring-amber-400"
              />
              <span className="text-xs text-stone-400">
                {selected.size > 0 ? `${selected.size} of ${groups.length} selected` : `Select all ${groups.length}`}
              </span>
            </div>

            {groups.map(group => (
              <div key={group.key} className={`rounded-xl border bg-white overflow-hidden transition-colors ${selected.has(group.key) ? 'border-amber-300 bg-amber-50/30' : 'border-stone-200'}`}>
                {/* Group header row */}
                <div
                  className="flex items-center gap-4 px-5 py-4 cursor-pointer hover:bg-stone-50 transition-colors"
                  onClick={() => setExpandedKey(expandedKey === group.key ? null : group.key)}
                >
                  <input
                    type="checkbox"
                    checked={selected.has(group.key)}
                    onChange={e => { e.stopPropagation(); toggleSelect(group.key) }}
                    onClick={e => e.stopPropagation()}
                    className="h-4 w-4 flex-shrink-0 rounded border-stone-300 text-amber-500 focus:ring-amber-400"
                  />
                  <div className="flex-1 min-w-0 grid grid-cols-4 gap-4 items-center">
                    <div>
                      <div className="font-medium text-stone-800 text-sm">{group.customer_name || '—'}</div>
                      <div className="text-xs text-stone-400 truncate">{group.customer_email || '—'}</div>
                    </div>
                    <div className="text-sm text-stone-600">
                      {group.rows.length === 1
                        ? group.rows[0].product_name || '—'
                        : `${group.rows.length} items`}
                      <div className="text-xs text-stone-400">
                        {group.rows.length > 1 && group.rows.map(r => r.product_name).filter(Boolean).join(', ')}
                      </div>
                    </div>
                    <div className="text-sm font-semibold text-stone-900">
                      {group.total > 0 ? `$${group.total.toFixed(2)}` : '—'}
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_COLORS[group.status] || 'bg-stone-100 text-stone-500'}`}>
                        {group.status}
                      </span>
                      {group.channel === 'inquiry' && (
                        <span className="rounded-full border border-stone-200 px-2 py-0.5 text-xs text-stone-400">request</span>
                      )}
                    </div>
                  </div>
                  <div className="text-xs text-stone-400 whitespace-nowrap">{fmtDate(group.created_at)}</div>
                  <button
                    onClick={e => { e.stopPropagation(); deleteGroup(group) }}
                    disabled={deletingKey === group.key}
                    className="rounded-full p-1.5 text-stone-300 hover:bg-red-50 hover:text-red-400 transition-colors disabled:opacity-40"
                    title="Delete order"
                  >
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                  <svg className={`h-4 w-4 text-stone-400 transition-transform flex-shrink-0 ${expandedKey === group.key ? 'rotate-180' : ''}`}
                    fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </div>

                {/* Expanded detail */}
                {expandedKey === group.key && (
                  <div className="border-t border-stone-100 bg-stone-50 px-5 py-5 space-y-5">
                    {/* Items */}
                    {group.rows.length > 1 && (
                      <div>
                        <p className="text-xs font-semibold text-stone-500 uppercase tracking-wider mb-2">Items</p>
                        <div className="rounded-lg border border-stone-200 bg-white divide-y divide-stone-100">
                          {group.rows.map(r => (
                            <div key={r.id} className="flex items-center justify-between px-4 py-2.5 text-sm">
                              <span className="text-stone-700">{r.product_name || '—'} <span className="text-stone-400">×{r.qty}</span></span>
                              <span className="font-medium text-stone-800">{r.sold_price != null ? `$${r.sold_price.toFixed(2)}` : '—'}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 max-w-2xl">
                      {/* Order details */}
                      <div className="space-y-2 text-sm">
                        <h3 className="font-semibold text-stone-700">Order Details</h3>
                        <div className="text-stone-500">
                          <span className="text-stone-400">Order ID: </span>
                          <span className="font-mono text-xs">{group.key}</span>
                        </div>
                        <div className="text-stone-500">
                          <span className="text-stone-400">Channel: </span>{group.channel}
                        </div>
                        <div className="mt-3">
                          <label className="block text-xs font-medium text-stone-500 mb-1">Status</label>
                          <select
                            value={group.status}
                            onChange={e => updateStatus(group, e.target.value)}
                            onClick={e => e.stopPropagation()}
                            className="rounded-lg border border-stone-300 px-3 py-1.5 text-sm text-stone-700 focus:border-amber-400 focus:outline-none"
                          >
                            <option value="inquiry">Inquiry (pending)</option>
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
                            value={trackingEdit[group.key] ?? (group.tracking_number || '')}
                            onChange={e => setTrackingEdit(p => ({ ...p, [group.key]: e.target.value }))}
                            onClick={e => e.stopPropagation()}
                            placeholder="Enter tracking number…"
                            className="w-full rounded-lg border border-stone-300 px-3 py-2 text-sm font-mono focus:border-amber-400 focus:outline-none"
                          />
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-stone-500 mb-1">Notes</label>
                          <textarea
                            value={notesEdit[group.key] ?? (group.notes || '')}
                            onChange={e => setNotesEdit(p => ({ ...p, [group.key]: e.target.value }))}
                            onClick={e => e.stopPropagation()}
                            rows={2}
                            placeholder="Internal notes…"
                            className="w-full rounded-lg border border-stone-300 px-3 py-2 text-sm focus:border-amber-400 focus:outline-none resize-none"
                          />
                        </div>
                        <div className="flex gap-2">
                          <button
                            onClick={e => { e.stopPropagation(); saveTracking(group) }}
                            disabled={savingKey === group.key}
                            className="rounded-lg bg-amber-500 px-4 py-2 text-sm font-medium text-white hover:bg-amber-600 disabled:opacity-50 transition-colors"
                          >
                            {savingKey === group.key ? 'Saving…' : 'Save'}
                          </button>
                          <button
                            onClick={e => { e.stopPropagation(); deleteGroup(group) }}
                            disabled={deletingKey === group.key}
                            className="rounded-lg border border-red-200 px-4 py-2 text-sm font-medium text-red-500 hover:bg-red-50 disabled:opacity-50 transition-colors"
                          >
                            Delete order
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </main>
    </PublicLayout>
  )
}
