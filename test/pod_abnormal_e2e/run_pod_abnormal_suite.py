#!/usr/bin/env python3
"""Serial pod-abnormal E2E suite runner.

Reads scenario aliases from a text file, prepares the matching manifest,
waits for the injected fault to settle, then invokes run_pod_abnormal_cases.py.
Each scenario is isolated by cleaning known E2E resources before and after it.
"""

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
from typing import Any, Dict, Iterable, List, Optional

try:
    import yaml
except ImportError:
    print("需要 pyyaml: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[1]
DEFAULT_CASES_FILE = ROOT / "cases.yaml"
DEFAULT_SCENARIOS_FILE = ROOT / "test.txt"
DEFAULT_MANIFEST_NAMESPACE = REPO_ROOT / "test/e2e/manifests/00-namespace.yaml"


@dataclass(frozen=True)
class SuiteCase:
    id: str
    name: str
    aliases: List[str]
    enabled: bool
    manual: bool
    manifest: Path
    namespace: str
    trigger: List[str]


def _repo_path(path: str) -> Path:
    raw = Path(path)
    if raw.is_absolute():
        return raw
    return (ROOT / raw).resolve()


def load_cases(path: Path) -> List[SuiteCase]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    defaults = data.get("defaults") or {}
    cases: List[SuiteCase] = []
    for item in data.get("cases") or []:
        manifest = item.get("manifest")
        if not manifest:
            continue
        cases.append(
            SuiteCase(
                id=str(item["id"]),
                name=str(item.get("name") or item["id"]),
                aliases=[str(alias).lower() for alias in item.get("aliases") or []],
                enabled=bool(item.get("enabled", True)),
                manual=bool(item.get("manual", False)),
                manifest=_repo_path(str(manifest)),
                namespace=str(item.get("namespace") or defaults.get("namespace") or "aiops-e2e"),
                trigger=[str(cmd) for cmd in item.get("trigger") or []],
            )
        )
    return cases


def load_requested_scenarios(path: Path) -> List[str]:
    text = path.read_text(encoding="utf-8")
    items: List[str] = []
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        for item in re.split(r"[\s,，、]+", line):
            item = item.strip().lower()
            if item:
                items.append(item)
    return items


def select_cases(cases: List[SuiteCase], requested: Iterable[str], include_manual: bool = False) -> List[SuiteCase]:
    selected: List[SuiteCase] = []
    missing: List[str] = []
    skipped_manual: List[str] = []

    for item in requested:
        matches = [
            case
            for case in cases
            if item == case.id.lower() or item in case.aliases
        ]
        if not matches:
            missing.append(item)
            continue
        for case in matches:
            if case.manual and not include_manual:
                skipped_manual.append(item)
                continue
            if case not in selected:
                selected.append(case)

    if missing:
        available = sorted({alias for case in cases for alias in [case.id.lower(), *case.aliases]})
        raise SystemExit("Unknown scenario: " + ", ".join(missing) + "\nAvailable: " + ", ".join(available))

    if skipped_manual:
        print("跳过 manual 场景: " + ", ".join(skipped_manual))
        print("原因: unknown/NodeLost 需要手动停止 kubelet 或隔离节点网络；如需只 apply 资源并测试，请加 --include-manual。")

    return selected


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
    result = subprocess.run(
        command,
        cwd=str(cwd),
        shell=shell,
        text=True,
        stdout=None,
        stderr=None,
    )
    if check and result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, command)
    return result


def cleanup_known_resources(cases: List[SuiteCase], dry_run: bool = False) -> None:
    namespaces = sorted({case.namespace for case in cases})
    for namespace in namespaces:
        run_command(
            ["kubectl", "-n", namespace, "patch", "pod", "terminating-stuck", "-p", '{"metadata":{"finalizers":null}}', "--type=merge"],
            dry_run=dry_run,
            check=False,
        )

    seen: set[Path] = set()
    for case in cases:
        if case.manifest in seen:
            continue
        seen.add(case.manifest)
        if case.manifest.exists():
            run_command(["kubectl", "delete", "-f", str(case.manifest), "--ignore-not-found=true", "--wait=false"], dry_run=dry_run, check=False)

    for namespace in namespaces:
        run_command(["kubectl", "-n", namespace, "delete", "pod", "-l", "e2e-test=true", "--ignore-not-found=true", "--wait=false"], dry_run=dry_run, check=False)
        run_command(["kubectl", "-n", namespace, "delete", "deployment", "-l", "e2e-test=true", "--ignore-not-found=true", "--wait=false"], dry_run=dry_run, check=False)


