import json
import sys
from pathlib import Path
from types import SimpleNamespace


DEMO_DIR = Path("test/aiops_quality_e2e").resolve()
if str(DEMO_DIR) not in sys.path:
    sys.path.insert(0, str(DEMO_DIR))

from evaluator import (  # noqa: E402
    EvidenceExpectation,
    EvidenceLaneScore,
    EvidenceScore,
    RootCauseExpectation,
    extract_root_claims,
    score_runbooks,
    score_evidence_lanes,
    score_evidence_contract,
    score_root_causes,
)
from run_quality_demo import (  # noqa: E402
    ARCHIVE_END,
    ARCHIVE_START,
    QUALITY_THRESHOLDS,
    SCORING_VERSION,
    DiagnosisResult,
    _parse_archive_stdout,
    _sse_events,
    _aggregate_runs,
    build_summary,
    build_console_report,
    default_output_dir,
    launch_protected_worker,
    load_scenarios,
    protected_worker_command,
    rescore_existing_report,
    run_diagnosis_once,
    select_scenarios,
)
import run_quality_demo as quality_demo  # noqa: E402


def _expectation(root_id, include_all, include_any=(), exclude_any=()):
    return RootCauseExpectation(
        id=root_id,
        include_all=tuple(include_all),
        include_any=tuple(include_any),
        exclude_any=tuple(exclude_any),
    )


def test_current_single_group_report_scores_only_root_conclusion():
    report = """
## 🕵️ 证据内容 · g1

证据中还检查过 liveness probe，但已经排除。

## 🎯 根因分析 · g1

### 因果链

`/work 内存持续增长 → OOMKilled`

### 根因结论

已确认根因：容器 64Mi memory limit 不足，最终 OOMKilled（Exit Code: 137）。
已经排除 liveness probe 故障。

## 📊 性能统计
"""
    expectation = _expectation(
        "oom",
        ["OOMKilled", "64Mi"],
        ["Exit Code: 137", "memory limit"],
        ["liveness probe"],
    )

    claims = extract_root_claims(report)
    score = score_root_causes([expectation], claims)

    assert len(claims) == 1
    assert claims[0].group == "g1"
    assert "证据中" not in claims[0].text
    assert score.passed is True
    assert score.recall == 1.0
    assert score.precision == 1.0


def test_multi_group_report_requires_every_expected_root_cause():
    report = """
## 🎯 根因分析 · g1
### 根因结论
Secret workload-input 缺少 unavailable-key，导致 CreateContainerConfigError。

## 🎯 根因分析 · g2
### 根因结论
应用内存持续增长并超过 64Mi 内存限制，触发 OOMKilled 和 Exit Code 137。
"""
    expectations = [
        _expectation("secret", ["Secret", "unavailable-key"], ["CreateContainerConfigError"]),
        _expectation("oom", ["OOMKilled", "64Mi"], ["Exit Code 137", "内存持续增长"]),
    ]

    score = score_root_causes(expectations, extract_root_claims(report))

    assert score.passed is True
    assert score.matched_count == 2
    assert score.expected_count == 2
    assert score.recall == 1.0
    assert score.precision == 1.0


def test_multiple_expected_roots_can_share_one_claim_section():
    report = """
## 🎯 根因分析 · g1
### 根因结论
同一应用同时存在 Secret unavailable-key 缺失，以及超过 64Mi 后触发的 OOMKilled。
"""
    expectations = [
        _expectation("secret", ["Secret", "unavailable-key"]),
        _expectation("oom", ["OOMKilled", "64Mi"]),
    ]

    score = score_root_causes(expectations, extract_root_claims(report))

    assert score.passed is True
    assert score.matched_count == 2
    assert score.diagnosed_claim_count == 1
    assert score.precision == 1.0


def test_unexpected_diagnosed_group_fails_precision_but_inconclusive_group_does_not():
    base = """
## 🎯 根因分析 · g1
### 根因结论
Secret workload-input 缺少 unavailable-key。
"""
    expectation = _expectation("secret", ["Secret", "unavailable-key"])
    unexpected = base + """
## 🎯 根因分析 · g2
### 根因结论
镜像地址错误导致 ImagePullBackOff。
"""
    inconclusive = base + """
## 🎯 根因分析 · g2
### 根因结论
证据不足，无法确认该组根因。
"""

    unexpected_score = score_root_causes([expectation], extract_root_claims(unexpected))
    inconclusive_score = score_root_causes([expectation], extract_root_claims(inconclusive))

    assert unexpected_score.passed is False
    assert unexpected_score.precision == 0.5
    assert unexpected_score.unexpected_claim_groups == ("g2",)
    assert inconclusive_score.passed is True
    assert inconclusive_score.precision == 1.0


def test_confirmed_root_cause_is_not_erased_by_secondary_unknown_detail():
    report = """
## 🎯 根因分析 · g1
### 根因结论
**已确认的根因**：Pod 引用了不存在的 unavailable-network，导致 Multus
返回 FailedCreatePodSandBox。

**证据不足部分**：无法确定该网络定义是未创建还是被误删。
"""
    expectation = _expectation(
        "missing-network",
        ["unavailable-network"],
        ["Multus", "FailedCreatePodSandBox"],
    )

    claims = extract_root_claims(report)
    score = score_root_causes([expectation], claims)

    assert claims[0].inconclusive is False
    assert score.passed is True


