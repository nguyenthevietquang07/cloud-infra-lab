# Security Baseline

This project uses a staging-oriented security baseline. It is meant to make the
service safer to demo and deploy, not to claim production hardening.

## Controls Implemented

- Runtime dependencies are pinned in `requirements.txt`.
- Mutating and job-read endpoints support optional API-key enforcement through
  `API_KEY` and the `X-API-Key` request header.
- `/health` stays unauthenticated so infrastructure checks can run.
- The Docker image drops to a non-root `app` user before starting Uvicorn.
- `.gitignore` excludes local virtual environments, Terraform state, and
  generated report output by default.
- `scripts/security_checklist.py` performs a repeatable baseline check and
  writes `reports/security_checklist.json`.
- `scripts/dependency_audit.py` runs `pip-audit` against `requirements.txt` and
  writes `reports/dependency_audit.json`.

## Claim Boundary

The current baseline is appropriate for a portfolio staging service with no
private customer data. Before a real client launch, add hosted TLS verification,
rate limiting, centralized logs, managed secret storage, backup policy,
container image scanning, and a deployment-specific threat model.

## Local Verification

```bash
python -m pip install -r requirements-dev.txt
python scripts/security_checklist.py
python scripts/dependency_audit.py
```
