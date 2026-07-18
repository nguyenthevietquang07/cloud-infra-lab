from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = PROJECT_ROOT / "infra" / "kubernetes" / "app.yaml"
DEFAULT_REPORT = PROJECT_ROOT / "reports" / "kubernetes_manifest_check.json"


def _load_documents(manifest_path: Path) -> list[str]:
    text = manifest_path.read_text(encoding="utf-8")
    return [doc.strip() for doc in re.split(r"^---\s*$", text, flags=re.MULTILINE) if doc.strip()]


def _field(document: str, name: str) -> str | None:
    match = re.search(rf"(?m)^\s*{re.escape(name)}:\s*([^\n]+)\s*$", document)
    return match.group(1).strip().strip('"') if match else None


def inspect_manifest(manifest_path: Path = DEFAULT_MANIFEST) -> dict[str, Any]:
    documents = _load_documents(manifest_path)
    kinds = [_field(document, "kind") for document in documents]
    names = [_field(document, "name") for document in documents]
    manifest_text = manifest_path.read_text(encoding="utf-8")

    checks = {
        "has_namespace": "Namespace" in kinds,
        "has_configmap": "ConfigMap" in kinds,
        "has_secret_template": "Secret" in kinds and "replace-me-for-local-kind" in manifest_text,
        "has_deployment": "Deployment" in kinds and "cloud-infra-lab-api" in names,
        "has_service": "Service" in kinds and "targetPort: 8000" in manifest_text,
        "has_health_probes": "readinessProbe:" in manifest_text and "livenessProbe:" in manifest_text,
        "has_resource_bounds": "requests:" in manifest_text and "limits:" in manifest_text,
        "uses_local_image": "image: cloud-infra-lab:local" in manifest_text,
    }

    return {
        "passed": all(checks.values()),
        "manifest": str(manifest_path.relative_to(PROJECT_ROOT)),
        "document_count": len(documents),
        "kinds": [kind for kind in kinds if kind],
        "checks": checks,
        "claim_boundary": (
            "This validates manifest structure and expected deployment controls. "
            "Cluster apply, rollout, and runtime behavior require a local kind/minikube or managed Kubernetes run."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Kubernetes manifests for the cloud infra lab.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    report = inspect_manifest(args.manifest)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
