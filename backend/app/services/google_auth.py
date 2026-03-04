from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx
from google.oauth2.credentials import Credentials
from jose import JWTError, jwt

from app.core.config import get_settings
from app.core.security import decrypt_secret, encrypt_secret
from app.db.models import OAuthToken

GOOGLE_AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_ENDPOINT = "https://www.googleapis.com/oauth2/v3/userinfo"


def build_google_auth_url() -> tuple[str, str]:
    settings = get_settings()
    state = build_signed_oauth_state()
    query = urlencode(
        {
            "client_id": settings.google_client_id,
            "redirect_uri": settings.google_redirect_uri,
            "response_type": "code",
            "scope": " ".join(settings.google_required_scopes_list),
            "access_type": "offline",
            "prompt": "consent",
            "include_granted_scopes": "true",
            "state": state,
        }
    )
    return f"{GOOGLE_AUTH_ENDPOINT}?{query}", state


def build_signed_oauth_state() -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "nonce": secrets.token_urlsafe(24),
        "purpose": "google_oauth_state",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=10)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def validate_signed_oauth_state(state: str) -> bool:
    settings = get_settings()
    try:
        payload = jwt.decode(state, settings.jwt_secret, algorithms=["HS256"])
    except JWTError:
        return False
    return payload.get("purpose") == "google_oauth_state"


async def exchange_code_for_token(code: str) -> dict:
    settings = get_settings()
    payload = {
        "code": code,
        "client_id": settings.google_client_id,
        "client_secret": settings.google_client_secret,
        "redirect_uri": settings.google_redirect_uri,
        "grant_type": "authorization_code",
    }
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(GOOGLE_TOKEN_ENDPOINT, data=payload)
        response.raise_for_status()
        return response.json()


async def fetch_userinfo(access_token: str) -> dict:
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(GOOGLE_USERINFO_ENDPOINT, headers=headers)
        response.raise_for_status()
        return response.json()


def token_expiry(expires_in_seconds: int | None) -> datetime | None:
    if not expires_in_seconds:
        return None
    return datetime.now(timezone.utc) + timedelta(seconds=int(expires_in_seconds))


def scopes_are_sufficient(scope_text: str) -> bool:
    granted = set(scope_text.split())
    required = set(get_settings().google_required_scopes_list)

    # Google may return userinfo scopes instead of short "email/profile" scopes.
    aliases = {
        "email": "https://www.googleapis.com/auth/userinfo.email",
        "profile": "https://www.googleapis.com/auth/userinfo.profile",
    }
    normalized_required = {(aliases.get(scope, scope)) for scope in required}
    return normalized_required.issubset(granted)


def update_oauth_token(model: OAuthToken, token_data: dict) -> OAuthToken:
    model.access_token_enc = encrypt_secret(token_data["access_token"])
    if token_data.get("refresh_token"):
        model.refresh_token_enc = encrypt_secret(token_data["refresh_token"])
    model.scope = token_data.get("scope", model.scope)
    model.expires_at = token_expiry(token_data.get("expires_in"))
    return model


async def refresh_google_access_token(token_row: OAuthToken) -> str:
    settings = get_settings()
    refresh_token = decrypt_secret(token_row.refresh_token_enc)
    payload = {
        "client_id": settings.google_client_id,
        "client_secret": settings.google_client_secret,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(GOOGLE_TOKEN_ENDPOINT, data=payload)
        response.raise_for_status()
        new_data = response.json()
    token_row.access_token_enc = encrypt_secret(new_data["access_token"])
    token_row.expires_at = token_expiry(new_data.get("expires_in"))
    return new_data["access_token"]


def build_google_credentials(token_row: OAuthToken, access_token: str | None = None) -> Credentials:
    settings = get_settings()
    return Credentials(
        token=access_token or decrypt_secret(token_row.access_token_enc),
        refresh_token=decrypt_secret(token_row.refresh_token_enc),
        token_uri=GOOGLE_TOKEN_ENDPOINT,
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        scopes=token_row.scope.split(),
    )
