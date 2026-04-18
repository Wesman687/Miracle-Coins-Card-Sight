import { GetServerSideProps } from 'next'

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'https://miracle-coins.com'

function buildSitemap(slugs: string[]): string {
  const staticPages = [
    { url: '/', priority: '1.0', changefreq: 'daily' },
    { url: '/shop', priority: '0.9', changefreq: 'daily' },
    { url: '/shop?metal=gold', priority: '0.8', changefreq: 'daily' },
    { url: '/shop?metal=platinum', priority: '0.8', changefreq: 'daily' },
    { url: '/shop?metal=silver', priority: '0.8', changefreq: 'daily' },
    { url: '/shop?type=kits', priority: '0.8', changefreq: 'daily' },
  ]

  const staticEntries = staticPages.map(({ url, priority, changefreq }) => `
  <url>
    <loc>${SITE_URL}${url}</loc>
    <changefreq>${changefreq}</changefreq>
    <priority>${priority}</priority>
  </url>`).join('')

  const productEntries = slugs.map((slug) => `
  <url>
    <loc>${SITE_URL}/products/${slug}</loc>
    <changefreq>weekly</changefreq>
    <priority>0.7</priority>
  </url>`).join('')

  return `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${staticEntries}
${productEntries}
</urlset>`
}

export default function Sitemap() {
  return null
}

export const getServerSideProps: GetServerSideProps = async ({ res }) => {
  let slugs: string[] = []

  try {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:1270/api/v1'
    const response = await fetch(`${apiUrl}/storefront/catalog`)
    if (response.ok) {
      const data = await response.json()
      const products = data.products || data || []
      slugs = products.map((p: { slug: string }) => p.slug).filter(Boolean)
    }
  } catch {
    // serve sitemap with static pages only if API is down
  }

  res.setHeader('Content-Type', 'text/xml')
  res.setHeader('Cache-Control', 'public, s-maxage=3600, stale-while-revalidate=86400')
  res.write(buildSitemap(slugs))
  res.end()

  return { props: {} }
}