def test_confirmed_readiness_root_allows_unknown_dependency_identity():
    scenarios = load_scenarios(DEMO_DIR / "demo_cases.yaml")
    report = """
## 🎯 根因分析 · g1
### 根因结论
**已确认根因：** 应用依赖不可用导致健康检查端点 `/ready` 持续返回
HTTP 503，Pod 因此处于 NotReady。

具体哪个下游依赖服务不可用，现有证据不足。
"""

    score = score_root_causes(
        scenarios["c09"].expected_root_causes,
        extract_root_claims(report),
    )

    assert score.passed is True
    assert score.recall == 1.0
    assert score.precision == 1.0


def test_c09_wrong_readiness_path_is_not_scored_as_correct_root():
    scenario = load_scenarios(DEMO_DIR / "demo_cases.yaml")["c09"]
    reports = [
        """
## 🎯 根因分析 · g1
### 根因结论
已确认根因：Readiness Probe 配置了错误的路径 `/ready`，应用实际探测路径是
`/work`，该路径返回 HTTP 503。
""",
        """
## 🎯 根因分析 · g1
### 根因结论
已确认根因：依赖不可用导致 `/work` 返回 HTTP 503，Readiness Probe 探测该端点失败。
""",
    ]

    for report in reports:
        score = score_root_causes(
            scenario.expected_root_causes,
            extract_root_claims(report),
        )
        assert score.passed is False


def test_c08_root_accepts_real_oom_and_memory_unit_equivalents():
    scenario = load_scenarios(DEMO_DIR / "demo_cases.yaml")["c08"]
    reports = [
        """
## 🎯 根因分析 · g1
### 根因结论
已确认根因：/work 内存持续增长，突破 64 MiB 限制后导致 OOMKilled。
""",
        """
## 🎯 根因分析 · g1
### 根因结论
已确认根因：应用内存超出 64Mi 硬限制，内核 OOM Killer 终止进程，Exit Code 137。
""",
        """
## 🎯 根因分析 · g1
### 根因结论
已确认根因：容器限制为 67108864 bytes，/work 请求导致内存增长并因 OOM 被终止。
""",
    ]

    for report in reports:
        score = score_root_causes(
            scenario.expected_root_causes,
            extract_root_claims(report),
        )
        assert score.passed is True


def test_c08_root_does_not_accept_unconfirmed_oom_hypothesis():
    scenario = load_scenarios(DEMO_DIR / "demo_cases.yaml")["c08"]
    report = """
## 🎯 根因分析 · g1
### 根因结论
证据不足，可能是 64Mi 内存限制导致 OOM，也可能是探针失败。
"""

    score = score_root_causes(
        scenario.expected_root_causes,
        extract_root_claims(report),
    )

    assert score.passed is False


def test_c01_root_accepts_exact_selector_mismatch_without_repeating_event_reason():
    scenario = load_scenarios(DEMO_DIR / "demo_cases.yaml")["c01"]
    report = """
## 🎯 根因分析 · g1
### 根因结论
已确认根因为 Pod 的 NodeSelector 配置与集群节点标签不匹配。
Pod 要求 `aiops.lab/unavailable=true`，但集群中没有节点具备该标签。
"""

    score = score_root_causes(
        scenario.expected_root_causes,
        extract_root_claims(report),
    )

    assert score.passed is True


def test_c01_missing_selector_label_is_not_misread_as_a_negated_root():
    scenario = load_scenarios(DEMO_DIR / "demo_cases.yaml")["c01"]
    report = """
## 🎯 根因分析 · g1
### 根因结论
已确认根因：所有节点均缺乏标签 `aiops.lab/unavailable`，因此 Pod 的
nodeSelector 无法匹配任何节点并持续 Pending。
"""

    score = score_root_causes(scenario.expected_root_causes, extract_root_claims(report))

    assert score.passed is True


def test_c04_secret_key_reference_error_real_wording_is_accepted():
    scenario = load_scenarios(DEMO_DIR / "demo_cases.yaml")["c04"]
    report = """
## 🎯 根因分析 · g1
### 根因结论
已确认根因为 Secret 键名引用错误：Pod 请求 `unavailable-key`，但该 Secret
实际数据中仅包含 `available-key`，导致 Kubelet 无法注入配置。
"""

    score = score_root_causes(scenario.expected_root_causes, extract_root_claims(report))

    assert score.passed is True


def test_c06_structured_exit_code_and_confirmed_direct_root_are_accepted():
    scenario = load_scenarios(DEMO_DIR / "demo_cases.yaml")["c06"]
    report = """
## 🎯 根因分析 · g1
### 根因结论
**证据不足**以定位具体代码缺陷，但现有证据强有力地证实了根因现象为：
应用处理 `/work` 时发生运行时错误并以 `exit_code: 2` 主动退出。
"""

    claims = extract_root_claims(report)
    score = score_root_causes(scenario.expected_root_causes, claims)

    assert claims[0].inconclusive is False
    assert score.passed is True


