from __future__ import annotations

import statistics
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class WorkflowRunEvent:
    event_type: str
    source: str
    attributes: dict[str, Any]


def workflow_run_to_event(run: dict[str, Any]) -> WorkflowRunEvent:
    repository = str(run.get("repository", {}).get("full_name") or run.get("repo_full_name") or "unknown")
    conclusion = run.get("conclusion") or "in_progress"
    status = run.get("status") or "unknown"
    return WorkflowRunEvent(
        event_type=f"github_actions_{status}",
        source=repository,
        attributes={
            "run_id": run.get("id"),
            "workflow": run.get("name") or run.get("workflow_name") or "unknown",
            "head_branch": run.get("head_branch"),
            "head_sha": run.get("head_sha"),
            "status": status,
            "conclusion": conclusion,
            "html_url": run.get("html_url"),
        },
    )


def summarize_latency_ms(values: list[float]) -> dict[str, float]:
    if not values:
        raise ValueError("values cannot be empty")
    ordered = sorted(values)
    return {
        "count": float(len(values)),
        "mean_ms": round(statistics.mean(values), 4),
        "p50_ms": round(_percentile(ordered, 0.50), 4),
        "p95_ms": round(_percentile(ordered, 0.95), 4),
        "max_ms": round(max(values), 4),
    }


def build_ops_pipeline_report(
    source_url: str,
    processed_runs: int,
    event_latencies_ms: list[float],
    job_latencies_ms: list[float],
    fetch_job_latencies_ms: list[float],
) -> dict[str, object]:
    total_operations = len(event_latencies_ms) + len(job_latencies_ms) + len(fetch_job_latencies_ms)
    return {
        "project": "cloud-infra-lab",
        "pipeline": "real_ops_event_pipeline",
        "data_source": {
            "provider": "GitHub REST API",
            "url": source_url,
            "source_note": "Public workflow-run records processed as operational events.",
        },
        "processed_runs": processed_runs,
        "operation_count": total_operations,
        "measurements": {
            "event_ingest_latency": summarize_latency_ms(event_latencies_ms),
            "job_create_latency": summarize_latency_ms(job_latencies_ms),
            "job_fetch_latency": summarize_latency_ms(fetch_job_latencies_ms),
        },
        "passion_project_note": (
            "Built to practice production-style observability and job-processing "
            "flows with real CI/CD operations data before deploying paid infrastructure."
        ),
        "claim_boundary": (
            "This report measures local API processing of public GitHub workflow metadata; "
            "it is not evidence of production traffic or hosted reliability."
        ),
    }


def _percentile(ordered_values: list[float], probability: float) -> float:
    index = max(0, min(len(ordered_values) - 1, round((len(ordered_values) - 1) * probability)))
    return ordered_values[index]
