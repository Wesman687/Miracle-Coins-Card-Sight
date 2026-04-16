import Head from 'next/head'
import Link from 'next/link'
import { useRouter } from 'next/router'
import { ReactNode, useEffect, useState } from 'react'
import { isAdmin } from '../../lib/auth'
import { useCart } from '../../lib/cart'
import CartDrawer from './CartDrawer'

interface PublicLayoutProps {
  title?: string
  description?: string
  children: ReactNode
}

function CartIcon() {
  const { count } = useCart()
  const [open, setOpen] = useState(false)

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="relative ml-3 rounded-full border border-stone-300 p-2 text-stone-600 hover:border-amber-500 hover:text-amber-600 transition-colors"
        aria-label="Cart"
      >
        <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />
        </svg>
        {count > 0 && (
          <span className="absolute -top-1.5 -right-1.5 flex h-4 w-4 items-center justify-center rounded-full bg-amber-500 text-[10px] font-bold text-white">
            {count > 9 ? '9+' : count}
          </span>
        )}
      </button>
      <CartDrawer open={open} onClose={() => setOpen(false)} />
    </>
  )
}

export default function PublicLayout({
  title = 'Miracle Coins',
  description = 'Real gold, platinum, and silver collectible cards.',
  children,
}: PublicLayoutProps) {
  const router = useRouter()
  const [admin, setAdmin] = useState(false)
  const [mounted, setMounted] = useState(false)
  useEffect(() => { setAdmin(isAdmin()); setMounted(true) }, [])

  const navLinks = [
    { href: '/shop', label: 'All', exact: true },
    { href: '/shop?type=kits', label: 'Kits', exact: false },
    { href: '/shop?metal=gold', label: 'Gold', exact: false },
    { href: '/shop?metal=platinum', label: 'Platinum', exact: false },
    { href: '/shop?metal=silver', label: 'Silver', exact: false },
  ]

  return (
    <>
      <Head>
        <title>{title}</title>
        <meta name="description" content={description} />
      </Head>

      <div className="min-h-screen bg-stone-50 text-stone-900">
        <header className="sticky top-0 z-40 border-b border-stone-200 bg-white/90 backdrop-blur">
          <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6 lg:px-8">
            <Link href="/shop" className="no-underline">
              <div>
                <div className="text-xl font-bold tracking-tight text-stone-900">Miracle Coins</div>
                <div className="text-[10px] uppercase tracking-[0.3em] text-amber-600">Precious Metal Cards</div>
              </div>
            </Link>

            <nav className="flex items-center gap-1 text-sm">
              {navLinks.map((link) => {
                const isActive = mounted && (link.exact
                  ? router.pathname === '/shop' && !router.query.metal && !router.query.type
                  : router.asPath === link.href || router.asPath.startsWith(link.href))
                return (
                  <Link
                    key={link.href}
                    href={link.href}
                    className={`rounded-full px-4 py-2 no-underline transition-colors ${
                      isActive ? 'bg-amber-500 text-white font-medium' : 'text-stone-600 hover:text-stone-900 hover:bg-stone-100'
                    }`}
                  >
                    {link.label}
                  </Link>
                )
              })}
              {admin && (
                <Link
                  href="/manage"
                  className="ml-2 rounded-full border border-amber-400 bg-amber-50 px-4 py-2 text-amber-700 no-underline hover:bg-amber-100 transition-colors text-sm font-medium"
                >
                  Manage
                </Link>
              )}
              <Link
                href="/account"
                className="ml-2 rounded-full border border-stone-300 px-4 py-2 text-stone-600 no-underline hover:border-amber-500 hover:text-amber-600 transition-colors"
              >
                Account
              </Link>
              <CartIcon />
            </nav>
          </div>
        </header>

        {children}

        <footer className="border-t border-stone-200 bg-white">
          <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-4 py-6 sm:px-6 lg:px-8">
            <div className="text-sm text-stone-500">© {new Date().getFullYear()} Miracle Coins — Real gold, platinum & silver collectible cards.</div>
            <div className="flex gap-4 text-sm text-stone-500">
              <Link href="/shop?metal=gold" className="no-underline hover:text-stone-900">Gold</Link>
              <Link href="/shop?metal=platinum" className="no-underline hover:text-stone-900">Platinum</Link>
              <Link href="/shop?metal=silver" className="no-underline hover:text-stone-900">Silver</Link>
            </div>
          </div>
        </footer>
      </div>
    </>
  )
}

