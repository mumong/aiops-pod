#!/usr/bin/env bash
set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
lab_dir=$(cd -- "${script_dir}/.." && pwd)
repo_dir=$(cd -- "${lab_dir}/.." && pwd)
case_namespace=aiops-case-08
case_manifest="${lab_dir}/cases/oomkilled-traced"
prometheus_port=19090
elasticsearch_port=19200
observability_wait_seconds=90
runtime_dir=""
tunnel_pids=()

cd "${repo_dir}"

usage() {
  cat <<'EOF'
Usage:
  pod-anomaly-cases/scripts/oom-testpoint1.sh [run]
  pod-anomaly-cases/scripts/oom-testpoint1.sh collect --namespace <namespace> --pod <pod>
  pod-anomaly-cases/scripts/oom-testpoint1.sh view --case <case-directory>
  pod-anomaly-cases/scripts/oom-testpoint1.sh cleanup

Commands:
  run      Deploy or reuse c08, confirm OOMKilled/137, collect five-source evidence, and leave it running.
  collect  Collect an existing OOMKilled Pod. Namespace and Pod are required inputs.
  view     Print the human-readable core evidence from an existing Case Package.
  cleanup  Delete only namespace aiops-case-08.
EOF
}

fail() {
  echo "ERROR: $*" >&2
  exit 1
}

cleanup_runtime() {
  local pid
  for pid in "${tunnel_pids[@]:-}"; do
    if [[ -n "${pid}" ]] && kill -0 "${pid}" 2>/dev/null; then
      kill "${pid}" 2>/dev/null || true
    fi
  done
  for pid in "${tunnel_pids[@]:-}"; do
    if [[ -n "${pid}" ]]; then
      wait "${pid}" 2>/dev/null || true
    fi
  done
  if [[ -n "${runtime_dir}" && -d "${runtime_dir}" ]]; then
    rm -r -- "${runtime_dir}"
  fi
}

trap cleanup_runtime EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

preflight() {
  local command
  for command in kubectl python3 base64 jq; do
    command -v "${command}" >/dev/null || fail "required command not found: ${command}"
  done
  kubectl version -o json --request-timeout=10s >/dev/null
  kubectl kustomize "${case_manifest}" >/dev/null
  [[ -f "${repo_dir}/scripts/collect_case.py" ]] || fail "scripts/collect_case.py not found"
  [[ -f "${repo_dir}/scripts/audit_aiops_case.py" ]] || fail "scripts/audit_aiops_case.py not found"
  [[ -f "${repo_dir}/scripts/summarize_oom_case.py" ]] || fail "scripts/summarize_oom_case.py not found"
}

view_preflight() {
  command -v jq >/dev/null || fail "required command not found: jq"
}

