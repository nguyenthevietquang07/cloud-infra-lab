from __future__ import annotations

import io
import json
import logging
import sys
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.main import app
from app.observability import ACCESS_LOGGER_NAME, REQUEST_ID_HEADER


def run_observability_demo() -> dict[str, object]:
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    logger = logging.getLogger(ACCESS_LOGGER_NAME)
    previous_level = logger.level
    previous_propagate = logger.propagate
    logger.setLevel(logging.INFO)
    logger.propagate = False
    logger.addHandler(handler)
    try:
        client = TestClient(app)
        health = client.get("/health", headers={REQUEST_ID_HEADER: "demo-request-1"})
        job = client.post(
            "/jobs",
            headers={REQUEST_ID_HEADER: "demo-request-2"},
            json={"kind": "observability demo", "source": "observability_demo", "payload": {"safe": True}},
        )
    finally:
        logger.removeHandler(handler)
        logger.setLevel(previous_level)
        logger.propagate = previous_propagate

    logs = [json.loads(line) for line in stream.getvalue().splitlines() if line.strip()]
    required_fields = {"event", "request_id", "method", "path", "status_code", "duration_ms"}
    checks = {
        "health_request_id_echoed": health.headers.get(REQUEST_ID_HEADER) == "demo-request-1",
        "job_request_id_echoed": job.headers.get(REQUEST_ID_HEADER) == "demo-request-2",
        "structured_json_logs": all(required_fields.issubset(log.keys()) for log in logs),
        "no_sensitive_payload_logged": all("headers" not in log and "body" not in log for log in logs),
        "http_status_logged": {log["status_code"] for log in logs} == {200},
    }
    return {
        "project": "cloud-infra-lab",
        "stage": "observability_demo",
        "claim_boundary": (
            "Observability demo verifies local request IDs and structured access logs. "
            "It is not evidence of hosted log retention, alerting, or production tracing."
        ),
        "checks": checks,
        "log_count": len(logs),
        "sample_logs": logs,
        "passed": all(checks.values()) and len(logs) >= 2,
    }


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    report = run_observability_demo()
    report_path = project_root / "reports" / "observability_demo.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"report_path": str(report_path.relative_to(project_root)), "summary": report}, indent=2, sort_keys=True))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