def test_c10_accepts_liveness_http_500_without_requiring_repeated_path():
    scenario = load_scenarios(DEMO_DIR / "demo_cases.yaml")["c10"]
    report = """
## 🎯 根因分析 · g1
### 根因结论
已确认根因：应用 Liveness Probe 持续返回 HTTP 500，Kubelet 因探针失败
终止容器并触发 CrashLoopBackOff。
"""

    score = score_root_causes(scenario.expected_root_causes, extract_root_claims(report))

    assert score.passed is True


def test_c10_does_not_accept_oom_or_probe_timeout_as_the_root():
    scenario = load_scenarios(DEMO_DIR / "demo_cases.yaml")["c10"]
    reports = [
        """
## 🎯 根因分析 · g1
### 根因结论
已确认根因为 96Mi 内存限制过低触发 OOM，Liveness Probe 返回 HTTP 500
只是容器退出后的伴随现象。
""",
        """
## 🎯 根因分析 · g1
### 根因结论
已确认根因：Liveness Probe 超时后杀死容器，当前未发现 HTTP 500 或 `/health`
响应作为支撑。
""",
    ]

    for report in reports:
        score = score_root_causes(scenario.expected_root_causes, extract_root_claims(report))
        assert score.passed is False


def test_c10_secondary_unconfirmed_oom_detail_does_not_override_direct_root():
    scenario = load_scenarios(DEMO_DIR / "demo_cases.yaml")["c10"]
    report = """
## 🎯 根因分析 · g1
### 根因结论
**已确认的直接根因：** Liveness Probe 持续收到 HTTP 状态码 500，Kubelet
因此终止容器并触发重启。

**未确认的业务根因：** 当前存在 96Mi 内存硬限制，但没有证据证明发生
OOMKilled；它不改变上述直接根因。
"""

    score = score_root_causes(scenario.expected_root_causes, extract_root_claims(report))

    assert score.passed is True
    assert score.matches[0].conflicts == ()


def test_confirmed_finalizer_root_is_not_negated_by_missing_oom_evidence():
    scenario = load_scenarios(DEMO_DIR / "demo_cases.yaml")["c11"]
    report = """
## 🎯 根因分析 · g1
### 根因结论
1. **确认现象根因（Terminating 卡死）**：Pod 滞留 Terminating 的直接原因是
自定义 Finalizer `aiops.lab/hold` 未被移除，删除流程因此无法完成。

2. **说明未知项（应用为何崩溃）**：缺乏 OOMKilled 指标，无法确认 Exit 137
是内存耗尽还是外部信号，但不影响上述 finalizer 根因。
"""

    claims = extract_root_claims(report)
    score = score_root_causes(scenario.expected_root_causes, claims)

    assert claims[0].inconclusive is False
    assert score.matches[0].conflicts == ()
    assert score.passed is True


def test_compact_chinese_negation_does_not_create_false_conflict():
    expectation = _expectation(
        "liveness-probe-500",
        ["liveness", "/health"],
        ["HTTP 500"],
        ["OOMKilled"],
    )
    report = """
## 🎯 根因分析 · g1
### 根因结论
已确认根因：Liveness Probe `/health` 返回 HTTP 500，并非 OOMKilled。
"""

    score = score_root_causes([expectation], extract_root_claims(report))

    assert score.passed is True
    assert score.matches[0].conflicts == ()


def test_wrong_probe_path_remains_a_root_cause_mismatch():
    expectation = _expectation(
        "liveness-probe-500",
        ["liveness", "/health"],
        ["HTTP 500"],
        ["OOMKilled"],
    )
    report = """
## 🎯 根因分析 · g1
### 根因结论
已确认根因：Liveness Probe `/healthz` 返回 HTTP 500，且非 OOMKilled。
"""

    score = score_root_causes([expectation], extract_root_claims(report))

    assert score.passed is False
    assert score.matches[0].missing_all == ("/health",)
    assert score.matches[0].conflicts == ()


def test_root_level_insufficient_evidence_remains_inconclusive():
    report = """
## 🎯 根因分析 · g1
### 根因结论
证据不足，无法确认该组根因；可能是 OOMKilled，也可能是探针失败。
"""
    expectation = _expectation("oom", ["OOMKilled"])

    claims = extract_root_claims(report)
    score = score_root_causes([expectation], claims)

    assert claims[0].inconclusive is True
    assert score.passed is False
    assert score.diagnosed_claim_count == 0


def test_evidence_completeness_sums_lane_plan_counts():
    score = score_evidence_lanes(
        [
            EvidenceLaneScore("g1", collected=6, planned=6),
            EvidenceLaneScore("g2", collected=6, planned=7),
        ],
        source="fixture",
    )

    assert score.collected == 12
    assert score.planned == 13
    assert score.completeness == 12 / 13


