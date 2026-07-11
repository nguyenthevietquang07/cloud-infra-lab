# Operations Runbook

## Health check

`GET /health` should return `status: ok`.

## Local startup

```bash
docker compose up --build
```

## Common checks

- API logs show request processing without tracebacks.
- Postgres container is healthy and accepts connections.
- Redis container starts and listens on port 6379.
- Unit tests pass before deployment changes.

## Incident notes

If the API starts but event ingestion fails:

1. Check request payload shape.
2. Check application logs.
3. Confirm database migration has been applied.
4. Re-run a small load test after the fix.

## Resume boundary

This lab proves operational thinking and setup quality. It is not evidence of
production user traffic unless a deployment and traffic report are added.
