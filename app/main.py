from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi import HTTPException

from .job_store import build_job_store
from .jobs import serialize_job
from .schemas import EventPayload, EventResponse, HealthResponse, JobCreateRequest, JobResponse
from .service import build_health_payload, normalize_event

app = FastAPI(title="Cloud Infrastructure Lab", version="0.1.0")
job_store = build_job_store(os.getenv("DATABASE_URL"))


@app.get("/health", response_model=HealthResponse)
def health() -> dict[str, object]:
    return build_health_payload(service_name="cloud-infra-lab")


@app.post("/events", response_model=EventResponse)
def ingest_event(payload: EventPayload) -> dict[str, object]:
    return normalize_event(payload.model_dump())


@app.post("/jobs", response_model=JobResponse)
def create_job(payload: JobCreateRequest) -> dict[str, object]:
    request_payload = payload.model_dump()
    job = job_store.create(kind=payload.kind, payload=request_payload)
    return serialize_job(job)


@app.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: str) -> dict[str, object]:
    job = job_store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return serialize_job(job)
