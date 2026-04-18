import { useRouter } from 'next/router'
import Link from 'next/link'
import { useEffect, useMemo, useState } from 'react'
import PublicLayout from '../../components/storefront/PublicLayout'
import { StoreProduct } from '../../data/storefront'
import { fetchStorefrontProduct } from '../../lib/storefront'
import { useCart } from '../../lib/cart'

export default function ProductDetailPage() {
  const router = useRouter()
  const slug = typeof router.query.slug === 'string' ? router.query.slug : ''
  const [product, setProduct] = useState<StoreProduct | null>(null)
  const [loaded, setLoaded] = useState(false)
  const [activeImage, setActiveImage] = useState(0)
  const [qty, setQty] = useState(1)
  const [addedToCart, setAddedToCart] = useState(false)

  const { addItem } = useCart()

  useEffect(() => {
    if (!slug) return
    fetchStorefrontProduct(slug).then((result) => {
      setProduct(result)
      setLoaded(true)
      setActiveImage(0)
    })
  }, [slug])

  const gallery = useMemo(() => {
    if (!product) return []
    const imgs = product.images?.length ? product.images : product.image ? [product.image] : []
    return imgs.filter(Boolean) as string[]
  }, [product])

  function handleAddToCart() {
    if (!product?.id || !product.priceValue) return
    for (let i = 0; i < qty; i++) {
      addItem({
        productId: product.id,
        slug: product.slug,
        name: product.name,
        metal: product.metal,
        image: gallery[0] || null,
        priceValue: product.priceValue,
        priceLabel: product.price,
      })
    }
    setAddedToCart(true)
    setTimeout(() => setAddedToCart(false), 2000)
  }

  const effectivePrice = useMemo(() => {
    if (!product?.priceValue) return null
    return product.priceValue
  }, [product])

  if (!loaded) {
    return (
      <PublicLayout title="Loading…">
        <main className="mx-auto max-w-4xl px-4 py-20 text-center text-stone-400">Loading…</main>
      </PublicLayout>
    )
  }

  if (!product) {
    return (
      <PublicLayout title="Not found">
        <main className="mx-auto max-w-4xl px-4 py-20 text-center sm:px-6 lg:px-8">
          <h1 className="text-3xl font-bold text-stone-900">Product not found</h1>
          <p className="mt-3 text-stone-500">This listing may have ended or been removed.</p>
          <Link href="/shop" className="mt-8 inline-flex rounded-full bg-amber-500 px-6 py-3 font-semibold text-white no-underline hover:bg-amber-600">
            Back to Shop
          </Link>
        </main>
      </PublicLayout>
    )
  }

  const heroImage = gallery[activeImage] || null
  const canAddToCart = !!(product.id && product.priceValue)

  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://miracle-coins.com'
  const productJsonLd = {
    '@context': 'https://schema.org',
    '@type': 'Product',
    name: product.name,
    description: product.description || `${product.metal} precious metal collectible card`,
    image: gallery.length ? gallery : undefined,
    brand: { '@type': 'Brand', name: 'Miracle Coins' },
    url: `${siteUrl}/products/${product.slug}`,
    ...(product.priceValue != null && {
      offers: {
        '@type': 'Offer',
        priceCurrency: 'USD',
        price: product.priceValue.toFixed(2),
        availability: product.quantity > 0
          ? 'https://schema.org/InStock'
          : 'https://schema.org/OutOfStock',
        url: `${siteUrl}/products/${product.slug}`,
      },
    }),
  }

  return (
    <PublicLayout
      title={`${product.name} — Miracle Coins`}
      description={product.description || `Buy ${product.name} — a real ${product.metal} precious metal collectible card.`}
      ogImage={gallery[0]}
      ogType="product"
      canonicalPath={`/products/${product.slug}`}
      jsonLd={productJsonLd}
    >
      <main className="mx-auto max-w-6xl px-4 py-10 sm:px-6 lg:px-8">
        <div className="mb-6 text-sm text-stone-400">
          <Link href="/shop" className="no-underline text-stone-400 hover:text-stone-700">Shop</Link>
          {' / '}
          <span className="text-stone-700">{product.name}</span>
        </div>

        <div className="grid gap-10 lg:grid-cols-[1fr_1fr]">
          {/* Images */}
          <div>
            <div className="overflow-hidden rounded-2xl border border-stone-200 bg-stone-100 aspect-square">
              {heroImage ? (
                <img src={heroImage} alt={product.name} className="w-full h-full object-cover" />
              ) : (
                <div className="flex items-center justify-center h-full text-stone-400">No image</div>
              )}
            </div>
            {gallery.length > 1 && (
              <div className="mt-3 grid grid-cols-5 gap-2">
                {gallery.slice(0, 10).map((img, i) => (
                  <button
                    key={i}
                    onClick={() => setActiveImage(i)}
                    className={`overflow-hidden rounded-lg border-2 transition-colors ${i === activeImage ? 'border-amber-500' : 'border-stone-200 hover:border-stone-400'}`}
                  >
                    <img src={img} alt="" className="aspect-square w-full object-cover" />
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Info */}
          <div>
            <div className="text-xs font-semibold uppercase tracking-widest text-amber-600">
              {product.metal} {product.productType === 'bundle' ? 'kit' : 'card'}
            </div>
            <h1 className="mt-2 text-3xl font-bold text-stone-900 leading-tight">{product.name}</h1>
            <p className="mt-1 text-sm text-stone-500">{product.weightLabel}</p>

            {product.description && (
              <p className="mt-5 text-stone-600 leading-relaxed">{product.description}</p>
            )}

            <div className="mt-6 rounded-2xl border border-stone-200 bg-white p-6 space-y-4">
              {/* Price */}
              <div className="flex items-center justify-between gap-4">
                <div>
                  <div className="text-4xl font-bold text-stone-900">
                    {effectivePrice != null ? `$${effectivePrice.toFixed(2)}` : product.price}
                    {qty > 1 && effectivePrice != null && (
                      <span className="ml-2 text-base font-normal text-stone-400">each</span>
                    )}
                  </div>
                  {qty > 1 && effectivePrice != null && (
                    <div className="mt-1 text-sm text-stone-500">
                      Total: <span className="font-semibold text-stone-700">${(effectivePrice * qty).toFixed(2)}</span>
                    </div>
                  )}
                </div>
                {product.badge && (
                  <span className="rounded-full bg-amber-50 border border-amber-200 px-3 py-1 text-xs font-medium text-amber-700">
                    {product.badge}
                  </span>
                )}
              </div>

              {/* Qty + Add to Cart */}
              {canAddToCart && (
                <div className="flex items-center gap-3">
                  <div className="flex items-center rounded-xl border border-stone-200 overflow-hidden">
                    <button
                      onClick={() => setQty(q => Math.max(1, q - 1))}
                      className="px-3 py-2 text-stone-500 hover:bg-stone-50 transition-colors"
                    >−</button>
                    <span className="px-3 py-2 text-stone-800 min-w-[2.5rem] text-center font-medium">{qty}</span>
                    <button
                      onClick={() => setQty(q => q + 1)}
                      className="px-3 py-2 text-stone-500 hover:bg-stone-50 transition-colors"
                    >+</button>
                  </div>
                  <button
                    onClick={handleAddToCart}
                    className={`flex-1 rounded-full py-3 font-semibold text-sm transition-colors ${
                      addedToCart
                        ? 'bg-green-500 text-white'
                        : 'bg-amber-500 text-white hover:bg-amber-600'
                    }`}
                  >
                    {addedToCart ? 'Added!' : `Add to Cart`}
                  </button>
                </div>
              )}

              {/* eBay link fallback */}
              <div className="flex flex-wrap gap-3">
                {product.buyUrl && (
                  <a
                    href={product.buyUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="rounded-full border border-stone-200 px-5 py-2 text-sm font-medium text-stone-600 no-underline hover:border-stone-400 transition-colors"
                  >
                    Also on eBay
                  </a>
                )}
                <Link
                  href="/shop"
                  className="rounded-full border border-stone-300 px-5 py-2 text-sm font-medium text-stone-600 no-underline hover:border-stone-400 transition-colors"
                >
                  Back to Shop
                </Link>
              </div>
            </div>

            {(product.features?.length > 0 || product.audience?.length > 0) && (
              <div className="mt-6 grid gap-4 sm:grid-cols-2">
                {product.features?.length > 0 && (
                  <div className="rounded-xl border border-stone-200 bg-white p-4">
                    <h2 className="text-sm font-semibold text-stone-700 mb-3">Highlights</h2>
                    <ul className="space-y-1.5 text-sm text-stone-500">
                      {product.features.map((f) => <li key={f}>• {f}</li>)}
                    </ul>
                  </div>
                )}
                {product.audience?.length > 0 && (
                  <div className="rounded-xl border border-stone-200 bg-white p-4">
                    <h2 className="text-sm font-semibold text-stone-700 mb-3">Great for</h2>
                    <ul className="space-y-1.5 text-sm text-stone-500">
                      {product.audience.map((a) => <li key={a}>• {a}</li>)}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </main>
    </PublicLayout>
  )
}
