# 🧠 Miracle Coins — AI Pricing Agent (Backend)

## 0️⃣ Metadata
| Field | Value |
|-------|-------|
| **Task ID** | MC-PRC-001 |
| **Owner / Agent** | PricingAgent / BuilderAgent |
| **Date** | 2025-01-27 |
| **Branch / Repo** | miracle-coins / feature/pricing-agent-backend |
| **Dependencies** | MC-001 (System Scaffolding), MC-007 (Silver Price API) |
| **Related Issues** | Pricing Engine Implementation, Scam Detection |
| **Priority** | High |

---

## 1️⃣ 🎯 Task Summary
> Implement an intelligent pricing agent that continuously updates coin values using live silver prices, market scraping, and AI-powered scam detection to ensure accurate and trustworthy pricing.

---

## 2️⃣ 🧩 Current Context
The system currently has basic pricing calculations but lacks real-time market data integration and scam detection capabilities. The pricing engine needs to be enhanced with:

**Current State:**
- Basic spot price integration (mock data)
- Simple markup calculations
- No market data scraping
- No scam price detection
- Manual price overrides only

**Why This Task is Needed:**
- Real-time market pricing requires live data sources
- Scam detection prevents fraudulent listings from affecting prices
- Automated pricing reduces manual work and errors
- Market competitiveness requires accurate pricing
- Trust and credibility depend on reliable pricing

---

## 3️⃣ 🧠 Goal & Acceptance Criteria

### Primary Goals
- [ ] Implement live silver spot price integration with multiple sources
- [ ] Build market data scraping for eBay, APMEX, JM Bullion, and other sources
- [ ] Create AI-powered scam price detection system
- [ ] Develop intelligent pricing algorithm with confidence scoring
- [ ] Implement automatic Shopify price updates
- [ ] Add comprehensive logging and monitoring

### Acceptance Criteria
- [ ] Live silver prices updated hourly from reliable sources
- [ ] Market data scraped daily from major dealers
- [ ] Scam prices detected and filtered with 95%+ accuracy
- [ ] Pricing algorithm produces consistent, competitive prices
- [ ] Shopify products update automatically when prices change >3%
- [ ] Manual refresh endpoint works reliably
- [ ] All pricing data logged with confidence scores
- [ ] Error handling prevents pricing failures
- [ ] Performance meets sub-second response times

---

## 4️⃣ 🏗️ Implementation Plan

### Phase 1: Database Schema Enhancement
1. **Create Market Prices Table**
   ```sql
   CREATE TABLE market_prices (
     id BIGSERIAL PRIMARY KEY,
     coin_id BIGINT REFERENCES coins(id),
     spot_price DECIMAL(10,2),
     market_avg DECIMAL(10,2),
     market_min DECIMAL(10,2),
     market_max DECIMAL(10,2),
     melt_value DECIMAL(10,2),
     markup_factor DECIMAL(6,3),
     final_price DECIMAL(10,2),
     confidence_score DECIMAL(3,2),
     scam_detected BOOLEAN DEFAULT FALSE,
     scam_reason TEXT,
     source TEXT,
     sample_size INTEGER,
     updated_at TIMESTAMP DEFAULT NOW()
   );
   ```

2. **Add Pricing Configuration Table**
   ```sql
   CREATE TABLE pricing_config (
     id BIGSERIAL PRIMARY KEY,
     coin_type VARCHAR(50),
     min_markup DECIMAL(6,3),
     max_markup DECIMAL(6,3),
     default_markup DECIMAL(6,3),
     scam_threshold DECIMAL(6,3),
     confidence_threshold DECIMAL(3,2),
     created_at TIMESTAMP DEFAULT NOW()
   );
   ```

### Phase 2: Core Services Implementation
1. **Spot Price Fetcher Service** (`app/services/spot_price_service.py`)
   - Multiple API sources (Metals-API, GoldAPI, Alpha Vantage)
   - Fallback mechanisms for API failures
   - Price validation and anomaly detection
   - Rate limiting and retry logic

2. **Market Scraper Service** (`app/services/market_scraper_service.py`)
   - eBay completed listings scraping
   - APMEX, JM Bullion, SD Bullion price fetching
   - Data cleaning and normalization
   - Anti-bot detection handling

3. **Scam Detection Service** (`app/services/scam_detection_service.py`)
   - Price anomaly detection using statistical analysis
   - Machine learning model for pattern recognition
   - Historical price trend analysis
   - Cross-reference validation with multiple sources

4. **Pricing Engine Service** (`app/services/pricing_engine_service.py`)
   - Intelligent pricing algorithm
   - Confidence scoring system
   - Market competitiveness analysis
   - Dynamic markup adjustment

### Phase 3: Background Tasks
1. **Celery Tasks** (`app/tasks/pricing_tasks.py`)
   - Hourly spot price updates
   - Daily market data scraping
   - Weekly scam detection model retraining
   - Price change notifications

2. **Shopify Integration** (`app/services/shopify_pricing_service.py`)
   - Automatic product price updates
   - Bulk update optimization
   - Change tracking and logging

### Phase 4: API Endpoints
1. **Pricing API** (`app/routers/pricing.py`)
   - Manual price refresh endpoint
   - Price history and analytics
   - Scam detection results
   - Configuration management

---

## 5️⃣ 🧪 Testing Strategy

