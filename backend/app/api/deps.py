from collections.abc import AsyncGenerator

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import AuthError, parse_jwt_or_raise
from app.db.models import OAuthToken, Resume, User
from app.db.session import get_db_session


async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_db_session():
        yield session


async def current_user(
    session: AsyncSession = Depends(db_session),
    proassist_session: str | None = Cookie(default=None),
) -> User:
    if not proassist_session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        claims = parse_jwt_or_raise(proassist_session)
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    user_id = claims.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")

    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


async def get_user_token(session: AsyncSession, user_id: str) -> OAuthToken:
    token = await session.scalar(select(OAuthToken).where(OAuthToken.user_id == user_id))
    if not token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Google OAuth not connected")
    return token


async def get_active_resume(session: AsyncSession, user_id: str) -> Resume | None:
    return await session.scalar(
        select(Resume).where(Resume.user_id == user_id, Resume.is_active.is_(True)).order_by(Resume.created_at.desc())
    )
