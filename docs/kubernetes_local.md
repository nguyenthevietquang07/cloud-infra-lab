# Kubernetes Local Deployment

This directory adds a local Kubernetes deployment path for the FastAPI service.
It is intended as infrastructure literacy evidence, not production cluster
operations evidence.

## What Is Covered

- Namespace, ConfigMap, Secret template, Deployment, and Service manifests.
- Health probes against `/health`.
- CPU and memory request/limit boundaries.
- Static manifest validation through `scripts/kubernetes_manifest_check.py`.

## Validate The Manifests

```bash
python scripts/kubernetes_manifest_check.py
```

The script writes `reports/kubernetes_manifest_check.json` and checks that the
manifest includes the expected runtime controls.

## Optional Local Cluster Flow

Use this only when Docker and `kind` or `minikube` are installed.

```bash
docker build -t cloud-infra-lab:local .
kubectl apply -f infra/kubernetes/app.yaml
kubectl -n cloud-infra-lab rollout status deployment/cloud-infra-lab-api
kubectl -n cloud-infra-lab port-forward service/cloud-infra-lab-api 8010:80
```

Then in another shell:

```bash
python scripts/staging_smoke.py --base-url http://127.0.0.1:8010 --api-key replace-me-for-local-kind
```

## Claim Boundary

Passing the static validator means the manifest has the expected deployment
shape. A real Kubernetes claim requires a saved dry-run, rollout, port-forward,
and smoke-test report from a local or managed cluster.
