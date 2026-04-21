import Link from 'next/link'
import { useRouter } from 'next/router'
import { useEffect, useState } from 'react'
import PublicLayout from '../../components/storefront/PublicLayout'
import { getAuth, clearAuth, AuthUser } from '../../lib/auth'

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

const STATUS_LABELS: Record<string, { label: string; color: string }> = {
  paid:      { label: 'Paid',      color: 'text-green-700 bg-green-50 border-green-200' },
  inquiry:   { label: 'Pending',   color: 'text-amber-700 bg-amber-50 border-amber-200' },
  shipped:   { label: 'Shipped',   color: 'text-blue-700 bg-blue-50 border-blue-200' },
  delivered: { label: 'Delivered', color: 'text-green-700 bg-green-50 border-green-200' },
  cancelled: { label: 'Cancelled', color: 'text-red-700 bg-red-50 border-red-200' },
  refunded:  { label: 'Refunded',  color: 'text-stone-600 bg-stone-50 border-stone-200' },
}

export default function AccountPage() {
  const router = useRouter()
  // Use state + useEffect to avoid SSR/client hydration mismatch with localStorage
  const [auth, setAuth] = useState<AuthUser | null>(null)
  const [mounted, setMounted] = useState(false)
  const [orders, setOrders] = useState<Order[]>([])
  const [loadingOrders, setLoadingOrders] = useState(false)

  useEffect(() => {
    const a = getAuth()
    setAuth(a)
    setMounted(true)
    if (!a) { router.replace('/account/login'); return }
    if (a.customerId) {
      setLoadingOrders(true)
      fetch(`${API}/auth/customer/orders/${a.customerId}`, {
        headers: { Authorization: `Bearer ${a.token}` },
      })
        .then(r => r.json())
        .then(d => setOrders(d.orders || []))
        .catch(() => {})
        .finally(() => setLoadingOrders(false))
    }
  }, [])

  function handleLogout() {
    clearAuth()
    router.push('/shop')
  }

  if (!mounted) return null

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
