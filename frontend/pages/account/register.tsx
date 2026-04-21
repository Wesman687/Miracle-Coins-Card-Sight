import Link from 'next/link'
import { useRouter } from 'next/router'
import { useState } from 'react'
import PublicLayout from '../../components/storefront/PublicLayout'
import { customerRegister } from '../../lib/auth'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:1270/api/v1'

function formatPhone(raw: string): string {
  const digits = raw.replace(/\D/g, '').slice(0, 10)
  if (digits.length <= 3) return digits
  if (digits.length <= 6) return `(${digits.slice(0, 3)}) ${digits.slice(3)}`
  return `(${digits.slice(0, 3)}) ${digits.slice(3, 6)}-${digits.slice(6)}`
}

export default function CustomerRegisterPage() {
  const router = useRouter()
  const [name,          setName]          = useState('')
  const [email,         setEmail]         = useState('')
  const [password,      setPassword]      = useState('')
  const [phone,         setPhone]         = useState('')
  const [addressLine1,  setAddressLine1]  = useState('')
  const [addressLine2,  setAddressLine2]  = useState('')
  const [city,          setCity]          = useState('')
  const [stateProvince, setStateProvince] = useState('')
  const [zipCode,       setZipCode]       = useState('')
  const [country,       setCountry]       = useState('United States')
  const [loading,       setLoading]       = useState(false)
  const [error,         setError]         = useState('')

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      // customerRegister only takes email/name/password — call API directly for extra fields
      const res = await fetch(`${API}/auth/customer/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email, name, password,
          phone: phone || null,
          address_line1: addressLine1 || null,
          address_line2: addressLine2 || null,
          city: city || null,
          state_province: stateProvince || null,
          zip_code: zipCode || null,
          country: country || 'United States',
        }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || 'Registration failed')
      }
      const data = await res.json()
      const { setAuth } = await import('../../lib/auth')
      setAuth({ token: data.token, role: 'customer', email, name: data.name, customerId: data.customer_id })
      router.push('/account')
    } catch (err: any) {
      setError(err.message || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  const inputClass = 'w-full rounded-xl border border-stone-200 px-4 py-2.5 text-sm focus:border-amber-400 focus:outline-none focus:ring-1 focus:ring-amber-400'

  return (
    <PublicLayout title="Create Account — Miracle Coins">
      <main className="mx-auto max-w-lg px-4 py-12 sm:px-6">
        <h1 className="mb-2 text-2xl font-bold text-stone-900">Create account</h1>
        <p className="mb-8 text-sm text-stone-500">
          Already have one?{' '}
          <Link href="/account/login" className="text-amber-600 hover:underline">Sign in</Link>
        </p>

        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Account info */}
          <div>
            <label className="mb-1.5 block text-sm font-medium text-stone-700">Full name</label>
            <input type="text" value={name} onChange={e => setName(e.target.value)} required autoFocus className={inputClass} />
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-stone-700">Email</label>
            <input type="email" value={email} onChange={e => setEmail(e.target.value)} required className={inputClass} />
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-stone-700">Phone</label>
            <input
              type="tel" value={phone}
              onChange={e => setPhone(formatPhone(e.target.value))}
              placeholder="(555) 000-0000"
              className={inputClass}
            />
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-stone-700">
              Password <span className="text-stone-400 font-normal">(min 8 chars)</span>
            </label>
            <input type="password" value={password} onChange={e => setPassword(e.target.value)} required minLength={8} className={inputClass} />
          </div>

          {/* Shipping address */}
          <div className="border-t border-stone-100 pt-5">
            <p className="mb-4 text-sm font-semibold text-stone-700">Shipping address</p>
            <div className="space-y-3">
              <div>
                <label className="mb-1.5 block text-sm font-medium text-stone-700">Address line 1</label>
                <input type="text" value={addressLine1} onChange={e => setAddressLine1(e.target.value)} placeholder="123 Main St" className={inputClass} />
              </div>
              <div>
                <label className="mb-1.5 block text-sm font-medium text-stone-700">
                  Address line 2 <span className="text-stone-400 font-normal">(optional)</span>
                </label>
                <input type="text" value={addressLine2} onChange={e => setAddressLine2(e.target.value)} placeholder="Apt, suite, etc." className={inputClass} />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-stone-700">City</label>
                  <input type="text" value={city} onChange={e => setCity(e.target.value)} className={inputClass} />
                </div>
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-stone-700">State</label>
                  <input type="text" value={stateProvince} onChange={e => setStateProvince(e.target.value)} placeholder="TX" className={inputClass} />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-stone-700">ZIP code</label>
                  <input type="text" value={zipCode} onChange={e => setZipCode(e.target.value)} className={inputClass} />
                </div>
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-stone-700">Country</label>
                  <input type="text" value={country} onChange={e => setCountry(e.target.value)} className={inputClass} />
                </div>
              </div>
            </div>
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
