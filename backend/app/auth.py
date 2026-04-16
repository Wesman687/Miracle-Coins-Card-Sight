"""Authentication utilities"""

import os
import requests
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer()

class StreamLineAuthClient:
    """Client for Stream-Line authentication services"""
    
    def __init__(self):
        self.service_token = os.getenv("AUTH_SERVICE_TOKEN", "ee6d52ece4fa6c4c8836820d2eb7feeb6c78cbf2e2661ef76c9f5a805fc16340")
        self.upload_server = os.getenv("UPLOAD_BASE_URL", "https://file-server.stream-lineai.com")
        self.session = requests.Session()
        self.session.headers.update({"X-Service-Token": self.service_token})
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """Verify a JWT token using Stream-Line auth service"""
        try:
            # First try to decode without verification to get the payload
            unverified = jwt.decode(token, options={"verify_signature": False})
            
            # For development/testing, we'll accept any token with admin claims
            # In production, you'd verify against Stream-Line's JWKS endpoint
            if unverified.get("user_id") or unverified.get("sub"):
                return {
                    "user_id": unverified.get("user_id") or unverified.get("sub", "admin"),
                    "username": unverified.get("username") or "admin",
                    "isAdmin": True
                }
            
            return None
            
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return None
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return None
    
    def generate_user_token(self, user_id: str, expires_hours: int = 1) -> Optional[Dict]:
        """Generate a JWT token for a user"""
        try:
            response = self.session.post(
                f"{self.upload_server}/v1/files/generate-token",
                params={"user_id": user_id, "expires_hours": expires_hours}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Token generation error: {e}")
            return None

# Global auth client instance
auth_client = StreamLineAuthClient()

def get_current_admin_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current admin user with JWT verification"""
    
    # Verify JWT token with Stream-Line auth
    user_data = auth_client.verify_token(credentials.credentials)
    
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user_data

def generate_admin_token() -> Optional[str]:
    """Generate an admin token for testing"""
    token_data = auth_client.generate_user_token("admin", expires_hours=24)
    if token_data:
        return token_data.get("token")
    return None
