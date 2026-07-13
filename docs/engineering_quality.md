# Engineering Quality

This service is organized around operational correctness, reproducible checks,
and evidence-backed claims.

## Delivered Practices

- FastAPI service with typed request and response schemas.
- Health endpoint for deployment and runtime checks.
- Postgres-backed job persistence through Docker Compose and Render.
- Redis/Key Value-backed status cache with restart verification.
- Request ID middleware and structured JSON access logs.
- API-key protection for staging write endpoints.
- Unit tests, Docker smoke test, security checklist, dependency audit, and
  staged Render smoke/load reports.

## Evidence Rules

- Local reports prove local behavior only.
- Render reports prove one staging deployment and bounded request load.
- Uptime, production traffic, and sustained-load claims require additional
  monitoring evidence.