def test_archive_output_prefers_per_lane_files_over_top_level_compatibility_file():
    top = json.dumps({"plan_total": 99, "plan_collected": 0})
    g1 = json.dumps({"plan_total": 6, "plan_collected": 6})
    g2 = json.dumps({"plan_total": 7, "plan_collected": 6})
    stdout = (
        f"{ARCHIVE_START}/tmp/archive/run/node_outputs/evidence.full.json\n{top}\n{ARCHIVE_END}\n"
        f"{ARCHIVE_START}/tmp/archive/run-g1/node_outputs/evidence.full.json\n{g1}\n{ARCHIVE_END}\n"
        f"{ARCHIVE_START}/tmp/archive/run-g2/node_outputs/evidence.full.json\n{g2}\n{ARCHIVE_END}\n"
    )

    lanes = _parse_archive_stdout(stdout)
    score = score_evidence_lanes(lanes, source="fixture")

    assert [lane.lane for lane in lanes] == ["run-g1", "run-g2"]
    assert score.collected == 12
    assert score.planned == 13


def test_sse_parser_keeps_run_id_final_answer_and_metrics():
    lines = [
        "event: run_start",
        'data: {"run_id":"run-1"}',
        "",
        "event: final",
        'data: {"run_id":"run-1","answer":"## 根因","metrics":{"evidence_completeness":{"collected":2,"planned":3}}}',
        "",
    ]

    events, raw = _sse_events(lines)

    assert events[0] == {"type": "run_start", "run_id": "run-1"}
    assert events[1]["type"] == "final"
    assert events[1]["answer"] == "## 根因"
    assert "event: final" in raw


def test_protected_worker_command_pins_generated_output_directory(tmp_path):
    output_dir = tmp_path / "report"

    command = protected_worker_command(
        ["--scenario", "c05,c09", "-n", "5"],
        output_dir,
    )

    assert command[0] == sys.executable
    assert command[1] == str((DEMO_DIR / "run_quality_demo.py").resolve())
    assert command[-2:] == ["--output-dir", str(output_dir)]


def test_protected_worker_command_preserves_explicit_output_directory(tmp_path):
    explicit = tmp_path / "explicit"

    command = protected_worker_command(
        ["--scenario", "c05", f"--output-dir={explicit}"],
        tmp_path / "ignored",
    )

    assert command.count("--output-dir") == 0
    assert f"--output-dir={explicit}" in command


