import { useRouter } from 'next/router'
import { useEffect, useMemo, useState } from 'react'
import PublicLayout from '../components/storefront/PublicLayout'
import ProductCard from '../components/storefront/ProductCard'
import EditProductModal from '../components/storefront/EditProductModal'
import { StoreProduct } from '../data/storefront'
import { fetchStorefrontProducts } from '../lib/storefront'
import { isAdmin as checkAdmin, getAuth } from '../lib/auth'

type EditableProduct = {
  id: number
  slug: string
  name: string
  metal: string
  productType: string
  price: string
  image: string | null
  buyUrl: string | null
  quantity: number
}

export default function ShopPage() {
  const router = useRouter()
  const metal = typeof router.query.metal === 'string' ? router.query.metal : undefined
  const typeFilter = typeof router.query.type === 'string' ? router.query.type : undefined
  const kitsOnly = typeFilter === 'kits'

  const [products, setProducts] = useState<StoreProduct[]>([])
  const [loading, setLoading] = useState(true)
  const [admin, setAdmin] = useState(false)
  const [editProduct, setEditProduct] = useState<EditableProduct | null>(null)

  useEffect(() => { setAdmin(checkAdmin()) }, [])

  useEffect(() => {
    setLoading(true)
    fetchStorefrontProducts(metal).then((p) => {
      setProducts(p)
      setLoading(false)
    })
  }, [metal])

  function reload() {
    fetchStorefrontProducts(metal).then(setProducts)
  }

  function toEditable(p: StoreProduct): EditableProduct | null {
    if (!p.id) return null
    return {
      id: p.id,
      slug: p.slug,
      name: p.name,
      metal: p.metal,
      productType: p.productType,
      price: p.price,
      image: p.image || p.images?.[0] || null,
      buyUrl: null,
      quantity: 1,
    }
  }

  const [search, setSearch] = useState('')

  const filtered = useMemo(() => {
    if (!search.trim()) return products
    const q = search.toLowerCase()
    return products.filter(p =>
      p.name?.toLowerCase().includes(q) ||
      p.metal?.toLowerCase().includes(q) ||
      p.description?.toLowerCase().includes(q) ||
      p.weightLabel?.toLowerCase().includes(q)
    )
  }, [products, search])

  const kits = useMemo(() => filtered.filter((p) => p.productType === 'bundle'), [filtered])
  const cards = useMemo(() => filtered.filter((p) => p.productType !== 'bundle'), [filtered])

  const displayed = kitsOnly ? kits : filtered

  let pageTitle = 'All Products'
  if (kitsOnly) pageTitle = 'Kits & Sets'
  else if (metal) pageTitle = `${metal.charAt(0).toUpperCase()}${metal.slice(1)} Cards`

  const subtitle = loading
    ? 'Loading…'
    : kitsOnly
    ? `${kits.length} kits and sets`
    : `${cards.length} cards · ${kits.length} kits`

  return (
    <PublicLayout title={`${pageTitle} — Miracle Coins`} description="Real precious metal collectible cards and kits.">
      <main className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-3xl font-bold text-stone-900">{pageTitle}</h1>
              <p className="mt-1 text-sm text-stone-400">{subtitle}</p>
            </div>
            {admin && (
              <a
                href="/manage"
                className="rounded-full border border-amber-400 bg-amber-50 px-4 py-2 text-sm font-medium text-amber-700 no-underline hover:bg-amber-100 transition-colors"
              >
                Manage catalog →
              </a>
            )}
          </div>
          <div className="relative max-w-sm">
            <svg className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-stone-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-4.35-4.35M17 11A6 6 0 115 11a6 6 0 0112 0z" />
            </svg>
            <input
              type="text"
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Search cards, metals…"
              className="w-full rounded-full border border-stone-200 bg-white pl-9 pr-4 py-2.5 text-sm text-stone-800 placeholder-stone-400 focus:border-amber-400 focus:outline-none focus:ring-1 focus:ring-amber-400 shadow-sm"
            />
            {search && (
              <button
                onClick={() => setSearch('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-stone-400 hover:text-stone-600"
              >
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>
        </div>

        {loading ? (
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="animate-pulse rounded-2xl border border-stone-200 bg-white h-80" />
            ))}
          </div>
        ) : kitsOnly ? (
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {kits.map((p) => (
              <ProductCard
                key={p.id ?? p.slug}
                product={p}
                isAdmin={admin}
                onEdit={() => { const e = toEditable(p); if (e) setEditProduct(e) }}
              />
            ))}
            {kits.length === 0 && <div className="col-span-3 py-20 text-center text-stone-400">No kits found.</div>}
          </div>
        ) : (
          <>
            {cards.length > 0 && (
              <section className={kits.length > 0 ? 'mb-12' : ''}>
                {kits.length > 0 && (
                  <h2 className="mb-5 text-xs font-semibold uppercase tracking-widest text-stone-400">Cards</h2>
                )}
                <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
                  {cards.map((p) => (
                    <ProductCard
                      key={p.id ?? p.slug}
                      product={p}
                      isAdmin={admin}
                      onEdit={() => { const e = toEditable(p); if (e) setEditProduct(e) }}
                    />
                  ))}
                </div>
              </section>
            )}

            {kits.length > 0 && (
              <section>
                <h2 className="mb-5 text-xs font-semibold uppercase tracking-widest text-stone-400">Kits & Sets</h2>
                <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
                  {kits.map((p) => (
                    <ProductCard
                      key={p.id ?? p.slug}
                      product={p}
                      isAdmin={admin}
                      onEdit={() => { const e = toEditable(p); if (e) setEditProduct(e) }}
                    />
                  ))}
                </div>
              </section>
            )}

            {displayed.length === 0 && (
              <div className="py-24 text-center text-stone-400">
                {search ? `No products matching "${search}".` : 'No products found.'}
              </div>
            )}
          </>
        )}
      </main>

      {editProduct && (
        <EditProductModal
          product={editProduct}
          onClose={() => setEditProduct(null)}
          onSaved={() => { setEditProduct(null); reload() }}
        />
      )}
    </PublicLayout>
  )
}
