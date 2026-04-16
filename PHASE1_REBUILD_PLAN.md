# Miracle Coins Website — Phase 1 Rebuild Plan

## Current state
The project already has two valuable pieces:
- a large internal/admin dashboard for operations
- a customer-facing Next.js storefront scaffold (`/`, `/shop`, `/products/[slug]`)

The main blocker was not lack of code. It was instability and drift:
- frontend type errors prevented production builds
- admin code contains legacy rough edges and duplicated local interfaces
- storefront is still hardcoded demo data instead of backend-driven catalog data
- auth/API handling is still development-grade in places

## What was fixed now
- Restored a successful production frontend build with `npm run build`
- Fixed TypeScript issues in admin/store collection components
- Loosened overly rigid form typing where dynamic metafields are expected
- Fixed a few DOM typing issues that were blocking compilation
- Normalized a couple of mismatched local interfaces enough to ship a build again

## Recommended implementation path

### Phase 1A — Stabilize and ship the public shell
Goal: make the public site trustworthy and usable immediately.

Deliverables:
- Keep `/` as the public homepage
- Keep `/shop` as product grid
- Keep `/products/[slug]` as product detail page
- Keep `/admin` as operations entry point
- Remove obvious placeholder/internal language from public pages where needed
- Add clearer trust content:
  - real metal content
  - giftable/collectible positioning
  - authenticity / clarity messaging
  - contact or purchase CTA path

### Phase 1B — Replace hardcoded storefront data
Goal: stop treating the public site like a mockup.

Deliverables:
- Create a backend endpoint for public storefront products
- Return only products marked public/active
- Map admin inventory fields to storefront fields:
  - slug
  - title
  - metal
  - weight label
  - description
  - images
  - price / starting price
  - product badges
  - outbound buy links
- Update frontend pages to fetch real data first, with static fallback only if needed

### Phase 1C — Clean route boundaries
Goal: separate public commerce from admin tooling.

Deliverables:
- Audit all header/nav links so public users never land in admin accidentally
- Move or group legacy admin pages more clearly under admin navigation
- Ensure login/auth only affects admin surfaces
- Keep public pages readable even if backend/admin API is unavailable

### Phase 1D — Conversion basics
Goal: make the storefront actually sell.

Deliverables:
- Add collection/category landing sections for gold/platinum/silver
- Add buy buttons per product:
  - direct checkout link if available
  - marketplace links if direct checkout is not ready
- Add FAQ / authenticity section
- Add simple lead/contact capture if direct purchase flow is not finished

## Technical debt to address next
- `frontend/lib/api.ts` still contains a fallback dev token pattern that should be removed before production use
- Several frontend components duplicate interface definitions instead of using shared types
- Public storefront currently relies on static demo data in `frontend/data/storefront.ts`
- Backend likely needs a dedicated public catalog contract rather than exposing internal admin models directly

## Proposed order of work
1. build stability ✅
2. public storefront copy/CTA cleanup
3. public product API contract
4. frontend fetch real catalog data
5. image and purchase-link integration
6. admin/auth cleanup
7. polish + deploy

## Bottom line
This repo is not a dead project. It is a partially-built one that needed stabilization first.

The fastest path is:
- keep the existing Next.js storefront routes
- keep the existing admin system
- connect them through a clean public product layer
- avoid rewriting the whole app
