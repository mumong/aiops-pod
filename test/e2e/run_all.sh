#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLUSTER_NAME="${CLUSTER_NAME:-aiops-e2e}"
NS="aiops-e2e"

need() { command -v "$1" >/dev/null 2>&1 || { echo "missing dependency: $1" >&2; exit 1; }; }
need docker
need kubectl
need kind
need curl

echo "[1/5] Creating kind cluster: ${CLUSTER_NAME}"
kind get clusters | grep -qx "${CLUSTER_NAME}" || kind create cluster --name "${CLUSTER_NAME}"

echo "[2/5] Applying manifests"
kubectl apply -f "${ROOT}/manifests/00-namespace.yaml"
kubectl apply -f "${ROOT}/manifests/l2-oomkilled.yaml"
kubectl apply -f "${ROOT}/manifests/l4-dependency-503.yaml"
kubectl apply -f "${ROOT}/manifests/l0-logfill-enospc.yaml"
kubectl apply -f "${ROOT}/manifests/l3-dns-tc-client.yaml"

echo "[3/5] Waiting for workloads (best effort)"
kubectl -n "${NS}" rollout status deploy/memhog --timeout=120s || true
kubectl -n "${NS}" rollout status deploy/dep503 --timeout=120s || true
kubectl -n "${NS}" rollout status deploy/appcaller --timeout=120s || true
kubectl -n "${NS}" rollout status deploy/logfill --timeout=120s || true
kubectl -n "${NS}" wait --for=condition=Ready pod/dns-latency-client --timeout=120s || true

echo "[4/5] Optional: inject L1 kubelet cert issue (best effort)"
if [[ "${INJECT_L1_KUBELET_CERT:-0}" == "1" ]]; then
  bash "${ROOT}/scripts/inject_l1_kubelet_cert.sh" "${CLUSTER_NAME}" || true
else
  echo "  (skipped; set INJECT_L1_KUBELET_CERT=1 to attempt)"
fi

echo "[5/5] Validate (prints suggestions for /ask queries)"
bash "${ROOT}/validate.sh" "${CLUSTER_NAME}"

echo "Done."

