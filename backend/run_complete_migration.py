#!/usr/bin/env python3
"""
Miracle Coins Database Migration Script
Run the complete database migration with collections and flexible pricing
"""

import psycopg2
import os
from pathlib import Path

def get_db_connection():
    """Get database connection using environment variables or defaults"""
    try:
        # Try environment variables first
        db_host = os.getenv('DB_HOST', 'server.stream-lineai.com')
        db_port = os.getenv('DB_PORT', '5432')
        db_name = os.getenv('DB_NAME', 'Miracle-Coins')
        db_user = os.getenv('DB_USER', 'Miracle-Coins')
        db_password = os.getenv('DB_PASSWORD', 'your_db_password_here')
        
        print(f"Connecting to database: {db_host}:{db_port}/{db_name}")
        
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=db_password
        )
        
        print("Database connection successful!")
        return conn
        
    except Exception as e:
        print(f"Database connection failed: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure PostgreSQL is running")
        print("2. Check your database credentials")
        print("3. Verify network connectivity")
        return None

def run_migration():
    """Run the complete database migration"""
    
    # Get database connection
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Read the migration file
        migration_file = Path(__file__).parent / "migrations" / "009_complete_database_migration.sql"
        
        if not migration_file.exists():
            print(f"Migration file not found: {migration_file}")
            return False
        
        print(f"Reading migration file: {migration_file}")
        
        with open(migration_file, 'r', encoding='utf-8') as f:
            migration_sql = f.read()
        
        print("Executing migration...")
        print("=" * 60)
        
        # Split the SQL into individual statements
        statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]
        
        for i, statement in enumerate(statements, 1):
            if statement.startswith('--') or not statement:
                continue
                
            print(f"Executing statement {i}/{len(statements)}")
            try:
                cursor.execute(statement)
                conn.commit()
                print(f"[OK] Statement {i} completed successfully")
            except Exception as e:
                print(f"[ERROR] Error in statement {i}: {e}")
                print(f"Statement: {statement[:100]}...")
                # Continue with other statements
                conn.rollback()
        
        print("=" * 60)
        print("Migration completed!")
        
        # Run verification queries
        print("\nRunning verification queries...")
        
        # Check collections
        cursor.execute("SELECT COUNT(*) FROM collections")
        collection_count = cursor.fetchone()[0]
        print(f"[OK] Collections created: {collection_count}")
        
        # Check pricing strategies
        cursor.execute("SELECT DISTINCT price_strategy FROM coins WHERE price_strategy IS NOT NULL")
        strategies = [row[0] for row in cursor.fetchall()]
        print(f"[OK] Pricing strategies available: {', '.join(strategies)}")
        
        # Show sample collections
        cursor.execute("SELECT name, color, icon, default_markup FROM collections LIMIT 3")
        collections = cursor.fetchall()
        print("[OK] Sample collections:")
        for name, color, icon, markup in collections:
            print(f"  - {name} ({color}) {icon} {markup}x")
        
        return True
        
    except Exception as e:
        print(f"Migration failed: {e}")
        return False
        
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")

if __name__ == "__main__":
    print("Miracle Coins Database Migration")
    print("=" * 40)
    
    success = run_migration()
    
    if success:
        print("\n[SUCCESS] Migration completed successfully!")
        print("Your database now has:")
        print("- Collections system for organizing coins")
        print("- Flexible pricing strategies")
        print("- Sample collections and data")
    else:
        print("\n[FAILED] Migration failed!")
        print("Please check the error messages above and try again.")
