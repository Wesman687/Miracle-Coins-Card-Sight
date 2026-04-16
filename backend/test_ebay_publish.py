"""
Test the full eBay publish flow for a specific coin.
  python test_ebay_publish.py
"""
import sys, os
from dotenv import load_dotenv
load_dotenv()

# Make app importable
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.routers.storefront import get_ebay_sell_access_token, build_ebay_listing_payload, resolve_ebay_policy_ids, load_ebay_publish_env, to_storefront_record, parse_json
import json

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
db = Session()

COIN_ID = int(sys.argv[1]) if len(sys.argv) > 1 else 2367

print(f"=== Testing eBay publish for coin {COIN_ID} ===\n")

row = db.execute(text("""
    SELECT c.id, c.sku, c.title, c.description, c.computed_price, c.quantity, c.status, c.shopify_metadata,
           COALESCE(json_agg(ci.url ORDER BY ci.sort_order) FILTER (WHERE ci.url IS NOT NULL), '[]'::json) AS images
    FROM coins c
    LEFT JOIN coin_images ci ON ci.coin_id = c.id
    WHERE c.id = :id
    GROUP BY c.id
"""), {'id': COIN_ID}).fetchone()

if not row:
    print(f"ERROR: coin {COIN_ID} not found")
    sys.exit(1)

print(f"Coin: {row.title}")
print(f"Price: {row.computed_price}, Qty: {row.quantity}")
images = row.images or []
print(f"Images: {images}\n")

# Step 1: get token
print("--- Step 1: get access token ---")
try:
    token = get_ebay_sell_access_token()
    print(f"OK ({len(token)} chars)\n")
except Exception as e:
    print(f"FAILED: {e}")
    sys.exit(1)

# Step 2: build payload
print("--- Step 2: build listing payload ---")
try:
    payload = build_ebay_listing_payload(row, images, {})
    print(f"OK — SKU={payload.get('sku')}, marketplace={payload.get('marketplace_id')}")
    print(f"     category={payload.get('category_id')}, price={payload.get('price')}\n")
except Exception as e:
    print(f"FAILED: {e}")
    import traceback; traceback.print_exc()
    sys.exit(1)

# Step 3: resolve policy IDs
print("--- Step 3: resolve policy IDs ---")
try:
    env = load_ebay_publish_env()
    policies = resolve_ebay_policy_ids(token, env, payload['marketplace_id'])
    print(f"OK — {policies}\n")
except Exception as e:
    print(f"FAILED: {e}")
    import traceback; traceback.print_exc()
    sys.exit(1)

# Step 4: full publish (dry-run via inventory item PUT then offer POST)
print("--- Step 4: full publish ---")
try:
    from app.routers.storefront import publish_coin_to_ebay
    result = publish_coin_to_ebay(row, images, {})
    print(f"OK — listing URL: {result.get('listing_url')}")
    print(f"     offer_id={result.get('offer_id')}, listing_id={result.get('listing_id')}")
except Exception as e:
    print(f"FAILED: {e}")
    import traceback; traceback.print_exc()

print("\nDone.")
db.close()
