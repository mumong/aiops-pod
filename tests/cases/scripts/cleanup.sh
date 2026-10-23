#!/usr/bin/env bash
set -euo pipefail

namespaces=(
  aiops-case-01 aiops-case-02 aiops-case-03 aiops-case-04 aiops-case-05 aiops-case-06
  aiops-case-07 aiops-case-08 aiops-case-09 aiops-case-10 aiops-case-11
)

if kubectl -n aiops-case-11 get pod workload >/dev/null 2>&1; then
  kubectl -n aiops-case-11 patch pod workload --type=json \
    -p='[{"op":"remove","path":"/metadata/finalizers"}]' || true
fi

for namespace in "${namespaces[@]}"; do
  kubectl delete namespace "${namespace}" --ignore-not-found=true --wait=true --timeout=180s
done
