# Operations Runbook

## Health check

`GET /health` should return `status: ok`.

## Local startup

```bash
docker compose up --build
```

## Common checks

- API logs show request processing without tracebacks.
- Every API response includes an `X-Request-ID`; access logs include the same
  request ID, method, path, status code, and request duration.
- Postgres container is healthy and accepts connections.
- Redis container starts, listens on port 6379, and `/jobs/{job_id}/status`
  returns `source: cache` after a job is created.
- Unit tests pass before deployment changes.

## Render staging checks

After a Render Blueprint deploy:

1. Confirm `/health` is healthy from the public `onrender.com` URL.
2. Confirm the Render service has `API_KEY`, `DATABASE_URL`, and `REDIS_URL`.
3. Run `python scripts/staging_smoke.py --base-url <url> --api-key <key>`.
4. Run `python scripts/staging_load_test.py --base-url <url> --api-key <key> --requests 50 --concurrency 5`.
5. Save `reports/render_staging_smoke.json` and `reports/render_load_test.json`.

Free Render instances can cold-start. If the first request is slow, rerun the
smoke test after the service is warm and keep the report's latency context.

## Incident notes

If the API starts but event ingestion fails:

1. Check request payload shape.
2. Check application logs.
3. Use the `X-Request-ID` from the client response to locate the structured
   access log line.
4. Confirm database migration has been applied.
5. Confirm Redis status cache connectivity through `/health`.
6. Re-run a small load test after the fix.

## Resume boundary

This lab proves operational thinking and setup quality. It is not evidence of
production user traffic unless a deployment and traffic report are added.
