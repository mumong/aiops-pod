#!/usr/bin/env bash
set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
lab_dir=$(cd -- "${script_dir}/.." && pwd)

command -v kubectl >/dev/null
command -v python3 >/dev/null
kubectl kustomize "${lab_dir}/safe" >/dev/null
python3 -m unittest discover -s "${lab_dir}/tests" -q

deletion_timestamp=$(kubectl -n aiops-case-11 get pod workload \
  -o jsonpath='{.metadata.deletionTimestamp}' 2>/dev/null || true)
if [[ -n "${deletion_timestamp}" ]]; then
  kubectl -n aiops-case-11 patch pod workload --type=json \
    -p='[{"op":"remove","path":"/metadata/finalizers"}]' || true
  kubectl -n aiops-case-11 wait --for=delete pod/workload --timeout=120s
fi

kubectl apply -k "${lab_dir}/safe"
kubectl -n aiops-case-11 wait --for=condition=Ready pod/workload --timeout=180s

telemetry_ready=false
for _attempt in $(seq 1 30); do
  if kubectl -n aiops-case-11 logs pod/workload --tail=20 2>/dev/null | grep -q '"event":"http_request"'; then
    telemetry_ready=true
    break
  fi
  sleep 2
done
if [[ "${telemetry_ready}" != true ]]; then
  echo "c11 did not emit a traced request before its bounded trigger" >&2
  exit 1
fi

kubectl -n aiops-case-11 delete pod workload --wait=false
"${script_dir}/validate.sh" --wait "$@"