def apply_case(case: SuiteCase, dry_run: bool = False) -> None:
    if not case.manifest.exists():
        raise FileNotFoundError(f"manifest not found for {case.id}: {case.manifest}")
    run_command(["kubectl", "apply", "-f", str(DEFAULT_MANIFEST_NAMESPACE)], dry_run=dry_run)
    run_command(["kubectl", "apply", "-f", str(case.manifest)], dry_run=dry_run)
    for command in case.trigger:
        run_command(command, dry_run=dry_run, shell=True)


def run_quality_case(args: argparse.Namespace, case: SuiteCase, index: int, result_root: Path) -> None:
    scenario = case.aliases[0] if case.aliases else case.id
    output_dir = result_root / f"{index:02d}-{scenario}"
    command = [
        sys.executable,
        str(ROOT / "run_pod_abnormal_cases.py"),
        "--scenario",
        scenario,
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
    if case.manual:
        command.append("--include-disabled")
    run_command(command, dry_run=args.dry_run)


def write_suite_summary(result_root: Path, selected: List[SuiteCase], args: argparse.Namespace, started: float) -> None:
    summary: Dict[str, Any] = {
        "timestamp": datetime.now().isoformat(),
        "elapsed_seconds": round(time.time() - started, 1),
        "repeat": args.repeat,
        "concurrency": args.concurrency,
        "url": args.url,
        "question": args.question,
        "scenarios": [
            {
                "id": case.id,
                "name": case.name,
                "aliases": case.aliases,
                "manual": case.manual,
                "manifest": str(case.manifest),
                "trigger": case.trigger,
            }
            for case in selected
        ],
    }
    result_root.mkdir(parents=True, exist_ok=True)
    (result_root / "suite_stats.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run selected pod abnormal scenarios serially")
    parser.add_argument("--scenarios-file", default=str(DEFAULT_SCENARIOS_FILE), help="text file containing scenario aliases")
    parser.add_argument("--cases-file", default=str(DEFAULT_CASES_FILE), help="cases.yaml path")
    parser.add_argument("--url", default="http://10.2.0.48:30800", help="AIOps base URL")
    parser.add_argument("-n", "--repeat", type=int, default=50, help="repeat count per scenario")
    parser.add_argument("-c", "--concurrency", type=int, default=2, help="concurrency inside each scenario")
    parser.add_argument("--question", default="我的集群有什么问题", help="question sent to /ask")
    parser.add_argument("--timeout", type=int, default=1200, help="per request timeout seconds")
    parser.add_argument("--settle-seconds", type=int, default=20, help="seconds to wait after apply/trigger")
    parser.add_argument("--output-dir", default=None, help="suite result directory")
    parser.add_argument("--model", default=None, help="model name shown in child reports")
    parser.add_argument("--include-manual", action="store_true", help="include manual scenarios such as unknown")
    parser.add_argument("--skip-cleanup", action="store_true", help="do not clean known E2E resources between scenarios")
    parser.add_argument("--keep-last", action="store_true", help="do not clean the final scenario after the test")
    parser.add_argument("--dry-run", action="store_true", help="print commands without executing them")
    args = parser.parse_args()

    cases = load_cases(Path(args.cases_file))
    requested = load_requested_scenarios(Path(args.scenarios_file))
    selected = select_cases(cases, requested, include_manual=args.include_manual)
    if not selected:
        raise SystemExit("No runnable scenarios selected")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_root = Path(args.output_dir) if args.output_dir else REPO_ROOT / "testreports" / f"pod_abnormal_suite_{timestamp}"
    started = time.time()

    print("=" * 72)
    print("Pod Abnormal Serial Suite")
    print("=" * 72)
    print(f"Scenarios file: {args.scenarios_file}")
    print(f"Selected: {', '.join(case.aliases[0] if case.aliases else case.id for case in selected)}")
    print(f"Repeat: {args.repeat} | concurrency: {args.concurrency} | settle: {args.settle_seconds}s")
    print(f"Output: {result_root}")
    print("")

    try:
        for index, case in enumerate(selected, start=1):
            scenario = case.aliases[0] if case.aliases else case.id
            print("\n" + "=" * 72)
            print(f"[{index}/{len(selected)}] {scenario} - {case.name}")
            print("=" * 72)
            if not args.skip_cleanup:
                cleanup_known_resources(cases, dry_run=args.dry_run)
            apply_case(case, dry_run=args.dry_run)
            print(f"等待 {args.settle_seconds}s 让异常状态稳定...")
            if not args.dry_run and args.settle_seconds > 0:
                time.sleep(args.settle_seconds)
            run_quality_case(args, case, index, result_root)
            if not args.skip_cleanup and (index < len(selected) or not args.keep_last):
                cleanup_known_resources(cases, dry_run=args.dry_run)
    finally:
        write_suite_summary(result_root, selected, args, started)
        print(f"\nSuite report: {result_root}")


if __name__ == "__main__":
    main()
