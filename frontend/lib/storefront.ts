import { StoreProduct } from '../data/storefront'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:1270/api/v1'
const MEDIA_BASE = API_BASE.replace(/\/api\/v1$/, '')

const SERVER_BASE = 'https://server.stream-lineai.com/miracle-coins'

export function resolveImageUrl(url: string | null | undefined): string | null {
  if (!url) return null
  // Localhost upload URLs → always serve from production server
  if (url.includes('localhost') && url.includes('/uploads/')) {
    const path = url.split('/uploads/').pop()
    return `${SERVER_BASE}/uploads/${path}`
  }
  // Fix server URLs missing the /miracle-coins/ prefix
  if (url.match(/https?:\/\/server\.stream-lineai\.com\/uploads\//)) {
    return url.replace(/https?:\/\/server\.stream-lineai\.com\/uploads\//, `${SERVER_BASE}/uploads/`)
  }
  if (url.startsWith('http')) return url
  return `${MEDIA_BASE}${url.startsWith('/') ? '' : '/'}${url}`
}

export async function fetchStorefrontProducts(metal?: string, options?: { featuredOnly?: boolean }): Promise<StoreProduct[]> {
  try {
    const url = new URL(`${API_BASE}/storefront/catalog`)
    if (metal) url.searchParams.set('metal', metal)
    if (options?.featuredOnly) url.searchParams.set('featured_only', 'true')
    const response = await fetch(url.toString())
    if (!response.ok) throw new Error(`Storefront API error: ${response.status}`)
    const payload = await response.json()
    if (Array.isArray(payload?.products) && payload.products.length > 0) {
      return payload.products
    }
  } catch (error) {
    console.warn('Falling back to static storefront data', error)
  }

  return []
}

export async function fetchStorefrontProduct(slug: string): Promise<StoreProduct | null> {
  try {
    const response = await fetch(`${API_BASE}/storefront/products/${slug}`)
    if (response.ok) {
      return await response.json()
    }
  } catch (error) {
    console.warn('Falling back to static storefront product', error)
  }

  return null
}
