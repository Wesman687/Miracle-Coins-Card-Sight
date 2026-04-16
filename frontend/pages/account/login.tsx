import Link from 'next/link'
import { useRouter } from 'next/router'
import { useState } from 'react'
import PublicLayout from '../../components/storefront/PublicLayout'
import { login } from '../../lib/auth'

export default function LoginPage() {
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const user = await login(email, password)
      if (user.role === 'admin') {
        router.push((router.query.next as string) || '/manage')
      } else {
        router.push('/account')
      }
    } catch (err: any) {
      setError(err.message || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <PublicLayout title="Sign In — Miracle Coins">
      <main className="mx-auto max-w-sm px-4 py-16 sm:px-6">
        <h1 className="mb-2 text-2xl font-bold text-stone-900">Sign in</h1>
        <p className="mb-8 text-sm text-stone-500">
          Don't have an account?{' '}
          <Link href="/account/register" className="text-amber-600 hover:underline">Create one</Link>
        </p>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-stone-700">Email</label>
            <input
              type="email" value={email} onChange={e => setEmail(e.target.value)} required autoFocus
              className="w-full rounded-xl border border-stone-200 px-4 py-2.5 text-sm focus:border-amber-400 focus:outline-none focus:ring-1 focus:ring-amber-400"
            />
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-stone-700">Password</label>
            <input
              type="password" value={password} onChange={e => setPassword(e.target.value)} required
              autoComplete="current-password"
              className="w-full rounded-xl border border-stone-200 px-4 py-2.5 text-sm focus:border-amber-400 focus:outline-none focus:ring-1 focus:ring-amber-400"
            />
          </div>

          {error && <p className="rounded-xl bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-600">{error}</p>}

          <button
            type="submit" disabled={loading}
            className="w-full rounded-full bg-amber-500 py-3 text-sm font-semibold text-white hover:bg-amber-600 disabled:opacity-50 transition-colors"
          >
            {loading ? 'Signing in…' : 'Sign in'}
          </button>
        </form>
      </main>
    </PublicLayout>
  )
}
