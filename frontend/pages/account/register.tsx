import Link from 'next/link'
import { useRouter } from 'next/router'
import { useState } from 'react'
import PublicLayout from '../../components/storefront/PublicLayout'
import { customerRegister } from '../../lib/auth'

export default function CustomerRegisterPage() {
  const router = useRouter()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await customerRegister(email, name, password)
      router.push('/account')
    } catch (err: any) {
      setError(err.message || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <PublicLayout title="Create Account — Miracle Coins">
      <main className="mx-auto max-w-sm px-4 py-16 sm:px-6">
        <h1 className="mb-2 text-2xl font-bold text-stone-900">Create account</h1>
        <p className="mb-8 text-sm text-stone-500">
          Already have one?{' '}
          <Link href="/account/login" className="text-amber-600 hover:underline">Sign in</Link>
        </p>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-stone-700">Name</label>
            <input
              type="text" value={name} onChange={e => setName(e.target.value)} required autoFocus
              className="w-full rounded-xl border border-stone-200 px-4 py-2.5 text-sm focus:border-amber-400 focus:outline-none focus:ring-1 focus:ring-amber-400"
            />
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-stone-700">Email</label>
            <input
              type="email" value={email} onChange={e => setEmail(e.target.value)} required
              className="w-full rounded-xl border border-stone-200 px-4 py-2.5 text-sm focus:border-amber-400 focus:outline-none focus:ring-1 focus:ring-amber-400"
            />
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-stone-700">Password <span className="text-stone-400 font-normal">(min 8 chars)</span></label>
            <input
              type="password" value={password} onChange={e => setPassword(e.target.value)} required minLength={8}
              className="w-full rounded-xl border border-stone-200 px-4 py-2.5 text-sm focus:border-amber-400 focus:outline-none focus:ring-1 focus:ring-amber-400"
            />
          </div>

          {error && <p className="rounded-xl bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-600">{error}</p>}

          <button
            type="submit" disabled={loading}
            className="w-full rounded-full bg-amber-500 py-3 text-sm font-semibold text-white hover:bg-amber-600 disabled:opacity-50 transition-colors"
          >
            {loading ? 'Creating account…' : 'Create account'}
          </button>
        </form>
      </main>
    </PublicLayout>
  )
}
