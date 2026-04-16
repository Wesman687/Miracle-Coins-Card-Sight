from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Coin
from decimal import Decimal

def seed_sample_data():
    """Add some sample coins for testing."""
    db = SessionLocal()
    
    try:
        # Check if we already have coins
        existing_coins = db.query(Coin).count()
        if existing_coins > 0:
            print(f"Database already has {existing_coins} coins. Skipping seed.")
            return
        
        sample_coins = [
            Coin(
                name="1921 Morgan Silver Dollar",
                year=1921,
                denomination="1 Dollar",
                mint_mark="S",
                grade="MS-65",
                category="Morgan Dollars",
                description="Beautiful Morgan silver dollar in excellent condition",
                is_silver=True,
                silver_percent=90.0,
                silver_content_oz=Decimal("0.7734"),
                paid_price=Decimal("45.00"),
                price_strategy="spot_multiplier",
                price_multiplier=Decimal("1.30"),
                quantity=1,
                status="active",
                created_by="system"
            ),
            Coin(
                name="1964 Kennedy Half Dollar",
                year=1964,
                denomination="50 Cents",
                mint_mark="D",
                grade="MS-63",
                category="Kennedy Halves",
                description="Classic Kennedy half dollar",
                is_silver=True,
                silver_percent=90.0,
                silver_content_oz=Decimal("0.3617"),
                paid_price=Decimal("12.00"),
                price_strategy="spot_multiplier",
                price_multiplier=Decimal("1.30"),
                quantity=5,
                status="active",
                created_by="system"
            ),
            Coin(
                name="1943 Steel Penny",
                year=1943,
                denomination="1 Cent",
                mint_mark="S",
                grade="AU-55",
                category="Wheat Pennies",
                description="Rare steel penny from WWII era",
                is_silver=False,
                paid_price=Decimal("2.50"),
                price_strategy="fixed_price",
                price_multiplier=Decimal("1.00"),
                quantity=1,
                status="active",
                created_by="system"
            ),
            Coin(
                name="2021 Silver Eagle",
                year=2021,
                denomination="1 Ounce",
                mint_mark="W",
                grade="MS-70",
                category="Silver Eagles",
                description="Modern silver eagle in perfect condition",
                is_silver=True,
                silver_percent=99.9,
                silver_content_oz=Decimal("1.0000"),
                paid_price=Decimal("35.00"),
                price_strategy="spot_multiplier",
                price_multiplier=Decimal("1.30"),
                quantity=10,
                status="active",
                created_by="system"
            ),
            Coin(
                name="1881 Morgan Silver Dollar",
                year=1881,
                denomination="1 Dollar",
                mint_mark="CC",
                grade="VF-20",
                category="Morgan Dollars",
                description="Carson City mint Morgan dollar",
                is_silver=True,
                silver_percent=90.0,
                silver_content_oz=Decimal("0.7734"),
                paid_price=Decimal("85.00"),
                price_strategy="spot_multiplier",
                price_multiplier=Decimal("1.30"),
                quantity=1,
                status="active",
                created_by="system"
            )
        ]
        
        for coin in sample_coins:
            db.add(coin)
        
        db.commit()
        print(f"Successfully added {len(sample_coins)} sample coins to the database.")
        
    except Exception as e:
        print(f"Error seeding data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_sample_data()
