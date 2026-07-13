from __future__ import annotations

import argparse
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


def request_json(
    base_url: str,
    method: str,
    path: str,
    api_key: str,
    payload: dict[str, object] | None = None,
) -> tuple[dict[str, Any], float]:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}{path}",
        data=body,
        method=method,
        headers={"Content-Type": "application/json", "X-API-Key": api_key},
    )
    started = time.perf_counter()
    with urllib.request.urlopen(request, timeout=15) as response:
        elapsed_ms = (time.perf_counter() - started) * 1000
        return json.loads(response.read().decode("utf-8")), elapsed_ms


def run_smoke(base_url: str, api_key: str) -> dict[str, Any]:
    measurements: list[dict[str, object]] = []

    def call(name: str, method: str, path: str, payload: dict[str, object] | None = None) -> dict[str, Any]:
        response, latency_ms = request_json(base_url, method, path, api_key, payload)
        measurements.append({"name": name, "latency_ms": round(latency_ms, 3)})
        return response

    health = call("health", "GET", "/health")
    event = call(
        "event_ingest",
        "POST",
        "/events",
        {
            "event_type": " Render Deploy ",
            "source": " staging_smoke ",
            "attributes": {"environment": "render", "verification": "smoke"},
        },
    )
    created_job = call(
        "job_create",
        "POST",
        "/jobs",
        {"kind": "render staging smoke", "source": "staging_smoke", "payload": event},
    )
    fetched_job = call("job_fetch", "GET", f"/jobs/{created_job['id']}")
    cached_status = call("job_status", "GET", f"/jobs/{created_job['id']}/status")

    checks = {
        "health_ok": health.get("status") == "ok",
        "postgres_configured": health.get("checks", {}).get("database") == "configured",
        "redis_available": health.get("checks", {}).get("cache") == "ok",
        "event_normalized": event.get("event_type") == "render deploy",
        "job_created": bool(created_job.get("id")),
        "job_persisted": fetched_job.get("id") == created_job.get("id"),
        "job_status_cached": cached_status.get("source") == "cache",
        "latency_measurements_recorded": len(measurements) == 5,
    }
    return {
        "project": "cloud-infra-lab",
        "stage": "render_staging_smoke",
        "base_url": base_url.rstrip("/"),
        "measurements": measurements,
        "checks": checks,
        "passed": all(checks.values()),
        "claim_boundary": (
            "This report verifies one deployed Render staging instance and its managed "
            "Postgres/Key Value wiring. It is not uptime, scale, or production-user evidence."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke-test a deployed Cloud Infrastructure Lab staging URL.")
    parser.add_argument("--base-url", default=os.getenv("STAGING_BASE_URL"), help="Render service URL, for example https://cloud-infra-lab-api.onrender.com")
    parser.add_argument("--api-key", default=os.getenv("STAGING_API_KEY"), help="API key configured as API_KEY on the staging service")
    parser.add_argument("--report", default="reports/render_staging_smoke.json")
    args = parser.parse_args()

    if not args.base_url:
        raise SystemExit("--base-url or STAGING_BASE_URL is required")
    if not args.api_key:
        raise SystemExit("--api-key or STAGING_API_KEY is required so protected endpoints are verified")

    report = run_smoke(args.base_url, args.api_key)
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"report_path": str(report_path), "summary": report}, indent=2, sort_keys=True))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
