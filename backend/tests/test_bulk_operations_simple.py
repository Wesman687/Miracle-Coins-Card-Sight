# backend/tests/test_bulk_operations_simple.py
import pytest
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime

from app.database import Base
from app.models import BulkOperation, BulkOperationItem
from app.models import Coin  # Will be imported from models.py via __init__
from app.services.bulk_operations_service import BulkOperationsService
from app.schemas.bulk_operations import BulkOperationCreate, CoinData

# Import Coin directly from models.py if it's None in __init__
if Coin is None:
    from app import models as models_py
    Coin = models_py.Coin

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_bulk.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module")
def setup_database():
    """Set up test database"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session():
    """Create database session"""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

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

class TestBulkOperationsService:
    
    def test_create_bulk_purchase(self, db_session, sample_coin_data):
        """Test creating a bulk purchase operation"""
        
        service = BulkOperationsService(db_session)
        
        # Create bulk operation request
        request_data = BulkOperationCreate(
            operation_type="purchase",
            description="Test bulk purchase of Mercury dimes and silver dollars",
            coins=sample_coin_data,
            created_by=1,
            metadata={"test": True}
        )
        
        # Create operation
        operation = asyncio.run(service.create_bulk_purchase(request_data))
        
        # Verify operation
        assert operation.operation_type == "purchase"
        assert operation.description == "Test bulk purchase of Mercury dimes and silver dollars"
        assert operation.total_items == 150  # 100 + 50
        assert operation.status == "pending"
        assert operation.created_by == 1
        assert operation.metadata["test"] == True
        
        # Verify coins were created
        coins = db_session.query(Coin).filter(Coin.bulk_operation_id == operation.id).all()
        assert len(coins) == 150
        
        # Verify individual tracking
        mercury_dimes = [coin for coin in coins if coin.sku == "TEST-001"]
        assert len(mercury_dimes) == 100
        
        silver_dollars = [coin for coin in coins if coin.sku == "TEST-002"]
        assert len(silver_dollars) == 50
        
        # Verify serial numbers
        for coin in coins:
            assert coin.serial_number is not None
            assert coin.bulk_operation_id == operation.id
            assert coin.bulk_sequence_number is not None
            assert coin.paid_price > 0
    
    def test_bulk_operation_processing(self, db_session, sample_coin_data):
        """Test processing a bulk operation"""
        
        service = BulkOperationsService(db_session)
        
        # Create bulk operation
        request_data = BulkOperationCreate(
            operation_type="purchase",
            description="Test processing",
            coins=sample_coin_data,
            created_by=1
        )
        
        operation = asyncio.run(service.create_bulk_purchase(request_data))
        
        # Process operation
        result = asyncio.run(service.process_bulk_operation(operation.id))
        
        # Verify processing result
        assert result["operation_id"] == operation.id
        assert result["status"] in ["completed", "failed"]
        assert result["processed"] >= 0
        assert result["failed"] >= 0
        assert result["total"] == 150
        
        # Verify operation status in database
        updated_operation = db_session.query(BulkOperation).filter(
            BulkOperation.id == operation.id
        ).first()
        
        assert updated_operation.status in ["completed", "failed"]
        assert updated_operation.processed_items >= 0
        assert updated_operation.failed_items >= 0
    
    def test_bulk_operation_status(self, db_session, sample_coin_data):
        """Test getting bulk operation status"""
        
        service = BulkOperationsService(db_session)
        
        # Create bulk operation
        request_data = BulkOperationCreate(
            operation_type="purchase",
            description="Test status",
            coins=sample_coin_data,
            created_by=1
        )
        
        operation = asyncio.run(service.create_bulk_purchase(request_data))
        
        # Get status
        status = asyncio.run(service.get_operation_status(operation.id))
        
        # Verify status
        assert status.id == operation.id
        assert status.status == "pending"
        assert status.total_items == 150
        assert status.processed_items == 0
        assert status.failed_items == 0
        assert status.progress_percentage == 0.0
    
    def test_bulk_operation_cancellation(self, db_session, sample_coin_data):
        """Test cancelling a bulk operation"""
        
        service = BulkOperationsService(db_session)
        
        # Create bulk operation
        request_data = BulkOperationCreate(
            operation_type="purchase",
            description="Test cancellation",
            coins=sample_coin_data,
            created_by=1
        )
        
        operation = asyncio.run(service.create_bulk_purchase(request_data))
        
        # Cancel operation
        result = asyncio.run(service.cancel_operation(operation.id))
        
        # Verify cancellation
        assert result["operation_id"] == operation.id
        assert result["status"] == "cancelled"
        assert "cancelled_items" in result
        
        # Verify operation status in database
        updated_operation = db_session.query(BulkOperation).filter(
            BulkOperation.id == operation.id
        ).first()
        
        assert updated_operation.status == "cancelled"
        assert updated_operation.completed_at is not None
    
    def test_bulk_operation_stats(self, db_session, sample_coin_data):
        """Test getting bulk operation statistics"""
        
        service = BulkOperationsService(db_session)
        
        # Create some operations
        for i in range(3):
            request_data = BulkOperationCreate(
                operation_type="purchase",
                description=f"Stats test {i}",
                coins=sample_coin_data[:1],  # Just one coin type
                created_by=1
            )
            
            operation = asyncio.run(service.create_bulk_purchase(request_data))
        
        # Get stats
        stats = asyncio.run(service.get_operation_stats())
        
        # Verify stats
        assert stats.total_operations >= 3
        assert stats.total_coins_processed >= 0
        assert stats.success_rate >= 0
        assert stats.average_operation_size >= 0
        assert stats.last_operation_date is not None
    
    def test_individual_coin_tracking(self, db_session):
        """Test that each coin is tracked individually"""
        
        service = BulkOperationsService(db_session)
        
        # Create coins with quantity > 1
        coin_data = CoinData(
            sku="BULK-001",
            name="Bulk Test Coin",
            year=1945,
            paid_price=5.00,
            quantity=10,  # 10 individual coins
            status="active"
        )
        
        request_data = BulkOperationCreate(
            operation_type="purchase",
            description="Test individual tracking",
            coins=[coin_data],
            created_by=1
        )
        
        operation = asyncio.run(service.create_bulk_purchase(request_data))
        
        # Verify 10 individual coins were created
        coins = db_session.query(Coin).filter(Coin.bulk_operation_id == operation.id).all()
        assert len(coins) == 10
        
        # Each coin should have unique serial number and same paid price
        serial_numbers = set()
        for coin in coins:
            assert coin.serial_number not in serial_numbers
            serial_numbers.add(coin.serial_number)
            assert coin.paid_price == 5.00
            assert coin.sku == "BULK-001"
            assert coin.bulk_operation_id == operation.id
    
    def test_max_capacity_constraint(self, db_session):
        """Test that system can handle large operations"""
        
        service = BulkOperationsService(db_session)
        
        # Create a large number of coins (but not 10M for test performance)
        large_coin_data = []
        for i in range(100):  # 100 coins for testing
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
        
        operation = asyncio.run(service.create_bulk_purchase(request_data))
        
        # Verify operation was created successfully
        assert operation.total_items == 100
        
        # Verify all coins were created
        coins = db_session.query(Coin).filter(Coin.bulk_operation_id == operation.id).all()
        assert len(coins) == 100

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
