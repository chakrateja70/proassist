from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_active_resume, get_user_token
from app.db.models import Draft, DraftStatus, SendRequest, SendStatus, User
from app.services.drive_service import download_drive_file
from app.services.gmail_service import send_gmail_message
from app.services.google_client import get_valid_access_token


async def execute_send_request(session: AsyncSession, send_request: SendRequest) -> SendRequest:
    draft = await session.get(Draft, send_request.draft_id)
    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found for send")
    user = await session.get(User, send_request.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found for send")
    if draft.status != DraftStatus.approved and draft.status != DraftStatus.scheduled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Draft must be approved before sending")

    resume = await get_active_resume(session, user.id)
    if not resume:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Active resume required to send email")

    token_row = await get_user_token(session, user.id)
    access_token = await get_valid_access_token(session, token_row)
    attachment_content = await download_drive_file(token_row, access_token, resume.drive_file_id)
    gmail_message_id = await send_gmail_message(
        token_row=token_row,
        access_token=access_token,
        to_email=send_request.to_email,
        subject=draft.gmail_subject,
        body=draft.gmail_body,
        attachment_filename=resume.filename,
        attachment_content=attachment_content,
        attachment_mime_type=resume.mime_type,
    )

    send_request.status = SendStatus.sent
    send_request.sent_at = datetime.now(timezone.utc)
    send_request.gmail_message_id = gmail_message_id
    send_request.failure_reason = None
    draft.status = DraftStatus.sent
    return send_request
