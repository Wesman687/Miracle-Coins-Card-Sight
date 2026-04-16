# Database Setup Instructions

## Prerequisites

1. **PostgreSQL must be running** on your system
2. **Database user and database must exist** with proper permissions

## Option 1: Using psql Command Line

1. **Connect to PostgreSQL:**
   ```bash
   psql -U Miracle-Coins -d Miracle-Coins -h localhost
   ```

2. **Run the schema updates:**
   ```sql
   \i database_schema_updates.sql
   ```

## Option 2: Using pgAdmin or other GUI tools

1. Open pgAdmin or your preferred PostgreSQL GUI
2. Connect to your PostgreSQL server
3. Navigate to the "Miracle-Coins" database
4. Open the Query Tool
5. Copy and paste the contents of `database_schema_updates.sql`
6. Execute the script

## Option 3: Using Python (if database connection works)

1. **Run the Python script:**
   ```bash
   python execute_schema_updates.py
   ```

## Database Connection Troubleshooting

If you're getting connection errors, try these steps:

### 1. Check PostgreSQL Service
```bash
# Windows (as Administrator)
net start postgresql-x64-13

# Or check if it's running
sc query postgresql-x64-13
```

### 2. Create Database and User (if they don't exist)
Connect as postgres superuser and run:
```sql
-- Create user
CREATE USER "Miracle-Coins" WITH PASSWORD 'your_db_password_here';

-- Create database
CREATE DATABASE "Miracle-Coins" OWNER "Miracle-Coins";

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE "Miracle-Coins" TO "Miracle-Coins";
```

### 3. Test Connection
```bash
psql -U Miracle-Coins -d Miracle-Coins -h localhost
```

## What Gets Added

After running the schema updates, you'll have:

### New Tables:
- `coin_categories` - Category management system
- `shopify_categories` - Shopify collection mappings
- `category_metadata` - Metadata fields per category
- `category_rules` - Auto-categorization rules
- `coin_metadata` - Additional coin metadata

### New Features:
- **Auto-SKU generation** - Unique SKUs for each coin
- **Category management** - Organized coin categories
- **Enhanced metadata** - Rich data for each coin
- **Shopify integration** - Category sync with Shopify

### Sample Data:
- 10 default coin categories (Silver Eagles, Morgan Dollars, etc.)
- Metadata fields for key categories
- Auto-categorization rules
- SKUs generated for existing coins

## Verification

After running the updates, verify by checking:

```sql
-- Check if new tables exist
\dt

-- Check if SKUs were generated
SELECT id, title, sku FROM coins LIMIT 5;

-- Check categories
SELECT name, display_name FROM coin_categories;

-- Test SKU generation function
SELECT generate_coin_sku('2023 Silver Eagle', 2023, '1 Ounce', 'W', 'MS70', 'Silver Eagles');
```

## Expected Output

You should see SKUs like:
- `ASE-2023-1OZ-W-MS70-001` (2023 Silver Eagle)
- `MOR-1881-1DOL-S-MS65-001` (1881 Morgan Dollar)
- `KEN-1964-50C-D-MS64-001` (1964 Kennedy Half Dollar)

## Troubleshooting

### Common Issues:

1. **Permission denied**: Make sure the user has proper privileges
2. **Database doesn't exist**: Create the database first
3. **Connection refused**: Check if PostgreSQL is running
4. **Authentication failed**: Verify username and password

### Getting Help:

If you continue to have issues:
1. Check PostgreSQL logs for detailed error messages
2. Verify your `.env` file has the correct database credentials
3. Make sure PostgreSQL is running and accessible
4. Check firewall settings if using remote database
