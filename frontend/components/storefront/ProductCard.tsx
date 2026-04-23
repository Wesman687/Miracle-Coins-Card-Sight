import Link from 'next/link'
import { StoreProduct } from '../../data/storefront'
import { useCart } from '../../lib/cart'
import { resolveImageUrl } from '../../lib/storefront'

const metalAccent: Record<string, string> = {
  gold: 'text-amber-600',
  platinum: 'text-slate-500',
  silver: 'text-gray-500',
}

const metalBadgeBg: Record<string, string> = {
  gold: 'bg-amber-50 text-amber-700 border-amber-200',
  platinum: 'bg-slate-100 text-slate-600 border-slate-200',
  silver: 'bg-gray-100 text-gray-600 border-gray-200',
}

interface Props {
  product: StoreProduct
  isAdmin?: boolean
  onEdit?: () => void
}

export default function ProductCard({ product, isAdmin, onEdit }: Props) {
  const image = resolveImageUrl(product.image || product.images?.[0])
  const accent = metalAccent[product.metal] ?? 'text-stone-500'
  const { addItem } = useCart()

  function handleAddToCart(e: React.MouseEvent) {
    e.preventDefault()
    if (!product.id || !product.priceValue) return
    addItem({
      productId: product.id,
      slug: product.slug,
      name: product.name,
      metal: product.metal,
      image,
      priceValue: product.priceValue,
      priceLabel: product.price,
    })
  }

  const canAddToCart = !!(product.id && product.priceValue)

  return (
    <div className="flex flex-col rounded-2xl border border-stone-200 bg-white shadow-sm hover:shadow-md transition-shadow overflow-hidden">
      <div className="relative aspect-[4/3] bg-stone-100 overflow-hidden">
        {image ? (
          <img src={image} alt={product.name} className="w-full h-full object-contain" />
        ) : (
          <div className="flex items-center justify-center h-full text-stone-400 text-sm">No image</div>
        )}
        {product.badge && (
          <span className={`absolute top-3 right-3 rounded-full border px-2.5 py-1 text-xs font-medium ${metalBadgeBg[product.metal] ?? 'bg-stone-100 text-stone-600 border-stone-200'}`}>
            {product.badge}
          </span>
        )}
        {product.bulkPricing && product.bulkPricing.length > 0 && (
          <span className="absolute bottom-3 left-3 rounded-full bg-stone-800/70 px-2.5 py-1 text-[10px] font-medium text-white backdrop-blur-sm">
            Bulk pricing
          </span>
        )}
        {isAdmin && onEdit && (
          <button
            onClick={(e) => { e.preventDefault(); onEdit() }}
            className="absolute top-3 left-3 flex items-center gap-1.5 rounded-full bg-white/90 backdrop-blur-sm border border-stone-200 px-2.5 py-1.5 text-xs font-medium text-stone-700 shadow hover:bg-amber-50 hover:border-amber-300 hover:text-amber-700 transition-colors"
          >
            <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
            Edit
          </button>
        )}
      </div>

      <div className="flex flex-1 flex-col p-5">
        <div className={`text-xs font-semibold uppercase tracking-widest ${accent}`}>
          {product.metal} {product.productType === 'bundle' ? 'Kit' : 'Card'}
        </div>
        <h3 className="mt-1.5 text-base font-semibold text-stone-900 leading-snug">{product.name}</h3>
        <p className="mt-1 text-xs text-stone-500">{product.weightLabel}</p>

        <div className="mt-auto pt-5 flex items-center justify-between gap-2">
          <div className="text-2xl font-bold text-stone-900">{product.price}</div>
          <div className="flex gap-2">
            {canAddToCart && (
              <button
                onClick={handleAddToCart}
                className="rounded-full border border-amber-400 bg-amber-50 px-3 py-2 text-sm font-medium text-amber-700 hover:bg-amber-100 transition-colors"
                title="Add to cart"
              >
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
              </button>
            )}
            <Link
              href={`/products/${product.slug}`}
              className="rounded-full bg-amber-500 px-5 py-2 text-sm font-medium text-white no-underline hover:bg-amber-600 transition-colors"
            >
              View
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
