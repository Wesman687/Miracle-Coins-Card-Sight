# 🧠 Miracle Coins — AI Pricing Agent Documentation

## Overview

The AI Pricing Agent is a comprehensive system that automatically calculates coin prices using live market data, AI-powered scam detection, and intelligent pricing algorithms. It integrates with multiple data sources and provides real-time pricing updates to your Shopify store.

## 🏗️ Architecture

### Core Components

1. **Spot Price Service** - Fetches live silver prices from multiple APIs
2. **Market Scraper Service** - Scrapes market data from eBay, APMEX, JM Bullion, SD Bullion
3. **Scam Detection Service** - AI-powered detection of fraudulent prices
4. **Pricing Engine Service** - Core pricing calculation logic
5. **Shopify Integration Service** - Automatic price updates to Shopify
6. **Background Tasks** - Celery tasks for automated updates

### Data Flow

```
Spot Price APIs → Market Scrapers → Scam Detection → Pricing Engine → Shopify Store
     ↓                ↓                ↓              ↓              ↓
  Live Prices    Market Data    Fraud Detection   Final Price   Auto Updates
```

## 🚀 Quick Start

### 1. Environment Setup

```bash
# Copy environment template
cp backend/env.example backend/.env

# Edit configuration
nano backend/.env
```

### 2. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 3. Database Setup

```bash
# Run database migrations
python -m alembic upgrade head

# Or run the SQL schema directly
psql -d miracle_coins -f migrations/001_pricing_agent_schema.sql
```

### 4. Start Services

```bash
# Start Redis (required for Celery)
redis-server

# Start Celery worker
celery -A app.tasks.pricing_tasks worker --loglevel=info

# Start Celery beat (scheduler)
celery -A app.tasks.pricing_tasks beat --loglevel=info

# Start FastAPI server
python main.py
```

## 📊 API Endpoints

### Spot Price Endpoints

- `GET /api/v1/pricing-agent/spot-price` - Get current silver spot price
- `POST /api/v1/pricing-agent/spot-price/refresh` - Manually refresh spot prices

### Market Data Endpoints

- `GET /api/v1/pricing-agent/market-data` - Get market data for coin type
- `POST /api/v1/pricing-agent/market-data/refresh` - Refresh market data

### Scam Detection Endpoints

- `POST /api/v1/pricing-agent/scam-detection` - Detect scam prices
- `POST /api/v1/pricing-agent/scam-detection/batch` - Batch scam detection

### Pricing Engine Endpoints

- `POST /api/v1/pricing-agent/calculate-price` - Calculate price for coin
- `POST /api/v1/pricing-agent/calculate-prices/batch` - Batch price calculation

### Configuration Endpoints

- `GET /api/v1/pricing-agent/config` - Get pricing configurations
- `POST /api/v1/pricing-agent/config` - Create pricing configuration
- `PUT /api/v1/pricing-agent/config/{id}` - Update pricing configuration

### Analytics Endpoints

- `GET /api/v1/pricing-agent/history/{coin_id}` - Get price history
- `GET /api/v1/pricing-agent/summary/{coin_id}` - Get pricing summary
- `GET /api/v1/pricing-agent/analytics` - Get pricing analytics

### Task Management Endpoints

- `POST /api/v1/pricing-agent/tasks/refresh-all` - Run full pricing update
- `GET /api/v1/pricing-agent/tasks/{task_id}` - Get task status

### Shopify Integration Endpoints