def test_launcher_detaches_worker_and_redirects_output(monkeypatch, tmp_path):
    captured = {}

    class FakeProcess:
        pid = 4321

    def fake_popen(command, **kwargs):
        captured["command"] = command
        captured["kwargs"] = kwargs
        return FakeProcess()

    monkeypatch.setattr(quality_demo.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(quality_demo, "_follow_protected_worker", lambda *args: 0)

    result = launch_protected_worker(tmp_path, ["--scenario", "c05"])

    assert result == 0
    assert captured["kwargs"]["start_new_session"] is True
    assert captured["kwargs"]["stdin"] is quality_demo.subprocess.DEVNULL
    assert captured["kwargs"]["stderr"] is quality_demo.subprocess.STDOUT
    assert captured["kwargs"]["env"][quality_demo.PROTECTED_WORKER_ENV] == "1"
    assert captured["kwargs"]["env"][quality_demo.PROTECTED_STATUS_ENV] == str(
        tmp_path / quality_demo.RUNNER_STATUS_NAME
    )


def test_protected_worker_publishes_completion_status(monkeypatch, tmp_path):
    status_path = tmp_path / "runner.status.json"
    monkeypatch.setenv(quality_demo.PROTECTED_STATUS_ENV, str(status_path))
    monkeypatch.setattr(quality_demo, "main", lambda: None)

    quality_demo._protected_worker_entrypoint()

    status = json.loads(status_path.read_text(encoding="utf-8"))
    assert status["status"] == "completed"
    assert status["exit_code"] == 0
    assert status["pid"] > 0


def test_demo_contract_contains_all_isolated_catalog_scenarios():
    scenarios = load_scenarios(DEMO_DIR / "demo_cases.yaml")

    assert [s.id for s in select_scenarios(scenarios, "all")] == [f"c{index:02d}" for index in range(1, 12)]
    assert len(scenarios) == 28
    assert all(scenario.members == (scenario.id,) for scenario in scenarios.values())
    assert len(scenarios["c04"].expected_root_causes) == 1
    assert scenarios["c04"].anomaly_type == "ConfigError"
    assert scenarios["c04"].fault_scenario == "Secret key unavailable-key 缺失"
    assert scenarios["c04"].expected_runbooks == ("pod-config-error",)
    assert sum(item.weight for item in scenarios["c04"].expected_evidence) == 6
    assert sum(item.weight for item in scenarios["c08"].expected_evidence) == 8
    assert all(scenario.expected_evidence for scenario in scenarios.values())
    assert scenarios["c10"].expected_runbooks == (
        "pod-notready-probe-failed",
        "pod-crashloop-runtime",
    )


def test_fixed_evidence_contract_scores_only_canonical_tool_facts():
    scenarios = load_scenarios(DEMO_DIR / "demo_cases.yaml")
    payload = {
        "plan_total": 99,
        "plan_collected": 99,
        "llm_analysis": "这段模型文字不能计分：OOMKilled 64Mi working set /work",
        "tool_data": [
            {
                "tool": "kubectl_describe",
                "semantic_success": True,
                "fact_ledger": {
                    "records": [
                        {
                            "fact_id": "fact-oom",
                            "dimension": "kubernetes",
                            "attribute": "container.last_terminated_reason",
                            "value": {"reason": "OOMKilled"},
                        },
                        {
                            "fact_id": "fact-exit",
                            "dimension": "kubernetes",
                            "attribute": "container.last_exit_code",
                            "value": {"exit_code": 137},
                        },
                        {
                            "fact_id": "fact-limit",
                            "dimension": "kubernetes",
                            "attribute": "container.resource_limit.memory",
                            "value": {"value": "64Mi"},
                        },
                    ]
                },
            },
            {
                "tool": "execute_pod_promql",
                "semantic_success": True,
                "fact_ledger": {
                    "records": [
                        {
                            "fact_id": "fact-memory",
                            "dimension": "metrics",
                            "attribute": "container_memory_working_set_bytes",
                            "value": "61972480",
                            "metadata": {
                                "sample_count": 20,
                                "trend_evaluable": True,
                                "stats": {"first": 30515200, "last": 61972480},
                            },
                        }
                    ]
                },
            },
            {
                "tool": "query_pod_logs",
                "semantic_success": True,
                "fact_ledger": {
                    "records": [
                        {
                            "fact_id": "fact-log-1",
                            "dimension": "logging",
                            "attribute": "log.message",
                            "value": '{"path":"/work","allocated_mib":2,"trace_id":"abc123"}',
                        },
                        {
                            "fact_id": "fact-log-2",
                            "dimension": "logging",
                            "attribute": "log.message",
                            "value": '{"path":"/work","allocated_mib":48,"trace_id":"def456"}',
                        },
                    ]
                },
            },
            {
                "tool": "query_pod_tracing",
                "semantic_success": True,
                "fact_ledger": {
                    "records": [
                        {
                            "fact_id": "fact-trace",
                            "dimension": "tracing",
                            "attribute": "l7_flow",
                            "value": {"request_resource": "/work", "response_code": 200},
                        }
                    ]
                },
            },
        ],
    }

    score = score_evidence_contract(
        scenarios["c08"].expected_evidence,
        [("/archive/run-g1/evidence.full.json", payload)],
    )

    assert score.mode == "fixed_contract"
    assert score.collected == 8
    assert score.planned == 8
    assert score.completeness == 1.0
    assert all(item["matched"] for item in score.matches)


def test_fixed_evidence_contract_does_not_accept_plan_or_llm_prose_as_evidence():
    expectation = EvidenceExpectation(
        id="oom",
        description="OOM terminal state",
        weight=2,
        dimensions=("kubernetes",),
        include_all=("OOMKilled",),
    )
    payload = {
        "plan_total": 1,
        "plan_collected": 1,
        "llm_analysis": "已确认 OOMKilled",
        "evidence_inventory": [{"description": "OOMKilled", "collected": True}],
        "tool_data": [],
    }

    score = score_evidence_contract([expectation], [("archive", payload)])

    assert score.collected == 0
    assert score.planned == 2
    assert score.completeness == 0.0


def test_fixed_evidence_contract_does_not_count_successful_empty_query():
    expectation = EvidenceExpectation(
        id="memory",
        description="memory metric",
        dimensions=("metrics",),
        include_all=("container_memory_working_set_bytes",),
    )
    payload = {
        "tool_data": [
            {
                "tool": "execute_pod_promql",
                "semantic_success": True,
                "data": json.dumps(
                    {
                        "coverage": "empty",
                        "counts": {"matched": 0, "returned": 0},
                        "query_ref": {"promql": "container_memory_working_set_bytes{pod='x'}"},
                    }
                ),
            }
        ]
    }

    score = score_evidence_contract([expectation], [("archive", payload)])

    assert score.completeness == 0.0


def test_all_selector_expands_only_ordered_isolated_cnn_scenarios():
    scenarios = load_scenarios(DEMO_DIR / "demo_cases.yaml")

    selected = select_scenarios(scenarios, "all")

    assert [scenario.id for scenario in selected] == [f"c{index:02d}" for index in range(1, 12)]
    assert [scenario.id for scenario in select_scenarios(scenarios, "c08,c04")] == ["c08", "c04"]


def test_default_output_dir_contains_scenario_and_timestamp():
    scenarios = load_scenarios(DEMO_DIR / "demo_cases.yaml")

    single = default_output_dir([scenarios["c04"]], timestamp="20260901_120000")
    full = default_output_dir(
        select_scenarios(scenarios, "all"), timestamp="20260901_120000"
    )

    assert single.name == "aiops_quality_c04_20260901_120000"
    assert full.name == "aiops_quality_all_20260901_120000"


def test_console_report_is_anomaly_oriented_and_contains_four_metrics(tmp_path):
    stats = {
        "total_elapsed_seconds": 55.5,
        "scenarios": [
            {
                "id": "c04",
                "name": "CreateContainerConfigError：Secret key 缺失",
                "anomaly_type": "ConfigError",
                "fault_scenario": "Secret key unavailable-key 缺失",
                "expected_runbooks": ["pod-config-error"],
                "runs": [
                    {
                        "run_index": 1,
                        "success": True,
                        "run_id": "run-1",
                        "elapsed_seconds": 55.5,
                        "root_cause": {
                            "passed": True,
                            "matched_count": 1,
                            "expected_count": 1,
                        },
                        "runbook": {
                            "passed": True,
                            "matched": ["pod-config-error"],
                            "expected": ["pod-config-error"],
                        },
                        "evidence": {
                            "collected": 4,
                            "planned": 7,
                            "completeness": 4 / 7,
                        },
                    }
                ],
            }
        ],
    }

    report = build_console_report(stats, tmp_path)

    assert "AIOps 异常 Case E2E 质量报告（盲测模式）" in report
    assert "| c04 | ConfigError | Secret key unavailable-key 缺失 | pod-config-error |" in report
    assert "根因准确率" in report
    assert "根因匹配" not in report
    assert "根因召回" not in report
    assert "根因精确率" not in report
    assert "Runbook 覆盖率" in report
    assert "证据完整度" in report
    assert "57.1% (4/7)" in report
    assert "MTTR" in report


def test_markdown_summary_uses_one_root_cause_accuracy_column():
    stats = {
        "scenarios": [
            {
                "id": "c04",
                "runs": [
                    {
                        "success": True,
                        "run_id": "run-1",
                        "elapsed_seconds": 60.0,
                        "root_cause": {
                            "passed": True,
                            "matched_count": 1,
                            "expected_count": 1,
                            "recall": 1.0,
                            "precision": 1.0,
                        },
                        "runbook": {
                            "matched": ["pod-config-error"],
                            "expected": ["pod-config-error"],
                            "coverage": 1.0,
                        },
                        "evidence": {
                            "collected": 7,
                            "planned": 7,
                            "completeness": 1.0,
                        },
                    }
                ],
            }
        ]
    }

    report = build_summary(stats)

    assert "| 场景 | 运行 | 状态 | 根因准确率 | Runbook |" in report
    assert "| c04 | 1 | ✅ | 100.0% | 100.0% |" in report
    assert "根因匹配" not in report
    assert "根因召回" not in report
    assert "根因精确率" not in report


def test_percentage_quality_acceptance_thresholds_are_seventy_percent(tmp_path):
    runs = []
    for index in range(10):
        passed = index < 7
        runs.append(
            {
                "run_index": index + 1,
                "success": True,
                "run_id": f"run-{index + 1}",
                "elapsed_seconds": 60.0,
                "root_cause": {
                    "passed": passed,
                    "matched_count": int(passed),
                    "expected_count": 1,
                    "recall": float(passed),
                    "precision": float(passed),
                },
                "runbook": {
                    "passed": passed,
                    "matched": ["pod-config-error"] if passed else [],
                    "expected": ["pod-config-error"],
                    "coverage": float(passed),
                },
                "evidence": {
                    "collected": 7,
                    "planned": 10,
                    "completeness": 0.7,
                },
            }
        )
    stats = {
        "total_elapsed_seconds": 600.0,
        "scenarios": [
            {
                "id": "c04",
                "name": "ConfigError",
                "anomaly_type": "ConfigError",
                "fault_scenario": "Secret key 缺失",
                "expected_runbooks": ["pod-config-error"],
                "runs": runs,
            }
        ],
    }

    report = build_console_report(stats, tmp_path)

    assert QUALITY_THRESHOLDS["root_cause_accuracy"] == 0.7
    assert QUALITY_THRESHOLDS["runbook_coverage"] == 0.7
    assert QUALITY_THRESHOLDS["evidence_completeness"] == 0.7
    assert "| 根因准确率 | >= 70% | 70.0% | ✅ |" in report
    assert "| Runbook 覆盖率 | >= 70% | 70.0% | ✅ |" in report
    assert "| 证据完整度 | >= 70% | 70.0% | ✅ |" in report


def test_diagnosis_request_retry_preserves_failed_attempt_and_scores_success(
    tmp_path, monkeypatch
):
    scenario = load_scenarios(DEMO_DIR / "demo_cases.yaml")["c04"]
    calls = []

    def fake_diagnose(*args, live_path, raw_path, **kwargs):
        attempt = len(calls) + 1
        calls.append(attempt)
        live_path.write_text(f"attempt={attempt}\n", encoding="utf-8")
        if attempt == 1:
            raw_path.write_text(
                'event: run_start\ndata: {"run_id":"failed-run-1"}\n',
                encoding="utf-8",
            )
            raise TimeoutError("transient timeout")
        raw_path.write_text(
            'event: final\ndata: {"run_id":"successful-run-2"}\n',
            encoding="utf-8",
        )
        return DiagnosisResult(
            run_id="successful-run-2",
            answer="""
## 🎯 根因分析 · g1
### 根因结论
已确认根因：Secret 缺少 unavailable-key，触发 CreateContainerConfigError。
""",
            metrics={},
            elapsed_seconds=42.0,
            events=(),
            raw_sse="",
        )

    monkeypatch.setattr(quality_demo, "diagnose", fake_diagnose)
    monkeypatch.setattr(
        quality_demo,
        "evidence_archive_from_kubectl",
        lambda *args, **kwargs: (
            EvidenceScore(2, 3, 2 / 3, (), "fixture_plan"),
            [],
        ),
    )
    monkeypatch.setattr(quality_demo.time, "sleep", lambda seconds: None)
    args = SimpleNamespace(
        url="http://example.invalid",
        timeout=1200,
        live_mode="compact",
        request_attempts=2,
        retry_backoff_seconds=30.0,
        aiops_namespace="aiops",
        aiops_target="deployment/aiops-copilot",
        aiops_container="aiops-copilot",
        archive_root="/tmp/aiops/reports/context_archives",
    )

    scored = run_diagnosis_once(
        run_index=1,
        repeat=1,
        scenario=scenario,
        scenario_dir=tmp_path,
        args=args,
    )

    run_dir = tmp_path / "run-01-successful-run-2"
    assert calls == [1, 2]
    assert scored["success"] is True
    assert scored["root_cause"]["passed"] is True
    assert scored["evidence"]["source"] == "fixture_plan"
    assert scored["evidence"]["collected"] == 2
    assert scored["evidence"]["planned"] == 3
    assert scored["evidence_plan_audit"] == scored["evidence"]
    assert scored["evidence_contract_audit"]["mode"] == "fixed_contract"
    assert scored["request_attempt_count"] == 2
    assert scored["request_attempt_failures"][0]["run_id"] == "failed-run-1"
    assert (run_dir / "attempt-01" / "error.txt").exists()
    assert (run_dir / "attempt-02" / "raw.sse").exists()
    assert (run_dir / "live.log").read_text(encoding="utf-8") == "attempt=2\n"


def test_evidence_summary_uses_arithmetic_mean_of_successful_run_rates(tmp_path):
    rates = [(4, 5), (6, 9), (5, 7), (5, 8)]
    runs = [
        {
            "run_index": index,
            "success": True,
            "run_id": f"run-{index}",
            "elapsed_seconds": 60.0,
            "root_cause": {
                "passed": True,
                "matched_count": 1,
                "expected_count": 1,
                "recall": 1.0,
                "precision": 1.0,
            },
            "runbook": {
                "passed": True,
                "matched": ["pod-config-error"],
                "expected": ["pod-config-error"],
                "coverage": 1.0,
            },
            "evidence": {
                "collected": collected,
                "planned": planned,
                "completeness": collected / planned,
            },
        }
        for index, (collected, planned) in enumerate(rates, start=1)
    ]
    stats = {
        "total_elapsed_seconds": 240.0,
        "scenarios": [
            {
                "id": "c04",
                "name": "ConfigError",
                "anomaly_type": "ConfigError",
                "fault_scenario": "Secret key 缺失",
                "expected_runbooks": ["pod-config-error"],
                "runs": runs,
            }
        ],
    }

    aggregate = _aggregate_runs(runs)
    console = build_console_report(stats, tmp_path)
    markdown = build_summary(stats)

    expected = sum(collected / planned for collected, planned in rates) / len(rates)
    assert aggregate["evidence_completeness"] == expected
    assert aggregate["evidence_completeness"] != 20 / 29
    assert "70.1%" in console
    assert "70.1%（1 个 Case 完整度算术平均）" in markdown
    assert "每个 Case 先独立计算四项指标" in console


def test_overall_quality_metrics_use_equal_weighted_case_arithmetic_mean(tmp_path):
    def run(index, *, root_passed, runbook_coverage, evidence, elapsed):
        expected_runbooks = ["pod-a", "pod-b"]
        matched_count = round(runbook_coverage * len(expected_runbooks))
        return {
            "run_index": index,
            "success": True,
            "run_id": f"run-{index}",
            "elapsed_seconds": elapsed,
            "root_cause": {"passed": root_passed},
            "runbook": {
                "matched": expected_runbooks[:matched_count],
                "expected": expected_runbooks,
                "coverage": runbook_coverage,
            },
            "evidence": {
                "collected": round(evidence * 10),
                "planned": 10,
                "completeness": evidence,
            },
        }

    stats = {
        "total_elapsed_seconds": 240.0,
        "scenarios": [
            {
                "id": "c01",
                "anomaly_type": "A",
                "fault_scenario": "A",
                "expected_runbooks": ["pod-a", "pod-b"],
                "runs": [
                    run(1, root_passed=True, runbook_coverage=1.0, evidence=1.0, elapsed=60.0)
                ],
            },
            {
                "id": "c02",
                "anomaly_type": "B",
                "fault_scenario": "B",
                "expected_runbooks": ["pod-a", "pod-b"],
                "runs": [
                    run(1, root_passed=True, runbook_coverage=0.5, evidence=0.5, elapsed=120.0),
                    run(2, root_passed=False, runbook_coverage=0.5, evidence=0.5, elapsed=120.0),
                ],
            },
        ],
    }

    console = build_console_report(stats, tmp_path)
    markdown = build_summary(stats)

    # Case A is 100%, Case B is 50%; both Cases have equal overall weight.
    assert "| 根因准确率 | >= 70% | 75.0% | ✅ |" in console
    assert "| Runbook 覆盖率 | >= 70% | 75.0% | ✅ |" in console
    assert "| 证据完整度 | >= 70% | 75.0% | ✅ |" in console
    assert "根因准确率：75.0%（2 个 Case 准确率算术平均）" in markdown
    assert "Runbook 覆盖率：75.0%（2 个 Case 覆盖率算术平均）" in markdown
    assert "证据完整度：75.0%（2 个 Case 完整度算术平均）" in markdown


def test_runbook_coverage_uses_exact_ids_from_final_report():
    report = """
📋 Runbook 参考

- **g1 aiops-case-04/workload**: pod-config-error
- unrelated prose: pod-oomkilled.md
"""

    score = score_runbooks(["pod-config-error", "pod-oomkilled"], report)

    assert score.found == ("pod-config-error",)
    assert score.matched == ("pod-config-error",)
    assert score.coverage == 0.5
    assert score.passed is False


def test_runbook_coverage_ignores_labels_and_runbook_body_cross_references():
    report = """
诊断对象标签为 pod-template-hash=abc123。

📋 Runbook 参考

- **g1 ns/pod**: pod-config-error
"""
    observations = [
        "<runbook>正文建议另见 pod-oomkilled 与 pod-crashloop-runtime</runbook>",
        json.dumps({"matched_runbooks": ["pod-config-error.md"]}),
    ]

    score = score_runbooks(
        ["pod-config-error", "pod-oomkilled"], report, observations=observations
    )

    assert score.found == ("pod-config-error",)
    assert score.coverage == 0.5
    assert score.passed is False


def test_rescore_existing_report_reuses_archives_without_changing_evidence(tmp_path):
    scenarios = load_scenarios(DEMO_DIR / "demo_cases.yaml")
    scenario = scenarios["c04"]
    run_id = "archived-run"
    run_dir = tmp_path / "c04" / f"run-01-{run_id}"
    run_dir.mkdir(parents=True)
    (run_dir / "report.md").write_text(
        """
## 🎯 根因分析 · g1
### 根因结论
已确认根因为 Secret 键名引用错误：Pod 请求 unavailable-key，但 Secret
实际数据中仅包含 available-key。

📋 Runbook 参考

- **g1 aiops-case-04/workload**: pod-config-error
""",
        encoding="utf-8",
    )
    (run_dir / "events.json").write_text("[]", encoding="utf-8")
    original_run = {
        "run_index": 1,
        "run_id": run_id,
        "success": True,
        "elapsed_seconds": 12.0,
        "root_cause": {"passed": False},
        "runbook": {"passed": False},
        "evidence": {"collected": 3, "planned": 4, "completeness": 0.75},
    }
    (run_dir / "score.json").write_text(json.dumps(original_run), encoding="utf-8")
    (tmp_path / "stats.json").write_text(
        json.dumps(
            {
                "total_elapsed_seconds": 12.0,
                "scenarios": [
                    {
                        "id": "c04",
                        "name": scenario.name,
                        "anomaly_type": scenario.anomaly_type,
                        "fault_scenario": scenario.fault_scenario,
                        "expected_runbooks": list(scenario.expected_runbooks),
                        "runs": [original_run],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    rescored = rescore_existing_report(tmp_path, scenarios, [scenario])
    run = rescored["scenarios"][0]["runs"][0]

    assert run["root_cause"]["passed"] is True
    assert run["runbook"]["passed"] is True
    assert run["evidence"]["completeness"] == 0.75
    assert run["scoring_version"] == SCORING_VERSION
    assert (Path(rescored["revision_dir"]) / "summary.md").is_file()
    assert json.loads((run_dir / "score.json").read_text()) == original_run
    assert json.loads((tmp_path / "stats.json").read_text())["scenarios"][0]["runs"][0] == original_run


def test_confirmed_root_is_not_invalidated_by_an_unconfirmed_secondary_detail():
    report = """
## 🎯 根因分析 · g1
### 根因结论
已确认的根因是 Secret workload-input 缺失 unavailable-key，导致 CreateContainerConfigError。
该 key 为什么被误删目前无法确认，但不影响上述根因。
"""
    expectation = _expectation(
        "secret", ["Secret", "unavailable-key"], ["缺失", "CreateContainerConfigError"]
    )

    claims = extract_root_claims(report)
    score = score_root_causes([expectation], claims)

    assert claims[0].inconclusive is False
    assert score.passed is True


def test_runbook_coverage_can_use_structured_runtime_observation():
    score = score_runbooks(
        ["pod-config-error"],
        "最终报告未打印 Runbook 区块",
        observations=['{"matched_runbooks":["pod-config-error.md"]}'],
    )

    assert score.found == ("pod-config-error",)
    assert score.passed is True
