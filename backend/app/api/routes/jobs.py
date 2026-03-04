from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_user, db_session
from app.db.models import JobInput, User
from app.db.schemas import ExtractedContact, JobCreate, JobResponse
from app.services.audit import write_audit_log
from app.services.email_extractor import extract_hr_emails, rank_contacts_with_llm
from app.services.jd_parser import extract_role_company

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", response_model=JobResponse)
async def create_job(
    payload: JobCreate,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(db_session),
):
    role_title, company_name = extract_role_company(payload.jd_text)
    contacts = extract_hr_emails(payload.jd_text)
    contacts = await rank_contacts_with_llm(payload.jd_text, contacts)
    job = JobInput(
        user_id=user.id,
        jd_text=payload.jd_text,
        jd_url=payload.jd_url,
        language=payload.language,
        role_title=role_title,
        company_name=company_name,
        extracted_emails_json=[
            {"email": contact.email, "source_span": contact.source_span, "confidence": contact.confidence}
            for contact in contacts
        ],
    )
    session.add(job)
    await session.flush()
    await write_audit_log(
        session=session,
        user_id=user.id,
        entity="job_inputs",
        entity_id=job.id,
        action="create",
        before_json=None,
        after_json={"role_title": role_title, "company_name": company_name, "email_count": len(contacts)},
    )
    await session.commit()
    await session.refresh(job)
    return JobResponse(
        id=job.id,
        company_name=job.company_name,
        role_title=job.role_title,
        selected_hr_email=job.selected_hr_email,
        language=job.language,
        extracted_contacts=[ExtractedContact(**item) for item in job.extracted_emails_json],
    )
