import Link from 'next/link'
import PublicLayout from '../../components/storefront/PublicLayout'

export default function CheckoutCancel() {
  return (
    <PublicLayout title="Checkout Cancelled — Miracle Coins">
      <main className="mx-auto max-w-xl px-4 py-24 text-center sm:px-6">
        <div className="mb-6 flex items-center justify-center">
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-stone-100">
            <svg className="h-8 w-8 text-stone-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
        </div>
        <h1 className="text-3xl font-bold text-stone-900">Checkout cancelled</h1>
        <p className="mt-3 text-stone-500">No charge was made. Your cart is still saved.</p>
        <div className="mt-8 flex flex-wrap justify-center gap-3">
          <Link
            href="/shop"
            className="rounded-full bg-amber-500 px-8 py-3 font-semibold text-white no-underline hover:bg-amber-600 transition-colors"
          >
            Back to Shop
          </Link>
        </div>
      </main>
    </PublicLayout>
  )
}
