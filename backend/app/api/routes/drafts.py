from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_user, db_session, get_active_resume
from app.db.models import Draft, DraftStatus, JobInput, Profile, User
from app.db.schemas import DraftPatch, DraftResponse, GenerateDraftRequest, GenerateDraftResponse
from app.services.audit import write_audit_log
from app.services.draft_logic import compute_draft_state
from app.services.llm_service import generate_outreach

router = APIRouter(prefix="/drafts", tags=["drafts"])


@router.post("/generate", response_model=GenerateDraftResponse)
async def generate_draft(
    payload: GenerateDraftRequest,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(db_session),
):
    profile = await session.scalar(select(Profile).where(Profile.user_id == user.id))
    if not profile:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Profile required before generation")
    resume = await get_active_resume(session, user.id)
    if not resume:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Active resume required before generation")

    job = await session.get(JobInput, payload.job_id)
    if not job or job.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job input not found")

    generated = await generate_outreach(user=user, profile=profile, resume=resume, job=job)
    draft = Draft(
        user_id=user.id,
        job_input_id=job.id,
        gmail_subject=generated["gmail_subject"],
        gmail_body=generated["gmail_body"],
        linkedin_message=generated["linkedin_message"],
        generation_meta_json={"personalization_rationale": generated["personalization_rationale"]},
        status=DraftStatus.generated,
    )
    session.add(draft)
    await session.flush()
    await write_audit_log(
        session=session,
        user_id=user.id,
        entity="draft",
        entity_id=draft.id,
        action="generate",
        before_json=None,
        after_json={"job_id": job.id},
    )
    await session.commit()
    await session.refresh(draft)
    return GenerateDraftResponse(
        draft_id=draft.id,
        gmail_subject=draft.gmail_subject,
        gmail_body=draft.gmail_body,
        linkedin_message=draft.linkedin_message,
        personalization_rationale=draft.generation_meta_json.get("personalization_rationale", ""),
    )


@router.patch("/{draft_id}", response_model=DraftResponse)
async def update_draft(
    draft_id: str,
    payload: DraftPatch,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(db_session),
):
    draft = await session.get(Draft, draft_id)
    if not draft or draft.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")

    job = await session.get(JobInput, draft.job_input_id)
    if not job or job.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    before = {
        "gmail_subject": draft.gmail_subject,
        "gmail_body": draft.gmail_body,
        "linkedin_message": draft.linkedin_message,
        "status": draft.status.value,
    }

    changed_content = False
    if payload.gmail_subject is not None and payload.gmail_subject != draft.gmail_subject:
        draft.gmail_subject = payload.gmail_subject
        changed_content = True
    if payload.gmail_body is not None and payload.gmail_body != draft.gmail_body:
        draft.gmail_body = payload.gmail_body
        changed_content = True
    if payload.linkedin_message is not None and payload.linkedin_message != draft.linkedin_message:
        draft.linkedin_message = payload.linkedin_message
        changed_content = True
    if payload.selected_hr_email is not None:
        job.selected_hr_email = payload.selected_hr_email

    if payload.approve and not job.selected_hr_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="HR email must be confirmed before approval")

    next_status, next_approved_at = compute_draft_state(
        current_status=draft.status,
        content_changed=changed_content,
        approve=payload.approve,
        current_approved_at=draft.approved_at,
        now=datetime.now(timezone.utc),
    )
    draft.status = next_status
    draft.approved_at = next_approved_at

    await write_audit_log(
        session=session,
        user_id=user.id,
        entity="draft",
        entity_id=draft.id,
        action="update",
        before_json=before,
        after_json={
            "gmail_subject": draft.gmail_subject,
            "gmail_body": draft.gmail_body,
            "linkedin_message": draft.linkedin_message,
            "status": draft.status.value,
            "selected_hr_email": job.selected_hr_email,
        },
    )
    await session.commit()
    await session.refresh(draft)
    return DraftResponse.model_validate(draft)
