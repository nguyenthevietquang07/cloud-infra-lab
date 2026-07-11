# Agile Backlog

## Sprint 1 - Local platform baseline

- Create API health endpoint.
- Add event ingestion shape.
- Add job/status model for async workflow practice.
- Add Docker Compose for API, Postgres, and Redis.
- Add unit tests and CI.

## Sprint 2 - Operations depth

- Persist events to Postgres.
- Add Redis cache for repeated event summaries.
- Persist job records to Postgres.
- Add structured logging and request IDs.
- Add load-test report.

## Sprint 3 - Cloud planning

- Extend Terraform skeleton for a managed database and container service.
- Add backup/restore procedure.
- Add deployment checklist.
- Add incident-response runbook.

## Definition of done

- Tests pass locally and in CI.
- Docker Compose starts the full local stack.
- Runbook explains common failure modes.
- README avoids production-scale claims.
