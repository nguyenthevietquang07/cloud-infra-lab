# Render Staging Deployment

This project is prepared for a Render Blueprint deployment and has a verified
staging service at `https://cloud-infra-lab-api.onrender.com`. The goal is a
repeatable staging service with managed Postgres, managed Key Value cache,
health checks, API-key protection, and saved verification artifacts.

## Resources

`render.yaml` provisions:

- `cloud-infra-lab-api`: Python web service running `uvicorn app.main:app`
- `cloud-infra-lab-db`: managed Postgres database exposed as `DATABASE_URL`
- `cloud-infra-lab-cache`: managed Key Value cache exposed as `REDIS_URL`
- `API_KEY`: generated secret used by protected `/events` and `/jobs` routes

## Deploy

1. Push the latest commit to GitHub.
2. In Render, choose **New > Blueprint**.
3. Connect `nguyenthevietquang07/cloud-infra-lab`.
4. Keep the default Blueprint path as `render.yaml`.
5. Apply the plan and wait for the web service to pass `/health`.
6. Copy the generated `API_KEY` from the service environment.
7. Copy the deployed `https://...onrender.com` service URL.

Render may cold-start free instances. Run smoke checks after the first healthy
deploy, not while the initial build is still starting.

## Verify Staging

Smoke test the deployed service:

```bash
python scripts/staging_smoke.py --base-url https://YOUR-SERVICE.onrender.com --api-key YOUR_API_KEY
```

Run a bounded load test:

```bash
python scripts/staging_load_test.py --base-url https://YOUR-SERVICE.onrender.com --api-key YOUR_API_KEY --requests 50 --concurrency 5
```

Expected artifacts:

- `reports/render_staging_smoke.json`
- `reports/render_load_test.json`

## Launch Gate

The staging launch gaps are resolved when both of these are true:

- a real Render staging URL is saved in the smoke/load reports;
- both staging verification scripts pass against that deployed URL.

Do not claim uptime, production load, or client traffic from these reports.
They prove a reproducible staging deployment and a small measured request burst.
