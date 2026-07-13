from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "reports" / "dependency_audit.json"


def run_pip_audit() -> tuple[int, dict[str, object], str]:
    command = [
        sys.executable,
        "-m",
        "pip_audit",
        "-r",
        "requirements.txt",
        "--format",
        "json",
        "--no-deps",
        "--disable-pip",
        "--progress-spinner",
        "off",
    ]
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    raw_stdout = completed.stdout.strip()
    if not raw_stdout:
        return completed.returncode, {"dependencies": []}, completed.stderr.strip()
    try:
        return completed.returncode, json.loads(raw_stdout), completed.stderr.strip()
    except json.JSONDecodeError as exc:
        return completed.returncode, {"dependencies": [], "parse_error": str(exc)}, completed.stderr.strip()


def normalize(raw: dict[str, object], returncode: int, stderr: str) -> dict[str, object]:
    dependencies = raw.get("dependencies", [])
    vulnerability_count = 0
    audited_dependency_count = 0
    vulnerable_dependencies: list[dict[str, object]] = []
    if isinstance(dependencies, list):
        audited_dependency_count = len(dependencies)
        for dependency in dependencies:
            if not isinstance(dependency, dict):
                continue
            vulns = dependency.get("vulns", [])
            if isinstance(vulns, list) and vulns:
                vulnerability_count += len(vulns)
                vulnerable_dependencies.append(
                    {
                        "name": dependency.get("name"),
                        "version": dependency.get("version"),
                        "vulnerability_count": len(vulns),
                    }
                )
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project": "cloud-infra-lab",
        "stage": "dependency_audit",
        "tool": "pip-audit",
        "requirements_file": "requirements.txt",
        "dependency_scope": "direct pinned runtime dependencies",
        "audited_dependency_count": audited_dependency_count,
        "vulnerability_count": vulnerability_count,
        "vulnerable_dependencies": vulnerable_dependencies,
        "passed": returncode == 0 and vulnerability_count == 0,
        "stderr": stderr,
        "claim_boundary": (
            "Dependency audit checks direct pinned Python runtime dependencies with "
            "pip-audit. It does not cover OS image CVEs, container registry scans, "
            "or unresolved transitive dependencies."
        ),
    }


def main() -> None:
    returncode, raw, stderr = run_pip_audit()
    report = normalize(raw, returncode, stderr)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