- `POST /api/v1/pricing-agent/shopify/sync` - Sync prices to Shopify
- `GET /api/v1/pricing-agent/shopify/products-needing-updates` - Get products needing updates

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:password@localhost/miracle_coins` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `METALS_API_KEY` | Metals-API.com API key | Required |
| `GOLDAPI_KEY` | GoldAPI.io API key | Optional |
| `SHOPIFY_DOMAIN` | Shopify store domain | Required |
| `SHOPIFY_ACCESS_TOKEN` | Shopify API access token | Required |
| `DEFAULT_MARKUP_FACTOR` | Default markup factor | `1.500` |
| `SCAM_DETECTION_ENABLED` | Enable scam detection | `true` |
| `PRICE_UPDATE_THRESHOLD` | Price update threshold % | `3.00` |

### Pricing Configuration

The system uses coin-type-specific configurations:

```json
{
  "coin_type": "silver_eagle",
  "min_markup": 1.300,
  "max_markup": 1.800,
  "default_markup": 1.550,
  "scam_threshold": 0.250,
  "confidence_threshold": 0.75,
  "price_update_threshold": 3.00
}
```

## 🤖 AI Scam Detection

### Detection Methods

1. **Statistical Analysis** - Z-score and IQR analysis
2. **Price Deviation** - Deviation from market average
3. **Pattern Recognition** - Suspicious pricing patterns
4. **Market Consistency** - Cross-reference validation

### Scam Indicators

- Prices >50% above/below market average
- Suspicious round numbers (10.00, 25.00, 50.00)
- Sequential patterns (12.34, 23.45)
- Repeated digits (22.22, 33.33)
- Prices too close to spot price

### Confidence Scoring

- **0.9-1.0**: High confidence, reliable pricing
- **0.7-0.9**: Good confidence, minor concerns
- **0.5-0.7**: Medium confidence, review recommended
- **0.0-0.5**: Low confidence, manual review required

## 📈 Background Tasks

### Scheduled Tasks

| Task | Schedule | Description |
|------|----------|-------------|
| Update Spot Prices | Every hour | Fetch latest silver prices |
| Scrape Market Data | Daily at 2 AM | Scrape eBay, APMEX, etc. |
| Calculate Prices | Every hour at 30 min | Calculate all coin prices |
| Sync Shopify | Every hour at 45 min | Update Shopify prices |
| Detect Scams | Daily at 3 AM | Run scam detection |
| Cleanup Data | Weekly Monday 4 AM | Clean old pricing data |

### Manual Tasks

```bash
# Run full pricing update
curl -X POST http://localhost:13000/api/v1/pricing-agent/tasks/refresh-all

# Check task status
curl http://localhost:13000/api/v1/pricing-agent/tasks/{task_id}
```

## 🧪 Testing

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_pricing_agent.py

# Run async tests
pytest -k "asyncio"
```

### Test Categories

- **Unit Tests** - Individual service testing
- **Integration Tests** - Service interaction testing
- **Performance Tests** - Load and performance testing
- **Error Handling Tests** - Failure scenario testing

## 📊 Monitoring

### Health Check

```bash
curl http://localhost:13000/api/v1/pricing-agent/health
```

### Metrics

- Price calculation success rate
- Scam detection accuracy
- API response times
- Background task completion rates

### Logging

Logs are structured and include:
- Pricing decisions with confidence scores
- Scam detection results
- API call success/failure
- Performance metrics

## 🔒 Security

### API Security

- JWT token authentication required
- Admin-only access for pricing endpoints
- Rate limiting on all endpoints
- Input validation and sanitization

### Data Protection

- Sensitive API keys stored in environment variables
- Database connections encrypted
- Audit logging for all pricing changes
- Scam detection results logged for review

## 🚨 Troubleshooting

### Common Issues

1. **Spot Price API Failures**
   - Check API keys in environment variables
   - Verify API rate limits
   - Check network connectivity

2. **Market Scraping Failures**
   - Websites may block requests
   - Check scraping delays in configuration
   - Verify user agent strings

3. **Database Connection Issues**
   - Verify DATABASE_URL format
   - Check PostgreSQL server status
   - Ensure database exists

4. **Celery Task Failures**
   - Check Redis server status
   - Verify task time limits
   - Check worker logs

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
export DEBUG=true

# Start with debug mode
python main.py
```

## 📚 Examples

### Calculate Price for Coin

```python
import httpx

async def calculate_coin_price():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:13000/api/v1/pricing-agent/calculate-price",
            json={
                "coin_id": 1,
                "coin_type": "silver_eagle",
                "weight_oz": 1.0,
                "purity": 0.999,
                "force_update": True
            },
            headers={"Authorization": "Bearer your-jwt-token"}
        )
        return response.json()
```

### Detect Scam Price

```python
async def detect_scam():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:13000/api/v1/pricing-agent/scam-detection",
            json={
                "price": 50.00,
                "coin_type": "silver_eagle",
                "market_data": {
                    "avg_price": 25.00,
                    "min_price": 24.00,
                    "max_price": 26.00
                }
            }
        )
        return response.json()
```

## 🔄 Updates and Maintenance

### Regular Maintenance

1. **Weekly**: Review scam detection accuracy
2. **Monthly**: Update pricing configurations
3. **Quarterly**: Review API rate limits and costs
4. **Annually**: Update scraped website selectors

### Performance Optimization

- Monitor API response times
- Optimize database queries
- Adjust batch sizes for processing
- Review caching strategies

## 📞 Support

For issues or questions:

1. Check the troubleshooting section
2. Review logs for error messages
3. Test with debug mode enabled
4. Contact development team with specific error details

---

**Version**: 1.0  
**Last Updated**: 2025-01-27  
**Author**: Stream-Line AI




