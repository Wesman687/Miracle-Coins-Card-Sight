# 💰 Miracle Coins — Flexible Pricing Strategies Implementation

> **Task ID:** MC-PRC-002  
> **Owner / Agent:** BuilderAgent  
> **Date:** 2025-01-28  
> **Branch / Repo:** miracle-coins / feature/flexible-pricing  
> **Dependencies:** MC-COLL-001 (collections system)  
> **Related Issues:** User request for multiple pricing options  
> **Priority:** High  

---

## 1️⃣ 🎯 Task Summary
> "Implement flexible pricing strategies allowing users to choose between paid price multiplier, silver spot multiplier, gold spot multiplier, and hardcoded fixed pricing when adding products."

---

## 2️⃣ 🧩 Current Context

**Current State:**
- System has basic pricing with single "spot_multiplier" strategy
- Users can only multiply spot prices or use fixed prices
- No flexibility for different pricing approaches based on coin type
- Owner requested: "When we add a product, using a multiplier should be an option. And the multiplier should have choices like go off paid price, or go off silver, or gold price. But we should be able to hardcode the price as well."

**System Overview:**
- Backend: FastAPI with PostgreSQL database
- Frontend: Next.js with TypeScript and Tailwind CSS
- Pricing Engine: Current spot_multiplier with 1.3x default
- Business Rules: 50-60% general silver, 30% over spot, 20% under spot
- Collections: Single organizational unit for coin grouping

---

## 3️⃣ 🧠 Goal & Acceptance Criteria

### Primary Goals
- [x] Implement multiple pricing strategies: paid price, silver spot, gold spot, fixed price, entry-based
- [x] Update backend models and schemas to support new pricing options
- [x] Create dynamic frontend forms that show relevant fields based on strategy
- [x] Add pricing preview and recommendations
- [x] Update memory system with new pricing decisions

### Acceptance Criteria
- [x] Users can select from 5 pricing strategies
- [x] Form fields dynamically show/hide based on selected strategy
- [x] Recommended multipliers provided for each strategy
- [x] Price preview shows calculation method
- [x] Hardcoded pricing option available
- [x] Backend validates all pricing strategies
- [x] Memory system updated with new pricing rules

---

## 4️⃣ 🏗️ Implementation Plan

1. **Memory System Updates**
   - ✅ Updated pricing.json with new strategies and multiplier options
   - ✅ Added flexible-pricing-strategies decision to decisions.json
   - ✅ Updated task log with implementation details

2. **Backend Implementation**
   - ✅ Updated Coin model with new pricing fields (fixed_price)
   - ✅ Updated price_strategy default to 'paid_price_multiplier'
   - ✅ Updated price_multiplier default to 1.5
   - ✅ Updated coin schemas with new pricing strategy enum
   - ✅ Created database migration for new pricing fields

3. **Frontend Implementation**
   - ✅ Updated AddCoinModal with dynamic pricing strategy selection
   - ✅ Added conditional form fields based on strategy
   - ✅ Added pricing preview and recommendations
   - ✅ Updated UploadNewItemModal with same pricing options
   - ✅ Added proper TypeScript types and Zod validation

4. **Database Migration**
   - ✅ Created migration script for flexible pricing fields
   - ✅ Added constraints and indexes for performance
   - ✅ Added documentation comments for fields

---

## 5️⃣ 🧪 Testing Strategy

| Type | Description | Test Cases |
|------|-------------|------------|
| **Unit** | Pricing strategy validation | Each strategy validates correctly |
| **Integration** | Form submission with different strategies | All strategies save properly |
| **End-to-End** | Complete pricing workflow | User can create coin with any strategy |
| **UI/UX** | Dynamic form behavior | Fields show/hide correctly based on selection |

### Test Scenarios
- Paid Price Multiplier: $50 paid × 1.5 = $75 final price
- Silver Spot Multiplier: $25 spot × 1.3 = $32.50 final price
- Gold Spot Multiplier: $2000 spot × 1.2 = $2400 final price
- Fixed Price: $100 hardcoded = $100 final price
- Entry Based: $40 melt × 1.3 = $52 final price

---

## 6️⃣ 📂 Deliverables

### Backend Files
- ✅ `app/models.py` - Updated Coin model with fixed_price field
- ✅ `app/schemas/coins.py` - Updated schemas with new pricing strategies
- ✅ `backend/migrations/008_flexible_pricing_strategies.sql` - Database migration

### Frontend Files
- ✅ `components/AddCoinModal.tsx` - Dynamic pricing strategy form
- ✅ `components/UploadNewItemModal.tsx` - Updated with same pricing options

### Configuration Files
- ✅ `AI/memory/coinsync/features/pricing.json` - Updated pricing configuration
- ✅ `AI/memory/coinsync/decisions.json` - Added pricing strategy decision
- ✅ `AI/memory/coinsync/tasks/log.jsonl` - Task log entry

---

## 7️⃣ 🔄 Review Criteria

### Code Quality
- [x] TypeScript types properly defined for all pricing strategies
- [x] Zod validation covers all pricing scenarios
- [x] Error handling for invalid pricing inputs
- [x] Proper database constraints and indexes
- [x] Clean, maintainable code structure

### Functionality
- [x] All 5 pricing strategies work correctly
- [x] Dynamic form fields show/hide appropriately
- [x] Price calculations are accurate
- [x] User experience is intuitive
- [x] Recommendations help users choose appropriate multipliers

### Testing
- [x] Form validation works for all strategies
- [x] Database migration successful
- [x] Frontend components render correctly
- [x] Memory system updated properly
- [x] No breaking changes to existing functionality

---

## 8️⃣ 🧠 Memory Notes (for AI Memory Bank)

```json
{
  "feature": "flexible_pricing_strategies",
  "implementation": {
    "strategies": [
      "paid_price_multiplier",
      "silver_spot_multiplier", 
      "gold_spot_multiplier",
      "fixed_price",
      "entry_based"
    ],
    "default_multipliers": {
      "paid_price_multiplier": 1.5,
      "silver_spot_multiplier": 1.3,
      "gold_spot_multiplier": 1.2,
      "entry_based": 1.3
    },
    "ui_patterns": ["dynamic_form_fields", "pricing_preview", "strategy_recommendations"]
  },
  "business_rules": {
    "profit_margins": {
      "paid_price_multiplier": "50% profit margin",
      "silver_spot_multiplier": "30% over spot",
      "gold_spot_multiplier": "20% over spot",
      "entry_based": "30% over entry melt"
    }
  },
  "status": "completed"
}
```

### Key Implementation Notes
- Dynamic form fields based on pricing strategy selection
- Recommended multipliers provided for each strategy
- Price preview shows calculation method
- Hardcoded pricing bypasses all calculations
- Entry-based pricing uses historical melt values

### Reusable Patterns
- Conditional form field rendering based on enum selection
- Dynamic placeholder text based on strategy
- Pricing preview component pattern
- Strategy-specific validation rules

---

## 9️⃣ 🪪 Cursor Rules / DevOps Checklist

- [x] All code follows TypeScript/Python type hints
- [x] Use versioned API endpoints (`/api/v1/coins`)
- [x] Commit messages follow conventional format
- [x] Keep pull requests atomic and focused
- [x] Log important events using structured logging
- [x] Run tests before merging
- [x] Update API documentation
- [x] Ensure environment variables are properly configured
- [x] Validate database migrations work correctly
- [x] Test with real data in staging environment

---

**Author:** Stream-Line AI  
**Project:** Miracle Coins — CoinSync Pro  
**Template Version:** v2.0  
**Date:** 2025-01-28
