from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine
from app.models import Base
import os
from dotenv import load_dotenv

load_dotenv()

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/miracle-coins")

def create_database():
    """Create database if it doesn't exist"""
    try:
        # Create engine
        engine = create_engine(DATABASE_URL)
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully!")
        
    except Exception as e:
        print(f"Error creating database: {e}")

def run_migrations():
    """Run Alembic migrations"""
    try:
        # Set up Alembic configuration
        alembic_cfg = Config("alembic.ini")
        
        # Run migrations
        command.upgrade(alembic_cfg, "head")
        print("Migrations completed successfully!")
        
    except Exception as e:
        print(f"Error running migrations: {e}")

if __name__ == "__main__":
    create_database()

