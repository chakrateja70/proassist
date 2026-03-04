from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_user, db_session
from app.db.models import Draft, DraftStatus, JobInput, SendMode, SendRequest, SendStatus, User
from app.db.schemas import SendRequestPayload, SendResponse
from app.services.audit import write_audit_log
from app.services.scheduler import enqueue_send_job
from app.services.send_processor import execute_send_request

router = APIRouter(prefix="/sends", tags=["sends"])


@router.post("", response_model=SendResponse)
async def create_send(
    payload: SendRequestPayload,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(db_session),
):
    draft = await session.get(Draft, payload.draft_id)
    if not draft or draft.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")
    if draft.status != DraftStatus.approved:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Draft must be approved before send")

    job = await session.get(JobInput, draft.job_input_id)
    if not job or job.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job input not found")
    if not job.selected_hr_email and not payload.to_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="HR email is required")

    target_email = payload.to_email or job.selected_hr_email
    if not target_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing destination email")
    job.selected_hr_email = target_email

    send_req = SendRequest(
        user_id=user.id,
        draft_id=draft.id,
        to_email=target_email,
        mode=SendMode(payload.mode.value),
        status=SendStatus.pending,
        scheduled_at=payload.scheduled_at,
        sent_subject=draft.gmail_subject,
        sent_body=draft.gmail_body,
        snapshot_json={
            "gmail_subject": draft.gmail_subject,
            "gmail_body": draft.gmail_body,
            "linkedin_message": draft.linkedin_message,
            "approved_at": draft.approved_at.isoformat() if draft.approved_at else None,
            "job_input_id": draft.job_input_id,
        },
    )
    session.add(send_req)
    await session.flush()

    if payload.mode.value == "scheduled":
        if not payload.scheduled_at:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="scheduled_at is required for scheduled mode")
        if payload.scheduled_at <= datetime.now(timezone.utc):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="scheduled_at must be in the future")
        draft.status = DraftStatus.scheduled
        await enqueue_send_job(
            session=session,
            send_request_id=send_req.id,
            run_at=payload.scheduled_at,
            idempotency_key=f"send:{send_req.id}",
        )
    else:
        try:
            await execute_send_request(session, send_req)
        except Exception as exc:
            send_req.status = SendStatus.failed
            send_req.failure_reason = str(exc)
            draft.status = DraftStatus.failed

    await write_audit_log(
        session=session,
        user_id=user.id,
        entity="send_requests",
        entity_id=send_req.id,
        action="create_send",
        before_json=None,
        after_json={
            "draft_id": draft.id,
            "to_email": send_req.to_email,
            "mode": send_req.mode.value,
            "status": send_req.status.value,
        },
    )
    await session.commit()
    await session.refresh(send_req)
    return SendResponse(
        id=send_req.id,
        status=send_req.status.value,
        mode=payload.mode,
        scheduled_at=send_req.scheduled_at,
        sent_at=send_req.sent_at,
        gmail_message_id=send_req.gmail_message_id,
        failure_reason=send_req.failure_reason,
    )
