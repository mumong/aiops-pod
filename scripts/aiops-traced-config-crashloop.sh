#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MANIFEST="${ROOT_DIR}/testcases/aiops-traced-config-crashloop.yaml"
NAMESPACE="${AIOPS_TRACED_CONFIG_NAMESPACE:-aiops-traced-config}"
ACTION="${1:-status}"

target_pod() {
  kubectl get pod -n "${NAMESPACE}" -l app=trace-config-api \
    -o jsonpath='{.items[0].metadata.name}'
}

apply_case() {
  kubectl apply -f "${MANIFEST}"
  kubectl rollout status deployment/trace-config-driver -n "${NAMESPACE}" --timeout=120s
  echo "Waiting for a real Error/exit 78 CrashLoopBackOff..."
  for _ in $(seq 1 120); do
    pod="$(target_pod 2>/dev/null || true)"
    if [[ -z "${pod}" ]]; then
      sleep 2
      continue
    fi
    waiting_reason="$(kubectl get pod "${pod}" -n "${NAMESPACE}" \
      -o jsonpath='{.status.containerStatuses[0].state.waiting.reason}' 2>/dev/null || true)"
    reason="$(kubectl get pod "${pod}" -n "${NAMESPACE}" \
      -o jsonpath='{.status.containerStatuses[0].lastState.terminated.reason}' 2>/dev/null || true)"
    exit_code="$(kubectl get pod "${pod}" -n "${NAMESPACE}" \
      -o jsonpath='{.status.containerStatuses[0].lastState.terminated.exitCode}' 2>/dev/null || true)"
    if [[ "${waiting_reason}" == "CrashLoopBackOff" && "${reason}" == "Error" && "${exit_code}" == "78" ]]; then
      echo "Observed CrashLoopBackOff Error/exit 78 on ${NAMESPACE}/${pod}"
      status_case
      return
    fi
    sleep 2
  done
  echo "Timed out waiting for CrashLoopBackOff" >&2
  status_case
  exit 1
}

status_case() {
  kubectl get pod,svc,deploy -n "${NAMESPACE}" -o wide
  pod="$(target_pod 2>/dev/null || true)"
  if [[ -n "${pod}" ]]; then
    kubectl get pod "${pod}" -n "${NAMESPACE}" \
      -o jsonpath='pod={.metadata.name} phase={.status.phase} ready={.status.containerStatuses[0].ready} restarts={.status.containerStatuses[0].restartCount} current_reason={.status.containerStatuses[0].state.waiting.reason} last_reason={.status.containerStatuses[0].lastState.terminated.reason} last_exit={.status.containerStatuses[0].lastState.terminated.exitCode} pod_ip={.status.podIP} node={.spec.nodeName}{"\n"}'
  fi
}

logs_case() {
  pod="$(target_pod)"
  echo "=== target current logs: ${pod} ==="
  kubectl logs "${pod}" -n "${NAMESPACE}" -c business-api --tail=60 || true
  echo "=== target previous logs: ${pod} ==="
  kubectl logs "${pod}" -n "${NAMESPACE}" -c business-api --previous --tail=100 || true
  echo "=== driver logs ==="
  kubectl logs -n "${NAMESPACE}" deployment/trace-config-driver -c driver --tail=60 || true
}

verify_case() {
  pod="$(target_pod)"
  waiting_reason="$(kubectl get pod "${pod}" -n "${NAMESPACE}" \
    -o jsonpath='{.status.containerStatuses[0].state.waiting.reason}')"
  reason="$(kubectl get pod "${pod}" -n "${NAMESPACE}" \
    -o jsonpath='{.status.containerStatuses[0].lastState.terminated.reason}')"
  exit_code="$(kubectl get pod "${pod}" -n "${NAMESPACE}" \
    -o jsonpath='{.status.containerStatuses[0].lastState.terminated.exitCode}')"
  previous_logs="$(kubectl logs "${pod}" -n "${NAMESPACE}" -c business-api --previous --tail=120)"
  driver_logs="$(kubectl logs -n "${NAMESPACE}" deployment/trace-config-driver -c driver --tail=200)"

  [[ "${waiting_reason}" == "CrashLoopBackOff" ]]
  [[ "${reason}" == "Error" ]]
  [[ "${exit_code}" == "78" ]]
  grep -q '"event": "config_missing"' <<<"${previous_logs}"
  grep -q 'PAYMENT_GATEWAY_TOKEN' <<<"${previous_logs}"
  grep -q '"trace_id":' <<<"${previous_logs}"
  grep -q '"span_id":' <<<"${previous_logs}"
  grep -q '"http_status": 500' <<<"${previous_logs}"
  grep -q '"event": "fatal_configuration_error"' <<<"${previous_logs}"
  grep -q '"event": "request_failed"' <<<"${driver_logs}"
  grep -q '"status": 500' <<<"${driver_logs}"
  grep -q '"traceparent":' <<<"${driver_logs}"

  ready_endpoint="$(kubectl get endpoints trace-config-api -n "${NAMESPACE}" \
    -o jsonpath='{.subsets[0].addresses[0].ip}' 2>/dev/null || true)"
  not_ready_endpoint="$(kubectl get endpoints trace-config-api -n "${NAMESPACE}" \
    -o jsonpath='{.subsets[0].notReadyAddresses[0].ip}' 2>/dev/null || true)"
  [[ -n "${ready_endpoint}" || -n "${not_ready_endpoint}" ]]

  echo "PASS: real config failure, HTTP 500, Error/exit 78, trace context and Service-to-Pod topology are present."
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
