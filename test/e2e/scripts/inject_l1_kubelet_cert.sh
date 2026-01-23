#!/usr/bin/env bash
set -euo pipefail

CLUSTER_NAME="${1:-aiops-e2e}"

need() { command -v "$1" >/dev/null 2>&1 || { echo "missing dependency: $1" >&2; exit 1; }; }
need docker
need kubectl

# kind node container naming convention
NODE_CONTAINER="kind-${CLUSTER_NAME}-control-plane"
echo "Attempting L1 kubelet cert injection on ${NODE_CONTAINER}"

if ! docker ps --format '{{.Names}}' | grep -qx "${NODE_CONTAINER}"; then
  echo "kind node container not found: ${NODE_CONTAINER}"
  exit 0
fi

CERT="/var/lib/kubelet/pki/kubelet-client-current.pem"
BAK="/var/lib/kubelet/pki/kubelet-client-current.pem.bak.aiops"

echo "Backing up cert: ${CERT} -> ${BAK}"
docker exec "${NODE_CONTAINER}" bash -lc "test -f '${CERT}' && cp -a '${CERT}' '${BAK}'"

echo "Simulating missing cert via mv"
docker exec "${NODE_CONTAINER}" bash -lc "test -f '${CERT}' && mv '${CERT}' '${CERT}.moved.aiops'"

echo "Restart kubelet (best effort)"
docker exec "${NODE_CONTAINER}" bash -lc "systemctl restart kubelet || (pkill kubelet || true)"

echo "Waiting up to 90s for node NotReady..."
for i in $(seq 1 90); do
  status="$(kubectl get node "${NODE_CONTAINER}" -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}' 2>/dev/null || true)"
  if [[ "${status}" == "False" || "${status}" == "Unknown" ]]; then
    echo "Node is NotReady/Unknown: ${status}"
    break
  fi
  sleep 1
done

echo "Restore cert"
docker exec "${NODE_CONTAINER}" bash -lc "test -f '${BAK}' && cp -a '${BAK}' '${CERT}' || true"
docker exec "${NODE_CONTAINER}" bash -lc "test -f '${CERT}.moved.aiops' && mv '${CERT}.moved.aiops' '${CERT}' || true"

echo "Restart kubelet to recover"
docker exec "${NODE_CONTAINER}" bash -lc "systemctl restart kubelet || (pkill kubelet || true)"

echo "Waiting up to 120s for node Ready..."
kubectl wait node/"${NODE_CONTAINER}" --for=condition=Ready --timeout=120s || true

echo "Done."

