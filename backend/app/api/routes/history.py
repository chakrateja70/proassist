from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_user, db_session
from app.db.models import Draft, JobInput, SendRequest, User
from app.db.schemas import HistoryItem

router = APIRouter(prefix="/history", tags=["history"])


@router.get("", response_model=list[HistoryItem])
async def history(user: User = Depends(current_user), session: AsyncSession = Depends(db_session)):
    drafts = list((await session.scalars(select(Draft).where(Draft.user_id == user.id).order_by(Draft.created_at.desc()))).all())
    items: list[HistoryItem] = []
    for draft in drafts:
        job = await session.get(JobInput, draft.job_input_id)
        send = await session.scalar(select(SendRequest).where(SendRequest.draft_id == draft.id).order_by(SendRequest.created_at.desc()))
        items.append(
            HistoryItem(
                draft_id=draft.id,
                send_id=send.id if send else None,
                company_name=job.company_name if job else None,
                role_title=job.role_title if job else None,
                to_email=send.to_email if send else None,
                draft_status=draft.status.value,
                send_status=send.status.value if send else None,
                created_at=draft.created_at,
                sent_at=send.sent_at if send else None,
                scheduled_at=send.scheduled_at if send else None,
            )
        )
    return items
