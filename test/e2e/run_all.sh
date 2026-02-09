#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLUSTER_NAME="${CLUSTER_NAME:-aiops-e2e}"
NS="aiops-e2e"

need() { command -v "$1" >/dev/null 2>&1 || { echo "missing dependency: $1" >&2; exit 1; }; }
need docker
need kubectl
need curl

echo "[1/5] Creating kind cluster: ${CLUSTER_NAME}"
kind get clusters | grep -qx "${CLUSTER_NAME}" || kind create cluster --name "${CLUSTER_NAME}"

echo "[1/5] Applying manifests"
kubectl apply -f "${ROOT}/manifests/00-namespace.yaml"
kubectl apply -f "${ROOT}/manifests/l2-oomkilled.yaml"
kubectl apply -f "${ROOT}/manifests/l4-dependency-503.yaml"
kubectl apply -f "${ROOT}/manifests/l0-logfill-enospc.yaml"
kubectl apply -f "${ROOT}/manifests/l3-dns-tc-client.yaml"
kubectl apply -f "${ROOT}/manifests/l1-taint-node.yaml"

echo "[1/5] Waiting for workloads (best effort)"
kubectl -n "${NS}" rollout status deploy/memhog --timeout=120s || true
kubectl -n "${NS}" rollout status deploy/dep503 --timeout=120s || true
kubectl -n "${NS}" rollout status deploy/logfill --timeout=120s || true
kubectl -n "${NS}" rollout status deploy/appcaller --timeout=120s || true

echo "[1/5] Optional: Inject L1 taint (easier validation)"
kubectl taint node aiops-e2e-control-plane aiops-test-scenario=l1-node-issue:NoSchedule || true

echo "[1/5] Validate (prints suggestions for /ask queries)"
bash "${ROOT}/validate.sh" "${CLUSTER_NAME}"
echo "Done."
