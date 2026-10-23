"""Use Supabase Auth to validate tokens and load the current user.

No password, service-role key, unverified JWT or client-supplied owner is trusted.
Online verification also supports legacy and rotated signing keys.
"""
from dataclasses import dataclass
from functools import lru_cache
from typing import Annotated
from uuid import UUID
import httpx
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.config import auth_settings

bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthUser:
    id: UUID
    email: str | None = None


@lru_cache(maxsize=1)
def auth_client() -> httpx.Client:
    return httpx.Client(timeout=10, follow_redirects=False,
                        limits=httpx.Limits(max_connections=20, max_keepalive_connections=5))


def get_current_user(credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]) -> AuthUser:
    unauthorized = HTTPException(401, 'Sign in to continue.', headers={'WWW-Authenticate': 'Bearer'})
    if credentials is None or credentials.scheme.lower() != 'bearer':
        raise unauthorized
    try:
        url, key = auth_settings()
    except ValueError:
        raise HTTPException(503, 'Authentication is not configured.') from None
    try:
        response = auth_client().get(f'{url}/auth/v1/user', headers={
            'apikey': key, 'Authorization': f'Bearer {credentials.credentials}',
        })
    except httpx.RequestError:
        raise HTTPException(503, 'Unable to verify your session. Please try again.') from None
    if response.status_code in (401, 403):
        raise unauthorized
    if response.status_code != 200:
        raise HTTPException(503, 'Unable to verify your session. Please try again.')
    try:
        user = response.json()
        user_id = UUID(user['id'])
        if user.get('is_anonymous') or user.get('role') != 'authenticated':
            raise unauthorized
        return AuthUser(user_id, user.get('email'))
    except (ValueError, KeyError, TypeError):
        raise HTTPException(503, 'Unable to verify your session. Please try again.') from None
