import psycopg2

def fix_price_strategy_column():
    """Fix the price_strategy column length and update values"""
    
    try:
        conn = psycopg2.connect(
            host='server.stream-lineai.com',
            port='5432',
            database='Miracle-Coins',
            user='Miracle-Coins',
            password='your_db_password_here'
        )
        cursor = conn.cursor()
        
        print("Connected to database successfully!")
        
        # 1. Alter the price_strategy column to allow longer values
        print("Altering price_strategy column length...")
        cursor.execute("ALTER TABLE coins ALTER COLUMN price_strategy TYPE VARCHAR(50)")
        print("[OK] Price strategy column length increased")
        
        # 2. Update existing records
        print("Updating existing records...")
        cursor.execute("UPDATE coins SET price_strategy = 'paid_price_multiplier' WHERE price_strategy = 'spot_multiplier'")
        cursor.execute("UPDATE coins SET price_multiplier = 1.500 WHERE price_multiplier = 1.300")
        print("[OK] Existing records updated")
        
        # 3. Set new defaults
        print("Setting new defaults...")
        cursor.execute("ALTER TABLE coins ALTER COLUMN price_strategy SET DEFAULT 'paid_price_multiplier'")
        cursor.execute("ALTER TABLE coins ALTER COLUMN price_multiplier SET DEFAULT 1.500")
        print("[OK] New defaults set")
        
        # Commit changes
        conn.commit()
        print("[OK] All changes committed")
        
        # Verify
        print("\nVerification:")
        cursor.execute("SELECT DISTINCT price_strategy FROM coins WHERE price_strategy IS NOT NULL")
        strategies = [row[0] for row in cursor.fetchall()]
        print(f"[OK] Pricing strategies: {', '.join(strategies)}")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False
        
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("Fix Price Strategy Column")
    print("=" * 30)
    
    success = fix_price_strategy_column()
    
    if success:
        print("\n[SUCCESS] Column fixed!")
    else:
        print("\n[FAILED] Fix failed!")
