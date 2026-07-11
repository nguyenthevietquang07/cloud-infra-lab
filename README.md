# Cloud Infrastructure Lab

Hands-on backend/platform lab for a small API service with local infrastructure,
health checks, caching, operations notes, CI, and runbook-style QA.

## Why this exists

This project is a resume-safe way to demonstrate infrastructure and operations
skills without claiming production ownership. It focuses on reproducible setup,
testing, observability habits, and deployment thinking.

## Architecture

- Python API service with FastAPI-compatible entrypoint
- Typed request/response schemas with Pydantic
- Job storage boundary with in-memory and SQLite implementations
- Postgres schema for request/audit records
- Redis-style cache boundary
- Docker Compose for local service, database, and cache
- In-memory job/status workflow for async processing patterns
- Terraform skeleton for cloud planning
- Standard-library tests for business logic
- GitHub Actions CI workflow

## Quickstart

```bash
python -m unittest discover -s tests
```

With dependencies installed:

```bash
python scripts/runtime_demo.py
docker compose up --build
python scripts/load_test.py --url http://localhost:8000/health --requests 25
```

`scripts/runtime_demo.py` starts the FastAPI service locally on
`127.0.0.1:8010`, calls `/health`, `/events`, `/jobs`, fetches the created job,
and writes `reports/runtime_api_demo.json`.

## Resume-safe claim

Built a cloud infrastructure lab with a containerized API, Postgres/Redis local
stack, health-check endpoints, job/status workflow, load-test script, CI tests,
Terraform planning skeleton, and runbook documentation.

Do not claim this handled real production users unless it is deployed and measured.
