# Real Ops Pipeline

## Purpose

This pipeline exercises the API with real operational data instead of synthetic
payloads. It uses public GitHub Actions workflow-run records as CI/CD events,
then measures local API ingest, job creation, and job lookup latency.

## Source

- Provider: GitHub REST API
- Endpoint pattern: `/repos/{owner}/{repo}/actions/runs`
- Latest measured repository: `nguyenthevietquang07/cloud-infra-lab`

## Command

```bash
python scripts/real_ops_pipeline.py --owner nguyenthevietquang07 --repo cloud-infra-lab --limit 5
```

## Processing Steps

1. Fetch public workflow-run metadata from GitHub.
2. Start the FastAPI service locally.
3. Normalize each workflow run into an operational event.
4. POST each event to `/events`.
5. POST a matching job to `/jobs`.
6. Fetch the job back from `/jobs/{job_id}`.
7. Save latency measurements to `reports/real_ops_pipeline.json`.

## Latest Measurements

| Metric | Value |
|---|---:|
| Workflow runs processed | 2 |
| API operations measured | 6 |
| Event ingest mean latency | 14.6652 ms |
| Job create mean latency | 9.8130 ms |
| Job fetch mean latency | 8.4729 ms |
| Event ingest p95 latency | 16.6326 ms |

## Claim Boundary

This proves local service behavior against real public CI/CD metadata. It does
not prove hosted uptime, production reliability, security hardening, or client
traffic handling.
