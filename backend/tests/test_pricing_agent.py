import pytest
import asyncio
from decimal import Decimal
from datetime import datetime, timezone
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.services.spot_price_service import SpotPriceService, SpotPriceData
from app.services.market_scraper_service import MarketScraperService, MarketData
from app.services.scam_detection_service import ScamDetectionService, ScamDetectionData
from app.services.pricing_engine_service import PricingEngineService, PricingInput, PricingResult
from app.services.shopify_pricing_service import ShopifyPricingService
from app.models.pricing_models import MarketPrice, PricingConfig, Coin
from app.schemas.pricing_schemas import (
    SpotPriceRequest, SpotPriceResponse, MarketDataRequest, MarketDataResponse,
    ScamDetectionRequest, ScamDetectionResponse, PricingInputRequest, PricingResultResponse
)

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db_session():
    """Create a test database session"""
    # Create tables
    from app.models.pricing_models import Base
    Base.metadata.create_all(bind=engine)
    
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Drop tables
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def sample_coin(db_session):
    """Create a sample coin for testing"""
    coin = Coin(
        id=1,
        title="Test Silver Eagle",
        description="Test coin for pricing",
        year=2023,
        mint_mark="P",
        grade="MS70",
        metal_type="silver_eagle",
        weight_oz=Decimal('1.0'),
        purity=Decimal('0.999'),
        quantity=1,
        sku="TEST-SE-2023",
        status="available"
    )
    db_session.add(coin)
    db_session.commit()
    return coin

@pytest.fixture
def sample_pricing_config(db_session):
    """Create a sample pricing configuration"""
    config = PricingConfig(
        coin_type="silver_eagle",
        min_markup=Decimal('1.300'),
        max_markup=Decimal('1.800'),
        default_markup=Decimal('1.550'),
        scam_threshold=Decimal('0.250'),
        confidence_threshold=Decimal('0.75'),
        price_update_threshold=Decimal('3.00'),
        is_active=True
    )
    db_session.add(config)
    db_session.commit()
    return config

# Spot Price Service Tests
class TestSpotPriceService:
    
    @pytest.fixture
    def spot_service(self):
        return SpotPriceService()
    
    @pytest.mark.asyncio
    async def test_fetch_spot_price_success(self, spot_service):
        """Test successful spot price fetching"""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {
                "rates": {"XAG": 25.50},
                "base": "USD"
            }
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            result = await spot_service.fetch_spot_price("metals-api")
            
            assert result is not None
            assert result.price == Decimal('25.50')
            assert result.currency == "USD"
            assert result.source == "metals-api"
            assert result.confidence > 0
    
    @pytest.mark.asyncio
    async def test_fetch_spot_price_failure(self, spot_service):
        """Test spot price fetching failure"""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.side_effect = Exception("API Error")
            
            result = await spot_service.fetch_spot_price("metals-api")
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_validate_price_valid(self, spot_service):
        """Test price validation with valid price"""
        with patch.object(spot_service, 'fetch_spot_price') as mock_fetch:
            mock_fetch.return_value = SpotPriceData(
                price=Decimal('25.00'),
                currency="USD",
                source="test",
                timestamp=datetime.now(timezone.utc),
                confidence=0.9
            )
            
            is_valid = await spot_service.validate_price(Decimal('30.00'))
            assert is_valid is True
    
    @pytest.mark.asyncio
    async def test_validate_price_invalid(self, spot_service):
        """Test price validation with invalid price"""
        with patch.object(spot_service, 'fetch_spot_price') as mock_fetch:
            mock_fetch.return_value = SpotPriceData(
                price=Decimal('25.00'),
                currency="USD",
                source="test",
                timestamp=datetime.now(timezone.utc),
                confidence=0.9
            )
            
            is_valid = await spot_service.validate_price(Decimal('50.00'))
            assert is_valid is False

# Market Scraper Service Tests
class TestMarketScraperService:
    
    @pytest.fixture
    def scraper_service(self):
        return MarketScraperService()
    
    @pytest.mark.asyncio
    async def test_scrape_market_data_success(self, scraper_service):
        """Test successful market data scraping"""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.text = """
            <html>
                <div class="s-item">
                    <span class="s-item__price">$25.50</span>
                    <h3 class="s-item__title">Silver Eagle</h3>
                </div>
                <div class="s-item">
                    <span class="s-item__price">$26.00</span>
                    <h3 class="s-item__title">Silver Eagle</h3>
                </div>
            </html>
            """
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            result = await scraper_service.scrape_market_data("silver_eagle", "ebay")
            
            assert result is not None
            assert result.avg_price > 0
            assert result.min_price > 0
            assert result.max_price > 0
            assert result.sample_size > 0
            assert result.source == "ebay"
    
    @pytest.mark.asyncio
    async def test_scrape_market_data_failure(self, scraper_service):
        """Test market data scraping failure"""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.side_effect = Exception("Scraping Error")
            
            result = await scraper_service.scrape_market_data("silver_eagle")
            
            assert result is None
    
    def test_extract_price_valid(self, scraper_service):
        """Test price extraction from text"""
        test_cases = [
            ("$25.50", Decimal('25.50')),
            ("$1,234.56", Decimal('1234.56')),
            ("25.50", Decimal('25.50')),
            ("$25", Decimal('25.00'))
        ]
        
        for text, expected in test_cases:
            result = scraper_service._extract_price(text)
            assert result == expected
    
    def test_extract_price_invalid(self, scraper_service):
        """Test price extraction with invalid text"""
        invalid_texts = ["", "invalid", "$0.00", "$10000.00"]
        
        for text in invalid_texts:
            result = scraper_service._extract_price(text)
            assert result is None

