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
You are helping a job seeker write a personalized interest email and LinkedIn message to a recruiter or hiring manager.
The candidate is expressing genuine interest in the role below, referencing specific experience and skills from their resume that match the job description.
Language: {job.language}

Candidate:
- Name: {user.name}
- Email: {user.email}
- Headline: {profile.headline or ""}
- Years of experience: {profile.years_experience or ""}
- Skills: {profile.skills or ""}
- Summary: {profile.summary or ""}
- LinkedIn: {profile.linkedin_url or ""}
- GitHub: {profile.github_url or ""}

Candidate's Resume:
{resume.parsed_text[:5000]}

Job Description:
{job.jd_text[:7000]}

Output JSON with:
1) gmail_subject  — compelling subject line from the candidate, e.g. "Interested in [Role] at [Company] – [Candidate Name]"
2) gmail_body     — email written in first person FROM the candidate TO the hiring team; open with why they are excited about this specific role/company, highlight 2-3 concrete resume achievements that directly map to the JD requirements, and close with a clear call-to-action (e.g. request a call)
3) linkedin_message — short (under 300 chars) first-person note FROM the candidate expressing interest and one key matching qualification
4) personalization_rationale — brief explanation of which resume points were matched to which JD requirements

Requirements:
- Write entirely from the candidate's perspective (first person: I, my, I've)
- Highlight specific overlaps between the resume and the job description
- Do NOT invent achievements not present in the resume
- Professional, enthusiastic, and concise tone
- Clear call-to-action at the end of the email
"""


def _fallback_generation(user: User, profile: Profile, job: JobInput) -> dict:
    role = job.role_title or "this position"
    company = f" at {job.company_name}" if job.company_name else ""
    skills = profile.skills or "relevant technologies"
    years = f"{profile.years_experience} years of" if profile.years_experience else "extensive"

    subject = f"Interest in {role}{company} – {user.name}"
    body = (
        f"Hi,\n\n"
        f"I hope this message finds you well. My name is {user.name}, and I am writing to express my strong interest "
        f"in the {role}{company} role.\n\n"
        f"With {years} experience and hands-on skills in {skills}, I believe my background aligns closely with "
        f"what you are looking for. I am particularly excited about this opportunity because it matches the kind of "
        f"work I have been doing and the direction I want to grow in.\n\n"
        f"I have attached my resume for your review. I would love the chance to speak with you and learn more about "
        f"the role — please let me know if you would be open to a quick call at your convenience.\n\n"
        f"Thank you for your time and consideration.\n\n"
        f"Best regards,\n"
        f"{user.name}\n"
        f"{user.email}"
    )
    linkedin = (
        f"Hi, I came across the {role}{company} and I'm very interested — "
        f"my {years} experience in {skills} seems like a strong match. Would love to connect!"
    )
    return {
        "gmail_subject": subject,
        "gmail_body": body,
        "linkedin_message": linkedin,
        "personalization_rationale": "Fallback template used because OpenAI key is not configured.",
    }
