from __future__ import annotations

import argparse
import json
import os
import statistics
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any


def percentile(values: list[float], percentile_rank: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = (len(ordered) - 1) * percentile_rank
    lower = int(index)
    upper = min(lower + 1, len(ordered) - 1)
    if lower == upper:
        return ordered[lower]
    weight = index - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def post_event(base_url: str, api_key: str, index: int) -> dict[str, Any]:
    payload = {
        "event_type": "load test event",
        "source": "staging_load_test",
        "attributes": {"sequence": index, "environment": "render"},
    }
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/events",
        data=body,
        method="POST",
        headers={"Content-Type": "application/json", "X-API-Key": api_key},
    )
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            elapsed_ms = (time.perf_counter() - started) * 1000
            parsed = json.loads(response.read().decode("utf-8"))
            return {
                "ok": response.status == 200 and parsed.get("accepted") is True,
                "status": response.status,
                "latency_ms": elapsed_ms,
            }
    except (urllib.error.URLError, TimeoutError, ConnectionError) as error:
        elapsed_ms = (time.perf_counter() - started) * 1000
        return {"ok": False, "status": "error", "latency_ms": elapsed_ms, "error": str(error)}


def run_load_test(
    base_url: str,
    api_key: str,
    requests: int,
    concurrency: int,
    max_p95_ms: float,
    max_error_rate: float,
    min_requests: int,
) -> dict[str, Any]:
    started = time.perf_counter()
    results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = [pool.submit(post_event, base_url, api_key, index) for index in range(requests)]
        for future in as_completed(futures):
            results.append(future.result())

    latencies = [float(result["latency_ms"]) for result in results]
    success_count = sum(1 for result in results if result["ok"])
    error_count = len(results) - success_count
    error_rate = error_count / len(results) if results else 1.0
    p50_ms = percentile(latencies, 0.50)
    p95_ms = percentile(latencies, 0.95)
    checks = {
        "minimum_sample_size": len(results) >= min_requests,
        "error_rate_within_threshold": error_rate <= max_error_rate,
        "p95_latency_within_threshold": p95_ms <= max_p95_ms,
        "all_responses_accepted": success_count == len(results),
    }
    return {
        "project": "cloud-infra-lab",
        "stage": "render_staging_load_test",
        "base_url": base_url.rstrip("/"),
        "requests": requests,
        "concurrency": concurrency,
        "duration_seconds": round(time.perf_counter() - started, 3),
        "success_count": success_count,
        "error_count": error_count,
        "error_rate": round(error_rate, 4),
        "latency_ms": {
            "min": round(min(latencies), 3) if latencies else 0.0,
            "mean": round(statistics.fmean(latencies), 3) if latencies else 0.0,
            "p50": round(p50_ms, 3),
            "p95": round(p95_ms, 3),
            "max": round(max(latencies), 3) if latencies else 0.0,
        },
        "thresholds": {
            "min_requests": min_requests,
            "max_error_rate": max_error_rate,
            "max_p95_ms": max_p95_ms,
        },
        "checks": checks,
        "passed": all(checks.values()),
        "claim_boundary": (
            "This bounded test validates staging responsiveness for a small client-style "
            "burst. It is not a substitute for sustained production monitoring."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a bounded load test against a deployed staging URL.")
    parser.add_argument("--base-url", default=os.getenv("STAGING_BASE_URL"))
    parser.add_argument("--api-key", default=os.getenv("STAGING_API_KEY"))
    parser.add_argument("--requests", type=int, default=50)
    parser.add_argument("--concurrency", type=int, default=5)
    parser.add_argument("--min-requests", type=int, default=30)
    parser.add_argument("--max-error-rate", type=float, default=0.0)
    parser.add_argument("--max-p95-ms", type=float, default=2000.0)
    parser.add_argument("--report", default="reports/render_load_test.json")
    args = parser.parse_args()

    if not args.base_url:
        raise SystemExit("--base-url or STAGING_BASE_URL is required")
    if not args.api_key:
        raise SystemExit("--api-key or STAGING_API_KEY is required")
    if args.requests < 1 or args.concurrency < 1:
        raise SystemExit("--requests and --concurrency must be positive")

    report = run_load_test(
        base_url=args.base_url,
        api_key=args.api_key,
        requests=args.requests,
        concurrency=args.concurrency,
        max_p95_ms=args.max_p95_ms,
        max_error_rate=args.max_error_rate,
        min_requests=args.min_requests,
    )
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"report_path": str(report_path), "summary": report}, indent=2, sort_keys=True))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