# Scam Detection Service Tests
class TestScamDetectionService:
    
    @pytest.fixture
    def scam_service(self):
        return ScamDetectionService()
    
    @pytest.mark.asyncio
    async def test_detect_scam_price_normal(self, scam_service):
        """Test scam detection with normal price"""
        market_data = {
            "avg_price": Decimal('25.00'),
            "min_price": Decimal('24.00'),
            "max_price": Decimal('26.00'),
            "spot_price": Decimal('20.00')
        }
        
        result = await scam_service.detect_scam_price(
            price=Decimal('25.00'),
            coin_type="silver_eagle",
            market_data=market_data
        )
        
        assert result is not None
        assert result.is_scam is False
        assert result.probability >= 0
        assert result.confidence >= 0
    
    @pytest.mark.asyncio
    async def test_detect_scam_price_suspicious(self, scam_service):
        """Test scam detection with suspicious price"""
        market_data = {
            "avg_price": Decimal('25.00'),
            "min_price": Decimal('24.00'),
            "max_price": Decimal('26.00'),
            "spot_price": Decimal('20.00')
        }
        
        result = await scam_service.detect_scam_price(
            price=Decimal('50.00'),  # Way above market
            coin_type="silver_eagle",
            market_data=market_data
        )
        
        assert result is not None
        assert result.is_scam is True
        assert result.probability > 0.5
        assert len(result.reasons) > 0
    
    def test_is_suspicious_round_number(self, scam_service):
        """Test suspicious round number detection"""
        suspicious_prices = [10.00, 25.00, 50.00, 100.00]
        normal_prices = [25.50, 26.75, 33.33]
        
        for price in suspicious_prices:
            assert scam_service._is_suspicious_round_number(price) is True
        
        for price in normal_prices:
            assert scam_service._is_suspicious_round_number(price) is False
    
    def test_detect_suspicious_patterns(self, scam_service):
        """Test suspicious pattern detection"""
        suspicious_patterns = [22.22, 33.33, 12.34, 23.45]
        normal_patterns = [25.50, 26.75, 33.21]
        
        for price in suspicious_patterns:
            assert scam_service._detect_suspicious_patterns(price) is True
        
        for price in normal_patterns:
            assert scam_service._detect_suspicious_patterns(price) is False

# Pricing Engine Service Tests
class TestPricingEngineService:
    
    @pytest.fixture
    def pricing_engine(self):
        return PricingEngineService()
    
    @pytest.fixture
    def sample_pricing_input(self):
        return PricingInput(
            coin_id=1,
            coin_type="silver_eagle",
            weight_oz=Decimal('1.0'),
            purity=Decimal('0.999'),
            override_price=None,
            force_update=False
        )
    
    @pytest.mark.asyncio
    async def test_calculate_price_success(self, pricing_engine, sample_pricing_input, db_session, sample_coin, sample_pricing_config):
        """Test successful price calculation"""
        with patch('app.services.pricing_engine_service.spot_price_service.fetch_spot_price') as mock_spot, \
             patch('app.services.pricing_engine_service.market_scraper_service.scrape_market_data') as mock_market, \
             patch('app.services.pricing_engine_service.scam_detection_service.detect_scam_price') as mock_scam:
            
            # Mock spot price
            mock_spot.return_value = SpotPriceData(
                price=Decimal('25.00'),
                currency="USD",
                source="test",
                timestamp=datetime.now(timezone.utc),
                confidence=0.9
            )
            
            # Mock market data
            mock_market.return_value = MarketData(
                avg_price=Decimal('26.00'),
                min_price=Decimal('25.50'),
                max_price=Decimal('26.50'),
                sample_size=10,
                source="test",
                timestamp=datetime.now(timezone.utc),
                confidence=0.8
            )
            
            # Mock scam detection
            mock_scam.return_value = ScamDetectionData(
                is_scam=False,
                probability=0.1,
                reasons=[],
                method="test",
                confidence=0.9
            )
            
            result = await pricing_engine.calculate_price(sample_pricing_input, db_session)
            
            assert result is not None
            assert result.final_price > 0
            assert result.melt_value > 0
            assert result.markup_factor > 1.0
            assert result.confidence_score > 0
            assert result.scam_detected is False
    
    def test_calculate_melt_value(self, pricing_engine):
        """Test melt value calculation"""
        weight = Decimal('1.0')
        purity = Decimal('0.999')
        spot_price = Decimal('25.00')
        
        melt_value = pricing_engine._calculate_melt_value(weight, purity, spot_price)
        expected = weight * purity * spot_price
        
        assert melt_value == expected
    
    def test_calculate_markup_factor(self, pricing_engine):
        """Test markup factor calculation"""
        final_price = Decimal('30.00')
        melt_value = Decimal('20.00')
        
        markup_factor = pricing_engine._calculate_markup_factor(final_price, melt_value)
        expected = final_price / melt_value
        
        assert markup_factor == expected
    
    @pytest.mark.asyncio
    async def test_should_update_price(self, pricing_engine, db_session):
        """Test price update threshold logic"""
        # Test with significant change
        should_update = await pricing_engine.should_update_price(
            coin_id=1,
            new_price=Decimal('30.00'),
            db=db_session
        )
        assert should_update is True
        
        # Test with small change
        should_update = await pricing_engine.should_update_price(
            coin_id=1,
            new_price=Decimal('25.10'),
            db=db_session
        )
        assert should_update is False

