from __future__ import annotations

import argparse
import json
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path


BASE_URL = "http://127.0.0.1:8000"


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


def run_compose(args: list[str], project_root: Path, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["docker", "compose", *args],
        cwd=project_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )


def wait_for_health(timeout_seconds: float = 45.0) -> dict[str, object]:
    deadline = time.monotonic() + timeout_seconds
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            return request_json("GET", "/health")
        except (urllib.error.URLError, TimeoutError, ConnectionError) as error:
            last_error = error
            time.sleep(1.0)
    raise RuntimeError(f"API did not become healthy: {last_error}")


def run_docker_smoke(keep_running: bool = False) -> dict[str, object]:
    project_root = Path(__file__).resolve().parents[1]
    started = False
    report: dict[str, object] = {
        "project": "cloud-infra-lab",
        "stage": "docker_compose_postgres_smoke",
        "base_url": BASE_URL,
        "claim_boundary": (
            "Docker smoke verifies local Compose wiring and Postgres-backed job "
            "persistence only; it is not hosted uptime or production load evidence."
        ),
    }
    try:
        up = run_compose(["up", "--build", "-d"], project_root, timeout=180)
        if up.returncode != 0:
            raise RuntimeError(f"docker compose up failed: {up.stderr.strip()}")
        started = True
        first_health = wait_for_health()
        created_job = request_json(
            "POST",
            "/jobs",
            {"kind": "docker smoke", "source": "docker_smoke", "payload": {"persistent": True}},
        )
        restart = run_compose(["restart", "api"], project_root, timeout=90)
        if restart.returncode != 0:
            raise RuntimeError(f"docker compose restart api failed: {restart.stderr.strip()}")
        second_health = wait_for_health()
        fetched_job = request_json("GET", f"/jobs/{created_job['id']}")
        checks = {
            "compose_started": True,
            "health_before_restart": first_health["status"] == "ok",
            "health_after_restart": second_health["status"] == "ok",
            "job_created": bool(created_job.get("id")),
            "job_persisted_after_api_restart": fetched_job["id"] == created_job["id"],
            "postgres_configured": first_health.get("checks", {}).get("database") == "configured",
        }
        report.update(
            {
                "checks": checks,
                "created_job_id": "<created_job_id>",
                "persisted_status": fetched_job["status"],
                "passed": all(checks.values()),
            }
        )
        return report
    finally:
        if started and not keep_running:
            down = run_compose(["down", "-v"], project_root, timeout=120)
            report["cleanup"] = {
                "command": "docker compose down -v",
                "returncode": down.returncode,
            }


def main() -> None:
    parser = argparse.ArgumentParser(description="Bounded Docker Compose smoke test.")
    parser.add_argument("--keep-running", action="store_true", help="Leave Compose services running for debugging.")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[1]
    report = run_docker_smoke(keep_running=args.keep_running)
    report_path = project_root / "reports" / "docker_smoke.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"report_path": str(report_path.relative_to(project_root)), "summary": report}, indent=2, sort_keys=True))
    if not report.get("passed"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
