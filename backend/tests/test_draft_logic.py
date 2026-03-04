from datetime import datetime, timezone

from app.db.models import DraftStatus
from app.services.draft_logic import compute_draft_state


def test_approve_sets_approved_and_timestamp() -> None:
    now = datetime.now(timezone.utc)
    status, approved_at = compute_draft_state(
        current_status=DraftStatus.generated,
        content_changed=False,
        approve=True,
        current_approved_at=None,
        now=now,
    )
    assert status == DraftStatus.approved
    assert approved_at == now


def test_content_change_resets_approval() -> None:
    now = datetime.now(timezone.utc)
    status, approved_at = compute_draft_state(
        current_status=DraftStatus.approved,
        content_changed=True,
        approve=False,
        current_approved_at=now,
        now=now,
    )
    assert status == DraftStatus.edited
    assert approved_at is None
