#!/usr/bin/env python3
"""Verify Pod anomaly state and bounded evidence in real observability backends."""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import ipaddress
import json
import os
import re
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
TRACE_ID = re.compile(r"^[0-9a-fA-F]{32}$")


@dataclass(frozen=True)
class CoverageResult:
    backend: str
    coverage: str
    summary: str
    sample_count: int = 0
    trace_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class PodIdentity:
    namespace: str
    name: str
    uid: str
    pod_ip: str
    created_at: str


def load_catalog(path: Path = ROOT / "catalog.yaml") -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def run_kubectl_json(args: list[str], timeout: int = 20) -> dict[str, Any]:
    completed = subprocess.run(
        ["kubectl", *args, "-o", "json"], check=True, text=True,
        capture_output=True, timeout=timeout,
    )
    return json.loads(completed.stdout)


def _items(value: dict[str, Any]) -> list[dict[str, Any]]:
    return value.get("items", [value]) if isinstance(value, dict) else []


def resolve_workload_pods(case: dict[str, Any]) -> list[tuple[PodIdentity, dict[str, Any]]]:
    namespace = case["namespace"]
    if case.get("workload_kind") == "Pod":
        raw = run_kubectl_json(["-n", namespace, "get", "pod", case["workload_name"]])
        pods = [raw]
    else:
        raw = run_kubectl_json([
            "-n", namespace, "get", "pods", "-l", "app.kubernetes.io/name=workload",
        ])
        pods = raw.get("items", [])
    resolved = []
    for pod in pods:
        metadata, status = pod.get("metadata", {}), pod.get("status", {})
        resolved.append((PodIdentity(
            namespace=namespace,
            name=str(metadata.get("name") or ""),
            uid=str(metadata.get("uid") or ""),
            pod_ip=str(status.get("podIP") or ""),
            created_at=str(metadata.get("creationTimestamp") or ""),
        ), pod))
    return sorted(resolved, key=lambda pair: pair[0].created_at, reverse=True)


def resolve_driver_run_id(namespace: str) -> str:
    try:
        data = run_kubectl_json([
            "-n", namespace, "get", "pods", "-l", "app.kubernetes.io/name=traffic-driver",
        ])
        pods = [item for item in data.get("items", []) if item.get("status", {}).get("phase") == "Running"]
        pods.sort(key=lambda item: item.get("metadata", {}).get("creationTimestamp", ""), reverse=True)
        return str(pods[0].get("metadata", {}).get("uid") or "") if pods else ""
    except (subprocess.SubprocessError, ValueError, KeyError):
        return ""


def _container_facts(pod: dict[str, Any]) -> dict[str, Any]:
    statuses = pod.get("status", {}).get("containerStatuses", []) or []
    waiting, terminated_reasons, exit_codes = set(), set(), set()
    restarts = 0
    for status in statuses:
        restarts += int(status.get("restartCount") or 0)
        for state in (status.get("state", {}), status.get("lastState", {})):
            if state.get("waiting", {}).get("reason"):
                waiting.add(state["waiting"]["reason"])
            if state.get("terminated", {}).get("reason"):
                terminated_reasons.add(state["terminated"]["reason"])
            if state.get("terminated", {}).get("exitCode") is not None:
                exit_codes.add(int(state["terminated"]["exitCode"]))
    ready = next((item.get("status") == "True" for item in pod.get("status", {}).get("conditions", []) if item.get("type") == "Ready"), False)
    return {
        "phase": pod.get("status", {}).get("phase", ""),
        "waiting_reasons": sorted(waiting),
        "terminated_reasons": sorted(terminated_reasons),
        "terminated_exit_codes": sorted(exit_codes),
        "restarts": restarts,
        "ready": ready,
        "deletion_timestamp": bool(pod.get("metadata", {}).get("deletionTimestamp")),
        "finalizers": pod.get("metadata", {}).get("finalizers", []) or [],
    }


