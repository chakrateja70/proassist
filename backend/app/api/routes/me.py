from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_user, db_session, get_active_resume, get_user_token
from app.db.models import Profile, User
from app.db.schemas import MeResponse

router = APIRouter(tags=["me"])


@router.get("/me", response_model=MeResponse)
async def me(user: User = Depends(current_user), session: AsyncSession = Depends(db_session)) -> MeResponse:
    profile = await session.scalar(select(Profile).where(Profile.user_id == user.id))
    resume = await get_active_resume(session, user.id)
    token = await get_user_token(session, user.id)
    scopes = token.scope.split()
    integrations_ready = (
        "https://www.googleapis.com/auth/gmail.send" in scopes
        and "https://www.googleapis.com/auth/drive.file" in scopes
        and resume is not None
    )
    return MeResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        preferred_language=user.preferred_language,
        has_profile=profile is not None,
        has_active_resume=resume is not None,
        google_scopes=scopes,
        integrations_ready=integrations_ready,
    )
