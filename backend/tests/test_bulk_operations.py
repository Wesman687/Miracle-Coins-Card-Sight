# backend/tests/test_bulk_operations.py
import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime
import json

from app.main import app
from app.database import get_db, Base
from app.models import Coin, BulkOperation, BulkOperationItem
from app.schemas.bulk_operations import BulkOperationCreate, CoinData

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
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
    """Set up test database"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)

@pytest.fixture
def sample_coin_data():
    """Sample coin data for testing"""
    return [
        CoinData(
            sku="TEST-001",
            name="Test Mercury Dime",
            year=1943,
            denomination="Dime",
            mint_mark="D",
            grade="MS-65",
            category="Silver",
            description="Test coin for bulk operations",
            condition_notes="Excellent condition",
            is_silver=True,
            silver_percent=90.0,
            silver_content_oz=0.0723,
            paid_price=2.00,
            price_strategy="fixed_price",
            quantity=100,  # 100 individual coins
            status="active"
        ),
        CoinData(
            sku="TEST-002",
            name="Test Silver Dollar",
            year=1921,
            denomination="Dollar",
            mint_mark="S",
            grade="MS-63",
            category="Silver",
            description="Test silver dollar",
            condition_notes="Good condition",
            is_silver=True,
            silver_percent=90.0,
            silver_content_oz=0.7734,
            paid_price=25.00,
            price_strategy="fixed_price",
            quantity=50,  # 50 individual coins
            status="active"
        )
    ]

class TestBulkOperations:
    
    def test_create_bulk_purchase(self, client, setup_database, sample_coin_data):
        """Test creating a bulk purchase operation"""
        
        # Create bulk operation request
        request_data = BulkOperationCreate(
            operation_type="purchase",
            description="Test bulk purchase of Mercury dimes and silver dollars",
            coins=sample_coin_data,
            created_by=1,
            metadata={"test": True}
        )
        
        # Make request
        response = client.post(
            "/api/v1/bulk-operations/purchase",
            json=request_data.dict()
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        assert data["operation_type"] == "purchase"
        assert data["description"] == "Test bulk purchase of Mercury dimes and silver dollars"
        assert data["total_items"] == 150  # 100 + 50
        assert data["status"] == "pending"
        assert data["created_by"] == 1
        assert data["metadata"]["test"] == True
        
        # Verify operation was created in database
        operation_id = data["id"]
        
        # Get operation status
        status_response = client.get(f"/api/v1/bulk-operations/{operation_id}/status")
        assert status_response.status_code == 200
        
        status_data = status_response.json()
        assert status_data["id"] == operation_id
        assert status_data["total_items"] == 150
        assert status_data["progress_percentage"] >= 0
    
    def test_bulk_purchase_individual_tracking(self, client, setup_database, sample_coin_data):
        """Test that bulk purchase creates individual coins"""
        
        # Create bulk operation
        request_data = BulkOperationCreate(
            operation_type="purchase",
            description="Test individual coin tracking",
            coins=sample_coin_data,
            created_by=1
        )
        
        response = client.post(
            "/api/v1/bulk-operations/purchase",
            json=request_data.dict()
        )
        
        assert response.status_code == 200
        operation_id = response.json()["id"]
        
        # Wait for processing to complete (in real scenario, this would be async)
        import time
        time.sleep(2)
        
        # Check that individual coins were created
        coins_response = client.get("/api/v1/coins/")
        assert coins_response.status_code == 200
        
        coins_data = coins_response.json()
        assert len(coins_data) >= 150  # Should have at least 150 coins
        
        # Verify serial numbers were generated
        mercury_dimes = [coin for coin in coins_data if coin["sku"] == "TEST-001"]
        assert len(mercury_dimes) == 100
        
        # Check serial numbers
        for i, coin in enumerate(mercury_dimes):
            expected_serial = f"TEST-001-{i+1:06d}-001"  # First coin of first batch
            assert coin["serial_number"] is not None
            assert coin["bulk_operation_id"] == operation_id
            assert coin["bulk_sequence_number"] == 1
            assert coin["paid_price"] == 2.00
    
    def test_bulk_operation_status_tracking(self, client, setup_database, sample_coin_data):
        """Test bulk operation status tracking"""
        
        # Create bulk operation
        request_data = BulkOperationCreate(
            operation_type="purchase",
            description="Test status tracking",
            coins=sample_coin_data,
            created_by=1
        )
        
        response = client.post(
            "/api/v1/bulk-operations/purchase",
            json=request_data.dict()
        )
        
        assert response.status_code == 200
        operation_id = response.json()["id"]
        
        # Get status multiple times to track progress
        statuses = []
        for _ in range(5):
            status_response = client.get(f"/api/v1/bulk-operations/{operation_id}/status")
            assert status_response.status_code == 200
            status_data = status_response.json()
            statuses.append(status_data["status"])
            time.sleep(1)
        
        # Status should progress from pending to processing to completed
        assert "pending" in statuses or "processing" in statuses or "completed" in statuses
    
    def test_bulk_operation_cancellation(self, client, setup_database, sample_coin_data):
        """Test cancelling a bulk operation"""
        
        # Create bulk operation
        request_data = BulkOperationCreate(
            operation_type="purchase",
            description="Test cancellation",
            coins=sample_coin_data,
            created_by=1
        )
        
        response = client.post(
            "/api/v1/bulk-operations/purchase",
            json=request_data.dict()
        )
        
        assert response.status_code == 200
        operation_id = response.json()["id"]
        
        # Cancel operation
        cancel_response = client.post(f"/api/v1/bulk-operations/{operation_id}/cancel")
        assert cancel_response.status_code == 200
        
        cancel_data = cancel_response.json()
        assert cancel_data["status"] == "cancelled"
        assert "cancelled_items" in cancel_data
    
    def test_bulk_operation_listing(self, client, setup_database, sample_coin_data):
        """Test listing bulk operations"""
        
        # Create multiple operations
        for i in range(3):
            request_data = BulkOperationCreate(
                operation_type="purchase",
                description=f"Test operation {i}",
                coins=sample_coin_data[:1],  # Just one coin type
                created_by=1
            )
            
            response = client.post(
                "/api/v1/bulk-operations/purchase",
                json=request_data.dict()
            )
            assert response.status_code == 200
        
        # List operations
        list_response = client.get("/api/v1/bulk-operations/")
        assert list_response.status_code == 200
        
        list_data = list_response.json()
        assert list_data["total"] >= 3
        assert len(list_data["operations"]) >= 3
        assert list_data["page"] == 1
        assert list_data["page_size"] == 50
    
    def test_bulk_operation_stats(self, client, setup_database, sample_coin_data):
        """Test bulk operation statistics"""
        
        # Create some operations
        for i in range(2):
            request_data = BulkOperationCreate(
                operation_type="purchase",
                description=f"Stats test {i}",
                coins=sample_coin_data[:1],
                created_by=1
            )
            
            response = client.post(
                "/api/v1/bulk-operations/purchase",
                json=request_data.dict()
            )
            assert response.status_code == 200
        
        # Get stats
        stats_response = client.get("/api/v1/bulk-operations/stats")
        assert stats_response.status_code == 200
        
        stats_data = stats_response.json()
        assert stats_data["total_operations"] >= 2
        assert stats_data["total_coins_processed"] >= 0
        assert stats_data["success_rate"] >= 0
        assert stats_data["average_operation_size"] >= 0
    
    def test_bulk_operation_validation(self, client, setup_database):
        """Test bulk operation validation"""
        
        # Test empty coins list
        request_data = BulkOperationCreate(
            operation_type="purchase",
            description="Test validation",
            coins=[],  # Empty list
            created_by=1
        )
        
        response = client.post(
            "/api/v1/bulk-operations/purchase",
            json=request_data.dict()
        )
        
        assert response.status_code == 422  # Validation error
        
        # Test invalid coin data
        invalid_coin = CoinData(
            sku="",  # Empty SKU
            name="Test",
            year=1800,
            paid_price=-1.0,  # Negative price
            quantity=1
        )
        
        request_data = BulkOperationCreate(
            operation_type="purchase",
            description="Test validation",
            coins=[invalid_coin],
            created_by=1
        )
        
        response = client.post(
            "/api/v1/bulk-operations/purchase",
            json=request_data.dict()
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_bulk_operation_max_capacity(self, client, setup_database):
        """Test bulk operation with maximum capacity (10M coins)"""
        
        # Create a large number of coins (but not 10M for test performance)
        large_coin_data = []
        for i in range(1000):  # 1000 coins for testing
            coin = CoinData(
                sku=f"LARGE-{i:06d}",
                name=f"Large Test Coin {i}",
                year=1900 + (i % 100),
                paid_price=1.0,
                quantity=1
            )
            large_coin_data.append(coin)
        
        request_data = BulkOperationCreate(
            operation_type="purchase",
            description="Test large capacity",
            coins=large_coin_data,
            created_by=1
        )
        
        response = client.post(
            "/api/v1/bulk-operations/purchase",
            json=request_data.dict()
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_items"] == 1000

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
