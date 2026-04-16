import Link from 'next/link'
import { useRouter } from 'next/router'
import { useEffect, useState } from 'react'
import PublicLayout from '../../components/storefront/PublicLayout'
import { getAuth, clearAuth } from '../../lib/auth'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:1270/api/v1'

interface Order {
  id: number
  order_id: string
  product: string
  qty: number
  total: number
  date: string
}

export default function AccountPage() {
  const router = useRouter()
  const auth = typeof window !== 'undefined' ? getAuth() : null
  const [orders, setOrders] = useState<Order[]>([])
  const [loadingOrders, setLoadingOrders] = useState(false)

  useEffect(() => {
    if (!auth) { router.replace('/account/login'); return }
    if (auth.customerId) {
      setLoadingOrders(true)
      fetch(`${API}/auth/customer/orders/${auth.customerId}`, {
        headers: { Authorization: `Bearer ${auth.token}` },
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

  if (!auth) return null

  return (
    <PublicLayout title="My Account — Miracle Coins">
      <main className="mx-auto max-w-3xl px-4 py-10 sm:px-6 lg:px-8">
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-stone-900">My Account</h1>
            <p className="mt-1 text-sm text-stone-500">{auth.email}</p>
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
          <p className="font-medium text-amber-800">Welcome back{auth.name ? `, ${auth.name}` : ''}!</p>
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
            <div className="overflow-hidden rounded-2xl border border-stone-200 bg-white">
              <table className="w-full text-sm">
                <thead className="border-b border-stone-100 bg-stone-50 text-xs uppercase tracking-wider text-stone-400">
                  <tr>
                    <th className="px-5 py-3 text-left">Product</th>
                    <th className="px-5 py-3 text-left">Qty</th>
                    <th className="px-5 py-3 text-left">Total</th>
                    <th className="px-5 py-3 text-left">Date</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-stone-100">
                  {orders.map(order => (
                    <tr key={order.id}>
                      <td className="px-5 py-3 text-stone-800">{order.product || '—'}</td>
                      <td className="px-5 py-3 text-stone-600">{order.qty}</td>
                      <td className="px-5 py-3 font-medium text-stone-900">${order.total.toFixed(2)}</td>
                      <td className="px-5 py-3 text-stone-400">
                        {order.date ? new Date(order.date).toLocaleDateString() : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>
    </PublicLayout>
  )
}
