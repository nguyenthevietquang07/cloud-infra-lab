from __future__ import annotations

from datetime import datetime, timezone


def build_health_payload(service_name: str) -> dict[str, object]:
    return {
        "service": service_name,
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": {
            "api": "ok",
            "database": "configured",
            "cache": "configured",
        },
    }


def normalize_event(payload: dict[str, object]) -> dict[str, object]:
    event_type = str(payload.get("event_type", "unknown")).strip().lower()
    source = str(payload.get("source", "manual")).strip().lower()
    if not event_type:
        event_type = "unknown"
    if not source:
        source = "manual"

    return {
        "event_type": event_type,
        "source": source,
        "accepted": True,
        "attributes": payload.get("attributes", {}),
    }
