from __future__ import annotations

import glob
import json
import os
import re
import base64
import urllib.parse
import urllib.request
import uuid
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional

import stripe

from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, File
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.auth_utils import verify_admin_token
from app.database import get_db
from app.notifications import notify as _discord_notify

router = APIRouter()

LISTS_DIR = Path(os.getenv('BOOTSTRAP_LISTS_DIR', 'data/lists'))



# ---------------------------------------------------------------------------
# Orders table bootstrap
# ---------------------------------------------------------------------------

def ensure_orders_table(db) -> None:
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS orders (
            id BIGSERIAL PRIMARY KEY,
            external_order_id VARCHAR(255),
            customer_id BIGINT REFERENCES customers(id) ON DELETE SET NULL,
            customer_email VARCHAR(255),
            customer_name VARCHAR(255),
            coin_id BIGINT,
            product_name TEXT,
            qty INTEGER NOT NULL DEFAULT 1,
            sold_price NUMERIC(10,2),
            channel VARCHAR(50) DEFAULT 'stripe',
            status VARCHAR(50) DEFAULT 'paid',
            tracking_number VARCHAR(255),
            notes TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
    """))
    db.commit()
OPTIONS_FILE = Path(os.getenv('PRODUCT_OPTIONS_FILE', 'data/product_options.json'))

DEFAULT_OPTIONS = {
    'metals': [
        {'value': 'gold', 'label': 'Gold', 'basePrice': None, 'offerPrice': None},
        {'value': 'platinum', 'label': 'Platinum', 'basePrice': None, 'offerPrice': None},
        {'value': 'silver', 'label': 'Silver', 'basePrice': None, 'offerPrice': None},
    ],
    'types': [
        {'value': 'card', 'label': 'Card'},
        {'value': 'bundle', 'label': 'Kit / Set'},
    ],
    'discounts': [],   # [{minTotal: float, pct: float}]
    'test_mode': False,
    'inquiry_mode': False,
}


def load_product_options() -> dict:
    if OPTIONS_FILE.exists():
        try:
            return json.loads(OPTIONS_FILE.read_text())
        except Exception:
            pass
    return DEFAULT_OPTIONS


def save_product_options(opts: dict) -> None:
    OPTIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    OPTIONS_FILE.write_text(json.dumps(opts, indent=2))


class BootstrapImportRequest(BaseModel):
    source_file: Optional[str] = None
    limit: Optional[int] = None
    only_cards: bool = False
    dry_run: bool = False


class EbayImportRequest(BaseModel):
    seller_username: str = 'miracle_coins'
    limit: int = 100
    dry_run: bool = True
    query_terms: Optional[List[str]] = None


class EbayPublishRequest(BaseModel):
    quantity: Optional[int] = None
    price: Optional[float] = None
    offer_price: Optional[float] = None   # best-offer auto-accept price
    category_id: Optional[str] = None
    marketplace_id: str = 'EBAY_US'


class StorefrontMetadataUpdateRequest(BaseModel):
    name: Optional[str] = None
    metal: Optional[str] = None
    weightLabel: Optional[str] = None
    description: Optional[str] = None
    badge: Optional[str] = None
    design: Optional[str] = None
    productType: Optional[str] = None
    features: Optional[List[str]] = None
    audience: Optional[List[str]] = None
    featured: Optional[bool] = None
    hidden: Optional[bool] = None


METAL_KEYWORDS = {
    'gold': ['gold card', 'gold foil', '1/4 grain gold', 'gold'],
    'platinum': ['platinum card', '1/4 grain platinum', 'platinum'],
    'silver': ['silver card', '1 grain silver', 'silver card', 'silver'],
}

WEIGHT_PATTERNS = [
    re.compile(r'(\d+(?:/\d+)?\s*grain\s*(?:gold|silver|platinum)?)', re.I),
    re.compile(r'(\d+(?:\.\d+)?\s*(?:g|gram|grams|oz|ounce|ounces))', re.I),
]


def slugify(value: str) -> str:
    value = (value or '').strip().lower()
    value = re.sub(r'[^a-z0-9]+', '-', value)
    value = re.sub(r'-+', '-', value)
    return value.strip('-') or 'product'


def parse_json(value: Any, default: Any):
    if value is None or value == '':
        return default
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except Exception:
        return default


def as_price(value: Any) -> Optional[float]:
    if value is None or value == '':
        return None
    if isinstance(value, (int, float, Decimal)):
        return float(value)
    cleaned = re.sub(r'[^0-9.]+', '', str(value))
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except Exception:
        return None


def infer_metal(text_value: str) -> str:
    hay = (text_value or '').lower()
    for metal, needles in METAL_KEYWORDS.items():
        if any(n in hay for n in needles):
            return metal
    return 'gold' if 'miracle' in hay and 'card' in hay else 'silver'


def infer_weight_label(payload: Dict[str, Any], metal: str) -> str:
    candidates = [
        payload.get('weight'),
        payload.get('silver_content'),
        payload.get('title'),
        payload.get('description'),
    ]
    for candidate in candidates:
        if not candidate:
            continue
        for pattern in WEIGHT_PATTERNS:
            match = pattern.search(str(candidate))
            if match:
                label = match.group(1).strip()
                if metal not in label.lower():
                    return f'{label} {metal}'
                return label
    defaults = {
        'gold': '1/4 grain gold',
        'platinum': '1/4 grain platinum',
        'silver': '1 grain silver',
    }
    return defaults.get(metal, '')




def infer_product_type(title: str, description: str = '') -> str:
    hay = f"{title} {description}".lower()
    if any(term in hay for term in ['ten pack', 'kit', 'bookmark', 'with envelope', 'pack of', 'bundle']):
        return 'bundle'
    return 'card'


def infer_badge_from_title(title: str, product_type: str, metal: str) -> str | None:
    hay = (title or '').lower()
    if product_type == 'bundle':
        return 'Kit'
    if 'limited' in hay:
        return 'Limited'
    return None


def build_features(payload: Dict[str, Any], metal: str, weight_label: str, product_type: str = 'card') -> List[str]:
    features = []
    if weight_label:
        features.append(f'Real {weight_label} content')
    composition = payload.get('composition')
    if composition:
        features.append(str(composition))
    rarity = payload.get('rarity')
    if rarity and rarity.lower() not in ('none', 'unknown', 'common'):
        features.append(f'Rarity: {rarity}')
    if product_type == 'bundle':
        features.append('Giftable collectible kit presentation')
    else:
        features.append('Giftable collectible card presentation')
    features.append('Great for collectors and precious metal buyers')
    deduped = []
    for feature in features:
        if feature and feature not in deduped:
            deduped.append(feature)
    return deduped[:5]


def build_audience(metal: str, product_type: str = 'card') -> List[str]:
    if product_type == 'bundle':
        return ['Bundle buyers', 'Gift buyers', 'Collectors']
    audiences = {
        'gold': ['Gift buyers', 'Collectors', 'Premium impulse buyers'],
        'platinum': ['Collectors', 'Luxury gift buyers', 'Metal enthusiasts'],
        'silver': ['New buyers', 'Collectors', 'Bundle shoppers'],
    }
    return audiences.get(metal, ['Collectors', 'Precious metal buyers', 'Gift buyers'])


def extract_images(item: Dict[str, Any]) -> List[str]:
    edited = item.get('edited') or {}
    data = item.get('data') or {}
    images = edited.get('_image_urls') or data.get('_image_urls') or item.get('imageUrls') or []
    normalized = []
    for img in images:
        if img and img not in normalized:
            normalized.append(img)
    fallback = edited.get('_image_url_file_server') or data.get('_image_url_file_server') or edited.get('_image_url') or data.get('_image_url')
    if fallback and fallback not in normalized:
        normalized.insert(0, fallback)
    return normalized


def to_storefront_record(coin_row: Any, image_urls: List[str], listing: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    metadata = parse_json(coin_row.shopify_metadata, {})
    storefront = metadata.get('storefront', {})
    title = storefront.get('name') or coin_row.title
    slug = storefront.get('slug') or slugify(title)
    metal = storefront.get('metal') or infer_metal(title)
    price = coin_row.computed_price if coin_row.computed_price is not None else storefront.get('price')
    price_label = f"${float(price):.2f}" if price is not None else 'Price coming soon'
    description = storefront.get('description') or coin_row.description or ''
    if not description:
        product_type = storefront.get('productType') or infer_product_type(title, coin_row.description or '')
        weight = storefront.get('weightLabel') or infer_weight_label(storefront, metal)
        description = f"Real {weight} in a collectible Miracle Coins {product_type}."
    price_value = float(price) if price is not None else None
    return {
        'id': coin_row.id,
        'slug': slug,
        'name': title,
        'metal': metal,
        'weightLabel': storefront.get('weightLabel') or infer_weight_label(storefront, metal),
        'description': description,
        'price': price_label,
        'priceValue': price_value,
        'bulkPricing': storefront.get('bulkPricing') or [],
        'badge': storefront.get('badge'),
        'design': storefront.get('design') or storefront.get('series') or title,
        'image': image_urls[0] if image_urls else None,
        'images': image_urls,
        'features': storefront.get('features') or [],
        'audience': storefront.get('audience') or build_audience(metal, storefront.get('productType') or infer_product_type(title, storefront.get('description') or '')),
        'buyUrl': listing.get('url') if listing else None,
        'liveUrl': listing.get('url') if listing else None,
        'quantity': coin_row.quantity,  # None = unlimited
        'ebayQuantity': storefront.get('ebayQuantity'),
        'offerPrice': storefront.get('offerPrice'),
        'metals': storefront.get('metals') or [metal],
        'productType': storefront.get('productType') or infer_product_type(title, storefront.get('description') or coin_row.description or ''),
        'featured': storefront.get('featured', False),
        'hidden': storefront.get('hidden', False),
    }


def get_ebay_app_token() -> str:
    app_id = os.getenv('EBAY_APP_ID')
    cert_id = os.getenv('EBAY_CERT_ID')
    if not app_id or not cert_id:
        raise HTTPException(status_code=500, detail='Missing eBay app credentials')

    auth = base64.b64encode(f"{app_id}:{cert_id}".encode()).decode()
    data = urllib.parse.urlencode({
        'grant_type': 'client_credentials',
        'scope': 'https://api.ebay.com/oauth/api_scope',
    }).encode()
    req = urllib.request.Request(
        'https://api.ebay.com/identity/v1/oauth2/token',
        data=data,
        headers={
            'Authorization': f'Basic {auth}',
            'Content-Type': 'application/x-www-form-urlencoded',
        },
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        payload = json.loads(response.read().decode())
    return payload['access_token']


def fetch_ebay_items_for_seller(seller_username: str, limit: int = 100, query_terms: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    token = get_ebay_app_token()
    terms = query_terms or ['gold card', 'platinum card', 'silver card', 'grain gold', 'grain platinum', 'grain silver', 'miracle card']
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'X-EBAY-C-MARKETPLACE-ID': 'EBAY_US',
    }

    found: Dict[str, Dict[str, Any]] = {}
    for term in terms:
        url = (
            'https://api.ebay.com/buy/browse/v1/item_summary/search?'
            + urllib.parse.urlencode({
                'q': term,
                'limit': min(limit, 50),
                'filter': f'sellers:{{{seller_username}}}',
            })
        )
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                payload = json.loads(response.read().decode())
        except Exception:
            continue

        for item in payload.get('itemSummaries', []):
            found[item['itemId']] = item
            if len(found) >= limit:
                return list(found.values())[:limit]

    return list(found.values())[:limit]


def ebay_summary_to_product(item: Dict[str, Any]) -> Dict[str, Any]:
    title = item.get('title', '').strip()
    metal = infer_metal(title)
    price_value = item.get('price', {}).get('value')
    weight_label = infer_weight_label({'title': title, 'description': item.get('shortDescription') or ''}, metal)
    image = (item.get('image') or {}).get('imageUrl')
    additional = [img.get('imageUrl') for img in item.get('thumbnailImages', []) if img.get('imageUrl')]
    images = []
    for url in [image, *additional]:
        if url and url not in images:
            images.append(url)
    return {
        'external_id': item.get('itemId'),
        'slug': slugify(title),
        'name': title,
        'metal': metal,
        'weightLabel': weight_label,
        'description': item.get('shortDescription') or '',
        'price': f"${float(price_value):.2f}" if price_value is not None else 'Price coming soon',
        'productType': infer_product_type(title, item.get('shortDescription') or ''),
        'badge': infer_badge_from_title(title, infer_product_type(title, item.get('shortDescription') or ''), metal),
        'design': title,
        'image': images[0] if images else None,
        'images': images,
        'features': build_features({'title': title}, metal, weight_label),
        'audience': build_audience(metal),
        'buyUrl': item.get('itemWebUrl'),
        'liveUrl': item.get('itemWebUrl'),
        'quantity': item.get('estimatedAvailabilities', [{}])[0].get('estimatedRemainingQuantity') or 1,
        'productType': infer_product_type(title, item.get('shortDescription') or ''),
        'categoryPath': item.get('categoryPath'),
    }


def load_ebay_publish_env() -> Dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k.startswith('EBAY_')}
    # Allow a local refresh token file override
    refresh_file = Path(os.getenv('EBAY_REFRESH_TOKEN_FILE', 'ebay_refresh_token.txt'))
    if refresh_file.exists():
        env['EBAY_REFRESH_TOKEN'] = refresh_file.read_text().strip()
    return env


def get_ebay_sell_access_token() -> str:
    env = load_ebay_publish_env()
    app_id = env.get('EBAY_APP_ID') or os.getenv('EBAY_APP_ID')
    cert_id = env.get('EBAY_CERT_ID') or os.getenv('EBAY_CERT_ID')
    refresh_token = env.get('EBAY_REFRESH_TOKEN')
    if not app_id or not cert_id or not refresh_token:
        raise HTTPException(status_code=500, detail='Missing eBay sell credentials or refresh token')
    auth = base64.b64encode(f"{app_id}:{cert_id}".encode()).decode()
    data = urllib.parse.urlencode({
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'scope': 'https://api.ebay.com/oauth/api_scope/sell.inventory https://api.ebay.com/oauth/api_scope/sell.account',
    }).encode()
    req = urllib.request.Request(
        'https://api.ebay.com/identity/v1/oauth2/token',
        data=data,
        headers={'Authorization': f'Basic {auth}', 'Content-Type': 'application/x-www-form-urlencoded'},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            payload = json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors='replace')
        raise HTTPException(status_code=502, detail=f'eBay token error ({e.code}): {body}')
    except urllib.error.URLError as e:
        raise HTTPException(status_code=502, detail=f'eBay token request failed: {e.reason}')
    if 'access_token' not in payload:
        raise HTTPException(status_code=502, detail=f'eBay token response: {payload}')
    return payload['access_token']


def infer_ebay_category_id(storefront: Dict[str, Any]) -> str:
    metal = storefront.get('metal', '')
    # eBay policy: grain items must be listed in Bullion > {Metal} > Other
    # Coins & Paper Money > Bullion > Gold > Other: 39486
    # Coins & Paper Money > Bullion > Silver > Other: 39484
    # Coins & Paper Money > Bullion > Platinum > Other: 39491
    return {'gold': '39486', 'platinum': '39491', 'silver': '39484'}.get(metal, '39486')


def build_ebay_listing_payload(coin_row: Any, image_urls: List[str], overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    metadata = parse_json(coin_row.shopify_metadata, {})
    storefront = metadata.get('storefront', {}) if isinstance(metadata, dict) else {}
    ebay = metadata.get('ebay', {}) if isinstance(metadata, dict) else {}
    title = storefront.get('name') or coin_row.title
    description = storefront.get('description') or coin_row.description or ''
    price = (overrides or {}).get('price') or (float(coin_row.computed_price) if coin_row.computed_price is not None else None)
    # eBay quantity: override > stored ebayQuantity > website quantity > 1
    quantity = int((overrides or {}).get('quantity') or storefront.get('ebayQuantity') or coin_row.quantity or 1)
    category_id = (overrides or {}).get('category_id') or ebay.get('categoryId') or infer_ebay_category_id(storefront)
    sku = coin_row.sku or f"MC-{coin_row.id}-{uuid.uuid4().hex[:6].upper()}"
    listing_description = description
    if storefront.get('weightLabel'):
        listing_description += f"\n\nMetal content: {storefront.get('weightLabel')}"
    if storefront.get('features'):
        listing_description += "\n\nHighlights:\n- " + "\n- ".join(storefront.get('features'))
    # Normalize image URLs for eBay — must be publicly accessible
    public_base = os.getenv('LOCAL_API_URL', 'http://localhost:1270')
    def _normalize_image_url(u: str) -> str:
        # Fix old URLs missing the /miracle-coins prefix
        import re
        u = re.sub(r'https?://server\.stream-lineai\.com/uploads/', f'{public_base}/uploads/', u)
        # Resolve relative paths
        if u.startswith('/'):
            u = f'{public_base}{u}'
        return u
    ebay_images = [_normalize_image_url(u) for u in image_urls[:12] if u]

    return {
        'sku': sku,
        'title': title[:80],
        'description': listing_description[:5000],
        'price': price,
        'quantity': quantity,
        'category_id': str(category_id),
        'marketplace_id': (overrides or {}).get('marketplace_id') or 'EBAY_US',
        'condition': 'NEW',
        'images': ebay_images,
        'existing_offer_id': ebay.get('offerId'),
        'existing_item_id': ebay.get('itemId'),
        'existing_url': ebay.get('url'),
        'offer_price': (overrides or {}).get('offer_price') or storefront.get('offerPrice'),
    }


def ebay_request(method: str, url: str, token: str, payload: Optional[Dict[str, Any]] = None) -> Any:
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json', 'Accept': 'application/json'}
    if method in ('PUT', 'POST'):
        headers['Content-Language'] = 'en-US'
    req = urllib.request.Request(url, method=method, headers=headers)
    if payload is not None:
        req.data = json.dumps(payload).encode()
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            body = response.read().decode()
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors='replace')
        raise HTTPException(status_code=e.code, detail=f'eBay API error {e.code} [{method} {url.split("ebay.com")[-1]}]: {body}')


def resolve_ebay_policy_ids(token: str, env: Dict[str, str], marketplace_id: str = 'EBAY_US') -> Dict[str, Optional[str]]:
    def first_id(endpoint: str, key: str, id_key: str, fallback_check=None):
        url = f'https://api.ebay.com/sell/account/v1/{endpoint}?marketplace_id={marketplace_id}'
        data = ebay_request('GET', url, token)
        items = data.get(key, []) if isinstance(data, dict) else []
        if fallback_check:
            for item in items:
                if fallback_check(item):
                    return item.get(id_key)
        return items[0].get(id_key) if items else None

    def first_location_key():
        data = ebay_request('GET', 'https://api.ebay.com/sell/inventory/v1/location?limit=1', token)
        locs = data.get('locations', []) if isinstance(data, dict) else []
        if locs:
            return locs[0].get('merchantLocationKey')
        # No location — create a default US warehouse location
        loc_key = 'miracle-coins-hq'
        try:
            ebay_request('POST', f'https://api.ebay.com/sell/inventory/v1/location/{loc_key}', token, {
                'location': {'address': {'country': 'US', 'stateOrProvince': 'TX', 'postalCode': '75001', 'city': 'Dallas'}},
                'locationTypes': ['WAREHOUSE'],
                'name': 'Miracle Coins HQ',
                'merchantLocationStatus': 'ENABLED',
            })
        except Exception:
            pass  # may already exist — that's fine
        return loc_key

    return {
        'fulfillmentPolicyId': env.get('EBAY_FULFILLMENT_POLICY_ID') or first_id('fulfillment_policy', 'fulfillmentPolicies', 'fulfillmentPolicyId'),
        'paymentPolicyId': env.get('EBAY_PAYMENT_POLICY_ID') or first_id('payment_policy', 'paymentPolicies', 'paymentPolicyId', lambda i: i.get('immediatePay') is False),
        'returnPolicyId': env.get('EBAY_RETURN_POLICY_ID') or first_id('return_policy', 'returnPolicies', 'returnPolicyId'),
        'merchantLocationKey': env.get('EBAY_MERCHANT_LOCATION_KEY') or first_location_key(),
    }


def publish_coin_to_ebay(coin_row: Any, image_urls: List[str], overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    env = load_ebay_publish_env()
    token = get_ebay_sell_access_token()
    payload = build_ebay_listing_payload(coin_row, image_urls, overrides)
    if not payload.get('price'):
        raise HTTPException(status_code=400, detail='A price is required before publishing to eBay. Set a price and try again.')
    if not payload.get('images'):
        raise HTTPException(status_code=400, detail='At least one product image is required before publishing to eBay.')
    policy_ids = resolve_ebay_policy_ids(token, env, payload['marketplace_id'])
    # Build category-required aspects for bullion categories
    _meta = parse_json(coin_row.shopify_metadata, {})
    _storefront = _meta.get('storefront', {}) if isinstance(_meta, dict) else {}
    _metals = _storefront.get('metals') or [_storefront.get('metal') or 'gold']
    metal_name = _metals[0].capitalize() if _metals else 'Gold'
    inventory_payload = {
        'product': {
            'title': payload['title'],
            'description': payload['description'],
            'aspects': {
                'Brand': ['Miracle Coins'],
                'Metal': [metal_name],
                'Certification': ['Uncertified'],
                'Country/Region of Manufacture': ['United States'],
                'Modified Item': ['No'],
            },
            'brand': 'Miracle Coins',
            'mpn': payload['sku'],
            'imageUrls': payload['images'],
        },
        'condition': payload['condition'],
        'availability': {'shipToLocationAvailability': {'quantity': payload['quantity']}},
    }
    ebay_request('PUT', f"https://api.ebay.com/sell/inventory/v1/inventory_item/{urllib.parse.quote(payload['sku'])}", token, inventory_payload)

    listing_policies = {k: v for k, v in policy_ids.items() if k != 'merchantLocationKey' and v}
    offer_base = {
        'sku': payload['sku'], 'marketplaceId': payload['marketplace_id'], 'format': 'FIXED_PRICE',
        'availableQuantity': payload['quantity'], 'categoryId': payload['category_id'],
        'listingDescription': payload['description'],
        'pricingSummary': {'price': {'value': str(payload['price']), 'currency': 'USD'}},
        'listingPolicies': listing_policies,
    }
    if payload.get('offer_price'):
        offer_base['bestOfferTerms'] = {
            'bestOfferEnabled': True,
            'autoDeclinePrice': {'value': str(round(float(payload['offer_price']), 2)), 'currency': 'USD'},
        }
    if policy_ids.get('merchantLocationKey'):
        offer_base['merchantLocationKey'] = policy_ids['merchantLocationKey']

    # Detect existing offer for this SKU if not already known
    existing_offer_id = payload.get('existing_offer_id')
    if not existing_offer_id:
        try:
            offers_resp = ebay_request('GET', f"https://api.ebay.com/sell/inventory/v1/offer?sku={urllib.parse.quote(payload['sku'])}", token)
            offers = offers_resp.get('offers', []) if isinstance(offers_resp, dict) else []
            if offers:
                existing_offer_id = offers[0].get('offerId')
        except Exception:
            pass

    if existing_offer_id:
        ebay_request('PUT', f"https://api.ebay.com/sell/inventory/v1/offer/{existing_offer_id}", token, offer_base)
        publish_result = ebay_request('POST', f"https://api.ebay.com/sell/inventory/v1/offer/{existing_offer_id}/publish", token, {})
        offer_id = existing_offer_id
    else:
        offer_result = ebay_request('POST', 'https://api.ebay.com/sell/inventory/v1/offer', token, offer_base)
        offer_id = offer_result.get('offerId')
        publish_result = ebay_request('POST', f"https://api.ebay.com/sell/inventory/v1/offer/{offer_id}/publish", token, {})

    listing = publish_result.get('listing', {}) if isinstance(publish_result, dict) else {}
    return {
        'sku': payload['sku'],
        'offer_id': offer_id,
        'listing_url': listing.get('listingUrl'),
        'listing_id': listing.get('listingId') or payload.get('existing_item_id'),
        'category_id': payload['category_id'],
        'price': payload['price'],
        'quantity': payload['quantity'],
        'raw': publish_result,
    }


def load_bootstrap_items(source_file: Optional[str]) -> List[Dict[str, Any]]:
    if source_file:
        path = Path(source_file)
    else:
        files = sorted(glob.glob(str(LISTS_DIR / '*.json')))
        if not files:
            raise HTTPException(status_code=404, detail='No bootstrap listing files found')
        path = Path(files[-1])

    if not path.exists():
        raise HTTPException(status_code=404, detail=f'Bootstrap file not found: {path}')

    data = json.loads(path.read_text())
    items = data.get('items', []) if isinstance(data, dict) else data
    if not isinstance(items, list):
        raise HTTPException(status_code=400, detail='Bootstrap file format not recognized')
    return items


LOCAL_API_URL = os.getenv('LOCAL_API_URL', 'http://localhost:1270')


class CreateProductRequest(BaseModel):
    title: str
    metal: str = 'gold'
    metals: Optional[List[str]] = None   # multi-metal; primary = metals[0] or metal
    product_type: str = 'card'
    price: Optional[float] = None
    description: Optional[str] = ''
    weight_label: Optional[str] = None
    quantity: Optional[int] = None   # None = unlimited
    ebay_quantity: Optional[int] = None
    offer_price: Optional[float] = None   # eBay best-offer auto-accept price
    image_urls: Optional[List[str]] = None


@router.post('/storefront/upload-image')
async def upload_product_image(
    file: UploadFile = File(...),
    _: str = Depends(verify_admin_token),
):
    ext = Path(file.filename or 'image.jpg').suffix.lower()
    if ext not in ('.jpg', '.jpeg', '.png', '.webp'):
        ext = '.jpg'
    filename = f"product-{uuid.uuid4().hex[:12]}{ext}"
    upload_dir = Path('uploads')
    upload_dir.mkdir(exist_ok=True)
    (upload_dir / filename).write_bytes(await file.read())
    return {'url': f'{LOCAL_API_URL}/uploads/{filename}'}


@router.post('/storefront/products')
async def create_product(
    req: CreateProductRequest,
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin_token),
):
    effective_metals = [m.lower() for m in req.metals] if req.metals else [req.metal.lower()]
    metal = effective_metals[0]
    product_type = req.product_type.lower()
    weight_label = req.weight_label or infer_weight_label({'title': req.title}, metal)
    slug_base = slugify(req.title)

    # Make slug unique
    slug = slug_base
    n = 1
    while db.execute(text("SELECT 1 FROM coins WHERE shopify_metadata->>'storefront' LIKE :p LIMIT 1"), {'p': f'%"slug": "{slug}"%'}).fetchone():
        slug = f'{slug_base}-{n}'
        n += 1

    storefront_meta = {
        'source': 'manage',
        'slug': slug,
        'name': req.title,
        'metal': metal,
        'weightLabel': weight_label,
        'description': req.description or '',
        'badge': 'Kit' if product_type == 'bundle' else None,
        'productType': product_type,
        'features': build_features({}, metal, weight_label),
        'audience': build_audience(metal),
        'featured': False,
        'hidden': False,
        'ebayQuantity': req.ebay_quantity,
        'offerPrice': req.offer_price,
        'metals': effective_metals,
    }

    sku = f"MC-{slug[:36].upper().replace('-', '')}"
    new_coin = db.execute(text("""
        INSERT INTO coins (sku, title, category, description, computed_price, quantity, status,
                          price_strategy, created_by, tags, shopify_metadata, created_at, updated_at)
        VALUES (:sku, :title, :category, :description, :price, :quantity, 'active',
                'fixed_price', 'manage', :tags, :shopify_metadata, NOW(), NOW())
        RETURNING id
    """), {
        'sku': sku,
        'title': req.title,
        'category': f'{metal}-{product_type}',
        'description': req.description or '',
        'price': req.price,
        'quantity': None if (req.quantity == 0 or req.quantity is None) else req.quantity,
        'tags': json.dumps(['manage', product_type, metal]),
        'shopify_metadata': json.dumps({'storefront': storefront_meta}),
    }).fetchone()

    coin_id = new_coin.id
    for idx, url in enumerate(req.image_urls or []):
        db.execute(text('INSERT INTO coin_images (coin_id, url, alt, sort_order) VALUES (:coin_id, :url, :alt, :sort_order)'), {
            'coin_id': coin_id, 'url': url, 'alt': req.title, 'sort_order': idx,
        })

    db.commit()
    return {'id': coin_id, 'slug': slug, 'title': req.title, 'success': True}


class UpdateProductRequest(BaseModel):
    title: Optional[str] = None
    metal: Optional[str] = None
    metals: Optional[List[str]] = None   # multi-metal array
    product_type: Optional[str] = None
    price: Optional[float] = None
    description: Optional[str] = None
    weight_label: Optional[str] = None
    quantity: Optional[int] = None   # None = unlimited (don't update if not sent)
    ebay_quantity: Optional[int] = None
    offer_price: Optional[float] = None   # eBay best-offer auto-accept price; 0 = disable
    image_urls: Optional[List[str]] = None
    bulk_pricing: Optional[List[Dict[str, Any]]] = None


@router.put('/storefront/products/{product_id}')
async def update_product(
    product_id: int,
    req: UpdateProductRequest,
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin_token),
):
    row = db.execute(text('SELECT id, shopify_metadata, computed_price, quantity FROM coins WHERE id = :id AND status = :status'),
                     {'id': product_id, 'status': 'active'}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail='Product not found')

    metadata = parse_json(row.shopify_metadata, {})
    storefront_meta = metadata.get('storefront', {})

    if req.title is not None:
        storefront_meta['name'] = req.title
        storefront_meta['slug'] = slugify(req.title)
    if req.metals is not None:
        effective_metals = [m.lower() for m in req.metals if m]
        if effective_metals:
            storefront_meta['metals'] = effective_metals
            storefront_meta['metal'] = effective_metals[0]
    elif req.metal is not None:
        storefront_meta['metal'] = req.metal.lower()
        existing_metals = storefront_meta.get('metals') or []
        if existing_metals:
            storefront_meta['metals'] = [req.metal.lower()] + [m for m in existing_metals if m != req.metal.lower()]
        else:
            storefront_meta['metals'] = [req.metal.lower()]
    if req.product_type is not None:
        storefront_meta['productType'] = req.product_type.lower()
        storefront_meta['badge'] = 'Kit' if req.product_type.lower() == 'bundle' else None
    if req.weight_label is not None:
        storefront_meta['weightLabel'] = req.weight_label
    if req.description is not None:
        storefront_meta['description'] = req.description
    if req.bulk_pricing is not None:
        storefront_meta['bulkPricing'] = req.bulk_pricing
    if req.ebay_quantity is not None:
        storefront_meta['ebayQuantity'] = req.ebay_quantity
    if req.offer_price is not None:
        storefront_meta['offerPrice'] = req.offer_price if req.offer_price > 0 else None

    # Regenerate features and audience whenever metal or type changes
    if req.metal is not None or req.product_type is not None:
        current_metal = storefront_meta.get('metal', 'gold')
        current_type = storefront_meta.get('productType', 'card')
        weight_label = storefront_meta.get('weightLabel') or infer_weight_label(storefront_meta, current_metal)
        storefront_meta['features'] = build_features({}, current_metal, weight_label, current_type)
        storefront_meta['audience'] = build_audience(current_metal, current_type)

    metadata['storefront'] = storefront_meta

    updates: dict = {'id': product_id, 'metadata': json.dumps(metadata)}
    set_clauses = ['shopify_metadata = :metadata']
    if req.price is not None:
        set_clauses.append('computed_price = :price')
        updates['price'] = req.price
    if req.quantity is not None:
        set_clauses.append('quantity = :quantity')
        # 0 on the wire means "unlimited" → store as NULL
        updates['quantity'] = None if req.quantity == 0 else req.quantity

    db.execute(text(f'UPDATE coins SET {", ".join(set_clauses)} WHERE id = :id'), updates)

    if req.image_urls is not None:
        db.execute(text('DELETE FROM coin_images WHERE coin_id = :id'), {'id': product_id})
        for idx, url in enumerate(req.image_urls):
            db.execute(text('INSERT INTO coin_images (coin_id, url, alt, sort_order) VALUES (:coin_id, :url, :alt, :sort_order)'),
                       {'coin_id': product_id, 'url': url, 'alt': storefront_meta.get('name', ''), 'sort_order': idx})

    db.commit()
    return {'id': product_id, 'success': True}


class BulkDeleteRequest(BaseModel):
    ids: List[int]

@router.post('/storefront/products/bulk-delete')
async def bulk_delete_products(
    req: BulkDeleteRequest,
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin_token),
):
    if not req.ids:
        return {'deleted': 0}
    id_list = req.ids
    db.execute(text('DELETE FROM coin_images WHERE coin_id = ANY(:ids)'), {'ids': id_list})
    db.execute(text('DELETE FROM listings WHERE coin_id = ANY(:ids)'), {'ids': id_list})
    result = db.execute(text('DELETE FROM coins WHERE id = ANY(:ids) RETURNING id'), {'ids': id_list})
    deleted = len(result.fetchall())
    db.commit()
    return {'deleted': deleted}


@router.delete('/storefront/products/{product_id}')
async def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin_token),
):
    db.execute(text('DELETE FROM coin_images WHERE coin_id = :id'), {'id': product_id})
    db.execute(text('DELETE FROM listings WHERE coin_id = :id'), {'id': product_id})
    result = db.execute(text('DELETE FROM coins WHERE id = :id RETURNING id'), {'id': product_id})
    row = result.fetchone()
    db.commit()
    if not row:
        raise HTTPException(status_code=404, detail='Product not found')
    return {'id': product_id, 'deleted': True}


@router.post('/storefront/products/{product_id}/image')
async def set_product_image(
    product_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin_token),
):
    """Upload and set as the primary image for an existing product."""
    ext = Path(file.filename or 'image.jpg').suffix.lower()
    if ext not in ('.jpg', '.jpeg', '.png', '.webp'):
        ext = '.jpg'
    filename = f"product-{uuid.uuid4().hex[:12]}{ext}"
    upload_dir = Path('uploads')
    upload_dir.mkdir(exist_ok=True)
    (upload_dir / filename).write_bytes(await file.read())
    url = f'{LOCAL_API_URL}/uploads/{filename}'

    db.execute(text('DELETE FROM coin_images WHERE coin_id = :id'), {'id': product_id})
    db.execute(text('INSERT INTO coin_images (coin_id, url, alt, sort_order) VALUES (:coin_id, :url, :alt, :sort_order)'),
               {'coin_id': product_id, 'url': url, 'alt': 'Product photo', 'sort_order': 0})
    db.commit()
    return {'url': url, 'success': True}


@router.get('/storefront/catalog')
async def get_catalog(
    metal: Optional[str] = Query(default=None),
    product_type: Optional[str] = Query(default=None),
    featured_only: bool = Query(default=False),
    limit: int = Query(default=60, ge=1, le=500),
    db: Session = Depends(get_db),
):
    query = text(
        """
        SELECT c.id, c.title, c.description, c.computed_price, c.quantity, c.status, c.shopify_metadata,
               COALESCE(
                   json_agg(ci.url ORDER BY ci.sort_order) FILTER (WHERE ci.url IS NOT NULL),
                   '[]'::json
               ) AS images,
               (SELECT l.url FROM listings l WHERE l.coin_id = c.id AND l.channel = 'ebay' ORDER BY l.updated_at DESC LIMIT 1) AS ebay_url,
               (SELECT l.external_id FROM listings l WHERE l.coin_id = c.id AND l.channel = 'ebay' ORDER BY l.updated_at DESC LIMIT 1) AS ebay_item_id
        FROM coins c
        LEFT JOIN coin_images ci ON ci.coin_id = c.id
        WHERE c.status = 'active'
        GROUP BY c.id
        ORDER BY c.updated_at DESC NULLS LAST, c.created_at DESC NULLS LAST
        LIMIT :limit
        """
    )
    rows = db.execute(query, {'limit': limit}).fetchall()

    products = []
    for row in rows:
        metadata = parse_json(row.shopify_metadata, {})
        ebay_meta = metadata.get('ebay') if isinstance(metadata, dict) else {}
        # Build listing from listings table first, fall back to metadata
        listing_url = row.ebay_url or (ebay_meta.get('url') if ebay_meta else None)
        listing = {
            'url': listing_url,
            'itemId': row.ebay_item_id or (ebay_meta.get('itemId') if ebay_meta else None),
            'seller': (ebay_meta or {}).get('seller', 'miracle_coins'),
        } if listing_url else None
        product = to_storefront_record(row, row.images or [], listing)
        if metal and metal not in product.get('metals', [product['metal']]):
            continue
        if product_type and product.get('productType') != product_type:
            continue
        if featured_only and not product.get('featured'):
            continue
        if product.get('hidden'):
            continue
        if not product.get('image'):
            continue
        products.append(product)

    products.sort(key=lambda p: (0 if p.get('featured') else 1, 0 if p.get('productType') == 'card' else 1, p.get('name', '')))
    return {'products': products, 'count': len(products)}


@router.get('/storefront/manage/catalog')
async def get_manage_catalog(
    limit: int = Query(default=500, ge=1, le=1000),
    search: Optional[str] = Query(None),
    metal: Optional[str] = Query(None),
    product_type: Optional[str] = Query(None),
    has_image: Optional[bool] = Query(None),
    has_ebay: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin_token),
):
    """Admin-only catalog: all active products, with optional search/filter."""
    where_clauses = ["c.status = 'active'"]
    params: dict = {'limit': limit}

    if search:
        where_clauses.append("(c.title ILIKE :search OR c.description ILIKE :search OR c.sku ILIKE :search)")
        params['search'] = f'%{search}%'
    metal_filter = metal.lower() if metal else None  # applied in Python to check metals[] array
    if product_type:
        if product_type.lower() == 'not_card':
            where_clauses.append("COALESCE(shopify_metadata->'storefront'->>'productType', '') != 'card'")
        else:
            where_clauses.append("shopify_metadata->'storefront'->>'productType' = :product_type")
            params['product_type'] = product_type.lower()

    where_sql = ' AND '.join(where_clauses)
    query = text(f"""
        SELECT c.id, c.title, c.description, c.computed_price, c.quantity, c.status, c.shopify_metadata,
               COALESCE(
                   json_agg(ci.url ORDER BY ci.sort_order) FILTER (WHERE ci.url IS NOT NULL),
                   '[]'::json
               ) AS images,
               (SELECT l.url FROM listings l WHERE l.coin_id = c.id AND l.channel = 'ebay' ORDER BY l.updated_at DESC LIMIT 1) AS ebay_url,
               (SELECT l.external_id FROM listings l WHERE l.coin_id = c.id AND l.channel = 'ebay' ORDER BY l.updated_at DESC LIMIT 1) AS ebay_item_id
        FROM coins c
        LEFT JOIN coin_images ci ON ci.coin_id = c.id
        WHERE {where_sql}
        GROUP BY c.id
        ORDER BY c.id ASC
        LIMIT :limit
    """)
    rows = db.execute(query, params).fetchall()
    products = []
    for row in rows:
        metadata = parse_json(row.shopify_metadata, {})
        ebay_meta = metadata.get('ebay') if isinstance(metadata, dict) else {}
        listing_url = row.ebay_url or (ebay_meta.get('url') if ebay_meta else None)
        listing = {
            'url': listing_url,
            'itemId': row.ebay_item_id or (ebay_meta.get('itemId') if ebay_meta else None),
            'seller': (ebay_meta or {}).get('seller', 'miracle_coins'),
        } if listing_url else None
        product = to_storefront_record(row, row.images or [], listing)
        if metal_filter and metal_filter not in product.get('metals', [product['metal']]):
            continue
        if has_image is not None:
            has_img = bool(product.get('image'))
            if has_image != has_img:
                continue
        if has_ebay is not None:
            has_e = bool(product.get('buyUrl'))
            if has_ebay != has_e:
                continue
        products.append(product)
    return {'products': products, 'count': len(products)}


@router.get('/storefront/products/{slug}')
async def get_product(slug: str, db: Session = Depends(get_db)):
    # shopify_metadata is JSONB — use JSONB operators, not LIKE
    row = db.execute(text("""
        SELECT c.id, c.title, c.description, c.computed_price, c.quantity, c.status, c.shopify_metadata,
               COALESCE(json_agg(ci.url ORDER BY ci.sort_order) FILTER (WHERE ci.url IS NOT NULL), '[]'::json) AS images,
               (SELECT l.url FROM listings l WHERE l.coin_id = c.id AND l.channel = 'ebay' ORDER BY l.updated_at DESC LIMIT 1) AS ebay_url,
               (SELECT l.external_id FROM listings l WHERE l.coin_id = c.id AND l.channel = 'ebay' ORDER BY l.updated_at DESC LIMIT 1) AS ebay_item_id
        FROM coins c
        LEFT JOIN coin_images ci ON ci.coin_id = c.id
        WHERE c.status = 'active'
        AND (shopify_metadata->'storefront'->>'slug' = :slug
             OR shopify_metadata::text LIKE :slug_pattern)
        GROUP BY c.id
        LIMIT 1
    """), {'slug': slug, 'slug_pattern': f'%"slug": "{slug}"%'}).fetchone()

    # Final fallback: slug may be derived from title, not stored at all
    if not row:
        all_rows = db.execute(text("""
            SELECT c.id, c.title, c.description, c.computed_price, c.quantity, c.status, c.shopify_metadata,
                   COALESCE(json_agg(ci.url ORDER BY ci.sort_order) FILTER (WHERE ci.url IS NOT NULL), '[]'::json) AS images,
                   (SELECT l.url FROM listings l WHERE l.coin_id = c.id AND l.channel = 'ebay' ORDER BY l.updated_at DESC LIMIT 1) AS ebay_url,
                   (SELECT l.external_id FROM listings l WHERE l.coin_id = c.id AND l.channel = 'ebay' ORDER BY l.updated_at DESC LIMIT 1) AS ebay_item_id
            FROM coins c
            LEFT JOIN coin_images ci ON ci.coin_id = c.id
            WHERE c.status = 'active'
            GROUP BY c.id
        """)).fetchall()
        for candidate in all_rows:
            meta = parse_json(candidate.shopify_metadata, {})
            storefront = meta.get('storefront', {}) if isinstance(meta, dict) else {}
            effective_title = storefront.get('name') or candidate.title or ''
            computed_slug = storefront.get('slug') or slugify(effective_title)
            if computed_slug == slug:
                row = candidate
                break

    if not row:
        raise HTTPException(status_code=404, detail='Product not found')

    metadata = parse_json(row.shopify_metadata, {})
    ebay_meta = metadata.get('ebay') if isinstance(metadata, dict) else {}
    listing_url = row.ebay_url or (ebay_meta.get('url') if ebay_meta else None)
    listing = {
        'url': listing_url,
        'itemId': row.ebay_item_id or (ebay_meta.get('itemId') if ebay_meta else None),
        'seller': (ebay_meta or {}).get('seller', 'miracle_coins'),
    } if listing_url else None
    images = list(row.images) if row.images else []
    return to_storefront_record(row, images, listing)


@router.get('/storefront/bootstrap/sources')
async def get_bootstrap_sources(_: str = Depends(verify_admin_token)):
    files = sorted(glob.glob(str(LISTS_DIR / '*.json')))
    return {
        'sources': [
            {'path': file, 'name': os.path.basename(file)}
            for file in files
        ]
    }


@router.get('/storefront/ebay/preview')
async def preview_ebay_import(
    seller_username: str = Query(default='miracle_coins'),
    limit: int = Query(default=50, ge=1, le=200),
    _: str = Depends(verify_admin_token),
):
    items = fetch_ebay_items_for_seller(seller_username=seller_username, limit=limit)
    products = [ebay_summary_to_product(item) for item in items]
    return {'seller_username': seller_username, 'count': len(products), 'products': products}


@router.post('/storefront/ebay/import')
async def import_from_ebay(
    request: EbayImportRequest,
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin_token),
):
    items = fetch_ebay_items_for_seller(
        seller_username=request.seller_username,
        limit=request.limit,
        query_terms=request.query_terms,
    )
    imported = []
    for item in items:
        product = ebay_summary_to_product(item)
        existing_listing = db.execute(
            text("SELECT id, shopify_metadata FROM coins WHERE (shopify_metadata->'ebay'->>'itemId') = :external_id LIMIT 1"),
            {'external_id': product['external_id']},
        ).fetchone()

        storefront_meta = {
            'source': 'ebay-api',
            'slug': product['slug'],
            'name': product['name'],
            'metal': product['metal'],
            'weightLabel': product['weightLabel'],
            'description': product['description'],
            'badge': product['badge'],
            'design': product['design'],
            'features': product['features'],
            'audience': product['audience'],
            'productType': product.get('productType') or infer_product_type(product['name'], product['description']),
        }

        ebay_meta = {
            'itemId': product['external_id'],
            'url': product['buyUrl'],
            'seller': request.seller_username,
        }

        if existing_listing:
            imported.append({'action': 'would_update' if request.dry_run else 'updated', 'title': product['name'], 'external_id': product['external_id']})
            if request.dry_run:
                continue
            coin_id = existing_listing.id
            existing_meta = parse_json(existing_listing.shopify_metadata, {})
            existing_meta['storefront'] = storefront_meta
            existing_meta['ebay'] = ebay_meta
            db.execute(text("UPDATE coins SET title = :title, description = :description, computed_price = :computed_price, quantity = :quantity, category = :category, status = 'active', shopify_metadata = :shopify_metadata, updated_at = NOW() WHERE id = :id"), {
                'id': coin_id, 'title': product['name'], 'description': product['description'], 'computed_price': as_price(item.get('price', {}).get('value')), 'quantity': product['quantity'], 'category': f"{product['metal']}-card", 'shopify_metadata': json.dumps(existing_meta)
            })
            db.execute(text('DELETE FROM coin_images WHERE coin_id = :coin_id'), {'coin_id': coin_id})
            for idx, image_url in enumerate(product['images']):
                db.execute(text('INSERT INTO coin_images (coin_id, url, alt, sort_order) VALUES (:coin_id, :url, :alt, :sort_order)'), {'coin_id': coin_id, 'url': image_url, 'alt': f"{product['name']} image {idx+1}", 'sort_order': idx})
            db.execute(text("DELETE FROM listings WHERE coin_id = :coin_id AND channel = 'ebay'"), {'coin_id': coin_id})
            if product['buyUrl']:
                db.execute(text("INSERT INTO listings (coin_id, channel, external_id, url, status, updated_at) VALUES (:coin_id, 'ebay', :external_id, :url, 'listed', NOW())"), {'coin_id': coin_id, 'external_id': product['external_id'], 'url': product['buyUrl']})
            continue

        imported.append({'action': 'would_create' if request.dry_run else 'created', 'title': product['name'], 'external_id': product['external_id']})
        if request.dry_run:
            continue
        new_coin = db.execute(text("INSERT INTO coins (sku, title, category, description, computed_price, quantity, status, price_strategy, created_by, tags, shopify_metadata, created_at, updated_at) VALUES (:sku, :title, :category, :description, :computed_price, :quantity, 'active', 'fixed_price', 'ebay-import', :tags, :shopify_metadata, NOW(), NOW()) RETURNING id"), {
            'sku': f"EBAY-{slugify(product['name'])[:36].upper().replace('-', '')}", 'title': product['name'], 'category': f"{product['metal']}-card", 'description': product['description'], 'computed_price': as_price(item.get('price', {}).get('value')), 'quantity': product['quantity'], 'tags': json.dumps(['storefront', 'ebay-import', product['metal']]), 'shopify_metadata': json.dumps({'storefront': storefront_meta, 'ebay': ebay_meta})
        }).fetchone()
        coin_id = new_coin.id
        for idx, image_url in enumerate(product['images']):
            db.execute(text('INSERT INTO coin_images (coin_id, url, alt, sort_order) VALUES (:coin_id, :url, :alt, :sort_order)'), {'coin_id': coin_id, 'url': image_url, 'alt': f"{product['name']} image {idx+1}", 'sort_order': idx})
        if product['buyUrl']:
            db.execute(text("INSERT INTO listings (coin_id, channel, external_id, url, status, updated_at) VALUES (:coin_id, 'ebay', :external_id, :url, 'listed', NOW())"), {'coin_id': coin_id, 'external_id': product['external_id'], 'url': product['buyUrl']})

    if not request.dry_run:
        db.commit()
    return {'success': True, 'seller_username': request.seller_username, 'count': len(imported), 'results': imported}


@router.post('/storefront/bootstrap/import')
async def bootstrap_import_catalog(
    request: BootstrapImportRequest,
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin_token),
):
    items = load_bootstrap_items(request.source_file)
    imported = []
    skipped = []

    if request.limit:
        items = items[: request.limit]

    for raw_item in items:
        payload = raw_item.get('edited') or raw_item.get('data') or {}
        title = (payload.get('title') or '').strip()
        if not title:
            skipped.append({'reason': 'missing_title', 'item': raw_item.get('id')})
            continue

        lower_title = title.lower()
        if request.only_cards and 'card' not in lower_title:
            skipped.append({'reason': 'not_card', 'title': title})
            continue

        metal = infer_metal(f"{title} {payload.get('description', '')}")
        weight_label = infer_weight_label(payload, metal)
        slug = slugify(title)
        price = as_price(payload.get('price'))
        quantity = int(float(payload.get('quantity') or 1)) if str(payload.get('quantity') or '1').strip() else 1
        images = extract_images(raw_item)
        eBay_url = raw_item.get('ebayUrl') or payload.get('ebay_url') or raw_item.get('url')
        ebay_id = raw_item.get('ebayItemId') or payload.get('ebay_item_id') or raw_item.get('id')

        storefront_meta = {
            'source': 'bootstrap-list',
            'slug': slug,
            'name': title,
            'metal': metal,
            'weightLabel': weight_label,
            'description': payload.get('description') or '',
            'badge': infer_badge(payload),
            'design': payload.get('coin_type') or title,
            'features': build_features(payload, metal, weight_label),
            'audience': build_audience(metal),
            'series': payload.get('coin_type'),
        }

        existing = db.execute(
            text("SELECT id, shopify_metadata FROM coins WHERE title = :title LIMIT 1"),
            {'title': title},
        ).fetchone()

        if existing:
            existing_meta = parse_json(existing.shopify_metadata, {})
            existing_meta['storefront'] = storefront_meta
            if not request.dry_run:
                db.execute(
                    text(
                        """
                        UPDATE coins
                        SET description = :description,
                            computed_price = COALESCE(:computed_price, computed_price),
                            quantity = :quantity,
                            category = :category,
                            status = 'active',
                            shopify_metadata = :shopify_metadata,
                            updated_at = NOW()
                        WHERE id = :id
                        """
                    ),
                    {
                        'id': existing.id,
                        'description': payload.get('description') or '',
                        'computed_price': price,
                        'quantity': quantity,
                        'category': f'{metal}-card',
                        'shopify_metadata': json.dumps(existing_meta),
                    },
                )
                db.execute(text('DELETE FROM coin_images WHERE coin_id = :coin_id'), {'coin_id': existing.id})
                for idx, image_url in enumerate(images):
                    db.execute(
                        text(
                            'INSERT INTO coin_images (coin_id, url, alt, sort_order) VALUES (:coin_id, :url, :alt, :sort_order)'
                        ),
                        {'coin_id': existing.id, 'url': image_url, 'alt': f'{title} image {idx + 1}', 'sort_order': idx},
                    )
                db.execute(text("DELETE FROM listings WHERE coin_id = :coin_id AND channel = 'ebay'"), {'coin_id': existing.id})
                if eBay_url or ebay_id:
                    db.execute(
                        text(
                            "INSERT INTO listings (coin_id, channel, external_id, url, status, updated_at) VALUES (:coin_id, 'ebay', :external_id, :url, 'listed', NOW())"
                        ),
                        {'coin_id': existing.id, 'external_id': str(ebay_id) if ebay_id else None, 'url': eBay_url},
                    )
            imported.append({'action': 'updated', 'title': title, 'slug': slug, 'metal': metal})
            continue

        if request.dry_run:
            imported.append({'action': 'would_create', 'title': title, 'slug': slug, 'metal': metal})
            continue

        new_coin = db.execute(
            text(
                """
                INSERT INTO coins (
                    sku, title, category, description, computed_price, quantity, status, created_by, tags, shopify_metadata, created_at, updated_at
                ) VALUES (
                    :sku, :title, :category, :description, :computed_price, :quantity, 'active', 'bootstrap-import', :tags, :shopify_metadata, NOW(), NOW()
                ) RETURNING id
                """
            ),
            {
                'sku': f'MC-{slug[:40].upper().replace('-', '')}',
                'title': title,
                'category': f'{metal}-card',
                'description': payload.get('description') or '',
                'computed_price': price,
                'quantity': quantity,
                'tags': json.dumps(['storefront', 'card', metal]),
                'shopify_metadata': json.dumps({'storefront': storefront_meta, 'bootstrap_source': str(request.source_file or 'latest-list')}),
            },
        ).fetchone()

        coin_id = new_coin.id
        for idx, image_url in enumerate(images):
            db.execute(
                text('INSERT INTO coin_images (coin_id, url, alt, sort_order) VALUES (:coin_id, :url, :alt, :sort_order)'),
                {'coin_id': coin_id, 'url': image_url, 'alt': f'{title} image {idx + 1}', 'sort_order': idx},
            )
        if eBay_url or ebay_id:
            db.execute(
                text("INSERT INTO listings (coin_id, channel, external_id, url, status, updated_at) VALUES (:coin_id, 'ebay', :external_id, :url, 'listed', NOW())"),
                {'coin_id': coin_id, 'external_id': str(ebay_id) if ebay_id else None, 'url': eBay_url},
            )

        imported.append({'action': 'created', 'title': title, 'slug': slug, 'metal': metal, 'coin_id': coin_id})

    if not request.dry_run:
        db.commit()

    return {
        'success': True,
        'imported_count': len(imported),
        'skipped_count': len(skipped),
        'imported': imported[:100],
        'skipped': skipped[:100],
    }


@router.put('/storefront/products/{coin_id}/metadata')
async def update_storefront_metadata(
    coin_id: int,
    payload: StorefrontMetadataUpdateRequest,
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin_token),
):
    row = db.execute(text("SELECT id, shopify_metadata FROM coins WHERE id = :id LIMIT 1"), {'id': coin_id}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail='Coin not found')

    metadata = parse_json(row.shopify_metadata, {})
    storefront = metadata.get('storefront', {}) if isinstance(metadata, dict) else {}

    updates = payload.model_dump(exclude_none=True)
    storefront.update(updates)
    metadata['storefront'] = storefront

    if payload.name:
        db.execute(text("UPDATE coins SET title = :title, updated_at = NOW() WHERE id = :id"), {'id': coin_id, 'title': payload.name})
    if payload.description is not None:
        db.execute(text("UPDATE coins SET description = :description, updated_at = NOW() WHERE id = :id"), {'id': coin_id, 'description': payload.description})
    if payload.metal or payload.productType:
        metal = payload.metal or storefront.get('metal') or 'gold'
        product_type = payload.productType or storefront.get('productType') or 'card'
        category = f"{metal}-bundle" if product_type == 'bundle' else f"{metal}-card"
        db.execute(text("UPDATE coins SET category = :category, updated_at = NOW() WHERE id = :id"), {'id': coin_id, 'category': category})

    db.execute(text("UPDATE coins SET shopify_metadata = :shopify_metadata, updated_at = NOW() WHERE id = :id"), {'id': coin_id, 'shopify_metadata': json.dumps(metadata)})
    db.commit()

    refreshed = db.execute(text("SELECT id, title, description, computed_price, quantity, status, shopify_metadata, COALESCE(json_agg(ci.url ORDER BY ci.sort_order) FILTER (WHERE ci.url IS NOT NULL), '[]'::json) AS images FROM coins c LEFT JOIN coin_images ci ON ci.coin_id = c.id WHERE c.id = :id GROUP BY c.id"), {'id': coin_id}).fetchone()
    return to_storefront_record(refreshed, refreshed.images or [], parse_json(refreshed.shopify_metadata, {}).get('ebay'))


@router.get('/storefront/products/{coin_id}/ebay-preview')
async def get_ebay_sync_preview(
    coin_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin_token),
):
    row = db.execute(text("SELECT id, sku, title, description, computed_price, quantity, shopify_metadata, COALESCE(json_agg(ci.url ORDER BY ci.sort_order) FILTER (WHERE ci.url IS NOT NULL), '[]'::json) AS images FROM coins c LEFT JOIN coin_images ci ON ci.coin_id = c.id WHERE c.id = :id GROUP BY c.id"), {'id': coin_id}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail='Coin not found')
    metadata = parse_json(row.shopify_metadata, {})
    storefront = metadata.get('storefront', {}) if isinstance(metadata, dict) else {}
    ebay = metadata.get('ebay', {}) if isinstance(metadata, dict) else {}
    preview = {
        'coin_id': row.id,
        'sku': row.sku,
        'title': storefront.get('name') or row.title,
        'description': storefront.get('description') or row.description,
        'price': float(row.computed_price) if row.computed_price is not None else None,
        'quantity': row.quantity,
        'images': row.images or [],
        'ebay_item_id': ebay.get('itemId'),
        'ebay_url': ebay.get('url'),
        'product_type': storefront.get('productType'),
        'metal': storefront.get('metal'),
        'weight_label': storefront.get('weightLabel'),
        'sync_action': 'update_existing' if ebay.get('itemId') else 'create_new',
    }
    return preview


@router.post('/storefront/products/{coin_id}/ebay-sync-queue')
async def queue_ebay_sync(
    coin_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin_token),
):
    preview = await get_ebay_sync_preview(coin_id=coin_id, db=db, _=_)
    channel = db.execute(text("SELECT id FROM sync_channels WHERE channel_name = 'ebay' LIMIT 1")).fetchone()
    channel_id = channel.id if channel else None
    if channel_id:
        db.execute(text("INSERT INTO sync_logs (channel_id, sync_type, status, started_at, items_processed, items_successful, items_failed, sync_data, created_at) VALUES (:channel_id, 'product_export_preview', 'queued', NOW(), 1, 0, 0, :sync_data, NOW())"), {'channel_id': channel_id, 'sync_data': json.dumps(preview)})
        db.commit()
    return {'success': True, 'queued': True, 'preview': preview}


@router.post('/storefront/products/{coin_id}/ebay-publish')
async def publish_product_to_ebay(
    coin_id: int,
    payload: EbayPublishRequest,
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin_token),
):
    row = db.execute(text("SELECT c.id, c.sku, c.title, c.description, c.computed_price, c.quantity, c.shopify_metadata, COALESCE(json_agg(ci.url ORDER BY ci.sort_order) FILTER (WHERE ci.url IS NOT NULL), '[]'::json) AS images FROM coins c LEFT JOIN coin_images ci ON ci.coin_id = c.id WHERE c.id = :id GROUP BY c.id"), {'id': coin_id}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail='Coin not found')
    result = publish_coin_to_ebay(row, row.images or [], payload.model_dump(exclude_none=True))
    metadata = parse_json(row.shopify_metadata, {})
    ebay = metadata.get('ebay', {}) if isinstance(metadata, dict) else {}
    ebay.update({
        'seller': 'miracle_coins',
        'itemId': str(result.get('listing_id') or ebay.get('itemId') or ''),
        'offerId': result.get('offer_id'),
        'url': result.get('listing_url') or ebay.get('url'),
        'categoryId': result.get('category_id'),
        'lastSyncDirection': 'website_to_ebay',
        'lastSyncStatus': 'success',
    })
    metadata['ebay'] = ebay
    db.execute(text("UPDATE coins SET sku = :sku, shopify_metadata = :shopify_metadata, updated_at = NOW() WHERE id = :id"), {'id': coin_id, 'sku': result.get('sku') or row.sku, 'shopify_metadata': json.dumps(metadata)})
    db.commit()
    return {'success': True, 'result': result, 'ebay': ebay}


# ---------------------------------------------------------------------------
# AI description generation
# ---------------------------------------------------------------------------

class GenerateDescriptionRequest(BaseModel):
    title: str = ''
    metal: str = ''
    product_type: str = ''
    instructions: str = ''  # whatever the user typed in the description box

@router.post('/storefront/generate-description')
async def generate_description(
    req: GenerateDescriptionRequest,
    _: str = Depends(verify_admin_token),
):
    import openai as _openai
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail='OPENAI_API_KEY not configured')

    client = _openai.OpenAI(api_key=api_key)

    system = (
        "You write short, compelling product descriptions for Miracle Coins — "
        "a brand that sells real gold, platinum, and silver collectible cards. "
        "Descriptions are 2-3 sentences max. Mention the metal, the collectible nature, "
        "and any unique detail. No fluff, no emojis. Plain text only."
    )

    parts = []
    if req.title:        parts.append(f"Product title: {req.title}")
    if req.metal:        parts.append(f"Metal: {req.metal}")
    if req.product_type: parts.append(f"Type: {req.product_type}")
    if req.instructions: parts.append(f"Notes/instructions from seller: {req.instructions}")

    user_msg = "\n".join(parts) + "\n\nWrite the product description."

    resp = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=[{'role': 'system', 'content': system}, {'role': 'user', 'content': user_msg}],
        max_tokens=200,
        temperature=0.7,
    )
    text = resp.choices[0].message.content.strip()
    return {'description': text}


# ---------------------------------------------------------------------------
# Product options (dynamic metal & type lists)
# ---------------------------------------------------------------------------

@router.get('/storefront/options')
async def get_product_options():
    return load_product_options()


class ProductOptionsRequest(BaseModel):
    metals: Optional[List[Dict[str, Any]]] = None
    types: Optional[List[Dict[str, Any]]] = None
    discounts: Optional[List[Dict[str, Any]]] = None
    test_mode: Optional[bool] = None
    inquiry_mode: Optional[bool] = None


@router.put('/storefront/options')
async def update_product_options(
    req: ProductOptionsRequest,
    _: str = Depends(verify_admin_token),
):
    opts = load_product_options()
    if req.metals is not None:
        opts['metals'] = req.metals
    if req.types is not None:
        opts['types'] = req.types
    if req.discounts is not None:
        opts['discounts'] = req.discounts
    if req.test_mode is not None:
        opts['test_mode'] = req.test_mode
    if req.inquiry_mode is not None:
        opts['inquiry_mode'] = req.inquiry_mode
    save_product_options(opts)
    return opts


# ---------------------------------------------------------------------------
# Stripe checkout
# ---------------------------------------------------------------------------

class CheckoutItem(BaseModel):
    product_id: int
    qty: int = 1


class CheckoutSessionRequest(BaseModel):
    items: List[CheckoutItem]
    success_url: str
    cancel_url: str


@router.post('/storefront/checkout/session')
async def create_checkout_session(
    req: CheckoutSessionRequest,
    db: Session = Depends(get_db),
):
    opts = load_product_options()
    test_mode = opts.get('test_mode', False)
    if test_mode:
        stripe.api_key = os.getenv('STRIPE_TEST_SECRET_KEY')
        if not stripe.api_key:
            raise HTTPException(status_code=500, detail='Test mode enabled but STRIPE_TEST_SECRET_KEY not set in .env')
    else:
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
        if not stripe.api_key:
            raise HTTPException(status_code=500, detail='Stripe not configured — add STRIPE_SECRET_KEY to .env')

    if not req.items:
        raise HTTPException(status_code=400, detail='No items in cart')

    # Load product info for each item
    ids = [item.product_id for item in req.items]
    placeholders = ', '.join(f':id{i}' for i in range(len(ids)))
    params = {f'id{i}': id_ for i, id_ in enumerate(ids)}
    rows = db.execute(
        text(f"SELECT c.id, c.title, c.computed_price, c.shopify_metadata, COALESCE(json_agg(ci.url ORDER BY ci.sort_order) FILTER (WHERE ci.url IS NOT NULL), '[]'::json) AS images FROM coins c LEFT JOIN coin_images ci ON ci.coin_id = c.id WHERE c.id IN ({placeholders}) AND c.status = 'active' GROUP BY c.id"),
        params,
    ).fetchall()

    by_id = {r.id: r for r in rows}
    line_items = []
    for item in req.items:
        row = by_id.get(item.product_id)
        if not row:
            raise HTTPException(status_code=404, detail=f'Product {item.product_id} not found')
        price = float(row.computed_price or 0)
        if price <= 0:
            raise HTTPException(status_code=400, detail=f'Product {item.product_id} has no price set')

        meta = parse_json(row.shopify_metadata, {})
        storefront = meta.get('storefront', {})
        name = storefront.get('name') or row.title

        images = json.loads(row.images) if isinstance(row.images, str) else (row.images or [])
        product_data: dict = {'name': name}
        if images:
            product_data['images'] = [images[0]]

        line_items.append({
            'price_data': {
                'currency': 'usd',
                'unit_amount': int(round(price * 100)),
                'product_data': product_data,
            },
            'quantity': item.qty,
        })

    # Calculate order total and find applicable discount tier
    order_total = sum(
        (float(by_id[item.product_id].computed_price or 0)) * item.qty
        for item in req.items
        if item.product_id in by_id
    )
    opts = load_product_options()
    discount_tiers = sorted(opts.get('discounts', []), key=lambda d: d['minTotal'], reverse=True)
    applicable = next((d for d in discount_tiers if order_total >= d['minTotal']), None)

    # Build session metadata for webhook order creation
    # For multi-item carts, store comma-separated list
    first_item = req.items[0]
    first_row = by_id.get(first_item.product_id)
    first_meta = parse_json(first_row.shopify_metadata, {}) if first_row else {}
    first_name = first_meta.get('storefront', {}).get('name') or (first_row.title if first_row else '')
    session_metadata: dict = {
        'coin_id': str(first_item.product_id),
        'product_name': first_name,
        'qty': str(sum(i.qty for i in req.items)),
    }

    session_kwargs: dict = dict(
        payment_method_types=['card'],
        line_items=line_items,
        mode='payment',
        success_url=req.success_url,
        cancel_url=req.cancel_url,
        metadata=session_metadata,
    )

    if applicable:
        coupon = stripe.Coupon.create(
            percent_off=float(applicable['pct']),
            duration='once',
            metadata={'source': 'miracle_coins_order_discount'},
        )
        session_kwargs['discounts'] = [{'coupon': coupon.id}]

    session = stripe.checkout.Session.create(**session_kwargs)
    return {'url': session.url, 'session_id': session.id, 'discount_pct': applicable['pct'] if applicable else None}


@router.post('/storefront/checkout/webhook')
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Stripe sends POST here after payment. Wire up STRIPE_WEBHOOK_SECRET."""
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature', '')
    opts = load_product_options()
    test_mode = opts.get('test_mode', False)
    if test_mode:
        stripe.api_key = os.getenv('STRIPE_TEST_SECRET_KEY', os.getenv('STRIPE_SECRET_KEY', ''))
        webhook_secret = os.getenv('STRIPE_TEST_WEBHOOK_SECRET', os.getenv('STRIPE_WEBHOOK_SECRET', ''))
    else:
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY', '')
        webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET', '')

    if webhook_secret:
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        except Exception:
            raise HTTPException(status_code=400, detail='Invalid webhook signature')
    else:
        event = json.loads(payload)

    if event.get('type') == 'checkout.session.completed':
        session = event.get('data', {}).get('object', {})
        customer_email = session.get('customer_details', {}).get('email') or session.get('customer_email', '')
        customer_name = session.get('customer_details', {}).get('name', '')
        amount_total = session.get('amount_total', 0)  # cents
        sold_price = round(amount_total / 100, 2) if amount_total else None
        external_order_id = session.get('id', '')

        # Look up customer record
        ensure_orders_table(db)
        customer_row = None
        if customer_email:
            customer_row = db.execute(
                text('SELECT id FROM customers WHERE email = :e'),
                {'e': customer_email.lower().strip()}
            ).fetchone()

        # Extract line items metadata from session metadata (coin_id stored there at checkout)
        meta = session.get('metadata') or {}
        coin_id = meta.get('coin_id')
        product_name = meta.get('product_name', '')
        try:
            qty = int(meta.get('qty', 1))
        except (TypeError, ValueError):
            qty = 1

        db.execute(text("""
            INSERT INTO orders (external_order_id, customer_id, customer_email, customer_name,
                                coin_id, product_name, qty, sold_price, channel, status)
            VALUES (:eid, :cid, :email, :name, :coin_id, :pname, :qty, :price, 'stripe', 'paid')
        """), {
            'eid': external_order_id,
            'cid': customer_row.id if customer_row else None,
            'email': customer_email,
            'name': customer_name,
            'coin_id': coin_id,
            'pname': product_name,
            'qty': qty,
            'price': sold_price,
        })
        db.commit()

        price_str = f'${sold_price:.2f}' if sold_price else '(unknown)'
        item_str = f'{qty}x {product_name}' if product_name else f'qty {qty}'
        _discord_notify(
            f'**New Purchase!** :moneybag:\n'
            f'Customer: {customer_name or customer_email or "unknown"} ({customer_email})\n'
            f'Order: {item_str} — {price_str}\n'
            f'Stripe ID: `{external_order_id}`'
        )

    return {'received': True}


# ---------------------------------------------------------------------------
# Inquiry checkout (no payment — sends notification to admin)
# ---------------------------------------------------------------------------

class InquiryItem(BaseModel):
    product_id: int
    qty: int = 1

class InquiryCheckoutRequest(BaseModel):
    items: List[InquiryItem]
    name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    note: Optional[str] = None


@router.post('/storefront/checkout/inquiry')
async def create_checkout_inquiry(
    req: InquiryCheckoutRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Non-payment checkout: record inquiry and notify admin via Discord."""
    if not req.items:
        raise HTTPException(status_code=400, detail='No items in cart')

    # Decode auth token to get customer_id (if logged in)
    from app.routers.auth_router import decode_token
    customer_id: Optional[int] = None
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        payload = decode_token(auth_header[7:])
        if payload:
            customer_id = payload.get('customer_id')

    # Look up product details
    ids = [item.product_id for item in req.items]
    placeholders = ', '.join(f':id{i}' for i in range(len(ids)))
    params = {f'id{i}': id_ for i, id_ in enumerate(ids)}
    rows = db.execute(
        text(f"SELECT id, title, computed_price, shopify_metadata FROM coins WHERE id IN ({placeholders}) AND status = 'active'"),
        params,
    ).fetchall()
    by_id = {r.id: r for r in rows}

    lines = []
    order_total = 0.0
    inquiry_id = f'inquiry-{uuid.uuid4().hex[:12]}'  # one ID for the whole cart

    for item in req.items:
        row = by_id.get(item.product_id)
        if not row:
            continue
        meta = parse_json(row.shopify_metadata, {})
        name = meta.get('storefront', {}).get('name') or row.title
        price = float(row.computed_price or 0)
        subtotal = price * item.qty
        order_total += subtotal
        lines.append(f'  • {item.qty}x {name} — ${subtotal:.2f}' if price else f'  • {item.qty}x {name}')

    # Send Discord notification first — always fires regardless of DB outcome
    cart_str = '\n'.join(lines) if lines else '  (no items matched)'
    contact_str = req.name
    if req.email:
        contact_str += f' <{req.email}>'
    if req.phone:
        contact_str += f' | {req.phone}'

    _discord_notify(
        f'**New Order Request** :shopping_cart:\n'
        f'From: {contact_str}\n'
        + (f'Ship to: {req.address}\n' if req.address else '')
        + f'Items:\n{cart_str}\n'
        f'**Total: ${order_total:.2f}**'
        + (f'\nNote: {req.note}' if req.note else '')
    )

    # Save to DB — all items share the same inquiry_id so they group together
    try:
        ensure_orders_table(db)
        for item in req.items:
            row = by_id.get(item.product_id)
            if not row:
                continue
            meta = parse_json(row.shopify_metadata, {})
            name = meta.get('storefront', {}).get('name') or row.title
            price = float(row.computed_price or 0)
            db.execute(text("""
                INSERT INTO orders (external_order_id, customer_id, customer_email, customer_name,
                                    coin_id, product_name, qty, sold_price, channel, status, notes)
                VALUES (:eid, :cid, :email, :name, :coin_id, :pname, :qty, :price, 'inquiry', 'inquiry', :notes)
            """), {
                'eid': inquiry_id,
                'cid': customer_id,
                'email': req.email,
                'name': req.name,
                'coin_id': row.id,
                'pname': name,
                'qty': item.qty,
                'price': price if price else None,
                'notes': '\n'.join(filter(None, [
                    f'Ship to: {req.address}' if req.address else None,
                    req.note or None,
                ])) or None,
            })
        db.commit()
    except Exception:
        pass  # Discord already notified; don't fail the request over a DB issue

    return {'ok': True}


# ---------------------------------------------------------------------------
# Admin orders endpoints
# ---------------------------------------------------------------------------

class TrackingUpdateRequest(BaseModel):
    tracking_number: str
    notes: Optional[str] = None


@router.get('/storefront/admin/orders')
async def admin_list_orders(
    sort: str = Query('date_desc', pattern='^(date_desc|date_asc|customer_asc|customer_desc|status_asc|status_desc|price_desc|price_asc)$'),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin_token),
):
    ensure_orders_table(db)

    sort_map = {
        'date_desc': 'o.created_at DESC',
        'date_asc': 'o.created_at ASC',
        'customer_asc': 'o.customer_email ASC',
        'customer_desc': 'o.customer_email DESC',
        'status_asc': 'o.status ASC',
        'status_desc': 'o.status DESC',
        'price_desc': 'o.sold_price DESC NULLS LAST',
        'price_asc': 'o.sold_price ASC NULLS LAST',
    }
    order_by = sort_map.get(sort, 'o.created_at DESC')

    where_clauses = []
    params: dict = {'limit': limit, 'offset': offset}

    if status:
        where_clauses.append('o.status = :status')
        params['status'] = status
    if search:
        where_clauses.append("(o.customer_email ILIKE :search OR o.customer_name ILIKE :search OR o.product_name ILIKE :search OR o.external_order_id ILIKE :search)")
        params['search'] = f'%{search}%'

    where_sql = ('WHERE ' + ' AND '.join(where_clauses)) if where_clauses else ''

    rows = db.execute(text(f"""
        SELECT o.id, o.external_order_id, o.customer_id, o.customer_email, o.customer_name,
               o.coin_id, o.product_name, o.qty, o.sold_price, o.channel,
               o.status, o.tracking_number, o.notes, o.created_at, o.updated_at,
               c.name AS customer_profile_name,
               c.phone AS customer_phone,
               c.address_line1, c.address_line2, c.city, c.state_province, c.zip_code, c.country
        FROM orders o
        LEFT JOIN customers c ON (
            c.id = o.customer_id
            OR (o.customer_id IS NULL AND LOWER(c.email) = LOWER(o.customer_email))
        )
        {where_sql}
        ORDER BY {order_by}
        LIMIT :limit OFFSET :offset
    """), params).fetchall()

    total = db.execute(text(f'SELECT COUNT(*) FROM orders o {where_sql}'), {k: v for k, v in params.items() if k not in ('limit', 'offset')}).scalar()

    def _addr(r) -> Optional[str]:
        parts = []
        if getattr(r, 'address_line1', None): parts.append(r.address_line1)
        if getattr(r, 'address_line2', None): parts.append(r.address_line2)
        city = getattr(r, 'city', None) or ''
        state = getattr(r, 'state_province', None) or ''
        zip_code = getattr(r, 'zip_code', None) or ''
        city_line = ', '.join(filter(None, [city, state]))
        if zip_code: city_line = (city_line + ' ' + zip_code).strip()
        if city_line: parts.append(city_line)
        country = getattr(r, 'country', None)
        if country and country != 'United States': parts.append(country)
        return ', '.join(parts) if parts else None

    return {
        'orders': [
            {
                'id': r.id,
                'external_order_id': r.external_order_id,
                'customer_id': r.customer_id,
                'customer_email': r.customer_email,
                'customer_name': r.customer_name or getattr(r, 'customer_profile_name', None),
                'customer_phone': getattr(r, 'customer_phone', None),
                'customer_address': _addr(r),
                'coin_id': r.coin_id,
                'product_name': r.product_name,
                'qty': r.qty,
                'sold_price': float(r.sold_price) if r.sold_price is not None else None,
                'channel': r.channel,
                'status': r.status,
                'tracking_number': r.tracking_number,
                'notes': r.notes,
                'created_at': r.created_at.isoformat() if r.created_at else None,
                'updated_at': r.updated_at.isoformat() if r.updated_at else None,
            }
            for r in rows
        ],
        'total': total,
    }


@router.put('/storefront/admin/orders/{order_id}/tracking')
async def admin_update_tracking(
    order_id: int,
    req: TrackingUpdateRequest,
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin_token),
):
    ensure_orders_table(db)
    result = db.execute(text("""
        UPDATE orders
        SET tracking_number = :tracking, notes = COALESCE(:notes, notes), updated_at = NOW()
        WHERE id = :id
        RETURNING id
    """), {'tracking': req.tracking_number, 'notes': req.notes, 'id': order_id})
    row = result.fetchone()
    db.commit()
    if not row:
        raise HTTPException(status_code=404, detail='Order not found')
    return {'success': True}


@router.patch('/storefront/admin/orders/{order_id}/status')
async def admin_update_order_status(
    order_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin_token),
    status: str = Query(..., pattern='^(paid|shipped|delivered|refunded|cancelled|inquiry)$'),
):
    ensure_orders_table(db)
    result = db.execute(text("""
        UPDATE orders SET status = :status, updated_at = NOW() WHERE id = :id RETURNING id
    """), {'status': status, 'id': order_id})
    row = result.fetchone()
    db.commit()
    if not row:
        raise HTTPException(status_code=404, detail='Order not found')
    return {'success': True}


@router.delete('/storefront/admin/orders/group/{external_order_id}')
async def admin_delete_order_group(
    external_order_id: str,
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin_token),
):
    """Delete all order rows sharing the same external_order_id."""
    ensure_orders_table(db)
    db.execute(text('DELETE FROM orders WHERE external_order_id = :eid'), {'eid': external_order_id})
    db.commit()
    return {'success': True}

