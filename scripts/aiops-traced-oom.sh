#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MANIFEST="${ROOT_DIR}/testcases/aiops-traced-oom.yaml"
NAMESPACE="${AIOPS_TRACED_OOM_NAMESPACE:-aiops-traced-oom}"
ACTION="${1:-status}"

target_pod() {
  kubectl get pod -n "${NAMESPACE}" -l app=trace-oom-api \
    -o jsonpath='{.items[0].metadata.name}'
}

apply_case() {
  kubectl apply -f "${MANIFEST}"
  kubectl rollout status deployment/trace-oom-api -n "${NAMESPACE}" --timeout=120s
  kubectl rollout status deployment/trace-oom-driver -n "${NAMESPACE}" --timeout=120s
  echo "Waiting for a real OOMKilled termination..."
  for _ in $(seq 1 90); do
    pod="$(target_pod)"
    reason="$(kubectl get pod "${pod}" -n "${NAMESPACE}" \
      -o jsonpath='{.status.containerStatuses[0].lastState.terminated.reason}' 2>/dev/null || true)"
    if [[ "${reason}" == "OOMKilled" ]]; then
      echo "Observed OOMKilled on ${NAMESPACE}/${pod}"
      status_case
      return
    fi
    sleep 2
  done
  echo "Timed out waiting for OOMKilled" >&2
  status_case
  exit 1
}

status_case() {
  kubectl get pod,svc,deploy -n "${NAMESPACE}" -o wide
  pod="$(target_pod 2>/dev/null || true)"
  if [[ -n "${pod}" ]]; then
    kubectl get pod "${pod}" -n "${NAMESPACE}" -o jsonpath='pod={.metadata.name} phase={.status.phase} restarts={.status.containerStatuses[0].restartCount} current_reason={.status.containerStatuses[0].state.waiting.reason} last_reason={.status.containerStatuses[0].lastState.terminated.reason} last_exit={.status.containerStatuses[0].lastState.terminated.exitCode} pod_ip={.status.podIP} node={.spec.nodeName}{"\n"}'
  fi
}

logs_case() {
  pod="$(target_pod)"
  echo "=== target current logs: ${pod} ==="
  kubectl logs "${pod}" -n "${NAMESPACE}" -c business-api --tail=40 || true
  echo "=== target previous logs: ${pod} ==="
  kubectl logs "${pod}" -n "${NAMESPACE}" -c business-api --previous --tail=40 || true
  echo "=== driver logs ==="
  kubectl logs -n "${NAMESPACE}" deployment/trace-oom-driver -c driver --tail=30 || true
}

verify_case() {
  pod="$(target_pod)"
  reason="$(kubectl get pod "${pod}" -n "${NAMESPACE}" \
    -o jsonpath='{.status.containerStatuses[0].lastState.terminated.reason}')"
  exit_code="$(kubectl get pod "${pod}" -n "${NAMESPACE}" \
    -o jsonpath='{.status.containerStatuses[0].lastState.terminated.exitCode}')"
  previous_logs="$(kubectl logs "${pod}" -n "${NAMESPACE}" -c business-api --previous --tail=100)"
  driver_logs="$(kubectl logs -n "${NAMESPACE}" deployment/trace-oom-driver -c driver --tail=100)"

  [[ "${reason}" == "OOMKilled" ]]
  [[ "${exit_code}" == "137" ]]
  grep -q '"event": "allocate"' <<<"${previous_logs}"
  grep -q '"trace_id":' <<<"${previous_logs}"
  grep -q '"span_id":' <<<"${previous_logs}"
  grep -q '"allocated_mib":' <<<"${previous_logs}"
  grep -q '"traceparent":' <<<"${driver_logs}"
  ready_endpoint="$(kubectl get endpoints trace-oom-api -n "${NAMESPACE}" \
    -o jsonpath='{.subsets[0].addresses[0].ip}' 2>/dev/null || true)"
  not_ready_endpoint="$(kubectl get endpoints trace-oom-api -n "${NAMESPACE}" \
    -o jsonpath='{.subsets[0].notReadyAddresses[0].ip}' 2>/dev/null || true)"
  [[ -n "${ready_endpoint}" || -n "${not_ready_endpoint}" ]]

  echo "PASS: real request-driven OOM, correlated logs, trace context and Service-to-Pod topology are present."
  echo "Service endpoint: ready=${ready_endpoint:-none} not_ready=${not_ready_endpoint:-none}"
  status_case
}

cleanup_case() {
  kubectl delete namespace "${NAMESPACE}" --ignore-not-found=true --wait=true --timeout=120s
}

case "${ACTION}" in
  apply) apply_case ;;
  status) status_case ;;
  logs) logs_case ;;
  verify) verify_case ;;
  cleanup) cleanup_case ;;
  *)
    echo "Usage: $0 {apply|status|logs|verify|cleanup}" >&2
    exit 2
    ;;
esac
