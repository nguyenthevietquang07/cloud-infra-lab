# Cloud Infrastructure Lab

[![CI](https://github.com/nguyenthevietquang07/cloud-infra-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/nguyenthevietquang07/cloud-infra-lab/actions/workflows/ci.yml)

Backend/platform engineering lab for a small operations API with health checks,
job workflows, local persistence boundaries, real CI/CD metadata ingestion,
latency measurement, Docker Compose, Terraform planning, runbooks, and CI.

## Why This Project Exists

This project demonstrates the operational side of backend engineering: the
parts that make a service understandable, testable, and maintainable after the
happy path works. It is built around reproducible setup, clear API boundaries,
measured behavior, and documentation that another engineer could use.

## What It Demonstrates

- Python API service with FastAPI-compatible entrypoint
- Typed request and response schemas with Pydantic
- Job storage boundary with in-memory and SQLite implementations
- Event normalization for public GitHub Actions workflow metadata
- Postgres schema for request and audit records
- Redis-style cache boundary
- Docker Compose for local service, database, and cache
- Terraform skeleton for future cloud deployment planning
- Runtime demo, load-test script, runbook, and GitHub Actions CI

## Tech Stack

| Layer | Tools |
|---|---|
| API | Python, FastAPI, Uvicorn, Pydantic |
| Data | SQLite boundary, Postgres schema, Redis-style cache boundary |
| Infrastructure | Docker, Docker Compose, Terraform skeleton |
| Quality | unittest, runtime API demo, load-test script, GitHub Actions |
| Operations | health checks, runbook, structured JSON report artifacts |

## Demo Flow

```mermaid
flowchart LR
    A["Fetch GitHub Actions runs"] --> B["Start FastAPI on 127.0.0.1:8010"]
    B --> C["POST /events"]
    C --> D["POST /jobs"]
    D --> E["GET /jobs/{job_id}"]
    E --> F["Measure endpoint latency"]
    F --> G["Write reports/real_ops_pipeline.json"]
    G --> H["CI reruns core tests and runtime demo"]
```

## Architecture

```mermaid
flowchart TB
    Client["Client or demo script"] --> API["FastAPI service"]
    API --> Schemas["Pydantic schemas"]
    API --> Jobs["Job store boundary"]
    Jobs --> Memory["In-memory store"]
    Jobs --> SQLite["SQLite store"]
    API --> Events["Event normalization"]
    API --> Health["Health checks"]
    Compose["Docker Compose"] --> Postgres["Postgres schema"]
    Compose --> Redis["Redis cache boundary"]
    Terraform["Terraform skeleton"] --> Cloud["Future cloud deployment"]
```

## Measured Evidence

Run the real-data operations pipeline:

```bash
python scripts/real_ops_pipeline.py --owner nguyenthevietquang07 --repo cloud-infra-lab --limit 5
```

Latest measured report: `reports/real_ops_pipeline.json`.

| Measurement | Value |
|---|---:|
| Source | GitHub Actions workflow runs |
| Workflow runs processed | 2 |
| API operations measured | 6 |
| Event ingest mean latency | 14.6652 ms |
| Job create mean latency | 9.8130 ms |
| Job fetch mean latency | 8.4729 ms |
| Event ingest p95 latency | 16.6326 ms |

These measurements validate local API processing of public CI/CD metadata. The
next evidence step is a deployed environment with saved monitoring data for
uptime, production traffic, and client-load measurements.

## Quickstart

Run the test suite:

```bash
python -m unittest discover -s tests
```

Run the local API demo and data pipeline:

```bash
python scripts/runtime_demo.py
python scripts/real_ops_pipeline.py --owner nguyenthevietquang07 --repo cloud-infra-lab --limit 5
```

Run with local infrastructure:

```bash
docker compose up --build
python scripts/load_test.py --url http://localhost:8000/health --requests 25
```

`scripts/runtime_demo.py` starts the service on `127.0.0.1:8010`, calls
`/health`, `/events`, and `/jobs`, fetches the created job, and writes
`reports/runtime_api_demo.json`.

## Documentation

- `docs/runbook.md`: operational runbook and troubleshooting notes
- `docs/real_data_pipeline.md`: source, measurement method, and claim boundary
- `docs/agile_backlog.md`: prioritized backlog and delivery plan

## Portfolio Positioning

Built a cloud infrastructure lab with a containerized API, Postgres/Redis local
stack, health-check endpoints, job/status workflow, real GitHub Actions
operations-data ingestion, latency measurement reports, CI tests, Terraform
planning, and runbook documentation.

Current scope: local, reproducible platform lab. Production-user, uptime, and
hosted-traffic claims require a deployed environment and saved monitoring
evidence.
