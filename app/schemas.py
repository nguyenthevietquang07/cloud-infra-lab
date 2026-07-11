from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class HealthChecks(BaseModel):
    api: str
    database: str
    cache: str


class HealthResponse(BaseModel):
    service: str
    status: str
    timestamp: str
    checks: HealthChecks


class EventPayload(BaseModel):
    event_type: str = Field(default="unknown", min_length=1)
    source: str = Field(default="manual", min_length=1)
    attributes: dict[str, Any] = Field(default_factory=dict)


class EventResponse(BaseModel):
    event_type: str
    source: str
    accepted: bool
    attributes: dict[str, Any]


class JobCreateRequest(BaseModel):
    kind: str = Field(default="event_processing", min_length=1)
    source: str = Field(default="manual", min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)


class JobResponse(BaseModel):
    id: str
    kind: str
    status: str
    payload: dict[str, Any]
    created_at: str
    updated_at: str
    error: str | None = None
