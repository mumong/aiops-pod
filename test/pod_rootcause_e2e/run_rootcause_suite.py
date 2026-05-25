#!/usr/bin/env python3
"""Serial suite runner for root-cause precise E2E cases."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, List

from run_rootcause_cases import Case, load_cases, select_cases


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[1]
DEFAULT_CASES_FILE = ROOT / "cases.yaml"
DEFAULT_SCENARIOS_FILE = ROOT / "test.txt"
DEFAULT_NAMESPACE_MANIFEST = ROOT / "manifests/00-namespace.yaml"
LEGACY_E2E_MANIFEST_DIR = REPO_ROOT / "test/e2e/manifests"
ABNORMAL_POD_STATUSES = {
    "ContainerCreating",
    "CrashLoopBackOff",
    "CreateContainerConfigError",
    "CreateContainerError",
    "ErrImagePull",
    "Error",
    "Evicted",
    "Failed",
    "ImageInspectError",
    "ImagePullBackOff",
    "Pending",
    "Terminating",
    "Unknown",
}


@dataclass(frozen=True)
class SuiteCase:
    case: Case
    manifest: Path
    cleanup_manifest: Path
    trigger: List[str]
    cleanup: List[str]


def _repo_path(raw: str) -> Path:
    path = Path(raw)
    if path.is_absolute():
        return path
    return (ROOT / path).resolve()


def load_requested(path: Path) -> tuple[List[str], List[str]]:
    text = path.read_text(encoding="utf-8")
    cases: List[str] = []
    groups: List[str] = []
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        for item in re.split(r"[\s,，、]+", line):
            item = item.strip()
            if not item:
                continue
            if item.startswith("group:"):
                groups.append(item.split(":", 1)[1])
            else:
                cases.append(item)
    return cases, groups


def build_suite_cases(selected: Iterable[Case]) -> List[SuiteCase]:
    suite_cases: List[SuiteCase] = []
    for case in selected:
        manifest = _repo_path(case.manifest)
        suite_cases.append(
            SuiteCase(
                case=case,
                manifest=manifest,
                cleanup_manifest=manifest,
                trigger=case.suite_triggers,
                cleanup=case.suite_cleanup,
            )
        )
    return suite_cases


def run_command(
    command: List[str] | str,
    *,
    cwd: Path = REPO_ROOT,
    dry_run: bool = False,
    shell: bool = False,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    printable = command if isinstance(command, str) else " ".join(command)
    print(f"$ {printable}")
    if dry_run:
        return subprocess.CompletedProcess(command, 0, "", "")
    result = subprocess.run(command, cwd=str(cwd), shell=shell, text=True)
    if check and result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, command)
    return result


def list_resource_names(namespace: str, resource: str, label: str, dry_run: bool = False) -> List[str]:
    """Return resource/name strings for selector-based operations.

    Some kubectl versions do not support `kubectl patch <type> -l ...`.
    Listing first and patching concrete names is compatible and gives clearer
    cleanup logs for stuck Terminating pods.
    """
    command = ["kubectl", "-n", namespace, "get", resource, "-l", label, "-o", "name"]
    print(f"$ {' '.join(command)}")
    if dry_run:
        return []
    result = subprocess.run(command, cwd=str(REPO_ROOT), text=True, capture_output=True)
    if result.returncode != 0:
        if result.stderr:
            print(result.stderr.strip())
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def is_abnormal_pod_status(status: str) -> bool:
    """Return whether a `kubectl get pods -A` STATUS should be cleaned.

    The root-cause suite evaluates one injected fault at a time. Ad-hoc
    diagnostic pods created outside the test namespace can pollute global pod
    scans even if they are unrelated to the current case.
    """
    if status in ABNORMAL_POD_STATUSES:
        return True
    return status.startswith(("Init:", "PodInitializing"))


def list_abnormal_pods_outside_namespaces(excluded_namespaces: set[str], dry_run: bool = False) -> List[tuple[str, str, str]]:
    command = ["kubectl", "get", "pods", "-A", "--no-headers"]
    print(f"$ {' '.join(command)}")
    if dry_run:
        return []
    result = subprocess.run(command, cwd=str(REPO_ROOT), text=True, capture_output=True)
    if result.returncode != 0:
        if result.stderr:
            print(result.stderr.strip())
        return []

    pods: List[tuple[str, str, str]] = []
    for line in result.stdout.splitlines():
        parts = line.split(maxsplit=4)
        if len(parts) < 4:
            continue
        namespace, name, _ready, status = parts[:4]
        if namespace in excluded_namespaces:
            continue
        if is_abnormal_pod_status(status):
            pods.append((namespace, name, status))
    return pods


def cleanup_non_e2e_abnormal_pods(excluded_namespaces: set[str], dry_run: bool = False) -> None:
    pods = list_abnormal_pods_outside_namespaces(excluded_namespaces, dry_run=dry_run)
    if not pods:
        print(f"No abnormal pods outside namespaces: {', '.join(sorted(excluded_namespaces))}")
        return
    for namespace, name, status in pods:
        print(f"Cleanup non-e2e abnormal pod: {namespace}/{name} status={status}")
        run_command(
            [
                "kubectl",
                "-n",
                namespace,
                "delete",
                "pod",
                name,
                "--ignore-not-found=true",
                "--wait=false",
                "--force",
                "--grace-period=0",
            ],
            dry_run=dry_run,
            check=False,
        )


def cleanup_namespace(namespace: str, dry_run: bool = False) -> None:
    """Clear aiops-e2e test resources before every injected case."""
    run_command(
        ["kubectl", "-n", namespace, "patch", "pod", "terminating-stuck", "-p", '{"metadata":{"finalizers":null}}', "--type=merge"],
        dry_run=dry_run,
        check=False,
    )
    for label in ["rootcause-e2e=true", "e2e-test=true"]:
        for pod_name in list_resource_names(namespace, "pod", label, dry_run=dry_run):
            run_command(
                ["kubectl", "-n", namespace, "patch", pod_name, "-p", '{"metadata":{"finalizers":null}}', "--type=merge"],
                dry_run=dry_run,
                check=False,
            )
    # The root-cause suite assumes one active injected fault at a time.
    # Clean all known E2E labels before every case, including resources
    # manually applied from older pod_abnormal_e2e manifests.
    for resource in [
        "pod",
        "deployment",
        "replicaset",
        "statefulset",
        "daemonset",
        "job",
        "cronjob",
        "service",
        "configmap",
        "secret",
        "pvc",
    ]:
        for label in ["rootcause-e2e=true", "e2e-test=true"]:
            command = ["kubectl", "-n", namespace, "delete", resource, "-l", label, "--ignore-not-found=true", "--wait=false"]
            if resource == "pod":
                command.extend(["--force", "--grace-period=0"])
            run_command(command, dry_run=dry_run, check=False)
    run_command(
        ["kubectl", "-n", namespace, "wait", "--for=delete", "pod", "--all", "--timeout=60s"],
        dry_run=dry_run,
        check=False,
    )
    run_command(
        ["kubectl", "delete", "runtimeclass", "-l", "rootcause-e2e=true", "--ignore-not-found=true", "--wait=false"],
        dry_run=dry_run,
        check=False,
    )


def cleanup_known_resources(
    suite_cases: List[SuiteCase],
    dry_run: bool = False,
    cleanup_non_e2e_abnormal: bool = True,
) -> None:
    for item in suite_cases:
        for command in item.cleanup:
            run_command(command, dry_run=dry_run, shell=True, check=False)

    seen: set[Path] = set()
    for item in suite_cases:
        if item.cleanup_manifest in seen:
            continue
        seen.add(item.cleanup_manifest)
        if item.cleanup_manifest.exists():
            run_command(
                ["kubectl", "delete", "-f", str(item.cleanup_manifest), "--ignore-not-found=true", "--wait=false"],
                dry_run=dry_run,
                check=False,
            )
    # Also remove old pod_abnormal_e2e resources. Users often run those
    # manifests manually; leaving them around makes root-cause precision tests
    # ambiguous because the cluster contains multiple unrelated abnormal Pods.
    for legacy_manifest in sorted(LEGACY_E2E_MANIFEST_DIR.glob("*.yaml")):
        if legacy_manifest.name == "00-namespace.yaml" or legacy_manifest in seen:
            continue
        seen.add(legacy_manifest)
        run_command(
            ["kubectl", "delete", "-f", str(legacy_manifest), "--ignore-not-found=true", "--wait=false"],
            dry_run=dry_run,
            check=False,
        )

    namespaces = sorted({item.case.namespace for item in suite_cases})
    for namespace in namespaces:
        cleanup_namespace(namespace, dry_run=dry_run)
    if cleanup_non_e2e_abnormal:
        cleanup_non_e2e_abnormal_pods(set(namespaces), dry_run=dry_run)


def apply_case(item: SuiteCase, dry_run: bool = False) -> None:
    if not item.manifest.exists():
        raise FileNotFoundError(f"manifest not found: {item.manifest}")
    run_command(["kubectl", "apply", "-f", str(DEFAULT_NAMESPACE_MANIFEST)], dry_run=dry_run)
    run_command(["kubectl", "apply", "-f", str(item.manifest)], dry_run=dry_run)
    for command in item.trigger:
        run_command(command, dry_run=dry_run, shell=True)


def run_quality_case(args: argparse.Namespace, item: SuiteCase, index: int, result_root: Path) -> None:
    output_dir = result_root / item.case.group / f"{index:02d}-{item.case.id}"
    command = [
        sys.executable,
        str(ROOT / "run_rootcause_cases.py"),
        "--case",
        item.case.id,
        "-n",
        str(args.repeat),
        "-c",
        str(args.concurrency),
        "--question",
        args.question,
        "--url",
        args.url,
        "--timeout",
        str(args.timeout),
        "--output-dir",
        str(output_dir),
    ]
    if args.model:
        command.extend(["--model", args.model])
    run_command(command, dry_run=args.dry_run)


def _fmt_rate(value: Any) -> str:
    return "N/A" if value is None else f"{float(value):.1f}%"


def _fmt_minutes(value: Any) -> str:
    return "N/A" if value is None else f"{float(value) / 60:.1f}m"


def _case_result_dir(result_root: Path, item: SuiteCase, index: int) -> Path:
    return result_root / item.case.group / f"{index:02d}-{item.case.id}"


def _load_child_stats(result_dir: Path, case_id: str) -> dict[str, Any] | None:
    stats_path = result_dir / "stats.json"
    if not stats_path.exists():
        return None
    try:
        data = json.loads(stats_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"error": f"invalid stats.json: {exc}"}
    case_stats = (data.get("cases") or {}).get(case_id) or {}
    return {
        "runs": data.get("total_runs", 0),
        "success": data.get("success", 0),
        "failed": data.get("failed", 0),
        "root_cause_accuracy": case_stats.get("root_cause_accuracy"),
        "runbook_coverage": case_stats.get("runbook_coverage"),
        "evidence_completeness": case_stats.get("evidence_completeness"),
        "avg_mttr_seconds": case_stats.get("avg_mttr_seconds"),
    }


def _weighted_average(rows: List[dict[str, Any]], key: str) -> float | None:
    total_weight = 0
    total_value = 0.0
    for row in rows:
        value = row.get(key)
        weight = int(row.get("success") or row.get("runs") or 0)
        if value is None or weight <= 0:
            continue
        total_weight += weight
        total_value += float(value) * weight
    return total_value / total_weight if total_weight else None


def build_suite_summary_lines(rows: List[dict[str, Any]], args: argparse.Namespace, elapsed_seconds: float) -> List[str]:
    completed_rows = [row for row in rows if row["status"] == "completed"]
    failed_rows = [row for row in rows if row["status"] != "completed"]
    lines = [
        "# Pod RootCause Suite 汇总",
        "",
        f"- 完成 Case: {len(completed_rows)}/{len(rows)}",
        f"- 失败/未完成 Case: {len(failed_rows)}",
        f"- 总耗时: {_fmt_minutes(elapsed_seconds)}",
        f"- Repeat: {args.repeat}",
        f"- Concurrency: {args.concurrency}",
        f"- URL: {args.url}",
        f"- Question: {args.question}",
        "",
        "## Case 明细",
        "",
        "| Case | Group | 状态 | 成功运行 | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR | 错误 |",
        "|------|-------|------|----------|------------|----------------|------------|-----------|------|",
    ]
    for row in rows:
        lines.append(
            f"| {row['id']} | {row['group']} | {row['status']} | {row.get('success') or 0} | "
            f"{_fmt_rate(row.get('root_cause_accuracy'))} | {_fmt_rate(row.get('runbook_coverage'))} | "
            f"{_fmt_rate(row.get('evidence_completeness'))} | {_fmt_minutes(row.get('avg_mttr_seconds'))} | "
            f"{row.get('error') or '-'} |"
        )

    groups = sorted({row["group"] for row in rows})
    lines.extend([
        "",
        "## Group 平均",
        "",
        "| Group | 完成 Case | 成功运行 | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR |",
        "|-------|-----------|----------|------------|----------------|------------|-----------|",
    ])
    for group in groups:
        group_rows = [row for row in completed_rows if row["group"] == group]
        success = sum(int(row.get("success") or 0) for row in group_rows)
        lines.append(
            f"| {group} | {len(group_rows)} | {success} | "
            f"{_fmt_rate(_weighted_average(group_rows, 'root_cause_accuracy'))} | "
            f"{_fmt_rate(_weighted_average(group_rows, 'runbook_coverage'))} | "
            f"{_fmt_rate(_weighted_average(group_rows, 'evidence_completeness'))} | "
            f"{_fmt_minutes(_weighted_average(group_rows, 'avg_mttr_seconds'))} |"
        )

    total_success = sum(int(row.get("success") or 0) for row in completed_rows)
    lines.extend([
        "",
        "## 总平均",
        "",
        "| Scope | 完成 Case | 成功运行 | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR |",
        "|-------|-----------|----------|------------|----------------|------------|-----------|",
        f"| TOTAL | {len(completed_rows)} | {total_success} | "
        f"{_fmt_rate(_weighted_average(completed_rows, 'root_cause_accuracy'))} | "
        f"{_fmt_rate(_weighted_average(completed_rows, 'runbook_coverage'))} | "
        f"{_fmt_rate(_weighted_average(completed_rows, 'evidence_completeness'))} | "
        f"{_fmt_minutes(_weighted_average(completed_rows, 'avg_mttr_seconds'))} |",
        "",
    ])
    return lines


def write_suite_summary(
    result_root: Path,
    selected: List[SuiteCase],
    args: argparse.Namespace,
    started: float,
    outcomes: dict[str, dict[str, Any]] | None = None,
) -> None:
    elapsed_seconds = round(time.time() - started, 1)
    outcomes = outcomes or {}
    groups: dict[str, list[dict[str, Any]]] = {}
    rows: List[dict[str, Any]] = []
    for index, item in enumerate(selected, start=1):
        result_dir = _case_result_dir(result_root, item, index)
        child_stats = _load_child_stats(result_dir, item.case.id)
        outcome = outcomes.get(item.case.id) or {}
        status = str(outcome.get("status") or ("completed" if child_stats and not child_stats.get("error") else "not_run"))
        error = str(outcome.get("error") or (child_stats or {}).get("error") or "")
        row = {
            "id": item.case.id,
            "group": item.case.group,
            "name": item.case.name,
            "status": status,
            "manifest": str(item.manifest),
            "result_dir": str(result_dir),
            "error": error,
            **(child_stats or {}),
        }
        rows.append(row)
        groups.setdefault(item.case.group, []).append({
            "id": item.case.id,
            "name": item.case.name,
            "manifest": str(item.manifest),
            "result_dir": str(result_dir),
            "status": status,
        })

    summary: dict[str, Any] = {
        "timestamp": datetime.now().isoformat(),
        "elapsed_seconds": elapsed_seconds,
        "repeat": args.repeat,
        "concurrency": args.concurrency,
        "url": args.url,
        "question": args.question,
        "layout": "results are grouped by <result_root>/<group>/<NN-case-id>/",
        "selected_cases": len(rows),
        "completed_cases": sum(1 for row in rows if row["status"] == "completed"),
        "failed_cases": sum(1 for row in rows if row["status"] != "completed"),
        "groups": groups,
        "cases": rows,
    }
    result_root.mkdir(parents=True, exist_ok=True)
    (result_root / "suite_stats.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (result_root / "suite_summary.md").write_text(
        "\n".join(build_suite_summary_lines(rows, args, elapsed_seconds)) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run selected root-cause E2E cases serially")
    parser.add_argument("--scenarios-file", default=str(DEFAULT_SCENARIOS_FILE), help="text file containing case ids or group:<name>")
    parser.add_argument("--cases-file", default=str(DEFAULT_CASES_FILE), help="cases.yaml path")
    parser.add_argument("--url", default="http://10.2.0.48:30800", help="AIOps base URL")
    parser.add_argument("-n", "--repeat", type=int, default=50, help="repeat count per case")
    parser.add_argument("-c", "--concurrency", type=int, default=2, help="concurrency inside each case")
    parser.add_argument("--question", default="我的集群有什么问题", help="question sent to /ask")
    parser.add_argument("--timeout", type=int, default=1200, help="per request timeout seconds")
    parser.add_argument("--settle-seconds", type=int, default=25, help="seconds to wait after apply")
    parser.add_argument("--output-dir", default=None, help="suite result directory")
    parser.add_argument("--model", default=None, help="model name shown in child reports")
    parser.add_argument("--include-disabled", action="store_true", help="include disabled/manual cases")
    parser.add_argument("--skip-cleanup", action="store_true", help="do not clean resources between cases")
    parser.add_argument(
        "--skip-non-e2e-abnormal-cleanup",
        action="store_true",
        help="do not delete abnormal pods outside the selected test namespaces during cleanup",
    )
    parser.add_argument("--keep-last", action="store_true", help="do not clean the final case after the test")
    parser.add_argument("--dry-run", action="store_true", help="print commands without executing them")
    args = parser.parse_args()

    _, cases = load_cases(Path(args.cases_file))
    case_items, group_items = load_requested(Path(args.scenarios_file))
    selected_cases = select_cases(
        cases,
        case_selector=",".join(case_items) if case_items else None,
        group_selector=",".join(group_items) if group_items else None,
        include_disabled=args.include_disabled,
    )
    if not selected_cases:
        raise SystemExit("No runnable root-cause cases selected")
    selected = build_suite_cases(selected_cases)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_root = Path(args.output_dir) if args.output_dir else REPO_ROOT / "testreports" / f"pod_rootcause_suite_{timestamp}"
    started = time.time()
    outcomes: dict[str, dict[str, Any]] = {}

    print("=" * 72)
    print("Pod RootCause Serial Suite")
    print("=" * 72)
    print(f"Scenarios file: {args.scenarios_file}")
    print(f"Selected: {', '.join(item.case.id for item in selected)}")
    print(f"Repeat: {args.repeat} | concurrency: {args.concurrency} | settle: {args.settle_seconds}s")
    print(f"Output: {result_root}")

    try:
        for index, item in enumerate(selected, start=1):
            print("\n" + "=" * 72)
            print(f"[{index}/{len(selected)}] {item.case.id} - {item.case.name}")
            print("=" * 72)
            try:
                if not args.skip_cleanup:
                    cleanup_known_resources(
                        selected,
                        dry_run=args.dry_run,
                        cleanup_non_e2e_abnormal=not args.skip_non_e2e_abnormal_cleanup,
                    )
                apply_case(item, dry_run=args.dry_run)
                print(f"等待 {args.settle_seconds}s 让异常状态稳定...")
                if not args.dry_run and args.settle_seconds > 0:
                    time.sleep(args.settle_seconds)
                run_quality_case(args, item, index, result_root)
                outcomes[item.case.id] = {"status": "completed"}
            except Exception as exc:
                outcomes[item.case.id] = {"status": "failed", "error": str(exc)}
                print(f"Case failed, continue next: {item.case.id}: {exc}", file=sys.stderr)
            finally:
                if not args.skip_cleanup and (index < len(selected) or not args.keep_last):
                    cleanup_known_resources(
                        selected,
                        dry_run=args.dry_run,
                        cleanup_non_e2e_abnormal=not args.skip_non_e2e_abnormal_cleanup,
                    )
    finally:
        write_suite_summary(result_root, selected, args, started, outcomes=outcomes)
        print(f"\nSuite report: {result_root}")
    if any(outcome.get("status") == "failed" for outcome in outcomes.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
