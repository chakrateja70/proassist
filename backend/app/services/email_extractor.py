import re
from dataclasses import dataclass
import json

from openai import AsyncOpenAI

from app.core.config import get_settings


EMAIL_PATTERN = re.compile(r"\b[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}\b")


@dataclass
class ExtractedEmail:
    email: str
    source_span: str
    confidence: float


def extract_hr_emails(jd_text: str) -> list[ExtractedEmail]:
    matches = EMAIL_PATTERN.findall(jd_text or "")
    unique_emails: list[str] = []
    for email in matches:
        lowered = email.lower()
        if lowered not in unique_emails:
            unique_emails.append(lowered)

    extracted: list[ExtractedEmail] = []
    for email in unique_emails:
        confidence = 0.75
        if any(token in email for token in ["hr", "recruit", "careers", "jobs"]):
            confidence = 0.9
        extracted.append(ExtractedEmail(email=email, source_span=email, confidence=confidence))

    extracted.sort(key=lambda item: item.confidence, reverse=True)
    return extracted


async def rank_contacts_with_llm(jd_text: str, contacts: list[ExtractedEmail]) -> list[ExtractedEmail]:
    settings = get_settings()
    if len(contacts) < 2 or not settings.openai_api_key:
        return contacts

    client = AsyncOpenAI(api_key=settings.openai_api_key)
    options = [item.email for item in contacts]
    prompt = (
        "Given this job description and candidate emails, rank best HR/recruiting contacts first.\n"
        f"Job Description:\n{jd_text[:3000]}\n"
        f"Emails: {options}\n"
        "Return only a JSON array of emails in ranked order."
    )
    try:
        response = await client.responses.create(model=settings.openai_model, input=prompt)
        output = response.output_text.strip()
        parsed = json.loads(output)
        if not isinstance(parsed, list):
            return contacts
        ranked_emails = [str(email).strip().lower() for email in parsed if str(email).strip()]
        if not ranked_emails:
            return contacts
        contact_map = {item.email: item for item in contacts}
        ordered = [contact_map[email] for email in ranked_emails if email in contact_map]
        remaining = [item for item in contacts if item.email not in {entry.email for entry in ordered}]
        return ordered + remaining
    except Exception:
        return contacts
