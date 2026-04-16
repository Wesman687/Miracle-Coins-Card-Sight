#!/usr/bin/env python3
"""
Simple database migration script
"""

import psycopg2
import os

def run_simple_migration():
    """Run a simple migration with individual statements"""
    
    try:
        # Connect to database
        conn = psycopg2.connect(
            host='server.stream-lineai.com',
            port='5432',
            database='Miracle-Coins',
            user='Miracle-Coins',
            password='your_db_password_here'
        )
        cursor = conn.cursor()
        
        print("Connected to database successfully!")
        
        # 1. Create collections table
        print("Creating collections table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS collections (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) UNIQUE NOT NULL,
                description TEXT,
                color VARCHAR(7) DEFAULT '#FFFFFF',
                icon VARCHAR(255),
                sort_order INTEGER DEFAULT 0,
                shopify_collection_id VARCHAR(255) UNIQUE,
                default_markup NUMERIC(6, 3) DEFAULT 1.300,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("[OK] Collections table created")
        
        # 2. Add collection_id to coins table
        print("Adding collection_id to coins table...")
        cursor.execute("""
            ALTER TABLE coins ADD COLUMN IF NOT EXISTS collection_id INTEGER REFERENCES collections(id) ON DELETE SET NULL
        """)
        print("[OK] collection_id column added")
        
        # 3. Add fixed_price to coins table
        print("Adding fixed_price to coins table...")
        cursor.execute("""
            ALTER TABLE coins ADD COLUMN IF NOT EXISTS fixed_price DECIMAL(10,2)
        """)
        print("[OK] fixed_price column added")
        
        # 4. Update price_strategy default
        print("Updating price_strategy default...")
        cursor.execute("""
            ALTER TABLE coins ALTER COLUMN price_strategy SET DEFAULT 'paid_price_multiplier'
        """)
        cursor.execute("""
            ALTER TABLE coins ALTER COLUMN price_multiplier SET DEFAULT 1.500
        """)
        print("[OK] Price strategy defaults updated")
        
        # 5. Update existing records
        print("Updating existing records...")
        cursor.execute("""
            UPDATE coins SET price_strategy = 'paid_price_multiplier' WHERE price_strategy = 'spot_multiplier'
        """)
        cursor.execute("""
            UPDATE coins SET price_multiplier = 1.500 WHERE price_multiplier = 1.300
        """)
        print("[OK] Existing records updated")
        
        # 6. Create indexes
        print("Creating indexes...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_collections_name ON collections(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_collections_sort ON collections(sort_order)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_collections_shopify ON collections(shopify_collection_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_coins_collection ON coins(collection_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_coins_price_strategy ON coins(price_strategy)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_coins_fixed_price ON coins(fixed_price) WHERE fixed_price IS NOT NULL")
        print("[OK] Indexes created")
        
        # 7. Insert sample collections
        print("Inserting sample collections...")
        cursor.execute("""
            INSERT INTO collections (name, description, color, icon, shopify_collection_id, default_markup) VALUES
            ('Silver Bullion', 'General silver bullion products', '#C0C0C0', '💰', 'gid://shopify/Collection/12345', 1.150),
            ('Gold Bullion', 'General gold bullion products', '#FFD700', '👑', 'gid://shopify/Collection/67890', 1.080),
            ('Mercury Dimes', 'Classic Mercury Dime collection', '#A9A9A9', '🪙', 'gid://shopify/Collection/11223', 1.500),
            ('Morgan Dollars', 'Historic Morgan Silver Dollars', '#D3D3D3', '💵', 'gid://shopify/Collection/44556', 1.400),
            ('Kennedy Half Dollars', 'Kennedy Half Dollar collection', '#BEBEBE', '🥈', 'gid://shopify/Collection/77889', 1.350)
            ON CONFLICT (name) DO NOTHING
        """)
        print("[OK] Sample collections inserted")
        
        # Commit all changes
        conn.commit()
        print("[OK] All changes committed")
        
        # Verify
        print("\nVerification:")
        cursor.execute("SELECT COUNT(*) FROM collections")
        count = cursor.fetchone()[0]
        print(f"[OK] Collections created: {count}")
        
        cursor.execute("SELECT DISTINCT price_strategy FROM coins WHERE price_strategy IS NOT NULL")
        strategies = [row[0] for row in cursor.fetchall()]
        print(f"[OK] Pricing strategies: {', '.join(strategies)}")
        
        cursor.execute("SELECT name, color, default_markup FROM collections LIMIT 3")
        collections = cursor.fetchall()
        print("[OK] Sample collections:")
        for name, color, markup in collections:
            print(f"  - {name} ({color}) {markup}x")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False
        
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("Simple Database Migration")
    print("=" * 30)
    
    success = run_simple_migration()
    
    if success:
        print("\n[SUCCESS] Migration completed!")
    else:
        print("\n[FAILED] Migration failed!")
