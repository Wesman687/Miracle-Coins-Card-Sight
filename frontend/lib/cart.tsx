import { createContext, useCallback, useContext, useEffect, useState } from 'react'

export interface CartItem {
  productId: number
  slug: string
  name: string
  metal: string
  image: string | null
  priceValue: number
  priceLabel: string
  qty: number
}

interface CartContextValue {
  items: CartItem[]
  count: number
  total: number
  addItem: (item: Omit<CartItem, 'qty'>) => void
  removeItem: (productId: number) => void
  updateQty: (productId: number, qty: number) => void
  clearCart: () => void
}

const CartContext = createContext<CartContextValue | null>(null)

const STORAGE_KEY = 'miracle_cart'

function loadCart(): CartItem[] {
  if (typeof window === 'undefined') return []
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

function saveCart(items: CartItem[]) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(items))
  } catch {}
}

export function CartProvider({ children }: { children: React.ReactNode }) {
  const [items, setItems] = useState<CartItem[]>([])

  useEffect(() => {
    setItems(loadCart())
  }, [])

  const persist = useCallback((next: CartItem[]) => {
    setItems(next)
    saveCart(next)
  }, [])

  const addItem = useCallback((item: Omit<CartItem, 'qty'>) => {
    setItems(prev => {
      const existing = prev.find(i => i.productId === item.productId)
      const next = existing
        ? prev.map(i => i.productId === item.productId ? { ...i, qty: i.qty + 1 } : i)
        : [...prev, { ...item, qty: 1 }]
      saveCart(next)
      return next
    })
  }, [])

  const removeItem = useCallback((productId: number) => {
    setItems(prev => {
      const next = prev.filter(i => i.productId !== productId)
      saveCart(next)
      return next
    })
  }, [])

  const updateQty = useCallback((productId: number, qty: number) => {
    setItems(prev => {
      const next = qty <= 0
        ? prev.filter(i => i.productId !== productId)
        : prev.map(i => i.productId === productId ? { ...i, qty } : i)
      saveCart(next)
      return next
    })
  }, [])

  const clearCart = useCallback(() => {
    setItems([])
    saveCart([])
  }, [])

  const count = items.reduce((s, i) => s + i.qty, 0)
  const total = items.reduce((s, i) => s + i.priceValue * i.qty, 0)

  return (
    <CartContext.Provider value={{ items, count, total, addItem, removeItem, updateQty, clearCart }}>
      {children}
    </CartContext.Provider>
  )
}

export function useCart() {
  const ctx = useContext(CartContext)
  if (!ctx) throw new Error('useCart must be used inside CartProvider')
  return ctx
}
