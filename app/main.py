from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi import HTTPException

from .job_store import build_job_store
from .jobs import serialize_job
from .schemas import EventPayload, EventResponse, HealthResponse, JobCreateRequest, JobResponse, JobStatusResponse
from .service import build_health_payload, normalize_event
from .status_cache import build_status_cache

app = FastAPI(title="Cloud Infrastructure Lab", version="0.1.0")
job_store = build_job_store(os.getenv("DATABASE_URL"))
status_cache = build_status_cache(os.getenv("REDIS_URL"))


@app.get("/health", response_model=HealthResponse)
def health() -> dict[str, object]:
    cache_status = "ok" if status_cache.ping() else "unavailable"
    return build_health_payload(service_name="cloud-infra-lab", cache_status=cache_status)


@app.post("/events", response_model=EventResponse)
def ingest_event(payload: EventPayload) -> dict[str, object]:
    return normalize_event(payload.model_dump())


@app.post("/jobs", response_model=JobResponse)
def create_job(payload: JobCreateRequest) -> dict[str, object]:
    request_payload = payload.model_dump()
    job = job_store.create(kind=payload.kind, payload=request_payload)
    status_cache.set_job_status(job.id, job.status)
    return serialize_job(job)


@app.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: str) -> dict[str, object]:
    job = job_store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    cached_status = status_cache.get_job_status(job.id)
    if cached_status is None:
        status_cache.set_job_status(job.id, job.status)
    return serialize_job(job)


@app.get("/jobs/{job_id}/status", response_model=JobStatusResponse)
def get_job_status(job_id: str) -> dict[str, object]:
    cached_status = status_cache.get_job_status(job_id)
    if cached_status is not None:
        return {"id": job_id, "status": cached_status, "source": "cache"}
    job = job_store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    status_cache.set_job_status(job.id, job.status)
    return {"id": job.id, "status": job.status, "source": "database"}
