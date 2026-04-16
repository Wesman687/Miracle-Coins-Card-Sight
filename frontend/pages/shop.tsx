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

  const kits = useMemo(() => products.filter((p) => p.productType === 'bundle'), [products])
  const cards = useMemo(() => products.filter((p) => p.productType !== 'bundle'), [products])

  const displayed = kitsOnly ? kits : products

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
        <div className="mb-8 flex items-center justify-between">
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
              <div className="py-24 text-center text-stone-400">No products found.</div>
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
