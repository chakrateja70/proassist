from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import db_session
from app.core.config import get_settings
from app.db.models import QueueStatus, SendRequest, SendStatus
from app.db.schemas import WorkerRunRequest
from app.services.scheduler import claim_due_jobs
from app.services.send_processor import execute_send_request

router = APIRouter(prefix="/internal/worker", tags=["worker"])


@router.post("/run-due-jobs")
async def run_due_jobs(
    payload: WorkerRunRequest,
    session: AsyncSession = Depends(db_session),
    x_worker_secret: str | None = Header(default=None),
):
    if x_worker_secret != get_settings().worker_secret:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid worker secret")

    jobs = await claim_due_jobs(session, payload.limit)
    processed = 0
    failed = 0
    for job in jobs:
        try:
            if job.job_type != "send_email":
                job.status = QueueStatus.failed
                job.last_error = f"Unsupported job type {job.job_type}"
                failed += 1
                continue

            send_req = await session.get(SendRequest, job.payload_json["send_request_id"])
            if not send_req:
                job.status = QueueStatus.failed
                job.last_error = "Send request not found"
                failed += 1
                continue

            await execute_send_request(session, send_req)
            job.status = QueueStatus.done
            processed += 1
        except Exception as exc:
            job.attempts += 1
            send_req = await session.get(SendRequest, job.payload_json["send_request_id"])
            if send_req:
                send_req.failure_reason = str(exc)
            if job.attempts >= job.max_attempts:
                job.status = QueueStatus.failed
                job.last_error = str(exc)
                if send_req:
                    send_req.status = SendStatus.failed
            else:
                job.status = QueueStatus.pending
                job.last_error = str(exc)
                job.run_at = datetime.now(timezone.utc) + timedelta(minutes=2 * job.attempts)
                if send_req:
                    send_req.status = SendStatus.pending
            failed += 1

    await session.commit()
    return {"claimed": len(jobs), "processed": processed, "failed": failed}
