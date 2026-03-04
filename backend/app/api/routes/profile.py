from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_user, db_session
from app.db.models import Profile, User
from app.db.schemas import ProfileResponse, ProfileUpdate
from app.services.audit import write_audit_log

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=ProfileResponse | None)
async def get_profile(user: User = Depends(current_user), session: AsyncSession = Depends(db_session)):
    return await session.scalar(select(Profile).where(Profile.user_id == user.id))


@router.put("", response_model=ProfileResponse)
async def upsert_profile(
    payload: ProfileUpdate,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(db_session),
):
    profile = await session.scalar(select(Profile).where(Profile.user_id == user.id))
    before = None
    if not profile:
        profile = Profile(user_id=user.id)
        session.add(profile)
    else:
        before = {
            "headline": profile.headline,
            "years_experience": profile.years_experience,
            "linkedin_url": profile.linkedin_url,
            "github_url": profile.github_url,
            "portfolio_url": profile.portfolio_url,
            "summary": profile.summary,
            "skills": profile.skills,
            "location": profile.location,
            "phone": profile.phone,
        }

    for field, value in payload.model_dump().items():
        setattr(profile, field, value)

    await session.flush()
    await write_audit_log(
        session=session,
        user_id=user.id,
        entity="profile",
        entity_id=profile.id,
        action="upsert",
        before_json=before,
        after_json=payload.model_dump(),
    )
    await session.commit()
    await session.refresh(profile)
    return profile