print_core_results() {
  local case_dir=$1
  local summary="${case_dir}/acceptance-summary.json"
  local kubernetes="${case_dir}/evidence/k8s_pod.yaml"
  local metrics="${case_dir}/evidence/metrics.jsonl"
  local logs="${case_dir}/evidence/logs.jsonl"
  local deepflow="${case_dir}/evidence/deepflow_l7.jsonl"
  local tempo="${case_dir}/evidence/tempo_traces.jsonl"
  local path trace_id

  view_preflight
  for path in "${summary}" "${kubernetes}" "${metrics}" "${logs}" "${deepflow}" "${tempo}"; do
    [[ -f "${path}" ]] || fail "Case Package file not found: ${path}"
  done
  jq -e . "${summary}" >/dev/null || fail "invalid acceptance summary: ${summary}"
  trace_id=$(jq -r '.correlation.common_trace_ids[0] // ""' "${summary}")

  echo
  echo "=== OOM TESTPOINT1 CORE RESULT ==="
  jq -r '
    "STATUS: \(.status)",
    "CASE: \(.case_id)",
    "ENTITY: \(.input.namespace)/\(.input.pod)",
    "SHARED_TRACE_ID: \(.correlation.common_trace_ids[0] // "unavailable")"
  ' "${summary}"

  echo
  echo "KUBERNETES"
  jq -r '
    "  OOM fact: reason=\(.oom.reason // "unavailable") exit_code=\(.oom.exit_code // "unavailable") restart_count=\(.oom.restart_count // "unavailable")",
    "  evidence_rows=\(.evidence_counts.kubernetes // 0)"
  ' "${summary}"

  echo
  echo "PROMETHEUS"
  jq -r '
    def mib:
      if . == null then "unavailable"
      else (((. / 1048576 * 100) | round) / 100 | tostring) + " MiB"
      end;
    "  memory_working_set: start=\(.metrics.memory_working_set_bytes.start | mib) max=\(.metrics.memory_working_set_bytes.max | mib) last=\(.metrics.memory_working_set_bytes.last | mib)",
    "  memory_limit=\(.metrics.memory_limit_bytes | mib)",
    "  restart_series: start=\(.metrics.restart_count.start // "unavailable") last=\(.metrics.restart_count.last // "unavailable")",
    "  evidence_rows=\(.evidence_counts.metrics // 0)"
  ' "${summary}"
  jq -sr '
    [.[] | select((.query_id // "") | contains("kube_pod_container_status_last_terminated_reason"))][0]
    | if . == null then "  termination_reason_series: unavailable"
      else "  termination_reason_series: \(.summary)"
      end
  ' "${metrics}"

  echo
  echo "LOGGING"
  jq -sr '
    def payload:
      (.raw.message? // .otel.body? // "{}")
      | if type == "string" then (try fromjson catch {}) else . end;
    [.[] | {timestamp: .timestamp, payload: payload} | select(.payload.allocated_mib != null)]
    | if length == 0 then "  max_allocation_log: unavailable"
      else max_by(.payload.allocated_mib)
      | "  max_allocation_log: allocated_mib=\(.payload.allocated_mib) timestamp=\(.timestamp // "unavailable") trace_id=\(.payload.trace_id // "unavailable")"
      end
  ' "${logs}"
  jq -sr --arg trace "${trace_id}" '
    def payload:
      (.raw.message? // .otel.body? // "{}")
      | if type == "string" then (try fromjson catch {}) else . end;
    [.[] | {timestamp: .timestamp, payload: payload} | select(.payload.trace_id == $trace)][0]
    | if . == null then "  correlated_log: unavailable"
      else "  correlated_log: allocated_mib=\(.payload.allocated_mib // "unavailable") timestamp=\(.timestamp // "unavailable") trace_id=\(.payload.trace_id)"
      end
  ' "${logs}"
  jq -r '"  evidence_rows=\(.evidence_counts.logging // 0)"' "${summary}"

  echo
  echo "DEEPFLOW"
  jq -sr --arg trace "${trace_id}" '
    [.[] | select((.raw.trace_id? // .otel.trace_id? // "") == $trace)][0]
    | if . == null then "  correlated_request: unavailable"
      else "  correlated_request: \(.raw.ip4_0 // "?") -> \(.raw.ip4_1 // "?") \(.raw.request_type // "?") \(.raw.request_resource // "?") status=\(.raw.response_code // "?") trace_id=\(.raw.trace_id // "unavailable")"
      end
  ' "${deepflow}"
  jq -r '"  L4_rows=\(.evidence_counts.deepflow_l4 // 0) L7_rows=\(.evidence_counts.deepflow_l7 // 0)"' "${summary}"

  echo
  echo "TEMPO"
  jq -sr --arg trace "${trace_id}" '
    [.[] | select((.raw.trace_id? // .otel.trace_id? // "") == $trace)][0]
    | if . == null then "  correlated_span: unavailable"
      else (.raw.spans[0] // .otel.spans[0] // {}) as $span
      | "  correlated_span: service=\($span.service // "unavailable") span=\($span.name // "unavailable") duration_ms=\($span.duration_ms // "unavailable") trace_id=\(.raw.trace_id // .otel.trace_id // "unavailable")"
      end
  ' "${tempo}"
  jq -r '"  trace_rows=\(.evidence_counts.tempo_traces // 0)"' "${summary}"

  echo
  echo "RAW EVIDENCE"
  printf '  SUMMARY=%s\n' "${summary}"
  printf '  KUBERNETES=%s\n' "${kubernetes}"
  printf '  PROMETHEUS=%s\n' "${metrics}"
  printf '  LOGGING=%s\n' "${logs}"
  printf '  DEEPFLOW=%s\n' "${deepflow}"
  printf '  TEMPO=%s\n' "${tempo}"

  echo
  echo "REVIEW COMMANDS"
  printf '  jq . %q\n' "${summary}"
  printf '  jq '\''{metadata: .metadata, containerStatuses: .status.containerStatuses}'\'' %q\n' "${kubernetes}"
  printf '  jq -r '\''[.query_id, .summary] | @tsv'\'' %q\n' "${metrics}"
  printf '  jq -c '\''{timestamp, summary, raw}'\'' %q\n' "${logs}"
  printf '  jq -c '\''{timestamp, summary, raw}'\'' %q\n' "${deepflow}"
  printf '  jq -c '\''{timestamp, summary, raw}'\'' %q\n' "${tempo}"
}

port_is_available() {
  python3 - "$1" <<'PY'
import socket
import sys

port = int(sys.argv[1])
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    sock.bind(("127.0.0.1", port))
except OSError:
    raise SystemExit(1)
finally:
    sock.close()
PY
}

wait_for_port() {
  local port=$1
  local attempt
  for ((attempt = 1; attempt <= 40; attempt++)); do
    if python3 - "${port}" <<'PY'
import socket
import sys

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.settimeout(0.2)
    raise SystemExit(0 if sock.connect_ex(("127.0.0.1", int(sys.argv[1]))) == 0 else 1)
PY
    then
      return 0
    fi
    sleep 0.25
  done
  return 1
}

start_tunnels() {
  port_is_available "${prometheus_port}" || fail "local port ${prometheus_port} is already in use"
  port_is_available "${elasticsearch_port}" || fail "local port ${elasticsearch_port} is already in use"
  kubectl -n monitor get svc observability-prometheus >/dev/null
  kubectl -n monitor get pod elasticsearch-master-0 >/dev/null

  runtime_dir=$(mktemp -d /tmp/oom-testpoint1.XXXXXX)
  kubectl -n monitor port-forward svc/observability-prometheus "${prometheus_port}:9090" \
    >"${runtime_dir}/prometheus-port-forward.log" 2>&1 &
  tunnel_pids+=("$!")
  kubectl -n monitor port-forward pod/elasticsearch-master-0 "${elasticsearch_port}:9200" \
    >"${runtime_dir}/elasticsearch-port-forward.log" 2>&1 &
  tunnel_pids+=("$!")

  wait_for_port "${prometheus_port}" || {
    sed -n '1,40p' "${runtime_dir}/prometheus-port-forward.log" >&2
    fail "Prometheus port-forward did not become ready"
  }
  wait_for_port "${elasticsearch_port}" || {
    sed -n '1,40p' "${runtime_dir}/elasticsearch-port-forward.log" >&2
    fail "Elasticsearch port-forward did not become ready"
  }
}

oom_identity() {
  local namespace=$1
  local pod=$2
  kubectl get pod -n "${namespace}" "${pod}" -o json | python3 -c '
import json, sys
pod = json.load(sys.stdin)
for status in pod.get("status", {}).get("containerStatuses", []):
    terminated = status.get("lastState", {}).get("terminated", {})
    if terminated.get("reason") == "OOMKilled" and int(terminated.get("exitCode") or 0) == 137:
        print("{}|{}".format(status.get("name", ""), int(status.get("restartCount") or 0)))
        raise SystemExit(0)
raise SystemExit(1)
'
}

wait_for_oom() {
  local namespace=$1
  local pod=$2
  local attempt identity
  for ((attempt = 1; attempt <= 72; attempt++)); do
    if identity=$(oom_identity "${namespace}" "${pod}" 2>/dev/null); then
      echo "OOM_CONFIRMED namespace=${namespace} pod=${pod} container_restart=${identity}"
      return 0
    fi
    if ((attempt % 6 == 0)); then
      echo "Waiting for OOMKilled/137: namespace=${namespace} pod=${pod} elapsed=$((attempt * 5))s"
    fi
    sleep 5
  done
  return 1
}

wait_for_workload_pod() {
  local attempt pod
  for ((attempt = 1; attempt <= 60; attempt++)); do
    pod=$(kubectl -n "${case_namespace}" get pod -l app.kubernetes.io/name=workload \
      -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || true)
    if [[ -n "${pod}" ]]; then
      printf '%s\n' "${pod}"
      return 0
    fi
    sleep 2
  done
  return 1
}

collect_case() {
  local namespace=$1
  local pod=$2
  local identity case_id output
  local es_username_b64 es_password_b64 es_username es_password
  local validate_rc=0 audit_rc=0 summary_rc=0

  identity=$(oom_identity "${namespace}" "${pod}") || fail "${namespace}/${pod} does not show OOMKilled with exit code 137"
  case_id="oom-testpoint1-$(date -u +%Y%m%d-%H%M%S)"
  output="${repo_dir}/cases/${case_id}"
  [[ ! -e "${output}" ]] || fail "output already exists: ${output}"

  start_tunnels
  es_username_b64=$(kubectl get secret -n monitor elasticsearch-master-credentials -o jsonpath='{.data.username}')
  es_password_b64=$(kubectl get secret -n monitor elasticsearch-master-credentials -o jsonpath='{.data.password}')
  [[ -n "${es_username_b64}" && -n "${es_password_b64}" ]] || fail "Elasticsearch credentials Secret is empty"
  es_username=$(printf '%s' "${es_username_b64}" | base64 -d)
  es_password=$(printf '%s' "${es_password_b64}" | base64 -d)

  PROMETHEUS_URL="http://127.0.0.1:${prometheus_port}" \
  ELASTICSEARCH_URL="https://127.0.0.1:${elasticsearch_port}" \
  ELASTICSEARCH_INDEX='filebeat-*' \
  ELASTICSEARCH_USERNAME="${es_username}" \
  ELASTICSEARCH_PASSWORD="${es_password}" \
  DEEPFLOW_CLICKHOUSE_URL='kubectl://monitor/observability-clickhouse-0?container=clickhouse' \
  TEMPO_EXEC_ENABLED=true \
  TEMPO_EXEC_NAMESPACE=monitor \
  TEMPO_EXEC_SELECTOR='app=lgtm' \
  TEMPO_LOCAL_URL='http://127.0.0.1:3200' \
    python3 "${repo_dir}/scripts/collect_case.py" package \
      --scenario oomkilled \
      --case-id "${case_id}" \
      --namespace "${namespace}" \
      --pod "${pod}" \
      --output "${output}"

  python3 "${repo_dir}/scripts/collect_case.py" validate --case "${output}" \
    >"${runtime_dir}/validate.out" 2>&1 || validate_rc=$?
  python3 "${repo_dir}/scripts/audit_aiops_case.py" \
    --case "${output}" \
    --scenario oomkilled \
    --require-dimension metrics \
    --require-dimension logging \
    --require-dimension network_flow \
    --require-dimension kubernetes \
    --require-dimension trace >"${runtime_dir}/audit.out" 2>&1 || audit_rc=$?
  python3 "${repo_dir}/scripts/summarize_oom_case.py" --case "${output}" \
    >"${runtime_dir}/summary.out" 2>&1 || summary_rc=$?

  print_core_results "${output}"

  if ((validate_rc != 0 || audit_rc != 0 || summary_rc != 0)); then
    echo >&2
    echo "VALIDATION DETAILS" >&2
    sed -n '1,120p' "${runtime_dir}/validate.out" >&2
    sed -n '1,160p' "${runtime_dir}/audit.out" >&2
    sed -n '1,160p' "${runtime_dir}/summary.out" >&2
    fail "OOM multimodal acceptance failed; inspect ${output}/acceptance-summary.json"
  fi
  echo "OOM_TESTPOINT1=PASS"
}

run_case() {
  local pod remaining
  local reuse_existing=false
  preflight
  if kubectl get namespace "${case_namespace}" >/dev/null 2>&1; then
    reuse_existing=true
    echo "REUSING_EXISTING_CASE namespace=${case_namespace}; deployment skipped"
  else
    kubectl apply -k "${case_manifest}"
    kubectl -n "${case_namespace}" wait \
      --for=condition=Available deployment/traffic-driver --timeout=180s
  fi

  pod=$(wait_for_workload_pod) || fail "workload Pod was not found in namespace ${case_namespace}"
  wait_for_oom "${case_namespace}" "${pod}" || fail "timed out waiting for OOMKilled/137"

  if [[ "${reuse_existing}" == false ]]; then
    for ((remaining = observability_wait_seconds; remaining > 0; remaining -= 5)); do
      echo "Waiting for observability backends to ingest the OOM window: ${remaining}s"
      sleep 5
    done
  else
    echo "EXISTING_CASE_QUERY namespace=${case_namespace} pod=${pod}; ingestion wait skipped"
  fi
  collect_case "${case_namespace}" "${pod}"
  echo "CASE_LEFT_RUNNING=${case_namespace}"
  echo "CLEANUP_COMMAND=${repo_dir}/pod-anomaly-cases/scripts/oom-testpoint1.sh cleanup"
}

cleanup_case() {
  preflight
  kubectl delete namespace "${case_namespace}" --ignore-not-found=true --wait=true --timeout=180s
  if kubectl get namespace "${case_namespace}" >/dev/null 2>&1; then
    fail "namespace ${case_namespace} still exists"
  fi
  echo "OOM_CASE_CLEANUP=PASS namespace=${case_namespace}"
}

command=${1:-run}
if (($# > 0)); then
  shift
fi

case "${command}" in
  run)
    (($# == 0)) || fail "run does not accept arguments"
    run_case
    ;;
  collect)
    namespace=""
    pod=""
    while (($# > 0)); do
      case "$1" in
        --namespace)
          (($# >= 2)) || fail "--namespace requires a value"
          namespace=$2
          shift 2
          ;;
        --pod)
          (($# >= 2)) || fail "--pod requires a value"
          pod=$2
          shift 2
          ;;
        -h|--help)
          usage
          exit 0
          ;;
        *)
          fail "unknown collect argument: $1"
          ;;
      esac
    done
    [[ -n "${namespace}" ]] || fail "collect requires --namespace"
    [[ -n "${pod}" ]] || fail "collect requires --pod"
    preflight
    collect_case "${namespace}" "${pod}"
    ;;
  view)
    case_dir=""
    while (($# > 0)); do
      case "$1" in
        --case)
          (($# >= 2)) || fail "--case requires a value"
          case_dir=$2
          shift 2
          ;;
        -h|--help)
          usage
          exit 0
          ;;
        *)
          fail "unknown view argument: $1"
          ;;
      esac
    done
    [[ -n "${case_dir}" ]] || fail "view requires --case"
    print_core_results "${case_dir}"
    ;;
  cleanup)
    (($# == 0)) || fail "cleanup does not accept arguments"
    cleanup_case
    ;;
  -h|--help|help)
    usage
    ;;
  *)
    usage >&2
    fail "unknown command: ${command}"
    ;;
esac
