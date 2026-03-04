import re


ROLE_PATTERNS = [
    re.compile(r"\b(role|position|title)\s*[:\-]\s*([^\n\r]+)", re.IGNORECASE),
]
COMPANY_PATTERNS = [
    re.compile(r"\b(company|organization)\s*[:\-]\s*([^\n\r]+)", re.IGNORECASE),
]


def extract_role_company(jd_text: str) -> tuple[str | None, str | None]:
    role = _extract_from_patterns(jd_text, ROLE_PATTERNS)
    company = _extract_from_patterns(jd_text, COMPANY_PATTERNS)
    return role, company


def _extract_from_patterns(text: str, patterns: list[re.Pattern[str]]) -> str | None:
    for pattern in patterns:
        match = pattern.search(text or "")
        if match:
            candidate = match.group(2).strip()
            if candidate:
                return candidate[:255]
    return None
