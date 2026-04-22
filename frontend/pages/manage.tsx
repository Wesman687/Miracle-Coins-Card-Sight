import { useEffect, useState, useCallback } from 'react'
import PublicLayout from '../components/storefront/PublicLayout'
import NewProductModal from '../components/storefront/NewProductModal'
import EditProductModal from '../components/storefront/EditProductModal'

import { getAuth } from '../lib/auth'
import { resolveImageUrl } from '../lib/storefront'
import ProductSearchBar from '../components/storefront/ProductSearchBar'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:1270/api/v1'
function getToken() { return getAuth()?.token || 'manage-token' }

type Product = {
  id: number
  slug: string
  name: string
  metal: string
  productType: string
  price: string
  image: string | null
  buyUrl: string | null
  quantity: number | null
  ebayQuantity?: number | null
  offerPrice?: number | null
  metals?: string[]
  tags?: string[]
  description?: string
}

const METAL_OPTIONS = ['gold', 'silver', 'platinum', 'palladium', 'copper', 'other']

export default function ManagePage() {
  const [products, setProducts] = useState<Product[]>([])
  const [loadingProducts, setLoadingProducts] = useState(true)
  const [showNewProduct, setShowNewProduct] = useState(false)
  const [editProduct, setEditProduct] = useState<Product | null>(null)
  const [deletingId, setDeletingId] = useState<number | null>(null)
  const [bulkDeleting, setBulkDeleting] = useState(false)

  async function deleteAllVisible() {
    if (!products.length) return
    if (!confirm(`Permanently delete all ${products.length} products shown? This cannot be undone.`)) return
    setBulkDeleting(true)
    try {
      const res = await fetch(`${API}/storefront/products/bulk-delete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${getToken()}` },
        body: JSON.stringify({ ids: products.map(p => p.id) }),
      })
      if (!res.ok) throw new Error(`${res.status}`)
      await loadProducts()
    } catch (e: any) {
      alert('Bulk delete failed: ' + e.message)
    } finally {
      setBulkDeleting(false)
    }
  }

  async function deleteProduct(product: Product) {
    if (!confirm(`Delete "${product.name}"? This cannot be undone.`)) return
    setDeletingId(product.id)
    try {
      const res = await fetch(`${API}/storefront/products/${product.id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${getToken()}` },
      })
      if (!res.ok) throw new Error(`${res.status}`)
      await loadProducts()
    } catch (e: any) {
      alert('Delete failed: ' + e.message)
    } finally {
      setDeletingId(null)
    }
  }

  const [search, setSearch] = useState('')
  const [searchInput, setSearchInput] = useState('')
  const [activeTag, setActiveTag] = useState<string | null>(null)
  const [metalFilter, setMetalFilter] = useState('')
  const [typeFilter, setTypeFilter] = useState('')
  const [hasImageFilter, setHasImageFilter] = useState('')
  const [hasEbayFilter, setHasEbayFilter] = useState('')

  const loadProducts = useCallback(async () => {
    setLoadingProducts(true)
    try {
      const params = new URLSearchParams()
      if (search) params.set('search', search)
      if (metalFilter) params.set('metal', metalFilter)
      if (hasImageFilter) params.set('has_image', hasImageFilter)
      if (hasEbayFilter) params.set('has_ebay', hasEbayFilter)

      if (typeFilter === 'not_card') {
        // Fetch all + fetch cards + fetch bundles, return what's left
        const [allRes, cardRes, bundleRes] = await Promise.all([
          fetch(`${API}/storefront/manage/catalog?${params}`, { headers: { Authorization: `Bearer ${getToken()}` } }),
          fetch(`${API}/storefront/manage/catalog?${params}&product_type=card`, { headers: { Authorization: `Bearer ${getToken()}` } }),
          fetch(`${API}/storefront/manage/catalog?${params}&product_type=bundle`, { headers: { Authorization: `Bearer ${getToken()}` } }),
        ])
        const [allData, cardData, bundleData] = await Promise.all([allRes.json(), cardRes.json(), bundleRes.json()])
        const keepIds = new Set([
          ...(cardData.products || []).map((p: Product) => p.id),
          ...(bundleData.products || []).map((p: Product) => p.id),
        ])
        setProducts((allData.products || []).filter((p: Product) => !keepIds.has(p.id)))
      } else {
        if (typeFilter) params.set('product_type', typeFilter)
        const res = await fetch(`${API}/storefront/manage/catalog?${params}`, {
          headers: { Authorization: `Bearer ${getToken()}` },
        })
        const data = await res.json()
        setProducts(data.products || [])
      }
    } catch {
      setProducts([])
    } finally {
      setLoadingProducts(false)
    }
  }, [search, metalFilter, typeFilter, hasImageFilter, hasEbayFilter])

  useEffect(() => { loadProducts() }, [loadProducts])

  function clearFilters() {
    setSearch(''); setSearchInput(''); setMetalFilter(''); setTypeFilter(''); setHasImageFilter(''); setHasEbayFilter(''); setActiveTag(null)
  }
  const filtersActive = search || metalFilter || typeFilter || hasImageFilter || hasEbayFilter || activeTag
  const displayedProducts = activeTag ? products.filter(p => (p.tags || []).includes(activeTag)) : products

  return (
    <PublicLayout title="Manage — Miracle Coins">
      <main className="mx-auto max-w-5xl px-4 py-10 sm:px-6 lg:px-8 space-y-8">

        {/* Top actions row */}
        <div className="flex flex-wrap gap-3">
          <button
            onClick={() => setShowNewProduct(true)}
            className="flex items-center gap-2 rounded-full bg-amber-500 px-5 py-2.5 text-sm font-medium text-white hover:bg-amber-600 transition-colors"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            New Product
          </button>

          <a
            href="/manage/orders"
            className="flex items-center gap-2 rounded-full border border-stone-300 px-5 py-2.5 text-sm font-medium text-stone-600 hover:border-amber-400 hover:text-amber-600 transition-colors no-underline"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
            Orders
          </a>

          <a
            href="/manage/options"
            className="flex items-center gap-2 rounded-full border border-stone-300 px-5 py-2.5 text-sm font-medium text-stone-600 hover:border-amber-400 hover:text-amber-600 transition-colors no-underline"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            Catalog Settings
          </a>

        </div>

        {/* Search + filters */}
        <div className="flex flex-wrap gap-3 items-center">
          <ProductSearchBar
            value={searchInput}
            onChange={setSearchInput}
            onSubmit={() => setSearch(searchInput)}
            placeholder="Search title, tags, SKU…"
            activeTag={activeTag}
            tags={(() => {
              const freq: Record<string, number> = {}
              products.forEach(p => (p.tags || []).forEach(t => { freq[t] = (freq[t] || 0) + 1 }))
              return Object.entries(freq).sort((a, b) => b[1] - a[1]).map(([t]) => t)
            })()}
            onTagClick={tag => setActiveTag(activeTag === tag ? null : tag)}
            onTagClear={() => setActiveTag(null)}
          />

          <select
            value={metalFilter}
            onChange={e => setMetalFilter(e.target.value)}
            className="rounded-lg border border-stone-300 px-3 py-2 text-sm text-stone-700 focus:border-amber-400 focus:outline-none"
          >
            <option value="">All metals</option>
            {METAL_OPTIONS.map(m => (
              <option key={m} value={m} className="capitalize">{m.charAt(0).toUpperCase() + m.slice(1)}</option>
            ))}
          </select>

          <select
            value={typeFilter}
            onChange={e => setTypeFilter(e.target.value)}
            className="rounded-lg border border-stone-300 px-3 py-2 text-sm text-stone-700 focus:border-amber-400 focus:outline-none"
          >
            <option value="">All types</option>
            <option value="card">Cards only</option>
            <option value="bundle">Kits only</option>
            <option value="not_card">Not cards</option>
          </select>

          <select
            value={hasImageFilter}
            onChange={e => setHasImageFilter(e.target.value)}
            className="rounded-lg border border-stone-300 px-3 py-2 text-sm text-stone-700 focus:border-amber-400 focus:outline-none"
          >
            <option value="">Any image</option>
            <option value="true">Has image</option>
            <option value="false">No image</option>
          </select>

          <select
            value={hasEbayFilter}
            onChange={e => setHasEbayFilter(e.target.value)}
            className="rounded-lg border border-stone-300 px-3 py-2 text-sm text-stone-700 focus:border-amber-400 focus:outline-none"
          >
            <option value="">Any eBay status</option>
            <option value="true">On eBay</option>
            <option value="false">Not on eBay</option>
          </select>

          {filtersActive && (
            <button
              onClick={clearFilters}
              className="rounded-lg border border-stone-300 px-3 py-2 text-sm text-stone-500 hover:border-amber-400 transition-colors"
            >
              Clear
            </button>
          )}
        </div>

        {/* Product list */}
        <section>
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-stone-500 uppercase tracking-widest">
              Products <span className="font-normal">({products.length})</span>
            </h2>
            {products.length > 0 && (
              <button
                onClick={deleteAllVisible}
                disabled={bulkDeleting}
                className="rounded-full border border-red-200 px-4 py-1.5 text-xs font-medium text-red-500 hover:bg-red-50 hover:border-red-400 disabled:opacity-50 transition-colors"
              >
                {bulkDeleting ? 'Deleting…' : `Delete all ${products.length}`}
              </button>
            )}
          </div>

          {loadingProducts ? (
            <div className="space-y-2">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="animate-pulse h-20 rounded-xl bg-stone-100" />
              ))}
            </div>
          ) : displayedProducts.length === 0 ? (
            <div className="rounded-xl border border-stone-200 bg-white p-12 text-center text-stone-400">
              {filtersActive ? 'No products match your filters.' : 'No products yet.'}
            </div>
          ) : (
            <div className="space-y-2">
              {displayedProducts.map((product) => {
                const image = resolveImageUrl(product.image)
                return (
                  <div key={product.id} className="flex items-center gap-4 rounded-xl border border-stone-200 bg-white p-4">
                    {image ? (
                      <img src={image} alt={product.name} className="h-14 w-14 rounded-lg object-cover border border-stone-100 flex-shrink-0" />
                    ) : (
                      <div className="h-14 w-14 rounded-lg bg-stone-100 border border-stone-200 flex items-center justify-center text-stone-300 flex-shrink-0">
                        <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                        </svg>
                      </div>
                    )}

                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-stone-900 text-sm truncate">{product.name}</div>
                      <div className="text-xs text-stone-400 mt-0.5 capitalize">
                        {product.metal} · {product.productType === 'bundle' ? 'Kit' : 'Card'} · {product.price}
                      </div>
                    </div>

                    <div className="flex items-center gap-2 flex-shrink-0">
                      {product.buyUrl && (
                        <a href={product.buyUrl} target="_blank" rel="noreferrer"
                          className="hidden sm:inline-flex rounded-full border border-stone-200 px-3 py-1.5 text-xs text-stone-500 no-underline hover:border-amber-300 hover:text-amber-600 transition-colors">
                          eBay ↗
                        </a>
                      )}
                      <button
                        onClick={() => setEditProduct(product)}
                        className="rounded-full border border-stone-200 px-3 py-1.5 text-xs text-stone-600 hover:border-amber-300 hover:text-amber-600 transition-colors"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => deleteProduct(product)}
                        disabled={deletingId === product.id}
                        className="rounded-full border border-stone-200 px-3 py-1.5 text-xs text-stone-400 hover:border-red-300 hover:text-red-500 disabled:opacity-50 transition-colors"
                      >
                        {deletingId === product.id ? '…' : 'Delete'}
                      </button>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </section>
      </main>

      {showNewProduct && (
        <NewProductModal
          onClose={() => setShowNewProduct(false)}
          onSaved={() => { setShowNewProduct(false); loadProducts() }}
        />
      )}
      {editProduct && (
        <EditProductModal
          product={editProduct}
          onClose={() => { setEditProduct(null); loadProducts() }}
          onSaved={() => { setEditProduct(null); loadProducts() }}
        />
      )}
    </PublicLayout>
  )
}
