from __future__ import annotations

import base64
from email.message import EmailMessage

from googleapiclient.discovery import build

from app.db.models import OAuthToken
from app.services.google_auth import build_google_credentials


async def send_gmail_message(
    token_row: OAuthToken,
    access_token: str,
    to_email: str,
    subject: str,
    body: str,
    attachment_filename: str,
    attachment_content: bytes,
    attachment_mime_type: str,
) -> str:
    credentials = build_google_credentials(token_row=token_row, access_token=access_token)
    gmail = build("gmail", "v1", credentials=credentials, cache_discovery=False)

    message = EmailMessage()
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)
    message.add_attachment(
        attachment_content,
        maintype=attachment_mime_type.split("/")[0],
        subtype=attachment_mime_type.split("/")[1],
        filename=attachment_filename,
    )

    encoded = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    payload = {"raw": encoded}
    result = gmail.users().messages().send(userId="me", body=payload).execute()
    return result["id"]
