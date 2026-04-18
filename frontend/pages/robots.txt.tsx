import { GetServerSideProps } from 'next'

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'https://miracle-coins.com'

export default function Robots() {
  return null
}

export const getServerSideProps: GetServerSideProps = async ({ res }) => {
  const content = `User-agent: *
Allow: /
Disallow: /admin
Disallow: /manage
Disallow: /manage/
Disallow: /financial
Disallow: /inventory
Disallow: /sales
Disallow: /pricing
Disallow: /tasks
Disallow: /alerts
Disallow: /search
Disallow: /account/
Disallow: /checkout/

Sitemap: ${SITE_URL}/sitemap.xml`

  res.setHeader('Content-Type', 'text/plain')
  res.setHeader('Cache-Control', 'public, s-maxage=86400')
  res.write(content)
  res.end()

  return { props: {} }
}
