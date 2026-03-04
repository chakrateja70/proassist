from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class DraftStatusEnum(str, Enum):
    generated = "generated"
    edited = "edited"
    approved = "approved"
    scheduled = "scheduled"
    sent = "sent"
    failed = "failed"


class SendModeEnum(str, Enum):
    immediate = "immediate"
    scheduled = "scheduled"


class ExtractedContact(BaseModel):
    email: EmailStr
    source_span: str = Field(default="")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class MeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: EmailStr
    name: str
    preferred_language: str
    has_profile: bool
    has_active_resume: bool
    google_scopes: list[str]
    integrations_ready: bool


class ProfileUpdate(BaseModel):
    headline: str | None = None
    years_experience: int | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    portfolio_url: str | None = None
    summary: str | None = None
    skills: str | None = None
    location: str | None = None
    phone: str | None = None


class ProfileResponse(ProfileUpdate):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str


class ResumeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    drive_file_id: str
    drive_web_link: str
    filename: str
    mime_type: str
    parsed_text_preview: str
    is_active: bool
    created_at: datetime


class JobCreate(BaseModel):
    jd_text: str = Field(min_length=30)
    jd_url: str | None = None
    language: str = "en"


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    company_name: str | None
    role_title: str | None
    selected_hr_email: str | None
    language: str
    extracted_contacts: list[ExtractedContact]


class GenerateDraftRequest(BaseModel):
    job_id: str


class GenerateDraftResponse(BaseModel):
    draft_id: str
    gmail_subject: str
    gmail_body: str
    linkedin_message: str
    personalization_rationale: str


class DraftPatch(BaseModel):
    gmail_subject: str | None = None
    gmail_body: str | None = None
    linkedin_message: str | None = None
    selected_hr_email: EmailStr | None = None
    approve: bool = False


class DraftResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    job_input_id: str
    gmail_subject: str
    gmail_body: str
    linkedin_message: str
    status: DraftStatusEnum
    approved_at: datetime | None
    created_at: datetime
    updated_at: datetime


class SendRequestPayload(BaseModel):
    draft_id: str
    to_email: EmailStr
    mode: SendModeEnum = SendModeEnum.immediate
    scheduled_at: datetime | None = None


class SendResponse(BaseModel):
    id: str
    status: str
    mode: SendModeEnum
    scheduled_at: datetime | None
    sent_at: datetime | None
    gmail_message_id: str | None
    failure_reason: str | None


class HistoryItem(BaseModel):
    draft_id: str
    send_id: str | None
    company_name: str | None
    role_title: str | None
    to_email: str | None
    draft_status: DraftStatusEnum
    send_status: str | None
    created_at: datetime
    sent_at: datetime | None
    scheduled_at: datetime | None


class WorkerRunRequest(BaseModel):
    limit: int = Field(default=20, ge=1, le=100)
