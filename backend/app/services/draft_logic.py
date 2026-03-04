from datetime import datetime

from app.db.models import DraftStatus


def compute_draft_state(
    current_status: DraftStatus,
    content_changed: bool,
    approve: bool,
    current_approved_at: datetime | None,
    now: datetime,
) -> tuple[DraftStatus, datetime | None]:
    if approve:
        return DraftStatus.approved, now
    if content_changed:
        return DraftStatus.edited, None
    if current_status == DraftStatus.approved:
        return DraftStatus.approved, current_approved_at
    return current_status, current_approved_at
