from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.jobs import InMemoryJobStore, serialize_job
from app.service import build_health_payload, normalize_event


def run_demo() -> dict[str, object]:
    store = InMemoryJobStore()
    health = build_health_payload("cloud-infra-lab")
    event = normalize_event(
        {
            "event_type": " Deployment ",
            "source": " CI ",
            "attributes": {"commit": "local-demo", "environment": "dev"},
        }
    )
    queued = store.create("event processing", event)
    finished = store.transition(queued.id, "succeeded")

    report = {
        "project": "cloud-infra-lab",
        "stage": "local_service_demo",
        "health": health,
        "normalized_event": event,
        "job": serialize_job(finished),
        "claim_boundary": "Local demo validates service logic and job flow; it is not production traffic evidence.",
    }
    report_path = Path("reports/demo_run.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return {"report_path": str(report_path), "summary": report}


if __name__ == "__main__":
    print(json.dumps(run_demo(), indent=2, sort_keys=True))
