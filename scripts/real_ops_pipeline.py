from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ops_pipeline import build_ops_pipeline_report, workflow_run_to_event  # noqa: E402
from scripts.runtime_demo import request_json, wait_for_health  # noqa: E402


BASE_URL = "http://127.0.0.1:8010"


def fetch_workflow_runs(owner: str, repo: str, limit: int) -> tuple[str, list[dict[str, Any]]]:
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs?per_page={limit}"
    request = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(request, timeout=20) as response:
        payload = json.loads(response.read().decode("utf-8"))
    runs = payload.get("workflow_runs", [])
    if not isinstance(runs, list) or not runs:
        raise RuntimeError(f"No workflow runs returned from {url}")
    return url, runs[:limit]


def load_workflow_runs(path: str | Path, owner: str, repo: str) -> tuple[str, list[dict[str, Any]]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    runs = payload.get("workflow_runs", payload if isinstance(payload, list) else [])
    if not isinstance(runs, list) or not runs:
        raise ValueError("fixture must be a list or include workflow_runs")
    return f"fixture://{owner}/{repo}", runs


def run_real_ops_pipeline(owner: str, repo: str, limit: int, input_json: str | None = None) -> dict[str, object]:
    project_root = Path(__file__).resolve().parents[1]
    source_url, runs = load_workflow_runs(input_json, owner, repo) if input_json else fetch_workflow_runs(owner, repo, limit)
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

    event_latencies_ms: list[float] = []
    job_latencies_ms: list[float] = []
    fetch_job_latencies_ms: list[float] = []
    processed = 0
    try:
        wait_for_health(server)
        for run in runs:
            event = workflow_run_to_event(run)
            event_start = time.perf_counter()
            accepted_event = request_json(
                "POST",
                "/events",
                {
                    "event_type": event.event_type,
                    "source": event.source,
                    "attributes": event.attributes,
                },
            )
            event_latencies_ms.append((time.perf_counter() - event_start) * 1000)

            job_start = time.perf_counter()
            created_job = request_json(
                "POST",
                "/jobs",
                {
                    "kind": "workflow run ingestion",
                    "source": "github_actions",
                    "payload": accepted_event,
                },
            )
            job_latencies_ms.append((time.perf_counter() - job_start) * 1000)

            fetch_start = time.perf_counter()
            fetched_job = request_json("GET", f"/jobs/{created_job['id']}")
            fetch_job_latencies_ms.append((time.perf_counter() - fetch_start) * 1000)
            if fetched_job["id"] != created_job["id"]:
                raise RuntimeError("Fetched job id did not match created job id")
            processed += 1
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()

    return build_ops_pipeline_report(
        source_url=source_url,
        processed_runs=processed,
        event_latencies_ms=event_latencies_ms,
        job_latencies_ms=job_latencies_ms,
        fetch_job_latencies_ms=fetch_job_latencies_ms,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Process real GitHub Actions data through the local API.")
    parser.add_argument("--owner", default="nguyenthevietquang07")
    parser.add_argument("--repo", default="cloud-infra-lab")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--input-json", help="Optional workflow-run fixture for offline verification.")
    parser.add_argument("--output", default="reports/real_ops_pipeline.json")
    args = parser.parse_args()

    report = run_real_ops_pipeline(args.owner, args.repo, args.limit, input_json=args.input_json)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"report_path": str(output_path), "summary": report}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
