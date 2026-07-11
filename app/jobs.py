from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4


VALID_JOB_STATES = {"queued", "running", "succeeded", "failed"}


@dataclass(frozen=True)
class Job:
    id: str
    kind: str
    status: str
    payload: dict[str, object]
    created_at: str
    updated_at: str
    error: str | None = None


def create_job_record(kind: str, payload: dict[str, object]) -> Job:
    now = _utc_now()
    return Job(
        id=str(uuid4()),
        kind=_normalize_kind(kind),
        status="queued",
        payload=payload,
        created_at=now,
        updated_at=now,
    )


def transition_job_record(job: Job, status: str, error: str | None = None) -> Job:
    if status not in VALID_JOB_STATES:
        raise ValueError(f"Invalid job status: {status}")
    return Job(
        id=job.id,
        kind=job.kind,
        status=status,
        payload=job.payload,
        created_at=job.created_at,
        updated_at=_utc_now(),
        error=error,
    )


def serialize_job(job: Job) -> dict[str, object]:
    return {
        "id": job.id,
        "kind": job.kind,
        "status": job.status,
        "payload": job.payload,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
        "error": job.error,
    }


def _normalize_kind(kind: str) -> str:
    normalized = kind.strip().lower().replace(" ", "_")
    if not normalized:
        raise ValueError("job kind cannot be empty")
    return normalized


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