def evaluate_status_gate(pod: dict[str, Any], events: list[dict[str, Any]], gate: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    facts = _container_facts(pod)
    facts["event_reasons"] = sorted({str(item.get("reason") or "") for item in events if item.get("reason")})
    checks = []
    for key in ("phase", "waiting_reasons", "terminated_reasons", "terminated_exit_codes", "event_reasons", "finalizers"):
        if key in gate:
            actual = {facts["phase"]} if key == "phase" else set(facts[key])
            checks.append(bool(actual.intersection(set(gate[key]))))
    if "minimum_restarts" in gate:
        checks.append(facts["restarts"] >= int(gate["minimum_restarts"]))
    if "ready" in gate:
        checks.append(facts["ready"] is bool(gate["ready"]))
    if "deletion_timestamp" in gate:
        checks.append(facts["deletion_timestamp"] is bool(gate["deletion_timestamp"]))
    return bool(checks) and all(checks), facts


def _events(identity: PodIdentity) -> list[dict[str, Any]]:
    try:
        data = run_kubectl_json([
            "-n", identity.namespace, "get", "events", "--field-selector", f"involvedObject.uid={identity.uid}",
        ])
        return data.get("items", [])
    except (subprocess.SubprocessError, ValueError):
        return []


def _http_json(request: urllib.request.Request, timeout: float = 8.0,
               context: ssl.SSLContext | None = None) -> dict[str, Any]:
    with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
        return json.loads(response.read(2_000_000).decode("utf-8"))


def _safe_prom_value(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _prometheus_rows(base_url: str, query: str, end: int, start: int | None = None) -> list[dict[str, Any]]:
    if start is None:
        path = "/api/v1/query"
        params: dict[str, Any] = {"query": query, "time": end}
    else:
        path = "/api/v1/query_range"
        params = {"query": query, "start": start, "end": end, "step": 15}
    url = base_url.rstrip("/") + path + "?" + urllib.parse.urlencode(params)
    payload = _http_json(urllib.request.Request(url, method="GET"))
    return payload.get("data", {}).get("result", []) if payload.get("status") == "success" else []


def _pod_matchers(identity: PodIdentity) -> str:
    return f'namespace="{_safe_prom_value(identity.namespace)}",pod="{_safe_prom_value(identity.name)}"'


def query_prometheus(identity: PodIdentity, base_url: str, start: int, end: int, case_id: str = "") -> CoverageResult:
    if not base_url:
        return CoverageResult("prometheus", "error", "PROMETHEUS_URL is not configured")
    matchers = _pod_matchers(identity)
    query = ('{__name__=~"kube_pod_.*|container_(memory_working_set_bytes|cpu_usage_seconds_total)",'
             f'{matchers}}}')
    try:
        rows = _prometheus_rows(base_url, query, end)
        if not rows:
            return CoverageResult("prometheus", "empty", "0 exact pod series at window end")
        evidence_queries = {
            "c01": f'kube_pod_status_phase{{{matchers},phase="Pending"}} == 1',
            "c02": f'kube_pod_container_status_waiting_reason{{{matchers},reason=~"ErrImagePull|ImagePullBackOff"}} == 1',
            "c03": f'kube_pod_status_phase{{{matchers},phase="Pending"}} == 1',
            "c04": f'kube_pod_container_status_waiting_reason{{{matchers},reason="CreateContainerConfigError"}} == 1',
            "c05": f'kube_pod_status_phase{{{matchers},phase="Pending"}} == 1',
            "c06": f'kube_pod_container_status_restarts_total{{{matchers},container="app"}} > 0',
            "c07": f'kube_pod_container_status_restarts_total{{{matchers},container="app"}} > 0',
            "c08": f'kube_pod_container_status_last_terminated_reason{{{matchers},container="app",reason="OOMKilled"}} == 1',
            "c09": f'kube_pod_status_ready{{{matchers},condition="false"}} == 1',
            "c10": f'kube_pod_container_status_restarts_total{{{matchers},container="app"}} > 0',
            "c11": f'kube_pod_deletion_timestamp{{{matchers}}} > 0',
        }
        if case_id and case_id in evidence_queries:
            evidence = _prometheus_rows(base_url, evidence_queries[case_id], end)
            if not evidence:
                return CoverageResult("prometheus", "empty", f"exact Pod series exist but {case_id} anomaly metric is absent", len(rows))
            rows += evidence
        if case_id == "c08":
            limit_query = f'kube_pod_container_resource_limits{{{matchers},container="app",resource="memory",unit="byte"}} > 0'
            limit_rows = _prometheus_rows(base_url, limit_query, end)
            if not limit_rows:
                return CoverageResult("prometheus", "empty", "OOM reason exists but the workload memory limit series is absent", len(rows))
            rows += limit_rows
            memory_query = f'container_memory_working_set_bytes{{{matchers},container="app",image!=""}}'
            history = _prometheus_rows(base_url, memory_query, end, start)
            values = []
            for series in history:
                for sample in series.get("values", []):
                    try:
                        values.append(float(sample[1]))
                    except (IndexError, TypeError, ValueError):
                        pass
            if len(values) < 2 or max(values) <= min(values):
                return CoverageResult("prometheus", "empty", "OOM reason exists but bounded memory growth history is absent", len(rows))
            rows += history
        return CoverageResult("prometheus", "present", f"{len(rows)} exact Pod/anomaly series groups", len(rows))
    except Exception as exc:
        return CoverageResult("prometheus", "error", f"query failed: {type(exc).__name__}")


def _iso(epoch: int) -> str:
    return dt.datetime.fromtimestamp(epoch, tz=dt.timezone.utc).isoformat().replace("+00:00", "Z")


def _extract_trace_ids(value: Any) -> tuple[str, ...]:
    found: set[str] = set()
    def walk(item: Any) -> None:
        if isinstance(item, dict):
            for key, child in item.items():
                if str(key).lower().replace(".", "_") in {"trace_id", "traceid"} and TRACE_ID.fullmatch(str(child or "")):
                    found.add(str(child).lower())
                walk(child)
        elif isinstance(item, list):
            for child in item:
                walk(child)
        elif isinstance(item, str):
            found.update(match.lower() for match in re.findall(r"(?<![0-9a-fA-F])[0-9a-fA-F]{32}(?![0-9a-fA-F])", item))
    walk(value)
    return tuple(sorted(found))[:10]


def query_elasticsearch(identity: PodIdentity, case_run_id: str, base_url: str, start: int, end: int,
                        username: str = "", password: str = "", tls_verify: bool = True,
                        ca_cert: str = "") -> CoverageResult:
    if not base_url:
        return CoverageResult("elasticsearch", "error", "ELASTICSEARCH_URL is not configured")
    namespace_fields = ["kubernetes.namespace", "kubernetes.namespace_name", "kubernetes.namespace.name"]
    pod_fields = ["kubernetes.pod.name", "kubernetes.pod_name", "pod.name"]
    uid_fields = ["kubernetes.pod.uid", "kubernetes.pod_uid", "pod.uid"]
    should_terms = lambda fields, value: [{"term": {field: value}} for field in fields]
    identity_should = should_terms(uid_fields, identity.uid) + should_terms(pod_fields, identity.name)
    body: dict[str, Any] = {
        "size": 20,
        "sort": [{"@timestamp": {"order": "desc", "unmapped_type": "date"}}],
        "_source": ["@timestamp", "message", "trace_id", "span_id", "case_run_id", "kubernetes.pod.*", "kubernetes.namespace*"],
        "query": {"bool": {"filter": [
            {"range": {"@timestamp": {"gte": _iso(start), "lte": _iso(end)}}},
            {"bool": {"should": should_terms(namespace_fields, identity.namespace), "minimum_should_match": 1}},
            {"bool": {"should": identity_should, "minimum_should_match": 1}},
        ]}},
    }
    if case_run_id:
        body["query"]["bool"]["should"] = (
            should_terms(["case_run_id", "aiops.case_run_id"], case_run_id)
            + [{"match_phrase": {"message": case_run_id}}]
        )
        body["query"]["bool"]["minimum_should_match"] = 1
    headers = {"Content-Type": "application/json"}
    if username:
        token = base64.b64encode(f"{username}:{password}".encode()).decode()
        headers["Authorization"] = f"Basic {token}"
    request = urllib.request.Request(base_url.rstrip("/") + "/_search", data=json.dumps(body).encode(), headers=headers, method="POST")
    context = None
    if base_url.lower().startswith("https://"):
        if tls_verify:
            context = ssl.create_default_context(cafile=ca_cert or None)
        else:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
    try:
        payload = _http_json(request, context=context)
        hits = payload.get("hits", {}).get("hits", [])
        traces = _extract_trace_ids(hits)
        samples = [str(item.get("_source", {}).get("message") or "")[:240] for item in hits[:2]]
        summary = f"{len(hits)} bounded hits" + (f"; sample={samples[0]}" if samples and samples[0] else "")
        return CoverageResult("elasticsearch", "present" if hits else "empty", summary, len(hits), traces)
    except Exception as exc:
        return CoverageResult("elasticsearch", "error", f"query failed: {type(exc).__name__}")


def query_case_elasticsearch(case: dict[str, Any], identity: PodIdentity, case_run_id: str,
                             base_url: str, start: int, end: int, username: str = "",
                             password: str = "", tls_verify: bool = True,
                             ca_cert: str = "") -> CoverageResult:
    if case.get("runtime") and not case_run_id:
        return CoverageResult("elasticsearch", "error", "current Running traffic-driver Pod UID is unavailable")
    return query_elasticsearch(identity, case_run_id, base_url, start, end, username, password,
                               tls_verify, ca_cert)


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() not in {"0", "false", "no", "off"}


def _clickhouse_time(epoch: int) -> str:
    return dt.datetime.fromtimestamp(epoch, tz=dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def query_deepflow(identity: PodIdentity, start: int, end: int, namespace: str, selector: str) -> CoverageResult:
    if not identity.pod_ip:
        return CoverageResult("deepflow", "absent", "workload has no Pod IP; direct Pod flow is impossible")
    try:
        ipaddress.ip_address(identity.pod_ip)
    except ValueError:
        return CoverageResult("deepflow", "error", "invalid Pod IP")
    try:
        pods = run_kubectl_json(["-n", namespace, "get", "pods", "-l", selector]).get("items", [])
        running = [pod for pod in pods if pod.get("status", {}).get("phase") == "Running"]
        if not running:
            return CoverageResult("deepflow", "error", "ClickHouse pod was not found")
        clickhouse_pod = str(running[0].get("metadata", {}).get("name") or "")
        sql = (
            "SELECT toString(flow.time) AS time, IPv4NumToString(ip4_0) AS src_ip, "
            "IPv4NumToString(ip4_1) AS dst_ip, l7_protocol_str, request_resource, response_code, "
            "response_status, response_duration, trace_id, span_id FROM flow_log.l7_flow_log AS flow "
            f"WHERE flow.time >= toDateTime('{_clickhouse_time(start)}', 'UTC') "
            f"AND flow.time <= toDateTime('{_clickhouse_time(end)}', 'UTC') "
            f"AND (ip4_0 = '{identity.pod_ip}' OR ip4_1 = '{identity.pod_ip}') "
            "AND request_resource = '/work' "
            "ORDER BY (trace_id != '') DESC, flow.time DESC LIMIT 20 FORMAT JSON"
        )
        command = ["kubectl", "-n", namespace, "exec", clickhouse_pod]
        container = os.getenv("DEEPFLOW_CLICKHOUSE_CONTAINER", "")
        if container:
            command.extend(["-c", container])
        command.extend(["--", "clickhouse-client", "--query", sql])
        completed = subprocess.run(command, check=True, text=True, capture_output=True, timeout=25)
        payload = json.loads(completed.stdout)
        rows = payload.get("data", [])
        traces = _extract_trace_ids(rows)
        return CoverageResult("deepflow", "present" if rows else "absent", f"{len(rows)} direct Pod L7 rows", len(rows), traces)
    except Exception as exc:
        return CoverageResult("deepflow", "error", f"query failed: {type(exc).__name__}")


def query_tempo(identity: PodIdentity, trace_ids: Iterable[str], base_url: str) -> CoverageResult:
    valid = tuple(dict.fromkeys(trace.lower() for trace in trace_ids if TRACE_ID.fullmatch(trace)))[:5]
    if not valid:
        return CoverageResult("tempo", "absent", "no trace ID was discovered in logs or direct flows")
    if not base_url:
        return CoverageResult("tempo", "error", "TEMPO_URL is not configured")
    matched = 0
    for trace_id in valid:
        request = urllib.request.Request(base_url.rstrip("/") + "/api/traces/" + trace_id, method="GET")
        try:
            payload = _http_json(request)
            rendered = json.dumps(payload, ensure_ascii=False)
            if identity.name in rendered and "aiops-lab-workload" in rendered:
                matched += 1
        except urllib.error.HTTPError as exc:
            if exc.code != 404:
                return CoverageResult("tempo", "error", f"query failed: HTTP {exc.code}")
        except Exception as exc:
            return CoverageResult("tempo", "error", f"query failed: {type(exc).__name__}")
    return CoverageResult("tempo", "present" if matched else "absent", f"{matched}/{len(valid)} trace IDs matched Pod and service", matched, valid)


def correlated_trace_ids(logs: CoverageResult, flows: CoverageResult) -> tuple[str, ...]:
    """Return only trace IDs independently observed in both logs and direct Pod flows."""
    return tuple(sorted(set(logs.trace_ids).intersection(flows.trace_ids)))


def coverage_matches(expected: str, actual: CoverageResult) -> bool:
    return expected == actual.coverage


def _window(identity: PodIdentity, now: int) -> tuple[int, int]:
    try:
        created = int(dt.datetime.fromisoformat(identity.created_at.replace("Z", "+00:00")).timestamp())
    except (ValueError, TypeError):
        created = now - 900
    return max(created - 60, now - 3600), now


def verify_case(case: dict[str, Any]) -> tuple[bool, list[CoverageResult]]:
    try:
        pods = resolve_workload_pods(case)
    except Exception as exc:
        result = CoverageResult("kubernetes", "error", f"Pod lookup failed: {type(exc).__name__}")
        return False, [result]
    if not pods:
        result = CoverageResult("kubernetes", "empty", "no current workload Pod")
        return False, [result]
    identity, pod = pods[0]
    matched, facts = evaluate_status_gate(pod, _events(identity), case["status_gate"])
    results = [CoverageResult("kubernetes", "present" if matched else "empty", json.dumps(facts, ensure_ascii=False, separators=(",", ":")), 1)]
    now = int(time.time())
    start, end = _window(identity, now)
    run_id = resolve_driver_run_id(identity.namespace)
    prom = query_prometheus(identity, os.getenv("PROMETHEUS_URL", ""), start, end, case["id"])
    logs = query_case_elasticsearch(case, identity, run_id, os.getenv("ELASTICSEARCH_URL", ""), start, end,
                                    os.getenv("ELASTICSEARCH_USERNAME", ""), os.getenv("ELASTICSEARCH_PASSWORD", ""),
                                    _env_bool("ELASTICSEARCH_TLS_VERIFY", True), os.getenv("ELASTICSEARCH_CA_CERT", ""))
    flow = query_deepflow(identity, start, end, os.getenv("DEEPFLOW_NAMESPACE", "monitor"),
                          os.getenv("DEEPFLOW_CLICKHOUSE_SELECTOR", "app.kubernetes.io/name=clickhouse"))
    shared_traces = correlated_trace_ids(logs, flow)
    tempo = query_tempo(identity, shared_traces, os.getenv("TEMPO_URL", ""))
    results.extend([prom, logs, flow, tempo])
    by_backend = {item.backend: item for item in results}
    ok = all(coverage_matches(expected, by_backend[backend]) for backend, expected in case["coverage"].items())
    return ok, results


def _selected(catalog: dict[str, Any], ids: list[str]) -> list[dict[str, Any]]:
    cases = catalog["cases"]
    if not ids:
        return cases
    wanted = set(ids)
    selected = [case for case in cases if case["id"] in wanted]
    missing = wanted - {case["id"] for case in selected}
    if missing:
        raise ValueError("unknown case IDs: " + ",".join(sorted(missing)))
    return selected


def _print_table(cases: list[dict[str, Any]], reports: dict[str, list[CoverageResult]]) -> None:
    print("case backend        coverage expected samples summary")
    for case in cases:
        for result in reports.get(case["id"], []):
            expected = case["coverage"].get(result.backend, "-")
            summary = result.summary.replace("\n", " ")[:180]
            print(f"{case['id']:<4} {result.backend:<14} {result.coverage:<8} {expected:<8} {result.sample_count:<7} {summary}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", action="append", default=[], help="catalog ID such as c08; repeatable")
    parser.add_argument("--wait", action="store_true", help="retry until all gates pass or timeout")
    parser.add_argument("--timeout", type=int, default=None, help="override every catalog case timeout")
    args = parser.parse_args(argv)
    try:
        cases = _selected(load_catalog(), args.case)
        env_timeout = os.getenv("OBSERVABILITY_TIMEOUT_SECONDS")
        timeout_override = args.timeout if args.timeout is not None else (int(env_timeout) if env_timeout else None)
        started = time.monotonic()
        deadlines = {
            case["id"]: started + max(1, timeout_override if timeout_override is not None
                                      else int(case["timeout_seconds"]))
            for case in cases
        }
    except (OSError, TypeError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"configuration error: {exc}", file=sys.stderr)
        return 2
    reports: dict[str, list[CoverageResult]] = {}
    passing: set[str] = set()
    retry_delay = 1
    while True:
        passing.clear()
        for case in cases:
            ok, results = verify_case(case)
            reports[case["id"]] = results
            if ok:
                passing.add(case["id"])
        if len(passing) == len(cases) or not args.wait:
            break
        now = time.monotonic()
        waiting = [case["id"] for case in cases if case["id"] not in passing]
        if any(now >= deadlines[case_id] for case_id in waiting):
            break
        remaining = min(deadlines[case_id] - now for case_id in waiting)
        time.sleep(min(retry_delay, remaining))
        retry_delay = min(10, retry_delay * 2)
    _print_table(cases, reports)
    return 0 if len(passing) == len(cases) else 1


if __name__ == "__main__":
    raise SystemExit(main())
