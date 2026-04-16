# MC-007: Silver Price API Integration

## 0️⃣ Metadata
| Field | Value |
|-------|-------|
| **Task ID** | MC-007 |
| **Owner / Agent** | BuilderAgent |
| **Date** | 2025-01-27 |
| **Branch / Repo** | miracle-coins / feature/silver-price-api |
| **Dependencies** | MC-001 (System Scaffolding) |
| **Related Issues** | Silver Price Integration |
| **Priority** | High |

---

## 1️⃣ 🎯 Task Summary
> Integrate with real silver price API service to replace mock spot prices with live market data for accurate pricing calculations.

---

## 2️⃣ 🧩 Current Context
The system currently uses mock silver prices (hardcoded $25.50) in the Celery task `refresh_spot_prices()`. The pricing engine relies on accurate spot prices for melt value calculations, making this integration critical for production use.

**Current State:**
- Backend: Mock spot price in `app/tasks.py`
- Database: `spot_prices` table ready for real data
- Pricing Engine: Uses spot prices for calculations
- Celery: Hourly task runs but fetches mock data

**Why This Task is Needed:**
- Production requires real market data
- Pricing accuracy depends on current spot prices
- Melt value calculations need live silver prices
- Dashboard KPIs require accurate market data

---

## 3️⃣ 🧠 Goal & Acceptance Criteria

### Primary Goals
- [ ] Integrate with reliable silver price API service
- [ ] Implement robust error handling for API failures
- [ ] Add fallback mechanisms for price data
- [ ] Store price history for analytics
- [ ] Update pricing engine with live data

### Acceptance Criteria
- [ ] Fetches real silver spot prices from API
- [ ] Handles API failures gracefully with fallbacks
- [ ] Stores price data in `spot_prices` table
- [ ] Updates pricing calculations automatically
- [ ] Provides price history for analysis
- [ ] Implements rate limiting and retry logic
- [ ] Logs price fetch events for monitoring
- [ ] Passes comprehensive test coverage

---

## 4️⃣ 🏗️ Implementation Plan

### API Service Integration
1. **Create Price API Service** (`app/services/price_api_service.py`)
   - Implement API client for silver price service
   - Add retry logic with exponential backoff
   - Handle rate limiting and API quotas
   - Parse and validate price data

2. **Update Celery Task** (`app/tasks.py`)
   - Replace mock price with real API call
   - Add error handling and fallback logic
   - Implement price validation
   - Log fetch results and errors

3. **Add Price Validation** (`app/services/price_validation.py`)
   - Validate price data from API
   - Check for reasonable price ranges
   - Detect and handle data anomalies
   - Implement price change alerts

### Database Enhancements
1. **Update Spot Price Model** (`app/models.py`)
   - Add price validation fields
   - Include API source tracking
   - Add price change tracking
   - Store fetch metadata

2. **Add Price History Service** (`app/services/price_history_service.py`)
   - Calculate price trends
   - Generate price statistics
   - Provide historical analysis
   - Support price alerts

### API Endpoints
1. **Price Endpoints** (`app/routers/pricing.py`)
   - Add price history endpoint
   - Implement price statistics endpoint
   - Add manual price refresh endpoint
   - Create price alert configuration

2. **Dashboard Integration** (`app/services/pricing_service.py`)
   - Update KPIs with live price data
   - Add price trend indicators
   - Implement price change notifications
   - Calculate price-based metrics

### Configuration
1. **Environment Variables** (`.env`)
   - Add API service credentials
   - Configure API endpoints and limits
   - Set price validation parameters
   - Add fallback price sources

2. **API Service Configuration** (`app/config/price_api.py`)
   - Define API service settings
   - Configure retry policies
   - Set price validation rules
   - Add monitoring configuration

---

## 5️⃣ 🧪 Testing

| Type | Description | Test Cases |
|------|-------------|------------|
| **Unit** | API service integration | Successful fetch, API failure, rate limiting, invalid response |
| **Unit** | Price validation | Valid price, invalid price, extreme values, missing data |
| **Unit** | Celery task execution | Task success, task failure, retry logic, error handling |
| **Integration** | Database operations | Price storage, history tracking, data retrieval |
| **Integration** | Pricing engine | Live price calculations, fallback scenarios |
| **End-to-end** | Complete flow | API fetch → storage → pricing → dashboard update |

