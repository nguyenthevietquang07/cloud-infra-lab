from __future__ import annotations

from dataclasses import dataclass, field
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


@dataclass
class InMemoryJobStore:
    jobs: dict[str, Job] = field(default_factory=dict)

    def create(self, kind: str, payload: dict[str, object]) -> Job:
        now = _utc_now()
        job = Job(
            id=str(uuid4()),
            kind=_normalize_kind(kind),
            status="queued",
            payload=payload,
            created_at=now,
            updated_at=now,
        )
        self.jobs[job.id] = job
        return job

    def get(self, job_id: str) -> Job | None:
        return self.jobs.get(job_id)

    def transition(self, job_id: str, status: str, error: str | None = None) -> Job:
        if status not in VALID_JOB_STATES:
            raise ValueError(f"Invalid job status: {status}")
        existing = self.jobs.get(job_id)
        if existing is None:
            raise KeyError(f"Unknown job id: {job_id}")
        updated = Job(
            id=existing.id,
            kind=existing.kind,
            status=status,
            payload=existing.payload,
            created_at=existing.created_at,
            updated_at=_utc_now(),
            error=error,
        )
        self.jobs[job_id] = updated
        return updated


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
