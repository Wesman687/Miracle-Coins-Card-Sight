"""
Quick eBay credential test — run from the backend directory:
  python test_ebay.py
"""
import os, base64, urllib.request, urllib.parse, urllib.error, json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

APP_ID       = os.getenv('EBAY_APP_ID', '')
CERT_ID      = os.getenv('EBAY_CERT_ID', '')
REFRESH_FILE = Path(os.getenv('EBAY_REFRESH_TOKEN_FILE', 'ebay_refresh_token.txt'))
REFRESH_TOKEN = REFRESH_FILE.read_text().strip() if REFRESH_FILE.exists() else os.getenv('EBAY_REFRESH_TOKEN', '')

print("=== eBay credential check ===")
print(f"APP_ID  : {APP_ID[:12]}...  (sandbox={APP_ID.startswith('SBX-')})")
print(f"CERT_ID : {CERT_ID[:12]}...  (sandbox={CERT_ID.startswith('SBX-')})")
print(f"REFRESH : {'set (' + str(len(REFRESH_TOKEN)) + ' chars)' if REFRESH_TOKEN else 'MISSING'}")
print()

if not APP_ID or not CERT_ID or not REFRESH_TOKEN:
    print("ERROR: missing credentials, can't proceed")
    raise SystemExit(1)

# --- Step 1: exchange refresh token for access token ---
print("--- Step 1: get access token from refresh token ---")
auth = base64.b64encode(f"{APP_ID}:{CERT_ID}".encode()).decode()
data = urllib.parse.urlencode({
    'grant_type':    'refresh_token',
    'refresh_token': REFRESH_TOKEN,
    'scope':         'https://api.ebay.com/oauth/api_scope/sell.inventory',
}).encode()
req = urllib.request.Request(
    'https://api.ebay.com/identity/v1/oauth2/token',
    data=data,
    headers={'Authorization': f'Basic {auth}', 'Content-Type': 'application/x-www-form-urlencoded'},
)
try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.loads(resp.read().decode())
    access_token = payload.get('access_token', '')
    print(f"OK — got access token ({len(access_token)} chars), expires_in={payload.get('expires_in')}s")
except urllib.error.HTTPError as e:
    body = e.read().decode(errors='replace')
    print(f"FAILED ({e.code}): {body}")
    raise SystemExit(1)
except urllib.error.URLError as e:
    print(f"NETWORK ERROR: {e.reason}")
    raise SystemExit(1)

# --- Step 2: check inventory API access ---
print()
print("--- Step 2: ping inventory API ---")
req2 = urllib.request.Request(
    'https://api.ebay.com/sell/inventory/v1/location?limit=1',
    headers={'Authorization': f'Bearer {access_token}', 'Content-Language': 'en-US'},
)
try:
    with urllib.request.urlopen(req2, timeout=15) as resp:
        body = json.loads(resp.read().decode())
    print(f"OK — inventory API reachable, total={body.get('total', '?')} locations")
except urllib.error.HTTPError as e:
    body = e.read().decode(errors='replace')
    print(f"FAILED ({e.code}): {body}")
except urllib.error.URLError as e:
    print(f"NETWORK ERROR: {e.reason}")

print()
print("Done.")
