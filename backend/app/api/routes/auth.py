from datetime import datetime, timezone
import logging

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import db_session
from app.core.config import get_settings
from app.core.security import create_access_token, encrypt_secret
from app.db.models import OAuthToken, User
from app.services.google_auth import (
    build_google_auth_url,
    exchange_code_for_token,
    fetch_userinfo,
    scopes_are_sufficient,
    token_expiry,
    update_oauth_token,
    validate_signed_oauth_state,
)

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)


def _extract_google_error(exc: httpx.HTTPStatusError) -> str:
    try:
        payload = exc.response.json()
    except Exception:
        return exc.response.text or "Unknown Google API error"
    if isinstance(payload, dict):
        if isinstance(payload.get("error"), dict):
            code = payload["error"].get("status") or payload["error"].get("code")
            msg = payload["error"].get("message")
            if code and msg:
                return f"{code}: {msg}"
            if msg:
                return msg
        if payload.get("error_description"):
            return f"{payload.get('error')}: {payload.get('error_description')}"
        if payload.get("error"):
            return str(payload.get("error"))
    return str(payload)


@router.post("/google/start")
async def google_start(response: Response) -> dict:
    auth_url, state = build_google_auth_url()
    response.set_cookie(
        key="google_oauth_state",
        value=state,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=600,
    )
    return {"auth_url": auth_url}


@router.get("/google/callback")
async def google_callback(
    request: Request,
    code: str = Query(...),
    state: str = Query(...),
    session: AsyncSession = Depends(db_session),
):
    expected_state = request.cookies.get("google_oauth_state")
    valid_state = bool(expected_state and expected_state == state) or validate_signed_oauth_state(state)
    if not valid_state:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OAuth state")

    try:
        token_data = await exchange_code_for_token(code)
    except httpx.HTTPStatusError as exc:
        detail = _extract_google_error(exc)
        logger.warning("Google token exchange failed: %s", detail)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Google token exchange failed: {detail}") from exc

    if not scopes_are_sufficient(token_data.get("scope", "")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Required Gmail/Drive scopes were not granted",
        )

    try:
        userinfo = await fetch_userinfo(token_data["access_token"])
    except httpx.HTTPStatusError as exc:
        detail = _extract_google_error(exc)
        logger.warning("Google userinfo fetch failed: %s", detail)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Google userinfo failed: {detail}") from exc

    google_sub = userinfo.get("sub")
    email = userinfo.get("email")
    name = userinfo.get("name", email)
    if not google_sub or not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Google user info missing required fields")

    user = await session.scalar(select(User).where(User.google_sub == google_sub))
    if not user:
        user = await session.scalar(select(User).where(User.email == email))
    if not user:
        user = User(google_sub=google_sub, email=email, name=name)
        session.add(user)
        await session.flush()
    else:
        # Backfill linkage if an email-only row already exists.
        user.google_sub = google_sub
        user.name = name or user.name
        session.add(user)

    oauth = await session.scalar(select(OAuthToken).where(OAuthToken.user_id == user.id))
    if not oauth:
        refresh_token = token_data.get("refresh_token")
        if not refresh_token:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing Google refresh token")
        oauth = OAuthToken(
            user_id=user.id,
            provider="google",
            access_token_enc=encrypt_secret(token_data["access_token"]),
            refresh_token_enc=encrypt_secret(refresh_token),
            scope=token_data.get("scope", ""),
            expires_at=token_expiry(token_data.get("expires_in")),
            updated_at=datetime.now(timezone.utc),
        )
        session.add(oauth)
    else:
        update_oauth_token(oauth, token_data)
        session.add(oauth)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        logger.exception("OAuth callback DB commit failed")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Account already exists with conflicting Google identity. Contact support or use the original account.",
        ) from exc

    app_token = create_access_token(subject=user.id, extra={"email": user.email})
    redirect = RedirectResponse(url=f"{get_settings().frontend_url}/app")
    redirect.delete_cookie("google_oauth_state")
    redirect.set_cookie(
        key="proassist_session",
        value=app_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=get_settings().jwt_expire_minutes * 60,
    )
    return redirect


@router.post("/logout")
async def logout():
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.delete_cookie("proassist_session")
    return response
