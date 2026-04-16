export type MetalType = 'gold' | 'platinum' | 'silver'
export type StoreProductType = 'card' | 'bundle'

export interface BulkPricingTier {
  qty: number
  price: number
}

export interface StoreProduct {
  id?: number
  slug: string
  name: string
  metal: string
  weightLabel: string
  description: string
  price: string
  priceValue?: number
  bulkPricing?: BulkPricingTier[]
  badge?: string
  design: string
  image?: string
  images?: string[]
  features: string[]
  audience: string[]
  buyUrl?: string
  liveUrl?: string
  quantity?: number
  productType?: string
  metals?: string[]
}

export const categories = [
  {
    slug: 'gold',
    name: 'Gold Cards',
    subtitle: '1/4 grain gold collectible cards',
    accent: 'from-yellow-300 via-yellow-500 to-amber-600',
    metal: 'gold' as MetalType,
  },
  {
    slug: 'platinum',
    name: 'Platinum Cards',
    subtitle: '1/4 grain platinum collectible cards',
    accent: 'from-slate-200 via-slate-400 to-slate-600',
    metal: 'platinum' as MetalType,
  },
  {
    slug: 'silver',
    name: 'Silver Cards',
    subtitle: '1 grain silver collectible cards',
    accent: 'from-gray-200 via-gray-400 to-gray-600',
    metal: 'silver' as MetalType,
  },
]

export const storefrontProducts: StoreProduct[] = [
  {
    slug: 'legacy-eagle-gold-card',
    name: 'Legacy Eagle Gold Card',
    metal: 'gold',
    weightLabel: '1/4 grain gold',
    description: 'A premium collectible gold card built for gift buyers, card collectors, and precious-metal novelty fans.',
    price: '$29+',
    badge: 'Best Seller',
    design: 'Classic luxury / patriotic display design',
    features: ['Real gold content', 'Wallet-friendly display format', 'Gift-ready collectible appeal'],
    audience: ['Gift buyers', 'Collectors', 'Impulse premium buyers'],
    productType: 'card',
  },
  {
    slug: 'vault-line-platinum-card',
    name: 'Vault Line Platinum Card',
    metal: 'platinum',
    weightLabel: '1/4 grain platinum',
    description: 'A rarer-feeling collectible built around platinum appeal and premium presentation.',
    price: '$39+',
    badge: 'Premium Pick',
    design: 'Minimal high-end metallic design',
    features: ['Real platinum content', 'Distinct premium category', 'Strong collector conversation piece'],
    audience: ['Collectors', 'Luxury gift buyers', 'Metal enthusiasts'],
    productType: 'card',
  },
  {
    slug: 'signature-silver-card',
    name: 'Signature Silver Card',
    metal: 'silver',
    weightLabel: '1 grain silver',
    description: 'An accessible collectible silver card that works especially well for first-time buyers and multi-item bundles.',
    price: '$14+',
    badge: 'Easy Entry',
    design: 'Bright silver collectible design',
    features: ['Real silver content', 'Accessible entry price', 'Great for bundles and repeat purchases'],
    audience: ['New buyers', 'Collectors', 'Bundle shoppers'],
    productType: 'card',
  },
]

export const featuredBenefits = [
  'Real precious metal in every card',
  'Designed to feel collectible, giftable, and display-worthy',
  'Perfect for live-selling audiences and impulse purchases',
  'Simple product lineup: gold, platinum, silver, and limited designs',
]