| Type | Description | Test Cases |
|------|-------------|------------|
| **Unit** | Individual pricing functions | Price calculations, scam detection, confidence scoring |
| **Integration** | API and database operations | Spot price fetching, market scraping, price storage |
| **End-to-End** | Complete pricing workflow | Spot → Market → Scam Detection → Final Price → Shopify |
| **Performance** | System performance | Response times, memory usage, concurrent requests |
| **Security** | Scam detection accuracy | Known scam prices, edge cases, false positives |

### Test Data Requirements
- Historical price data for testing
- Known scam price examples
- Mock API responses for different scenarios
- Test coins with various configurations

---

## 6️⃣ 📂 Deliverables

### Backend Files
- `app/services/spot_price_service.py` - Live silver price fetching
- `app/services/market_scraper_service.py` - Market data scraping
- `app/services/scam_detection_service.py` - AI scam detection
- `app/services/pricing_engine_service.py` - Core pricing logic
- `app/services/shopify_pricing_service.py` - Shopify integration
- `app/tasks/pricing_tasks.py` - Background pricing tasks
- `app/routers/pricing.py` - Pricing API endpoints
- `app/models/pricing_models.py` - Pricing database models
- `app/schemas/pricing_schemas.py` - Pricing Pydantic schemas

### Database Files
- `migrations/add_pricing_tables.py` - Database schema updates
- `migrations/add_pricing_config_data.py` - Initial configuration data

### Configuration Files
- `.env.example` - Updated environment variables
- `app/config/pricing_config.py` - Pricing configuration
- `docs/pricing-agent.md` - Pricing agent documentation

### Testing Files
- `tests/test_spot_price_service.py` - Spot price service tests
- `tests/test_market_scraper_service.py` - Market scraper tests
- `tests/test_scam_detection_service.py` - Scam detection tests
- `tests/test_pricing_engine_service.py` - Pricing engine tests
- `tests/test_pricing_integration.py` - Integration tests

---

## 7️⃣ 🔄 Review Criteria

### Code Quality
- [ ] TypeScript types properly defined for all pricing components
- [ ] Error handling comprehensive with proper fallbacks
- [ ] Pricing algorithms well-documented and tested
- [ ] Proper logging for all pricing operations
- [ ] Security best practices implemented

### Functionality
- [ ] Live pricing data integration working correctly
- [ ] Scam detection accurate and reliable
- [ ] Pricing algorithm produces competitive prices
- [ ] Shopify integration updates prices automatically
- [ ] Manual refresh endpoint functional

### Performance
- [ ] Pricing calculations complete in <1 second
- [ ] Background tasks run efficiently
- [ ] Database queries optimized
- [ ] Memory usage within acceptable limits
- [ ] Concurrent pricing requests handled properly

### Security
- [ ] Scam detection prevents fraudulent pricing
- [ ] API credentials stored securely
- [ ] Input validation prevents injection attacks
- [ ] Rate limiting prevents abuse
- [ ] Error messages don't leak sensitive information

### Testing
- [ ] Unit test coverage >90% for pricing components
- [ ] Integration tests cover all pricing workflows
- [ ] End-to-end tests verify complete pricing flow
- [ ] Scam detection tests validate accuracy
- [ ] Performance tests meet response time requirements

---

## 8️⃣ 🧠 Memory Notes (for AI Memory Bank)

```json
{
  "feature": "pricing_agent",
  "implementation": {
    "backend": [
      "spot_price_service.py",
      "market_scraper_service.py", 
      "scam_detection_service.py",
      "pricing_engine_service.py"
    ],
    "database": ["market_prices", "pricing_config"],
    "apis": ["/api/v1/pricing/refresh", "/api/v1/pricing/history"]
  },
  "pricing_sources": {
    "spot": ["metals-api", "goldapi", "alpha-vantage"],
    "market": ["ebay", "apmex", "jm-bullion", "sd-bullion"]
  },
  "scam_detection": {
    "methods": ["statistical_analysis", "ml_patterns", "cross_validation"],
    "accuracy_target": "95%",
    "confidence_threshold": 0.8
  },
  "dependencies": ["celery", "redis", "shopify_api", "beautifulsoup4"],
  "status": "planned"
}
```

### Key Implementation Notes
- Use multiple spot price sources for redundancy and accuracy
- Implement statistical analysis for scam detection (Z-score, IQR)
- Machine learning model for pattern recognition in pricing data
- Confidence scoring based on data quality and source reliability
- Dynamic markup adjustment based on market competitiveness

### Reusable Patterns
- Multi-source API integration pattern
- Scam detection algorithm pattern
- Confidence scoring system pattern
- Background task scheduling pattern
- Price change notification pattern

---

## 9️⃣ 🪪 Cursor Rules / DevOps Checklist

- [ ] Verify all pricing calculations use proper decimal precision
- [ ] Use versioned endpoints (/api/v1/...)
- [ ] Commit pricing algorithm changes separately
- [ ] Keep PRs atomic and type-safe
- [ ] Log all pricing decisions with confidence scores
- [ ] Run pricing tests before merging
- [ ] Update API documentation for pricing endpoints
- [ ] Ensure environment variables are properly typed
- [ ] Validate scam detection accuracy with test data
- [ ] Test with real market data in staging environment

---

**Author:** Stream-Line AI  
**Project:** Miracle Coins — CoinSync Pro  
**Task Version:** v1.0  
**Date:** 2025-01-27