# Shopify Pricing Service Tests
class TestShopifyPricingService:
    
    @pytest.fixture
    def shopify_service(self):
        return ShopifyPricingService()
    
    @pytest.mark.asyncio
    async def test_update_product_price_success(self, shopify_service):
        """Test successful product price update"""
        with patch.object(shopify_service, '_get_product') as mock_get, \
             patch.object(shopify_service, '_update_product_in_shopify') as mock_update:
            
            mock_get.return_value = Mock(
                id="123",
                title="Test Product",
                price=Decimal('25.00')
            )
            mock_update.return_value = True
            
            result = await shopify_service.update_product_price("123", Decimal('30.00'))
            
            assert result.success is True
            assert result.old_price == Decimal('25.00')
            assert result.new_price == Decimal('30.00')
    
    @pytest.mark.asyncio
    async def test_update_product_price_failure(self, shopify_service):
        """Test product price update failure"""
        with patch.object(shopify_service, '_get_product') as mock_get:
            mock_get.return_value = None
            
            result = await shopify_service.update_product_price("123", Decimal('30.00'))
            
            assert result.success is False
            assert "Product not found" in result.error_message
    
    @pytest.mark.asyncio
    async def test_should_update_price_threshold(self, shopify_service):
        """Test price update threshold logic"""
        # Test with significant change
        should_update = await shopify_service._should_update_price(
            Decimal('25.00'),
            Decimal('30.00')
        )
        assert should_update is True
        
        # Test with small change
        should_update = await shopify_service._should_update_price(
            Decimal('25.00'),
            Decimal('25.50')
        )
        assert should_update is False

# Integration Tests
class TestPricingIntegration:
    
    @pytest.mark.asyncio
    async def test_full_pricing_workflow(self, db_session, sample_coin, sample_pricing_config):
        """Test complete pricing workflow integration"""
        # This would test the full workflow from spot price to final price
        # For now, it's a placeholder for more comprehensive integration tests
        assert True
    
    @pytest.mark.asyncio
    async def test_scam_detection_integration(self, db_session, sample_coin):
        """Test scam detection integration with pricing"""
        # This would test scam detection in the context of pricing
        assert True

# Performance Tests
class TestPricingPerformance:
    
    @pytest.mark.asyncio
    async def test_batch_pricing_performance(self):
        """Test batch pricing performance"""
        # This would test performance with large batches
        assert True
    
    @pytest.mark.asyncio
    async def test_concurrent_pricing_requests(self):
        """Test concurrent pricing requests"""
        # This would test handling of concurrent requests
        assert True

# Error Handling Tests
class TestPricingErrorHandling:
    
    @pytest.mark.asyncio
    async def test_api_failure_handling(self):
        """Test handling of API failures"""
        # This would test error handling when external APIs fail
        assert True
    
    @pytest.mark.asyncio
    async def test_database_error_handling(self):
        """Test handling of database errors"""
        # This would test error handling when database operations fail
        assert True

# Test Configuration
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# Test Data Fixtures
@pytest.fixture
def sample_spot_price_data():
    """Sample spot price data for testing"""
    return SpotPriceData(
        price=Decimal('25.00'),
        currency="USD",
        source="test",
        timestamp=datetime.now(timezone.utc),
        confidence=0.9
    )

@pytest.fixture
def sample_market_data():
    """Sample market data for testing"""
    return MarketData(
        avg_price=Decimal('26.00'),
        min_price=Decimal('25.50'),
        max_price=Decimal('26.50'),
        sample_size=10,
        source="test",
        timestamp=datetime.now(timezone.utc),
        confidence=0.8
    )

@pytest.fixture
def sample_scam_detection_data():
    """Sample scam detection data for testing"""
    return ScamDetectionData(
        is_scam=False,
        probability=0.1,
        reasons=[],
        method="test",
        confidence=0.9
    )




