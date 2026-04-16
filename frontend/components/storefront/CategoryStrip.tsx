import Link from 'next/link'
import { categories } from '../../data/storefront'

export default function CategoryStrip() {
  return (
    <div className="grid gap-4 md:grid-cols-3">
      {categories.map((category) => (
        <Link
          key={category.slug}
          href={`/shop?metal=${category.metal}`}
          className={`rounded-2xl border border-white/10 bg-gradient-to-br ${category.accent} p-6 no-underline hover:scale-[1.01]`}
        >
          <div className="text-xs uppercase tracking-[0.25em] text-gray-300">Shop by metal</div>
          <h3 className="mt-3 text-2xl font-semibold text-white">{category.name}</h3>
          <p className="mt-2 text-sm text-gray-300">{category.subtitle}</p>
        </Link>
      ))}
    </div>
  )
}
