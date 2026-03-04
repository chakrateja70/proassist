from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import JobQueue, QueueStatus


async def enqueue_send_job(
    session: AsyncSession,
    send_request_id: str,
    run_at: datetime,
    idempotency_key: str,
) -> JobQueue:
    job = JobQueue(
        job_type="send_email",
        payload_json={"send_request_id": send_request_id},
        run_at=run_at,
        idempotency_key=idempotency_key,
        status=QueueStatus.pending,
    )
    session.add(job)
    return job


async def claim_due_jobs(session: AsyncSession, limit: int) -> list[JobQueue]:
    now = datetime.now(timezone.utc)
    stmt = (
        select(JobQueue)
        .where(JobQueue.status == QueueStatus.pending, JobQueue.run_at <= now)
        .order_by(JobQueue.run_at.asc())
        .limit(limit)
        .with_for_update(skip_locked=True)
    )
    jobs = list((await session.scalars(stmt)).all())
    for job in jobs:
        job.status = QueueStatus.processing
        job.locked_at = now
    return jobs
