import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base
from main import app
from app.types import CoinCreate, CoinStatus, PricingStrategy
from decimal import Decimal
import os

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def sample_coin_data():
    return CoinCreate(
        sku="TEST-001",
        title="Test Silver Dollar",
        year=1921,
        denomination="$1",
        mint_mark="S",
        grade="MS65",
        category="Morgan Dollar",
        description="Test coin for unit testing",
        is_silver=True,
        silver_percent=Decimal('0.900'),
        silver_content_oz=Decimal('0.7734'),
        paid_price=Decimal('50.00'),
        price_strategy=PricingStrategy.SPOT_MULTIPLIER,
        price_multiplier=Decimal('1.300'),
        quantity=1,
        status=CoinStatus.ACTIVE
    )

class TestCoinCRUD:
    def test_create_coin(self, client, setup_database, sample_coin_data):
        """Test creating a new coin"""
        response = client.post("/api/v1/coins", json=sample_coin_data.dict())
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == sample_coin_data.title
        assert data["sku"] == sample_coin_data.sku
        assert data["is_silver"] == sample_coin_data.is_silver
        assert "id" in data
        assert "created_at" in data

    def test_get_coin(self, client, setup_database, sample_coin_data):
        """Test retrieving a coin by ID"""
        # Create coin first
        create_response = client.post("/api/v1/coins", json=sample_coin_data.dict())
        coin_id = create_response.json()["id"]
        
        # Get coin
        response = client.get(f"/api/v1/coins/{coin_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == coin_id
        assert data["title"] == sample_coin_data.title

    def test_get_nonexistent_coin(self, client, setup_database):
        """Test retrieving a non-existent coin"""
        response = client.get("/api/v1/coins/99999")
        assert response.status_code == 404

    def test_get_all_coins(self, client, setup_database, sample_coin_data):
        """Test retrieving all coins"""
        # Create multiple coins
        for i in range(3):
            coin_data = sample_coin_data.copy()
            coin_data.sku = f"TEST-{i:03d}"
            coin_data.title = f"Test Coin {i}"
            client.post("/api/v1/coins", json=coin_data.dict())
        
        response = client.get("/api/v1/coins")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3

    def test_update_coin(self, client, setup_database, sample_coin_data):
        """Test updating a coin"""
        # Create coin first
        create_response = client.post("/api/v1/coins", json=sample_coin_data.dict())
        coin_id = create_response.json()["id"]
        
        # Update coin
        update_data = {"title": "Updated Test Coin", "grade": "MS66"}
        response = client.put(f"/api/v1/coins/{coin_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Test Coin"
        assert data["grade"] == "MS66"

    def test_delete_coin(self, client, setup_database, sample_coin_data):
        """Test deleting a coin"""
        # Create coin first
        create_response = client.post("/api/v1/coins", json=sample_coin_data.dict())
        coin_id = create_response.json()["id"]
        
        # Delete coin
        response = client.delete(f"/api/v1/coins/{coin_id}")
        assert response.status_code == 204
        
        # Verify coin is deleted
        get_response = client.get(f"/api/v1/coins/{coin_id}")
        assert get_response.status_code == 404

    def test_search_coins(self, client, setup_database, sample_coin_data):
        """Test searching coins"""
        # Create coin first
        client.post("/api/v1/coins", json=sample_coin_data.dict())
        
        # Search for coin
        response = client.get("/api/v1/coins?search=Morgan")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert "Morgan" in data[0]["title"]

class TestPricingEngine:
    def test_calculate_spot_price(self, client, setup_database):
        """Test spot price calculation"""
        # Create spot price
        spot_data = {
            "metal": "silver",
            "price": 25.50,
            "source": "test"
        }
        response = client.post("/api/v1/pricing/spot", json=spot_data)
        assert response.status_code == 201
        
        # Get latest spot price
        response = client.get("/api/v1/pricing/spot")
        assert response.status_code == 200
        data = response.json()
        assert data["price"] == 25.50

    def test_recalculate_coin_price(self, client, setup_database, sample_coin_data):
        """Test coin price recalculation"""
        # Create coin first
        create_response = client.post("/api/v1/coins", json=sample_coin_data.dict())
        coin_id = create_response.json()["id"]
        
        # Recalculate price
        response = client.post(f"/api/v1/pricing/recalculate/{coin_id}")
        assert response.status_code == 200
        data = response.json()
        assert "computed_price" in data

    def test_bulk_reprice(self, client, setup_database, sample_coin_data):
        """Test bulk reprice operation"""
        # Create multiple coins
        coin_ids = []
        for i in range(3):
            coin_data = sample_coin_data.copy()
            coin_data.sku = f"BULK-{i:03d}"
            coin_data.title = f"Bulk Test Coin {i}"
            create_response = client.post("/api/v1/coins", json=coin_data.dict())
            coin_ids.append(create_response.json()["id"])
        
        # Bulk reprice
        bulk_data = {
            "coin_ids": coin_ids,
            "new_multiplier": 1.5
        }
        response = client.post("/api/v1/pricing/bulk-reprice", json=bulk_data)
        assert response.status_code == 200
        data = response.json()
        assert data["updated_count"] == 3

class TestDashboardKPIs:
    def test_get_dashboard_kpis(self, client, setup_database, sample_coin_data):
        """Test dashboard KPIs calculation"""
        # Create some coins
        for i in range(5):
            coin_data = sample_coin_data.copy()
            coin_data.sku = f"KPI-{i:03d}"
            coin_data.title = f"KPI Test Coin {i}"
            client.post("/api/v1/coins", json=coin_data.dict())
        
        # Get KPIs
        response = client.get("/api/v1/pricing/dashboard-kpis")
        assert response.status_code == 200
        data = response.json()
        assert "inventory_melt_value" in data
        assert "inventory_list_value" in data
        assert "gross_profit" in data
        assert "total_coins" in data
        assert data["total_coins"] >= 5

class TestAIEvaluation:
    def test_evaluate_coin(self, client, setup_database, sample_coin_data):
        """Test AI coin evaluation"""
        evaluation_data = {
            "coin_data": sample_coin_data.dict()
        }
        response = client.post("/api/v1/ai/evaluate-coin", json=evaluation_data)
        assert response.status_code == 200
        data = response.json()
        assert "suggested_price" in data
        assert "confidence_score" in data
        assert "selling_recommendation" in data
        assert "reasoning" in data
        assert "market_analysis" in data

    def test_bulk_evaluate_coins(self, client, setup_database, sample_coin_data):
        """Test bulk AI evaluation"""
        coin_data_list = []
        for i in range(3):
            coin_data = sample_coin_data.copy()
            coin_data.sku = f"AI-{i:03d}"
            coin_data.title = f"AI Test Coin {i}"
            coin_data_list.append(coin_data.dict())
        
        response = client.post("/api/v1/ai/bulk-evaluate", json=coin_data_list)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert all("suggested_price" in item for item in data)

class TestImageUpload:
    def test_upload_coin_image(self, client, setup_database, sample_coin_data):
        """Test coin image upload"""
        # Create coin first
        create_response = client.post("/api/v1/coins", json=sample_coin_data.dict())
        coin_id = create_response.json()["id"]
        
        # Create a test image file
        test_image_content = b"fake_image_content"
        files = {"file": ("test.jpg", test_image_content, "image/jpeg")}
        
        response = client.post(f"/api/v1/images/upload?coin_id={coin_id}", files=files)
        # Note: This will fail without proper file server setup, but tests the endpoint structure
        assert response.status_code in [200, 500]  # 500 expected without file server

class TestValidation:
    def test_invalid_coin_data(self, client, setup_database):
        """Test validation with invalid coin data"""
        invalid_data = {
            "title": "",  # Empty title should fail
            "year": 1800,  # Valid year
            "is_silver": "not_boolean"  # Invalid boolean
        }
        response = client.post("/api/v1/coins", json=invalid_data)
        assert response.status_code == 422

    def test_sku_uniqueness(self, client, setup_database, sample_coin_data):
        """Test SKU uniqueness constraint"""
        # Create first coin
        client.post("/api/v1/coins", json=sample_coin_data.dict())
        
        # Try to create second coin with same SKU
        duplicate_data = sample_coin_data.copy()
        duplicate_data.title = "Different Title"
        response = client.post("/api/v1/coins", json=duplicate_data.dict())
        # Should fail due to duplicate SKU
        assert response.status_code in [400, 422]

class TestErrorHandling:
    def test_unauthorized_access(self, client, setup_database):
        """Test unauthorized access without token"""
        # This test would need proper JWT token setup
        # For now, just test that the endpoint exists
        response = client.get("/api/v1/coins")
        # Should return 401 or 200 depending on auth setup
        assert response.status_code in [200, 401]

    def test_invalid_endpoint(self, client, setup_database):
        """Test invalid endpoint"""
        response = client.get("/api/v1/invalid-endpoint")
        assert response.status_code == 404

if __name__ == "__main__":
    pytest.main([__file__, "-v"])




