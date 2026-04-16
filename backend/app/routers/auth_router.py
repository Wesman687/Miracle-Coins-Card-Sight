from __future__ import annotations

import json
import os
import secrets
import urllib.request
import bcrypt
import jwt
import requests
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db


def _discord_notify(content: str) -> None:
    url = os.getenv('DISCORD_WEBHOOK_URL', '')
    if not url:
        return
    try:
        body = json.dumps({'content': content}).encode()
        req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json'}, method='POST')
        with urllib.request.urlopen(req, timeout=5):
            pass
    except Exception:
        pass

router = APIRouter()

JWT_SECRET = os.getenv('JWT_SECRET', secrets.token_hex(32))
JWT_ALGORITHM = 'HS256'
JWT_EXPIRE_HOURS = 24 * 7  # 1 week

AUTH_SERVICE_URL = os.getenv('AUTH_SERVICE_URL', 'https://server.stream-lineai.com')
ADMIN_EMAILS = {e.strip().lower() for e in os.getenv('ADMIN_EMAILS', '').split(',') if e.strip()}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_token(payload: dict, hours: int = JWT_EXPIRE_HOURS) -> str:
    data = {**payload, 'exp': datetime.now(timezone.utc) + timedelta(hours=hours)}
    return jwt.encode(data, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except Exception:
        return None


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def check_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except Exception:
        return False


def ensure_customers_table(db: Session):
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS customers (
            id BIGSERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            name VARCHAR(255),
            password_hash TEXT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
    """))
    db.commit()


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class LoginRequest(BaseModel):
    email: str
    password: str


class AdminLoginRequest(BaseModel):
    email: str
    password: str


class CustomerRegisterRequest(BaseModel):
    email: str
    name: str
    password: str


class CustomerLoginRequest(BaseModel):
    email: str
    password: str


# ---------------------------------------------------------------------------
# Admin auth
# ---------------------------------------------------------------------------

def _check_admin(user: dict) -> bool:
    if user.get('is_admin') or user.get('user_type') == 'admin':
        return True
    email = (user.get('email') or '').lower()
    return bool(email and email in ADMIN_EMAILS)


@router.post('/auth/login')
async def unified_login(req: LoginRequest, db: Session = Depends(get_db)):
    """
    Single login endpoint for all users.
    1. Try stream-lineai auth server — if success, determine role from user profile.
    2. Fall back to local customer DB.
    """
    # --- Try stream-lineai ---
    try:
        login_resp = requests.post(
            f'{AUTH_SERVICE_URL}/api/auth/login',
            json={'email': req.email, 'password': req.password},
            timeout=8,
        )
        if login_resp.status_code == 200:
            data = login_resp.json()
            token = data.get('token') or data.get('access_token')
            if token:
                # Fetch user profile to determine admin status
                me_resp = requests.get(
                    f'{AUTH_SERVICE_URL}/api/auth/me',
                    headers={'Authorization': f'Bearer {token}'},
                    timeout=5,
                )
                user = {}
                if me_resp.status_code == 200:
                    me_data = me_resp.json()
                    user = me_data.get('user') or me_data

                role = 'admin' if _check_admin(user) else 'user'
                email = user.get('email', req.email)
                name = user.get('name') or user.get('username')

                if role == 'admin':
                    # Issue a local JWT so admin endpoints don't need network round-trips
                    local_token = make_token({'sub': email.lower(), 'role': 'admin', 'email': email, 'isAdmin': True})
                    return {
                        'token': local_token,
                        'role': 'admin',
                        'email': email,
                        'name': name,
                        'isAdmin': True,
                    }

                return {
                    'token': token,
                    'role': role,
                    'email': email,
                    'name': name,
                    'isAdmin': False,
                }
    except Exception:
        pass  # fall through to local customer check

    # --- Try local customer DB ---
    ensure_customers_table(db)
    row = db.execute(
        text('SELECT id, name, password_hash FROM customers WHERE email = :email'),
        {'email': req.email.lower().strip()}
    ).fetchone()

    if not row or not check_password(req.password, row.password_hash):
        raise HTTPException(status_code=401, detail='Invalid email or password')

    token = make_token({'sub': req.email.lower().strip(), 'role': 'customer', 'customer_id': row.id})
    return {
        'token': token,
        'role': 'customer',
        'email': req.email.lower().strip(),
        'name': row.name,
        'customerId': row.id,
        'isAdmin': False,
    }


@router.post('/auth/admin/login')
async def admin_login(req: AdminLoginRequest):
    """Legacy alias — redirects to unified login."""
    try:
        resp = requests.post(
            f'{AUTH_SERVICE_URL}/api/auth/login',
            json={'email': req.email, 'password': req.password},
            timeout=8,
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f'Auth server unreachable: {exc}')

    if resp.status_code == 401:
        raise HTTPException(status_code=401, detail='Invalid email or password')
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail='Auth server error')

    data = resp.json()
    token = data.get('token') or data.get('access_token')
    if not token:
        raise HTTPException(status_code=502, detail='Auth server returned no token')

    return {'token': token, 'role': 'admin'}


# ---------------------------------------------------------------------------
# Customer auth
# ---------------------------------------------------------------------------

@router.post('/auth/customer/register', status_code=201)
async def customer_register(req: CustomerRegisterRequest, db: Session = Depends(get_db)):
    ensure_customers_table(db)

    if len(req.password) < 8:
        raise HTTPException(status_code=400, detail='Password must be at least 8 characters')

    existing = db.execute(
        text('SELECT id FROM customers WHERE email = :email'),
        {'email': req.email.lower().strip()}
    ).fetchone()
    if existing:
        raise HTTPException(status_code=409, detail='An account with that email already exists')

    pw_hash = hash_password(req.password)
    row = db.execute(
        text('INSERT INTO customers (email, name, password_hash) VALUES (:email, :name, :pw) RETURNING id'),
        {'email': req.email.lower().strip(), 'name': req.name.strip(), 'pw': pw_hash}
    ).fetchone()
    db.commit()

    token = make_token({'sub': req.email.lower().strip(), 'role': 'customer', 'customer_id': row.id})

    _discord_notify(
        f'**New Account Signup!** :wave:\n'
        f'Name: {req.name.strip()}\n'
        f'Email: {req.email.lower().strip()}'
    )

    return {'token': token, 'role': 'customer', 'name': req.name.strip()}


@router.post('/auth/customer/login')
async def customer_login(req: CustomerLoginRequest, db: Session = Depends(get_db)):
    ensure_customers_table(db)

    row = db.execute(
        text('SELECT id, name, password_hash FROM customers WHERE email = :email'),
        {'email': req.email.lower().strip()}
    ).fetchone()

    if not row or not check_password(req.password, row.password_hash):
        raise HTTPException(status_code=401, detail='Invalid email or password')

    token = make_token({'sub': req.email.lower().strip(), 'role': 'customer', 'customer_id': row.id})
    return {'token': token, 'role': 'customer', 'name': row.name, 'customer_id': row.id}


@router.get('/auth/customer/me')
async def customer_me(db: Session = Depends(get_db), authorization: str = ''):
    # Token passed as query param or header — handled in frontend via fetch
    raise HTTPException(status_code=401, detail='Use Authorization header')


@router.get('/auth/customer/orders/{customer_id}')
async def customer_orders(customer_id: int, db: Session = Depends(get_db)):
    """Return orders for a customer (from Stripe webhook data stored in orders table)."""
    ensure_customers_table(db)
    rows = db.execute(
        text("""
            SELECT o.id, o.external_order_id, o.qty, o.sold_price, o.created_at,
                   c.title as product_name
            FROM orders o
            LEFT JOIN coins c ON c.id = o.coin_id
            WHERE o.channel = 'stripe'
            ORDER BY o.created_at DESC
            LIMIT 50
        """)
    ).fetchall()
    return {
        'orders': [
            {
                'id': r.id,
                'order_id': r.external_order_id,
                'product': r.product_name,
                'qty': r.qty,
                'total': float(r.sold_price) if r.sold_price is not None else None,
                'date': r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]
    }
