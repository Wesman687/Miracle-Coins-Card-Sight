const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:1270/api/v1'
const AUTH_SERVER = process.env.NEXT_PUBLIC_AUTH_SERVER_URL || 'https://server.stream-lineai.com'

export interface AuthUser {
  token: string
  role: 'admin' | 'customer'
  email?: string
  name?: string
  customerId?: number
}

const STORAGE_KEY = 'mc_auth'

export function getAuth(): AuthUser | null {
  if (typeof window === 'undefined') return null
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

export function setAuth(user: AuthUser) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(user))
}

export function clearAuth() {
  localStorage.removeItem(STORAGE_KEY)
}

export function isAdmin(): boolean {
  return getAuth()?.role === 'admin'
}

export function isCustomer(): boolean {
  return !!getAuth()
}

export function authHeaders(): Record<string, string> {
  const auth = getAuth()
  return auth ? { Authorization: `Bearer ${auth.token}` } : {}
}

const ADMIN_EMAILS = ['paul@miracle-coins.com']

/** Single login — handles both admin (stream-lineai) and customer (local) accounts. */
export async function login(email: string, password: string): Promise<AuthUser> {
  const res = await fetch(`${AUTH_SERVER}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'Invalid email or password')
  }
  const data = await res.json()
  const token = data.token || data.access_token

  // Fetch user profile to determine admin status
  let userEmail = data.email || email
  let userName = data.name
  let isAdmin = false
  try {
    const meRes = await fetch(`${AUTH_SERVER}/api/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    if (meRes.ok) {
      const meData = await meRes.json()
      const profile = meData.user || meData
      userEmail = profile.email || userEmail
      userName = profile.name || profile.username || userName
      isAdmin = profile.is_admin || profile.user_type === 'admin' || ADMIN_EMAILS.includes(userEmail.toLowerCase())
    }
  } catch {}

  const user: AuthUser = {
    token,
    role: isAdmin ? 'admin' : 'customer',
    email: userEmail,
    name: userName,
  }
  setAuth(user)
  return user
}

/** @deprecated Use login() instead */
export async function adminLogin(email: string, password: string): Promise<AuthUser> {
  return login(email, password)
}

/** @deprecated Use login() instead */
export async function customerLogin(email: string, password: string): Promise<AuthUser> {
  return login(email, password)
}

export async function customerRegister(email: string, name: string, password: string): Promise<AuthUser> {
  const res = await fetch(`${API}/auth/customer/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, name, password }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'Registration failed')
  }
  const data = await res.json()
  const user: AuthUser = { token: data.token, role: 'customer', email, name: data.name }
  setAuth(user)
  return user
}
