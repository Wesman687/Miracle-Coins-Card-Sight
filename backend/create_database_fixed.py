#!/usr/bin/env python3
"""
Fixed Database Creation for Miracle Coins CoinSync Pro
Creates tables in correct dependency order
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

def execute_sql(engine, sql_content, description):
    """Execute SQL content with error handling"""
    print(f"\nExecuting: {description}")
    print("-" * 50)
    
    try:
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
    print("Starting Fixed Miracle Coins Database Creation")
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
    
    # Step 1: Create core tables first (no dependencies)
    core_tables_sql = """
    -- Enable UUID extension
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    
    -- Core Tables (no dependencies)
    CREATE TABLE IF NOT EXISTS coins (
        id SERIAL PRIMARY KEY,
        sku VARCHAR(100) UNIQUE,
        name VARCHAR(200) NOT NULL,
        year INTEGER CHECK (year >= 1800 AND year <= 2030),
        denomination VARCHAR(50),
        mint_mark VARCHAR(10),
        grade VARCHAR(20),
        category VARCHAR(50),
        description TEXT,
        condition_notes TEXT,
        is_silver BOOLEAN DEFAULT FALSE,
        silver_percent DECIMAL(5,2) CHECK (silver_percent >= 0 AND silver_percent <= 100),
        silver_content_oz DECIMAL(10,4) CHECK (silver_content_oz >= 0),
        paid_price DECIMAL(10,2) CHECK (paid_price >= 0),
        price_strategy VARCHAR(20) DEFAULT 'spot_multiplier' CHECK (price_strategy IN ('spot_multiplier', 'fixed_price', 'entry_based')),
        price_multiplier DECIMAL(5,2) DEFAULT 1.30 CHECK (price_multiplier >= 0.1 AND price_multiplier <= 10),
        base_from_entry BOOLEAN DEFAULT TRUE,
        entry_spot DECIMAL(10,2) CHECK (entry_spot >= 0),
        entry_melt DECIMAL(10,2) CHECK (entry_melt >= 0),
        override_price BOOLEAN DEFAULT FALSE,
        override_value DECIMAL(10,2) CHECK (override_value >= 0),
        computed_price DECIMAL(10,2) CHECK (computed_price >= 0),
        quantity INTEGER DEFAULT 1 CHECK (quantity >= 1),
        status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'sold', 'inactive', 'pending')),
        created_by VARCHAR(100),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS spot_prices (
        id SERIAL PRIMARY KEY,
        metal VARCHAR(20) NOT NULL CHECK (metal IN ('silver', 'gold', 'platinum', 'palladium')),
        price DECIMAL(10,2) NOT NULL CHECK (price >= 0),
        source VARCHAR(100),
        fetched_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS locations (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        description TEXT,
        address TEXT,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    if not execute_sql(engine, core_tables_sql, "Creating core tables"):
        return False
    
    # Step 2: Create dependent tables
    dependent_tables_sql = """
    -- Tables that depend on coins
    CREATE TABLE IF NOT EXISTS coin_images (
        id SERIAL PRIMARY KEY,
        coin_id INTEGER REFERENCES coins(id) ON DELETE CASCADE,
        url VARCHAR(500) NOT NULL,
        alt_text VARCHAR(200),
        sort_order INTEGER DEFAULT 0,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS listings (
        id SERIAL PRIMARY KEY,
        coin_id INTEGER REFERENCES coins(id) ON DELETE CASCADE,
        channel VARCHAR(20) NOT NULL CHECK (channel IN ('shopify', 'ebay', 'etsy', 'tiktok', 'facebook')),
        external_id VARCHAR(100),
        external_variant_id VARCHAR(100),
        url VARCHAR(500),
        status VARCHAR(20) DEFAULT 'unlisted' CHECK (status IN ('unlisted', 'listed', 'sold', 'error')),
        last_error TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS orders (
        id SERIAL PRIMARY KEY,
        coin_id INTEGER REFERENCES coins(id) ON DELETE CASCADE,
        channel VARCHAR(20) NOT NULL CHECK (channel IN ('shopify', 'ebay', 'etsy', 'tiktok', 'facebook')),
        external_order_id VARCHAR(100) NOT NULL,
        qty INTEGER NOT NULL CHECK (qty >= 1),
        sold_price DECIMAL(10,2) NOT NULL CHECK (sold_price >= 0),
        fees DECIMAL(10,2) DEFAULT 0 CHECK (fees >= 0),
        shipping_cost DECIMAL(10,2) DEFAULT 0 CHECK (shipping_cost >= 0),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS sales (
        id SERIAL PRIMARY KEY,
        coin_id INTEGER REFERENCES coins(id) ON DELETE CASCADE,
        user_id VARCHAR(100) NOT NULL,
        channel VARCHAR(20) NOT NULL CHECK (channel IN ('shopify', 'in_store', 'auction', 'direct')),
        quantity INTEGER NOT NULL CHECK (quantity >= 1),
        unit_price DECIMAL(10,2) NOT NULL CHECK (unit_price >= 0),
        total_amount DECIMAL(10,2) NOT NULL CHECK (total_amount >= 0),
        fees DECIMAL(10,2) DEFAULT 0 CHECK (fees >= 0),
        shipping_cost DECIMAL(10,2) DEFAULT 0 CHECK (shipping_cost >= 0),
        customer_info JSONB,
        notes TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS inventory_items (
        id SERIAL PRIMARY KEY,
        coin_id INTEGER REFERENCES coins(id) ON DELETE CASCADE,
        location_id INTEGER REFERENCES locations(id),
        quantity INTEGER NOT NULL CHECK (quantity >= 0),
        reorder_point INTEGER DEFAULT 0 CHECK (reorder_point >= 0),
        last_counted TIMESTAMP WITH TIME ZONE,
        notes TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    if not execute_sql(engine, dependent_tables_sql, "Creating dependent tables"):
        return False
    
    # Step 3: Create category management tables
    category_tables_sql = """
    -- Category management tables
    CREATE TABLE IF NOT EXISTS coin_categories (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) UNIQUE NOT NULL,
        display_name VARCHAR(200) NOT NULL,
        description TEXT,
        category_type VARCHAR(50) DEFAULT 'US_COINS',
        status VARCHAR(20) DEFAULT 'ACTIVE',
        parent_id INTEGER REFERENCES coin_categories(id),
        shopify_category_id INTEGER,
        auto_sync_to_shopify BOOLEAN DEFAULT FALSE,
        is_auto_created BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        total_coins INTEGER DEFAULT 0,
        total_value DECIMAL(12, 2) DEFAULT 0.00,
        avg_price DECIMAL(10, 2) DEFAULT 0.00,
        last_stats_update TIMESTAMP WITH TIME ZONE
    );
    
    CREATE TABLE IF NOT EXISTS category_metadata (
        id SERIAL PRIMARY KEY,
        category_id INTEGER NOT NULL REFERENCES coin_categories(id) ON DELETE CASCADE,
        field_name VARCHAR(100) NOT NULL,
        display_name VARCHAR(200) NOT NULL,
        field_type VARCHAR(20) DEFAULT 'TEXT',
        is_required BOOLEAN DEFAULT FALSE,
        default_value TEXT,
        options JSONB,
        description TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    
    CREATE TABLE IF NOT EXISTS category_rules (
        id SERIAL PRIMARY KEY,
        category_id INTEGER NOT NULL REFERENCES coin_categories(id) ON DELETE CASCADE,
        rule_type VARCHAR(50) NOT NULL,
        rule_value TEXT NOT NULL,
        priority INTEGER DEFAULT 0,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    
    CREATE TABLE IF NOT EXISTS coin_metadata (
        id SERIAL PRIMARY KEY,
        coin_id INTEGER NOT NULL REFERENCES coins(id) ON DELETE CASCADE,
        field_name VARCHAR(100) NOT NULL,
        field_value TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    """
    
    if not execute_sql(engine, category_tables_sql, "Creating category management tables"):
        return False
    
    # Step 4: Create other tables
    other_tables_sql = """
    CREATE TABLE IF NOT EXISTS sales_forecasts (
        id SERIAL PRIMARY KEY,
        forecast_type VARCHAR(20) NOT NULL CHECK (forecast_type IN ('daily', 'weekly', 'monthly', 'quarterly', 'annually')),
        period_start DATE NOT NULL,
        period_end DATE NOT NULL,
        predicted_revenue DECIMAL(12,2) NOT NULL CHECK (predicted_revenue >= 0),
        confidence_level VARCHAR(10) NOT NULL CHECK (confidence_level IN ('high', 'medium', 'low')),
        algorithm_used VARCHAR(50),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS sales_metrics (
        id SERIAL PRIMARY KEY,
        metric_name VARCHAR(50) NOT NULL,
        metric_value DECIMAL(15,2) NOT NULL,
        metric_type VARCHAR(20) NOT NULL CHECK (metric_type IN ('revenue', 'profit', 'volume', 'count')),
        period_start DATE NOT NULL,
        period_end DATE NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS transactions (
        id SERIAL PRIMARY KEY,
        transaction_type VARCHAR(20) NOT NULL CHECK (transaction_type IN ('income', 'expense', 'transfer')),
        amount DECIMAL(12,2) NOT NULL,
        description TEXT NOT NULL,
        category VARCHAR(50),
        reference_id VARCHAR(100),
        transaction_date DATE NOT NULL,
        created_by VARCHAR(100) NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS expenses (
        id SERIAL PRIMARY KEY,
        expense_type VARCHAR(50) NOT NULL,
        amount DECIMAL(10,2) NOT NULL CHECK (amount >= 0),
        description TEXT NOT NULL,
        vendor VARCHAR(100),
        expense_date DATE NOT NULL,
        receipt_url VARCHAR(500),
        created_by VARCHAR(100) NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS profit_loss_statements (
        id SERIAL PRIMARY KEY,
        period_start DATE NOT NULL,
        period_end DATE NOT NULL,
        total_revenue DECIMAL(12,2) NOT NULL CHECK (total_revenue >= 0),
        total_expenses DECIMAL(12,2) NOT NULL CHECK (total_expenses >= 0),
        gross_profit DECIMAL(12,2) NOT NULL,
        net_profit DECIMAL(12,2) NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS alert_rules (
        id SERIAL PRIMARY KEY,
        name VARCHAR(200) NOT NULL,
        description TEXT,
        alert_type VARCHAR(50) NOT NULL CHECK (alert_type IN ('low_inventory', 'price_change', 'system_issue', 'sales_milestone', 'profit_margin')),
        conditions JSONB NOT NULL,
        product_specific BOOLEAN DEFAULT FALSE,
        product_id INTEGER REFERENCES coins(id) ON DELETE CASCADE,
        notification_channels TEXT[] DEFAULT ARRAY['in_app'],
        notification_frequency VARCHAR(20) DEFAULT 'immediate' CHECK (notification_frequency IN ('immediate', 'daily', 'weekly')),
        enabled BOOLEAN DEFAULT TRUE,
        last_triggered TIMESTAMP WITH TIME ZONE,
        trigger_count INTEGER DEFAULT 0,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        created_by VARCHAR(100) NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS alerts (
        id SERIAL PRIMARY KEY,
        rule_id INTEGER REFERENCES alert_rules(id) ON DELETE CASCADE,
        alert_type VARCHAR(50) NOT NULL CHECK (alert_type IN ('low_inventory', 'price_change', 'system_issue', 'sales_milestone', 'profit_margin')),
        severity VARCHAR(20) NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
        title VARCHAR(200) NOT NULL,
        message TEXT NOT NULL,
        context_data JSONB,
        affected_entity_id INTEGER,
        affected_entity_type VARCHAR(50),
        status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'acknowledged', 'resolved', 'dismissed')),
        acknowledged_by VARCHAR(100),
        acknowledged_at TIMESTAMP WITH TIME ZONE,
        resolved_by VARCHAR(100),
        resolved_at TIMESTAMP WITH TIME ZONE,
        resolution_notes TEXT,
        triggered_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS shopify_integrations (
        id SERIAL PRIMARY KEY,
        shop_domain VARCHAR(200) NOT NULL,
        access_token VARCHAR(500) NOT NULL,
        webhook_secret VARCHAR(500),
        sync_products BOOLEAN DEFAULT TRUE,
        sync_inventory BOOLEAN DEFAULT TRUE,
        sync_orders BOOLEAN DEFAULT TRUE,
        sync_pricing BOOLEAN DEFAULT TRUE,
        sync_frequency VARCHAR(20) DEFAULT 'hourly' CHECK (sync_frequency IN ('real_time', 'hourly', 'daily')),
        active BOOLEAN DEFAULT TRUE,
        last_sync TIMESTAMP WITH TIME ZONE,
        last_error TEXT,
        error_count INTEGER DEFAULT 0,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        created_by VARCHAR(100) NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS shopify_products (
        id SERIAL PRIMARY KEY,
        coin_id INTEGER REFERENCES coins(id) ON DELETE CASCADE,
        shopify_product_id VARCHAR(100) NOT NULL,
        shopify_variant_id VARCHAR(100),
        shopify_handle VARCHAR(200),
        sync_status VARCHAR(20) DEFAULT 'pending' CHECK (sync_status IN ('pending', 'synced', 'error')),
        last_synced TIMESTAMP WITH TIME ZONE,
        sync_error TEXT,
        shopify_title VARCHAR(500),
        shopify_description TEXT,
        shopify_price DECIMAL(10,2),
        shopify_inventory_quantity INTEGER,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(coin_id, shopify_product_id)
    );
    
    CREATE TABLE IF NOT EXISTS shopify_orders (
        id SERIAL PRIMARY KEY,
        shopify_order_id VARCHAR(100) NOT NULL UNIQUE,
        order_number VARCHAR(100),
        customer_email VARCHAR(200),
        customer_name VARCHAR(200),
        total_price DECIMAL(10,2) NOT NULL,
        currency VARCHAR(10) DEFAULT 'USD',
        order_status VARCHAR(50),
        fulfillment_status VARCHAR(50),
        sync_status VARCHAR(20) DEFAULT 'pending' CHECK (sync_status IN ('pending', 'synced', 'error')),
        last_synced TIMESTAMP WITH TIME ZONE,
        sync_error TEXT,
        order_date TIMESTAMP WITH TIME ZONE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS shopify_order_items (
        id SERIAL PRIMARY KEY,
        order_id INTEGER REFERENCES shopify_orders(id) ON DELETE CASCADE,
        coin_id INTEGER REFERENCES coins(id) ON DELETE CASCADE,
        shopify_line_item_id VARCHAR(100),
        product_title VARCHAR(500),
        variant_title VARCHAR(200),
        quantity INTEGER NOT NULL DEFAULT 1,
        price DECIMAL(10,2) NOT NULL
    );
    """
    
    if not execute_sql(engine, other_tables_sql, "Creating other tables"):
        return False
    
    # Step 5: Create indexes
    indexes_sql = """
    CREATE INDEX IF NOT EXISTS idx_coins_status ON coins(status);
    CREATE INDEX IF NOT EXISTS idx_coins_is_silver ON coins(is_silver);
    CREATE INDEX IF NOT EXISTS idx_coins_category ON coins(category);
    CREATE INDEX IF NOT EXISTS idx_coins_created_at ON coins(created_at);
    CREATE INDEX IF NOT EXISTS idx_coins_sku ON coins(sku);
    
    CREATE INDEX IF NOT EXISTS idx_coin_images_coin_id ON coin_images(coin_id);
    CREATE INDEX IF NOT EXISTS idx_spot_prices_metal ON spot_prices(metal);
    CREATE INDEX IF NOT EXISTS idx_spot_prices_fetched_at ON spot_prices(fetched_at);
    
    CREATE INDEX IF NOT EXISTS idx_listings_coin_id ON listings(coin_id);
    CREATE INDEX IF NOT EXISTS idx_listings_channel ON listings(channel);
    CREATE INDEX IF NOT EXISTS idx_listings_status ON listings(status);
    
    CREATE INDEX IF NOT EXISTS idx_orders_coin_id ON orders(coin_id);
    CREATE INDEX IF NOT EXISTS idx_orders_channel ON orders(channel);
    CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at);
    
    CREATE INDEX IF NOT EXISTS idx_sales_coin_id ON sales(coin_id);
    CREATE INDEX IF NOT EXISTS idx_sales_channel ON sales(channel);
    CREATE INDEX IF NOT EXISTS idx_sales_created_at ON sales(created_at);
    
    CREATE INDEX IF NOT EXISTS idx_alerts_rule_id ON alerts(rule_id);
    CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status);
    CREATE INDEX IF NOT EXISTS idx_alerts_triggered_at ON alerts(triggered_at);
    
    CREATE INDEX IF NOT EXISTS idx_shopify_products_coin_id ON shopify_products(coin_id);
    CREATE INDEX IF NOT EXISTS idx_shopify_products_shopify_product_id ON shopify_products(shopify_product_id);
    
    CREATE INDEX IF NOT EXISTS idx_coin_categories_name ON coin_categories(name);
    CREATE INDEX IF NOT EXISTS idx_coin_categories_type ON coin_categories(category_type);
    CREATE INDEX IF NOT EXISTS idx_coin_categories_status ON coin_categories(status);
    CREATE INDEX IF NOT EXISTS idx_category_metadata_category_id ON category_metadata(category_id);
    CREATE INDEX IF NOT EXISTS idx_category_rules_category_id ON category_rules(category_id);
    CREATE INDEX IF NOT EXISTS idx_coin_metadata_coin_id ON coin_metadata(coin_id);
    """
    
    if not execute_sql(engine, indexes_sql, "Creating indexes"):
        return False
    
    print("\n" + "=" * 60)
    print("DATABASE CREATION COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print("\nBase database schema created with all tables!")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
