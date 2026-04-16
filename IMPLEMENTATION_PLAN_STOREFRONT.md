# Miracle Coins Storefront Plan

## Goal
Turn the current Miracle Coins project from an admin-heavy inventory dashboard into a business that can also sell publicly through a clean storefront experience.

## What exists now
- Strong internal/admin foundation
- Inventory, pricing, collections, sync, uploads
- No real customer-facing storefront flow
- Public sales messaging is weak/nonexistent

## Product focus
Primary products:
- Gold cards — 1/4 grain gold
- Platinum cards — 1/4 grain platinum
- Silver cards — 1 grain silver
- Different designs / collectible variants
- Bundle and gift set potential

## Recommended architecture
### Keep
- Existing admin dashboard for operations
- Inventory / sales / pricing / uploads / sync workflows

### Add
- Public storefront layer in the same Next.js frontend
- Separate public routes from admin routes

## Phase plan

### Phase 1 — Storefront MVP
Ship a real public-facing surface:
- `/` public homepage
- `/shop` product grid
- `/products/[slug]` product page
- `/admin` keeps current dashboard entry point

Also add:
- Shared storefront data model for products and categories
- Strong mobile-first UI
- Trust messaging
- Clear calls to action

### Phase 2 — Conversion improvements
- Collection pages for gold / platinum / silver
- FAQ / authenticity page
- Bundle page
- Packaging / gift messaging
- Better product media handling from inventory system

### Phase 3 — Operational integration
- Pull public products from backend/admin data instead of hardcoded storefront data
- Real inventory visibility
- Real image association
- Per-product outbound sales links (eBay, Whatnot, TikTok Shop, etc.)

### Phase 4 — Automation and repeat revenue
- Drop calendar / limited edition logic
- Email/SMS capture
- VIP collector list
- Bundle logic
- Affiliate/reseller landing page

## Key decisions
1. The current homepage should become the public storefront.
2. The current admin dashboard should move behind `/admin`.
3. Public storefront should be simpler than the admin system.
4. Product pages should emphasize:
   - exact metal content
   - collectibility
   - giftability
   - trust / authenticity
   - easy buying

## Design direction
- Dark luxury look already matches precious metals well
- Gold accents stay
- Public site should feel premium, giftable, collectible
- Reduce dashboard feel on public routes

## Phase 1 deliverables
- Public homepage
- Shop page
- Product detail page
- Reusable storefront components
- Storefront data source file
- Admin route preserving current dashboard access

## Risks / cleanup to handle later
- Current auth flow is placeholder-level
- Hardcoded/fallback auth token in frontend API client
- Backend includes unsafe debug/test code patterns that should be cleaned before production exposure
- Public storefront should stay decoupled from admin internals until backend cleanup is done

## Why this approach
This gets the business a usable selling surface quickly without blocking on backend cleanup or rewriting the admin system.
