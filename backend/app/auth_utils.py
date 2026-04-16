import os
import jwt
import httpx
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer(auto_error=False)

AUTH_SERVICE_URL = os.getenv('AUTH_SERVICE_URL', 'https://server.stream-lineai.com')
MANAGE_TOKEN = os.getenv('MANAGE_TOKEN', 'manage-token')  # legacy dev fallback
JWT_SECRET = os.getenv('JWT_SECRET', '')
JWT_ALGORITHM = 'HS256'

# Optional comma-separated list of admin emails as a secondary admin check
ADMIN_EMAILS = {e.strip().lower() for e in os.getenv('ADMIN_EMAILS', '').split(',') if e.strip()}


def _decode_local(token: str) -> dict | None:
    """Try to decode a locally-signed JWT."""
    if not JWT_SECRET or not token:
        return None
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except Exception:
        return None


async def _validate_remote(token: str) -> dict | None:
    """Call /api/auth/me on the auth server to validate the token and get user info."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f'{AUTH_SERVICE_URL}/api/auth/me',
                headers={'Authorization': f'Bearer {token}'},
                timeout=5,
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get('user') or data
    except Exception:
        pass
    return None


def _is_admin(user: dict) -> bool:
    if user.get('is_admin') or user.get('user_type') == 'admin' or user.get('role') == 'admin':
        return True
    email = (user.get('email') or user.get('sub') or '').lower()
    return bool(email and email in ADMIN_EMAILS)


async def verify_admin_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials if credentials else ''

    # Legacy dev token
    if token == MANAGE_TOKEN:
        return {'user_id': 'admin', 'role': 'admin', 'isAdmin': True}

    # Local JWT (issued on login for admin users)
    local = _decode_local(token)
    if local and _is_admin(local):
        return {
            'user_id': local.get('sub'),
            'email': local.get('email') or local.get('sub'),
            'role': 'admin',
            'isAdmin': True,
        }

    # Remote stream-lineai validation (fallback for older sessions)
    user = await _validate_remote(token)
    if user and _is_admin(user):
        return {
            'user_id': user.get('id') or user.get('user_id'),
            'email': user.get('email'),
            'role': 'admin',
            'isAdmin': True,
        }

    raise HTTPException(status_code=401, detail='Admin access required')


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    return await verify_admin_token(credentials)
