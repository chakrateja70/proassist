from __future__ import annotations

import json

from openai import AsyncOpenAI

from app.core.config import get_settings
from app.db.models import JobInput, Profile, Resume, User


async def generate_outreach(
    user: User,
    profile: Profile,
    resume: Resume,
    job: JobInput,
) -> dict:
    settings = get_settings()
    if not settings.openai_api_key:
        return _fallback_generation(user=user, profile=profile, job=job)

    client = AsyncOpenAI(api_key=settings.openai_api_key)
    schema = {
        "type": "object",
        "properties": {
            "gmail_subject": {"type": "string"},
            "gmail_body": {"type": "string"},
            "linkedin_message": {"type": "string"},
            "personalization_rationale": {"type": "string"},
        },
        "required": ["gmail_subject", "gmail_body", "linkedin_message", "personalization_rationale"],
        "additionalProperties": False,
    }
    prompt = _build_prompt(user=user, profile=profile, resume=resume, job=job)
    response = await client.responses.create(
        model=settings.openai_model,
        input=prompt,
        text={
            "format": {
                "type": "json_schema",
                "name": "proassist_draft",
                "schema": schema,
                "strict": True,
            }
        },
    )
    text = response.output_text
    return json.loads(text)


def _build_prompt(user: User, profile: Profile, resume: Resume, job: JobInput) -> str:
    return f"""
You are writing highly personalized outreach for a job opportunity.
Language: {job.language}

Candidate:
- Name: {user.name}
- Email: {user.email}
- Headline: {profile.headline or ""}
- Experience years: {profile.years_experience or ""}
- Skills: {profile.skills or ""}
- Summary: {profile.summary or ""}
- LinkedIn: {profile.linkedin_url or ""}
- GitHub: {profile.github_url or ""}

Resume Text:
{resume.parsed_text[:5000]}

Job Description:
{job.jd_text[:7000]}

Output JSON with:
1) gmail_subject
2) gmail_body
3) linkedin_message
4) personalization_rationale

Requirements:
- Tailor to role/company requirements
- No fabricated claims
- Clear CTA
- Professional concise tone
"""


def _fallback_generation(user: User, profile: Profile, job: JobInput) -> dict:
    subject = f"Application Interest: {job.role_title or 'Open Role'}"
    body = (
        f"Hi Hiring Team,\n\n"
        f"My name is {user.name}, and I am interested in the {job.role_title or 'position'}"
        f"{f' at {job.company_name}' if job.company_name else ''}. "
        f"I bring {profile.years_experience or 'relevant'} years of experience and skills in "
        f"{profile.skills or 'software development'}.\n\n"
        "I have attached my resume for your review and would welcome a chance to discuss fit.\n\n"
        "Best regards,\n"
        f"{user.name}"
    )
    linkedin = (
        f"Hi, I came across the {job.role_title or 'role'}"
        f"{f' at {job.company_name}' if job.company_name else ''} and wanted to connect. "
        "I believe my profile aligns well and would appreciate the opportunity to discuss further."
    )
    return {
        "gmail_subject": subject,
        "gmail_body": body,
        "linkedin_message": linkedin,
        "personalization_rationale": "Fallback template used because OpenAI key is not configured.",
    }
