from __future__ import annotations

import io

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload

from app.db.models import OAuthToken
from app.services.google_auth import build_google_credentials


async def upload_resume_to_drive(
    token_row: OAuthToken, access_token: str, filename: str, mime_type: str, content: bytes
) -> dict:
    credentials = build_google_credentials(token_row=token_row, access_token=access_token)
    drive = build("drive", "v3", credentials=credentials, cache_discovery=False)
    media = MediaIoBaseUpload(io.BytesIO(content), mimetype=mime_type, resumable=False)
    metadata = {"name": filename, "parents": []}
    result = (
        drive.files()
        .create(body=metadata, media_body=media, fields="id, webViewLink, name, mimeType")
        .execute()
    )
    return result


async def download_drive_file(token_row: OAuthToken, access_token: str, file_id: str) -> bytes:
    credentials = build_google_credentials(token_row=token_row, access_token=access_token)
    drive = build("drive", "v3", credentials=credentials, cache_discovery=False)
    request = drive.files().get_media(fileId=file_id)
    stream = io.BytesIO()
    downloader = MediaIoBaseDownload(stream, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    return stream.getvalue()
