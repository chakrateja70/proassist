from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AuditLog


async def write_audit_log(
    session: AsyncSession,
    user_id: str,
    entity: str,
    entity_id: str,
    action: str,
    before_json: dict | None,
    after_json: dict | None,
) -> None:
    log = AuditLog(
        user_id=user_id,
        entity=entity,
        entity_id=entity_id,
        action=action,
        before_json=before_json,
        after_json=after_json,
    )
    session.add(log)
