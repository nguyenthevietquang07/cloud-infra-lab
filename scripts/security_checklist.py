from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "reports" / "security_checklist.json"
SKIP_PARTS = {".git", ".venv", "__pycache__"}
SECRET_PATTERNS = [
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"ghp_[A-Za-z0-9_]{30,}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def pinned_runtime_dependencies() -> dict[str, object]:
    lines = [
        line.strip()
        for line in read_text("requirements.txt").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    unpinned = [line for line in lines if "==" not in line]
    return {
        "passed": not unpinned,
        "dependency_count": len(lines),
        "unpinned": unpinned,
    }


def docker_non_root() -> dict[str, object]:
    dockerfile = read_text("Dockerfile")
    return {
        "passed": bool(re.search(r"^USER\s+\S+", dockerfile, flags=re.MULTILINE)),
        "details": "Dockerfile switches away from root before starting Uvicorn.",
    }


def api_key_guard_present() -> dict[str, object]:
    main = read_text("app/main.py")
    security = read_text("app/security.py")
    protected_routes = [
        '@app.post("/events"',
        '@app.post("/jobs"',
        '@app.get("/jobs/{job_id}"',
        '@app.get("/jobs/{job_id}/status"',
    ]
    decorator_lines = [
        line.strip()
        for line in main.splitlines()
        if line.strip().startswith("@app.")
    ]
    missing = [
        route
        for route in protected_routes
        if not any(route in line and "Depends(require_api_key)" in line for line in decorator_lines)
    ]
    return {
        "passed": "API_KEY" in security and "X-API-Key" in security and not missing,
        "missing_protection": missing,
        "boundary": "API key enforcement is optional for local demos and active when API_KEY is configured.",
    }


def gitignore_blocks_sensitive_outputs() -> dict[str, object]:
    gitignore = read_text(".gitignore")
    required = [".venv/", "*.tfstate", "*.tfstate.*", "reports/*"]
    missing = [item for item in required if item not in gitignore]
    return {"passed": not missing, "missing": missing}


def secret_scan() -> dict[str, object]:
    findings: list[str] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or any(part in SKIP_PARTS for part in path.relative_to(ROOT).parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                findings.append(str(path.relative_to(ROOT)))
                break
    return {"passed": not findings, "findings": sorted(findings)}


def build_report() -> dict[str, object]:
    checks = {
        "pinned_runtime_dependencies": pinned_runtime_dependencies(),
        "docker_non_root": docker_non_root(),
        "optional_api_key_guard": api_key_guard_present(),
        "gitignore_sensitive_outputs": gitignore_blocks_sensitive_outputs(),
        "secret_scan": secret_scan(),
    }
    passed = all(bool(check["passed"]) for check in checks.values())
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project": "cloud-infra-lab",
        "stage": "security_checklist",
        "claim_boundary": (
            "Security checklist verifies a staging baseline for this portfolio API. "
            "It is not a penetration test, compliance audit, or production threat model."
        ),
        "checks": checks,
        "passed": passed,
    }


def main() -> None:
    report = build_report()
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