### Test Scenarios
```python
# Mock API responses for testing
test_cases = {
    "successful_fetch": {"price": 25.50, "timestamp": "2025-01-27T10:00:00Z"},
    "api_failure": {"error": "API_UNAVAILABLE", "fallback_price": 25.00},
    "invalid_price": {"price": -10.00, "should_reject": True},
    "rate_limit": {"error": "RATE_LIMITED", "retry_after": 60}
}
```

---

## 6️⃣ 📂 Deliverables

### Backend Files
- `app/services/price_api_service.py` - Silver price API integration
- `app/services/price_validation.py` - Price data validation
- `app/services/price_history_service.py` - Price history and analytics
- `app/config/price_api.py` - API configuration
- `app/schemas/price_schemas.py` - Price-related schemas
- `tests/test_price_api.py` - Price API tests

### Updated Files
- `app/tasks.py` - Updated Celery task with real API
- `app/services/pricing_service.py` - Enhanced with live prices
- `app/routers/pricing.py` - Added price history endpoints
- `app/models.py` - Enhanced spot price model

### Configuration Files
- `.env.example` - Updated with API credentials
- `backend/env.example` - Backend API configuration
- `docs/price-api-integration.md` - API integration documentation

### Documentation
- API service integration guide
- Price validation rules documentation
- Error handling and fallback procedures
- Monitoring and alerting setup

---

## 7️⃣ 🔄 Review Criteria

### Code Quality
- [ ] TypeScript types properly defined for all price components
- [ ] Error handling comprehensive with proper fallbacks
- [ ] API integration follows best practices
- [ ] Proper logging for price fetch events
- [ ] Rate limiting and retry logic implemented

### Functionality
- [ ] Real silver price API integration working
- [ ] Price validation prevents invalid data
- [ ] Fallback mechanisms functional
- [ ] Price history tracking accurate
- [ ] Dashboard updates with live data

### Performance
- [ ] API calls optimized with caching
- [ ] Database queries efficient
- [ ] Celery task performance acceptable
- [ ] Price calculations fast and accurate
- [ ] Memory usage optimized

### Security
- [ ] API credentials stored securely
- [ ] No sensitive data in logs
- [ ] Input validation prevents injection
- [ ] Rate limiting prevents abuse
- [ ] Error messages don't leak information

### Testing
- [ ] Unit tests cover all price API logic
- [ ] Integration tests verify database operations
- [ ] End-to-end tests cover complete flow
- [ ] Test coverage above 90% for price components
- [ ] Mock API responses for reliable testing

---

## 8️⃣ 🧠 Memory Notes (for AI Memory Bank)

```json
{
  "price_api": {
    "service": "metals_api",
    "endpoint": "https://api.metals.live/v1/spot/silver",
    "rate_limit": "100_requests_per_hour",
    "retry_policy": "exponential_backoff",
    "fallback_price": "last_known_price"
  },
  "validation": {
    "min_price": 10.00,
    "max_price": 100.00,
    "max_change": 0.20,
    "required_fields": ["price", "timestamp", "currency"]
  },
  "storage": {
    "table": "spot_prices",
    "retention": "1_year",
    "indexes": ["fetched_at", "metal"],
    "backup": "daily"
  }
}
```

### Key Implementation Notes
- Use exponential backoff for API retries
- Implement price validation to prevent extreme values
- Store price history for trend analysis
- Add monitoring for API health and performance
- Consider multiple API sources for redundancy

### Reusable Patterns
- API service integration pattern
- Price validation pattern
- Celery task error handling pattern
- Fallback mechanism pattern
- Price history tracking pattern

---

## 9️⃣ 🪪 Cursor Rules / DevOps Checklist

- [ ] Verify API credentials are properly secured
- [ ] Use versioned endpoints (/api/v1/...)
- [ ] Commit price API changes separately
- [ ] Keep PRs atomic and type-safe
- [ ] Log price fetch events using structured logging
- [ ] Run price API tests before merging
- [ ] Update API documentation for price endpoints
- [ ] Ensure environment variables are properly typed
- [ ] Validate price data structure matches API format
- [ ] Test with real API in staging environment

---

**Author:** Stream-Line AI  
**Project:** Miracle Coins — CoinSync Pro  
**Task Version:** v1.0  
**Date:** 2025-01-27




