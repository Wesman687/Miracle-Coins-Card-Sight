import Link from 'next/link'
import { useEffect } from 'react'
import PublicLayout from '../../components/storefront/PublicLayout'
import { useCart } from '../../lib/cart'

export default function CheckoutSuccess() {
  const { clearCart } = useCart()

  useEffect(() => {
    clearCart()
  }, [])

  return (
    <PublicLayout title="Order Confirmed — Miracle Coins">
      <main className="mx-auto max-w-xl px-4 py-24 text-center sm:px-6">
        <div className="mb-6 flex items-center justify-center">
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-green-100">
            <svg className="h-8 w-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
        </div>
        <h1 className="text-3xl font-bold text-stone-900">Order confirmed!</h1>
        <p className="mt-3 text-stone-500">Thank you for your purchase. You'll receive an email confirmation shortly.</p>
        <Link
          href="/shop"
          className="mt-8 inline-flex rounded-full bg-amber-500 px-8 py-3 font-semibold text-white no-underline hover:bg-amber-600 transition-colors"
        >
          Continue Shopping
        </Link>
      </main>
    </PublicLayout>
  )
}
