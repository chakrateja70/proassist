from app.services.email_extractor import extract_hr_emails


def test_extract_hr_emails_multiple_and_unique() -> None:
    text = """
    Please send your profile to HR@Example.com and careers@example.com.
    For queries, contact careers@example.com.
    """
    result = extract_hr_emails(text)
    emails = [entry.email for entry in result]
    assert emails == ["hr@example.com", "careers@example.com"]
    assert result[0].confidence >= result[1].confidence


def test_extract_hr_emails_none() -> None:
    text = "Apply via portal only. No direct contact listed."
    result = extract_hr_emails(text)
    assert result == []
