from __future__ import annotations

import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


BASE_URL = "http://127.0.0.1:8010"


def request_json(method: str, path: str, payload: dict[str, object] | None = None) -> dict[str, object]:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=body,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def wait_for_health(timeout_seconds: float = 10.0) -> dict[str, object]:
    deadline = time.monotonic() + timeout_seconds
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            return request_json("GET", "/health")
        except (urllib.error.URLError, TimeoutError, ConnectionError) as error:
            last_error = error
            time.sleep(0.25)
    raise RuntimeError(f"API did not become healthy: {last_error}")


def run_runtime_demo() -> dict[str, object]:
    project_root = Path(__file__).resolve().parents[1]
    server = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8010",
        ],
        cwd=project_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        health = wait_for_health()
        event = request_json(
            "POST",
            "/events",
            {
                "event_type": " Deployment ",
                "source": " Runtime Demo ",
                "attributes": {"environment": "local", "stage": "stage_2"},
            },
        )
        created_job = request_json(
            "POST",
            "/jobs",
            {"kind": "arrangement export", "source": "runtime_demo", "payload": event},
        )
        fetched_job = request_json("GET", f"/jobs/{created_job['id']}")

        report = {
            "project": "cloud-infra-lab",
            "stage": "stage_2_runtime_api_demo",
            "base_url": BASE_URL,
            "checks": {
                "health_endpoint": health["status"] == "ok",
                "event_normalization": event["event_type"] == "deployment",
                "job_creation": bool(created_job.get("id")),
                "job_fetch": fetched_job["id"] == created_job["id"],
            },
            "responses": {
                "health": health,
                "event": event,
                "created_job": created_job,
                "fetched_job": fetched_job,
            },
            "claim_boundary": (
                "Runtime demo validates local API behavior only; it is not "
                "production deployment or real traffic evidence."
            ),
        }
        report_path = project_root / "reports" / "runtime_api_demo.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
        return {"report_path": str(report_path.relative_to(project_root)), "summary": report}
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == "__main__":
    print(json.dumps(run_runtime_demo(), indent=2, sort_keys=True))
