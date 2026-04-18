const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:1270/api/v1'
const AUTH_SERVER = process.env.NEXT_PUBLIC_AUTH_SERVER_URL

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

/** Single login — handles both admin (stream-lineai) and customer (local) accounts. */
export async function login(email: string, password: string): Promise<AuthUser> {
  const loginUrl = AUTH_SERVER
    ? `${AUTH_SERVER}/api/auth/login`
    : `${API}/auth/login`
  const res = await fetch(loginUrl, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'Invalid email or password')
  }
  const data = await res.json()
  const user: AuthUser = {
    token: data.token,
    role: data.role === 'admin' ? 'admin' : 'customer',
    email: data.email || email,
    name: data.name,
    customerId: data.customerId,
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
