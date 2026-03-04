from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_user, db_session, get_user_token
from app.db.models import Resume, User
from app.db.schemas import ResumeResponse
from app.services.audit import write_audit_log
from app.services.drive_service import upload_resume_to_drive
from app.services.google_client import get_valid_access_token
from app.services.resume_parser import SUPPORTED_RESUME_MIME, extract_resume_text

router = APIRouter(prefix="/resumes", tags=["resumes"])


@router.post("/upload", response_model=ResumeResponse)
async def upload_resume(
    file: UploadFile = File(...),
    user: User = Depends(current_user),
    session: AsyncSession = Depends(db_session),
):
    if file.content_type not in SUPPORTED_RESUME_MIME:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF/DOCX files are allowed")
    content = await file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file")

    parsed_text = extract_resume_text(content=content, mime_type=file.content_type)
    if not parsed_text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to extract resume text")

    token_row = await get_user_token(session, user.id)
    access_token = await get_valid_access_token(session, token_row)
    drive_file = await upload_resume_to_drive(
        token_row=token_row,
        access_token=access_token,
        filename=file.filename or "resume",
        mime_type=file.content_type,
        content=content,
    )

    await session.execute(update(Resume).where(Resume.user_id == user.id).values(is_active=False))
    resume = Resume(
        user_id=user.id,
        drive_file_id=drive_file["id"],
        drive_web_link=drive_file.get("webViewLink", ""),
        filename=drive_file.get("name", file.filename or "resume"),
        mime_type=drive_file.get("mimeType", file.content_type),
        parsed_text=parsed_text,
        is_active=True,
    )
    session.add(resume)
    await session.flush()
    await write_audit_log(
        session=session,
        user_id=user.id,
        entity="resume",
        entity_id=resume.id,
        action="upload",
        before_json=None,
        after_json={"filename": resume.filename, "drive_file_id": resume.drive_file_id},
    )
    await session.commit()
    await session.refresh(resume)

    return ResumeResponse(
        id=resume.id,
        drive_file_id=resume.drive_file_id,
        drive_web_link=resume.drive_web_link,
        filename=resume.filename,
        mime_type=resume.mime_type,
        parsed_text_preview=resume.parsed_text[:500],
        is_active=resume.is_active,
        created_at=resume.created_at,
    )


@router.get("", response_model=list[ResumeResponse])
async def list_resumes(user: User = Depends(current_user), session: AsyncSession = Depends(db_session)):
    rows = list((await session.scalars(select(Resume).where(Resume.user_id == user.id).order_by(Resume.created_at.desc()))).all())
    return [
        ResumeResponse(
            id=row.id,
            drive_file_id=row.drive_file_id,
            drive_web_link=row.drive_web_link,
            filename=row.filename,
            mime_type=row.mime_type,
            parsed_text_preview=row.parsed_text[:500],
            is_active=row.is_active,
            created_at=row.created_at,
        )
        for row in rows
    ]
