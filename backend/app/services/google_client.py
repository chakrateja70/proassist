from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decrypt_secret, is_token_expired
from app.db.models import OAuthToken
from app.services.google_auth import refresh_google_access_token


async def get_valid_access_token(session: AsyncSession, token_row: OAuthToken) -> str:
    access_token = decrypt_secret(token_row.access_token_enc)
    if is_token_expired(token_row.expires_at):
        access_token = await refresh_google_access_token(token_row)
        session.add(token_row)
        await session.commit()
        await session.refresh(token_row)
    return access_token
