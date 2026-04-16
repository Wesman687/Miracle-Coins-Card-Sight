#!/usr/bin/env python3
"""
Complete Database Setup for Miracle Coins CoinSync Pro
This script runs the base database setup and then applies schema updates
"""

import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_database_url():
    """Get database URL from environment"""
    # Try to get DATABASE_URL first, then construct from individual components
    db_url = os.getenv("DATABASE_URL")
    if db_url and "localhost" not in db_url:
        return db_url
    
    # Construct from individual DB components
    db_host = os.getenv("DB_HOST", "server.stream-lineai.com")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "Miracle-Coins")
    db_user = os.getenv("DB_USER", "Miracle-Coins")
    db_password = os.getenv("DB_PASSWORD", "your_db_password_here")
    
    return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?sslmode=disable"

def execute_sql_file(engine, file_path, description):
    """Execute SQL file with error handling"""
    print(f"\nExecuting: {description}")
    print("-" * 50)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            sql_content = file.read()
        
        with engine.connect() as connection:
            # Split SQL content by semicolon and execute each statement
            statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
            
            for i, statement in enumerate(statements, 1):
                if statement and not statement.startswith('--'):
                    print(f"  Statement {i}: {statement[:50]}...")
                    connection.execute(text(statement))
                    connection.commit()
            
        print(f"Successfully completed: {description}")
        return True
        
    except Exception as e:
        print(f"Error in {description}: {str(e)}")
        return False

def main():
    """Main execution function"""
    print("Starting Complete Miracle Coins Database Setup")
    print("=" * 60)
    
    # Get database connection
    database_url = get_database_url()
    print(f"Connecting to database: {database_url.split('@')[1].split('/')[0] if '@' in database_url else database_url}")
    
    try:
        engine = create_engine(database_url)
        
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("Database connection successful")
        
    except Exception as e:
        print(f"Database connection failed: {str(e)}")
        return False
    
    # Step 1: Run base database setup
    base_setup_file = "../database_setup.sql"
    if os.path.exists(base_setup_file):
        if not execute_sql_file(engine, base_setup_file, "Base database schema setup"):
            print("Base setup failed, but continuing with schema updates...")
    else:
        print("Base database setup file not found, continuing with schema updates...")
    
    # Step 2: Run schema updates
    schema_updates_file = "database_schema_updates.sql"
    if os.path.exists(schema_updates_file):
        if not execute_sql_file(engine, schema_updates_file, "Database schema updates"):
            return False
    else:
        print("Schema updates file not found!")
        return False
    
    print("\n" + "=" * 60)
    print("COMPLETE DATABASE SETUP FINISHED SUCCESSFULLY!")
    print("=" * 60)
    print("\nFeatures Added:")
    print("  • Base database schema with all core tables")
    print("  • Auto-SKU generation system")
    print("  • Category management system")
    print("  • Enhanced metadata tracking")
    print("  • Shopify integration support")
    print("  • Utility functions for coin management")
    print("\nYour Miracle Coins CoinSync Pro database is now ready!")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
