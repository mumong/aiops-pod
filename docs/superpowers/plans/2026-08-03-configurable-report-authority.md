# Configurable Report Authority Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make canonical Fact Ledger reports truthful about unexecuted dimensions, deterministic by default for small models, and optionally strict about validated supporting-fact authority.

**Architecture:** `ConclusionFormatterNode` resolves a default-off `workflow.conclusion.strict_report_authority` flag from the per-run workflow config snapshot and passes it into the pure report renderer. The renderer always distinguishes absent execution evidence from completed-empty coverage; template mode derives a non-authoritative structured association from core FactRecords, while strict mode derives the core conclusion and causal box only from validated supporting FactRecords. Free-text LLM causal chains never feed deterministic core sections in either mode.

**Tech Stack:** Python 3.11, Pydantic Fact Ledger models, FastAPI/LangGraph workflow nodes, PyYAML configuration, pytest.

---

## Execution constraints

- Work in the current `robusta` checkout because the target renderer and tests contain user-owned uncommitted work that is absent from a clean worktree.
- Do not reset, clean, stash, checkout, or overwrite any existing changes.
- Do not commit implementation files: committing either target Python file would also capture unrelated user-owned hunks already present in that file. Record each checkpoint in the T003 worker report instead.
- Do not modify `VERSION`, `deploy/k8s-simple.yaml`, Evidence ReAct code, prompts, MCPStander, data contracts, or live infrastructure.
- Preserve the existing machine appendix and diagnostic-only remediation behavior.

## File map

- Modify `app/core/workflow/report_presentation.py`: dimension states, coverage provenance, template/strict fact selection, causal labels, core conclusion, mode marker.
- Modify `app/core/workflow/nodes/conclusion_formatter.py`: config resolution and explicit mode propagation.
- Modify `tests/unit/workflow/test_report_presentation.py`: focused renderer red-green coverage.
- Modify `tests/unit/workflow/test_ask_conclusion_remediation_json.py`: postprocessor/config integration coverage.
- Modify `deploy/configmap/config.yaml`: visible default-off deployment switch.

### Task 1: Make missing execution evidence explicit

**Files:**
- Modify: `tests/unit/workflow/test_report_presentation.py:61-139`
- Modify: `app/core/workflow/report_presentation.py:95-122`
- Modify: `app/core/workflow/report_presentation.py:319-408`

- [ ] **Step 1: Add the failing no-execution and completed-empty tests**

Add these tests after `ledger()` and before the existing mixed-coverage tests:

```python
def test_core_dimensions_without_fact_or_coverage_are_not_executed():
    state_fact = fact(
        fact_id="fact-state006",
        dimension="kubernetes",
        fact_type="state",
        source_system="kubernetes",
        attribute="container.state",
        value={"state": "CrashLoopBackOff"},
    )

    rows = build_dimension_presentations([ledger([state_fact])])

    for dimension in ("metrics", "logging", "tracing"):
        row = rows[dimension]
        rendered = row.render_markdown()
        assert row.state == "not_executed"
        assert "未执行" in rendered
        assert "未验证" in rendered
        assert "已执行的数据源" not in rendered
        assert "查询完成" not in rendered
        assert "未采样到" not in rendered


def test_completed_empty_coverage_uses_real_provider_source():
    coverage_fact = fact(
        fact_id="fact-cover003",
        dimension="coverage",
        fact_type="coverage",
        source_system="prometheus",
        attribute="metrics.coverage",
        value={"dimension": "metrics", "coverage": "empty"},
    )

    row = build_dimension_presentations([ledger([coverage_fact])])["metrics"]

    assert row.state == "empty"
    assert row.sources == ("prometheus",)
    assert "查询完成" in row.render_markdown()
    assert "未执行" not in row.render_markdown()
```

- [ ] **Step 2: Run the two tests and verify RED**

Run:

```bash
.venv/bin/python -m pytest -q \
  tests/unit/workflow/test_report_presentation.py::test_core_dimensions_without_fact_or_coverage_are_not_executed \
  tests/unit/workflow/test_report_presentation.py::test_completed_empty_coverage_uses_real_provider_source
```

Expected: both tests fail against the current code. The first reports `empty != not_executed`; the second reports missing `prometheus` coverage source.

- [ ] **Step 3: Implement `not_executed` rendering**

Replace `DimensionPresentation.render_markdown()` with:

```python
def render_markdown(self) -> str:
    if self.state == "not_executed":
        return (
            f"| **{self.label}** | 本轮未执行 | 未验证 | "
            "本轮未执行该维度查询，当前状态未验证，不能解释为数据不存在 |"
        )
    source = "、".join(self.sources) or "已执行的数据源"
    signal = (
        "<br>".join(self.signals)
        or "查询完成，本轮窗口未采样到匹配数据"
    )
    state = {
        "present": "已有数据",
        "partial": "部分数据",
        "empty": "查询完成",
    }[self.state]
    return f"| **{self.label}** | {source} | {state} | {signal} |"
```

- [ ] **Step 4: Preserve coverage records and use their provenance only for completed-empty rows**

In `build_dimension_presentations()`, change the coverage accumulator and relevant row logic to:

```python
coverage: dict[str, list[FactRecord]] = {
    dimension: [] for dimension in DIMENSION_LABELS
}
```

```python
if record.fact_type == "coverage":
    coverage[dimension].append(record)
else:
    records[dimension].append(record)
```

```python
coverage_records = coverage[dimension]
states = [
    state
    for record in coverage_records
    if (state := _coverage_state(record))
]
if has_signal:
    state = (
        "partial"
        if any(item in _EMPTY_COVERAGE for item in states)
        else "present"
    )
elif states:
    state = "empty"
elif dimension in CORE_DIMENSIONS:
    state = "not_executed"
else:
    continue

sources = list(dict.fromkeys([
    *(record.source_system for record in dimension_records),
    *(item[0] for item in extra),
    *(
        record.source_system
        for record in coverage_records
        if not has_signal
    ),
]))
```

Do not add coverage providers to `sources` when a real signal already exists; this preserves the existing `("kubernetes",)` and `("deepflow",)` expectations.

- [ ] **Step 5: Verify GREEN and run the full renderer file**

Run:

```bash
.venv/bin/python -m pytest -q tests/unit/workflow/test_report_presentation.py
```

Expected: all tests in the file pass. Record count, warning count, exit code, and duration in the worker report.

- [ ] **Step 6: Record the no-commit checkpoint**

Run `git diff --check -- app/core/workflow/report_presentation.py tests/unit/workflow/test_report_presentation.py`; record exit 0 and do not commit.

### Task 2: Wire the default-off workflow switch

**Files:**
- Modify: `tests/unit/workflow/test_ask_conclusion_remediation_json.py` near the Fact Ledger postprocessor tests
- Modify: `app/core/workflow/nodes/conclusion_formatter.py:149-180`
- Modify: `app/core/workflow/nodes/conclusion_formatter.py:347-356`
- Modify: `app/core/workflow/nodes/conclusion_formatter.py:6540-6560`
- Modify: `app/core/workflow/report_presentation.py:574-581`

- [ ] **Step 1: Add the failing config-resolution test**

Add:

```python
def test_conclusion_strict_report_authority_defaults_off_and_reads_config():
    node = ConclusionFormatterNode()
    assert node._is_strict_report_authority_enabled() is False

    node.workflow_config_override = {
        "conclusion": {"strict_report_authority": True}
    }
    assert node._is_strict_report_authority_enabled() is True

    node.workflow_config_override = {
        "conclusion": {"strict_report_authority": "off"}
    }
    assert node._is_strict_report_authority_enabled() is False

    node.workflow_config_override = {
        "conclusion": {"strict_report_authority": "invalid"}
    }
    assert node._is_strict_report_authority_enabled() is False
```

- [ ] **Step 2: Run the config test and verify RED**

Run:

```bash
.venv/bin/python -m pytest -q \
  tests/unit/workflow/test_ask_conclusion_remediation_json.py::test_conclusion_strict_report_authority_defaults_off_and_reads_config
```

Expected: fail with `AttributeError` because the resolver does not exist.

- [ ] **Step 3: Implement config resolution**

Add next to `_get_query_mode()`:

```python
def _is_strict_report_authority_enabled(self) -> bool:
    workflow = self._get_workflow_config()
    conclusion = (
        workflow.get("conclusion", {})
        if isinstance(workflow, dict)
        else {}
    )
    value = (
        conclusion.get("strict_report_authority")
        if isinstance(conclusion, dict)
        else None
    )
    return self._parse_bool_config(value, False)
```

- [ ] **Step 4: Propagate the flag explicitly**

Add `strict_report_authority: bool = False` to both
`_apply_fact_ledger_report_contract()` and `render_human_report()`. In the instance postprocessor call, pass:

```python
strict_report_authority=self._is_strict_report_authority_enabled(),
```

Then forward the value from `_apply_fact_ledger_report_contract()` into `render_human_report()`:

```python
strict_report_authority=strict_report_authority,
```

Keep defaults on direct-call APIs so existing tests remain template mode.

- [ ] **Step 5: Verify GREEN**

Run the exact config test from Step 2. Expected: one pass, exit 0.

- [ ] **Step 6: Record the no-commit checkpoint**

Run `git diff --check -- app/core/workflow/nodes/conclusion_formatter.py app/core/workflow/report_presentation.py tests/unit/workflow/test_ask_conclusion_remediation_json.py`; record exit 0 and do not commit.

### Task 3: Make template mode deterministic and independent of free-text chains

**Files:**
- Modify: `tests/unit/workflow/test_report_presentation.py:282-343`
- Modify: `app/core/workflow/report_presentation.py:497-571`
- Modify: `app/core/workflow/report_presentation.py:574-655`

- [ ] **Step 1: Replace the current fallback test with a failing template-mode contract**

Keep the existing config/state/metric setup but replace its claim, render call, and assertions with:

```python
claim = {
    "diagnostic_status": "diagnosed",
    "confidence": 0.9,
    "claim_validation": {
        "valid": True,
        "valid_supporting_fact_ids": [state_fact.fact_id],
        "valid_contradicting_fact_ids": [],
    },
    "causal_chain": {
        "trigger": "unsupported trigger 9999Mi",
        "mechanism": "unsupported mechanism",
        "manifestation": "unsupported manifestation",
    },
}

report = render_human_report(
    model_content="",
    ledgers=[current_ledger],
    validated_claim=claim,
    dimensions=build_dimension_presentations([current_ledger]),
    causal_chain=claim["causal_chain"],
)

assert "<!-- report_authority_mode=template -->" in report
assert "unsupported" not in report
assert "9999Mi" not in report
assert "[关键条件]" in report
assert "[状态变化]" in report
assert "[观测结果]" in report
condition_pos = report.index("[关键条件]")
transition_pos = report.index("[状态变化]")
result_pos = report.index("[观测结果]")
assert condition_pos < transition_pos < result_pos
assert "256Mi" in report[condition_pos:transition_pos]
assert "CrashLoopBackOff" in report[transition_pos:result_pos]
assert "2508" in report[result_pos:]
```

Rename the test to `test_template_mode_uses_core_facts_and_ignores_free_text_chain`.

- [ ] **Step 2: Run the renamed test and verify RED**

Run:

```bash
.venv/bin/python -m pytest -q \
  tests/unit/workflow/test_report_presentation.py::test_template_mode_uses_core_facts_and_ignores_free_text_chain
```

Expected: fail because the current renderer prioritizes the unsupported explicit chain and has no template marker or template labels.

- [ ] **Step 3: Add core-record selection and mode-aware box labels**

Add:

```python
_TEMPLATE_CAUSAL_LABELS = (
    ("trigger", "关键条件"),
    ("mechanism", "状态变化"),
    ("manifestation", "观测结果"),
)
_STRICT_CAUSAL_LABELS = (
    ("trigger", "根本原因"),
    ("mechanism", "传导机制"),
    ("manifestation", "最终表现"),
)


def _template_core_records(records: Sequence[FactRecord]) -> list[FactRecord]:
    return [
        record
        for record in records
        if record.fact_type != "coverage"
        and record.dimension != "topology"
        and record.directness != "related_context"
        and record.confidence not in {"low", "weak"}
    ]
```

Replace `_causal_box()` with this complete mode-aware implementation:

```python
def _causal_box(
    causal_chain: Mapping[str, Any],
    *,
    strict_report_authority: bool,
) -> list[str]:
    if not isinstance(causal_chain, Mapping):
        return []
    labels = (
        _STRICT_CAUSAL_LABELS
        if strict_report_authority
        else _TEMPLATE_CAUSAL_LABELS
    )
    rows: list[tuple[str, str]] = []
    for key, label in labels:
        value = _cell(causal_chain.get(key))
        if not value or _is_sentinel(value):
            continue
        rows.append((label, value))
    if len(rows) < 2:
        return []
    box = ["```text"]
    for index, (label, value) in enumerate(rows):
        box.append(f"[{label}] {value}")
        if index < len(rows) - 1:
            box.append("      ↓")
    box.append("```")
    return box
```

- [ ] **Step 4: Replace explicit-chain priority with deterministic template selection**

In `render_human_report()`, retain the existing single-entity calculation, but replace lines that select `causal_chain` or `validated_claim["causal_chain"]` with:

```python
template_records = _template_core_records(non_coverage)
selected_records = template_records
chain = (
    _synthesize_causal_chain(selected_records)
    if single_entity
    else {}
)
causal_box = (
    _causal_box(
        chain,
        strict_report_authority=strict_report_authority,
    )
    if single_entity
    else []
)
```

The function keeps the `causal_chain` parameter for call compatibility but must not read it. Update comments/docstrings to state that unbound free text is intentionally excluded.

Choose the template core conclusion deterministically:

```python
trigger_text = _cell(chain.get("trigger")) if single_entity else ""
if trigger_text and not _is_sentinel(trigger_text):
    core_conclusion = trigger_text
elif selected_records:
    core_conclusion = _fact_signal(selected_records[0])
else:
    core_conclusion = "当前没有可用于结构化摘要的核心数据"
```

Append this hidden marker before returning the human report:

```python
lines.extend(["", "<!-- report_authority_mode=template -->"])
```

Task 4 will make the marker and selected records mode-aware; do not implement strict filtering before its failing test exists.

- [ ] **Step 5: Verify GREEN and run renderer tests**

Run:

```bash
.venv/bin/python -m pytest -q tests/unit/workflow/test_report_presentation.py
```

Expected: the template test and all adjacent renderer tests pass. Update only expectations that intentionally referred to the old root-cause labels; do not weaken unrelated grounding or safety assertions.

- [ ] **Step 6: Record the no-commit checkpoint**

Run `git diff --check`; record exit 0 and do not commit.

### Task 4: Enforce validated supporting authority in strict mode

**Files:**
- Modify: `tests/unit/workflow/test_report_presentation.py` after the template-mode test
- Modify: `app/core/workflow/report_presentation.py:601-655`

- [ ] **Step 1: Add the failing strict negative test**

Reuse the three facts from the template-mode test and add:

```python
def test_strict_mode_excludes_non_supporting_facts_from_core_and_causal_sections():
    config_fact, state_fact, metric_fact = causal_test_facts()
    current_ledger = ledger([config_fact, state_fact, metric_fact])
    claim = diagnosed_claim(supporting_fact_ids=[state_fact.fact_id])

    report = render_human_report(
        model_content="",
        ledgers=[current_ledger],
        validated_claim=claim,
        dimensions=build_dimension_presentations([current_ledger]),
        causal_chain={
            "trigger": "unsupported trigger 9999Mi",
            "mechanism": "unsupported mechanism",
        },
        strict_report_authority=True,
    )

    overview = report.split("## 📊 诊断概览", 1)[1].split("## 🔍 现象描述", 1)[0]
    root_section = report.split("## 🎯 根因分析", 1)[1].split("## 🛠️ 修复建议", 1)[0]
    assert "<!-- report_authority_mode=strict -->" in report
    assert "CrashLoopBackOff" in overview
    assert "256Mi" not in overview
    assert "2508" not in overview
    assert "256Mi" not in root_section
    assert "2508" not in root_section
    assert "unsupported" not in report
    assert "[根本原因]" not in root_section
```

Extract the repeated setup into these complete helpers before the template test:

```python
def causal_test_facts() -> tuple[FactRecord, FactRecord, FactRecord]:
    config_fact = fact(
        fact_id="fact-config01",
        dimension="kubernetes",
        fact_type="configuration",
        source_system="kubernetes",
        attribute="resources.limits.memory",
        value="256Mi",
    )
    state_fact = fact(
        fact_id="fact-state005",
        dimension="kubernetes",
        fact_type="state",
        source_system="kubernetes",
        attribute="container.state",
        value={"state": "CrashLoopBackOff"},
    )
    metric_fact = fact(
        fact_id="fact-metric02",
        dimension="metrics",
        fact_type="measurement",
        source_system="prometheus",
        attribute="restart_count",
        value=2508,
    )
    return config_fact, state_fact, metric_fact


def diagnosed_claim(*, supporting_fact_ids: list[str]) -> dict:
    return {
        "diagnostic_status": "diagnosed",
        "confidence": 0.9,
        "hypotheses": [{
            "hypothesis_id": "hyp-example",
            "entity_id": ENTITY_ID,
            "supporting_fact_ids": supporting_fact_ids,
            "contradicting_fact_ids": [],
        }],
        "claim_validation": {
            "valid": True,
            "valid_supporting_fact_ids": supporting_fact_ids,
            "valid_contradicting_fact_ids": [],
            "reasons": [],
        },
    }
```

Both helpers use real `FactRecord` instances; do not mock the renderer.

- [ ] **Step 2: Run the strict negative test and verify RED**

Run:

```bash
.venv/bin/python -m pytest -q \
  tests/unit/workflow/test_report_presentation.py::test_strict_mode_excludes_non_supporting_facts_from_core_and_causal_sections
```

Expected: fail because strict mode still selects template records and writes the template marker.

- [ ] **Step 3: Implement strict record selection and marker**

After computing `supporting`, make selection mode-aware:

```python
template_records = _template_core_records(non_coverage)
selected_records = supporting if strict_report_authority else template_records
```

Keep deterministic synthesis, but pass the mode into `_causal_box()`. Make the core fallback and marker mode-aware:

```python
if trigger_text and not _is_sentinel(trigger_text):
    core_conclusion = trigger_text
elif selected_records:
    core_conclusion = _fact_signal(selected_records[0])
elif strict_report_authority:
    core_conclusion = "当前证据不足以形成严格根因结论"
else:
    core_conclusion = "当前没有可用于结构化摘要的核心数据"
```

```python
mode = "strict" if strict_report_authority else "template"
lines.extend(["", f"<!-- report_authority_mode={mode} -->"])
```

- [ ] **Step 4: Add the failing strict positive test**

Add:

```python
def test_strict_mode_builds_full_box_when_all_role_facts_are_supporting():
    config_fact, state_fact, metric_fact = causal_test_facts()
    current_ledger = ledger([config_fact, state_fact, metric_fact])
    claim = diagnosed_claim(
        supporting_fact_ids=[
            config_fact.fact_id,
            state_fact.fact_id,
            metric_fact.fact_id,
        ]
    )

    report = render_human_report(
        model_content="",
        ledgers=[current_ledger],
        validated_claim=claim,
        dimensions=build_dimension_presentations([current_ledger]),
        strict_report_authority=True,
    )

    assert "[根本原因]" in report
    assert "[传导机制]" in report
    assert "[最终表现]" in report
    assert "256Mi" in report
    assert "CrashLoopBackOff" in report
    assert "2508" in report
```

- [ ] **Step 5: Run strict tests and verify GREEN**

Run both strict tests, then run the entire renderer file. Expected: all pass, exit 0.

- [ ] **Step 6: Record the no-commit checkpoint**

Run `git diff --check`; record exit 0 and do not commit.

### Task 5: Prove postprocessor wiring and expose the deployment default

**Files:**
- Modify: `tests/unit/workflow/test_ask_conclusion_remediation_json.py` near `test_fact_ledger_report_has_human_body_and_separate_machine_appendix`
- Modify: `deploy/configmap/config.yaml:196-200`

- [ ] **Step 1: Add the complete postprocessor-mode integration test**

Add the following test using this file's `_fact()` and `_ledger()` helpers:

```python
def test_fact_ledger_postprocessor_propagates_template_and_strict_modes():
    entity_id = "k8s.pod:demo/example:uid-1"
    config_fact = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="example",
        dimension="kubernetes",
        fact_type="configuration",
        attribute="resources.limits.memory",
        value="256Mi",
        source_system="kubernetes",
        evidence_ref="kubernetes:config:1",
    )
    state_fact = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="example",
        dimension="kubernetes",
        fact_type="state",
        attribute="container.state",
        value={"state": "CrashLoopBackOff"},
        source_system="kubernetes",
        evidence_ref="kubernetes:state:1",
    )
    metric_fact = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="example",
        dimension="metrics",
        fact_type="measurement",
        attribute="restart_count",
        value=2508,
        source_system="prometheus",
        evidence_ref="prometheus:restart:1",
    )
    current_ledger = FactLedger.model_validate(_ledger(
        "case-report-authority-modes",
        [entity_id],
        [config_fact, state_fact, metric_fact],
    ))
    claim = {
        "diagnostic_status": "diagnosed",
        "confidence": 0.9,
        "hypotheses": [{
            "hypothesis_id": "hyp-example",
            "entity_id": entity_id,
            "supporting_fact_ids": [state_fact["fact_id"]],
            "contradicting_fact_ids": [],
        }],
        "claim_validation": {
            "valid": True,
            "valid_supporting_fact_ids": [state_fact["fact_id"]],
            "valid_contradicting_fact_ids": [],
            "reasons": [],
        },
    }

    template_report = ConclusionFormatterNode._apply_fact_ledger_report_contract(
        "",
        ledgers=[current_ledger],
        validated_claim=claim,
        causal_chain={"trigger": "unsupported 9999Mi", "mechanism": "unsupported"},
    )
    strict_report = ConclusionFormatterNode._apply_fact_ledger_report_contract(
        "",
        ledgers=[current_ledger],
        validated_claim=claim,
        causal_chain={"trigger": "unsupported 9999Mi", "mechanism": "unsupported"},
        strict_report_authority=True,
    )

    assert "<!-- report_authority_mode=template -->" in template_report
    assert "[关键条件]" in template_report
    assert "<!-- report_authority_mode=strict -->" in strict_report
    overview = strict_report.split(
        "## 📊 诊断概览", 1
    )[1].split("## 🔍 现象描述", 1)[0]
    assert "256Mi" not in overview
    assert "unsupported" not in template_report
    assert "unsupported" not in strict_report
    assert "remediation_contract" in template_report
    assert "remediation_contract" in strict_report
    assert "机器可核验附录" in template_report
    assert "机器可核验附录" in strict_report
```

- [ ] **Step 2: Run the postprocessor integration test**

Run the exact test. Expected after Tasks 1–4: pass, proving both modes flow through the real postprocessor while preserving remediation and the machine appendix. If it fails, fix only missing flag propagation in `_apply_fact_ledger_report_contract()`; do not change renderer semantics here.

- [ ] **Step 3: Add the visible default-off ConfigMap entry**

Under `workflow.conclusion`, add:

```yaml
# false: 根据核心 FactRecords 用结构化模板稳定组织报告（默认，适合小模型）。
# true: 核心结论和因果框仅使用 validated supporting Fact IDs。
strict_report_authority: false
```

- [ ] **Step 4: Verify the ConfigMap parses and contains a real boolean**

Run:

```bash
.venv/bin/python - <<'PY'
from pathlib import Path
import yaml

manifest = yaml.safe_load(Path("deploy/configmap/config.yaml").read_text())
app_config = yaml.safe_load(manifest["data"]["config.yaml"])
value = app_config["workflow"]["conclusion"]["strict_report_authority"]
assert value is False, repr(value)
print("strict_report_authority=false (bool)")
PY
```

Expected: `strict_report_authority=false (bool)`, exit 0.

- [ ] **Step 5: Record the no-commit checkpoint**

Run `git diff --check`; record exit 0 and do not commit.

### Task 6: Full verification and handoff evidence

**Files:**
- Verify all T003 allowed business files
- Create only the agent-loop artifacts required by the T003 contract

- [ ] **Step 1: Run focused tests**

Run:

```bash
.venv/bin/python -m pytest -q \
  tests/unit/workflow/test_report_presentation.py \
  tests/unit/workflow/test_ask_conclusion_remediation_json.py \
  tests/unit/workflow/test_fast_paths.py
```

Expected: exit 0. Record exact pass/warning count and duration; do not reuse T002 counts.

- [ ] **Step 2: Run adjacent authority/config regressions**

Run:

```bash
.venv/bin/python -m pytest -q \
  tests/unit/workflow/test_fact_contract.py \
  tests/unit/workflow/test_context_handoff.py \
  tests/unit/workflow/test_structured_schemas.py \
  tests/unit/workflow/test_remediation_plan_handling.py \
  tests/unit/remediation/test_plans.py
```

Expected: exit 0 with exact count and duration recorded.

- [ ] **Step 3: Run direct behavior probes in both modes**

Use real `FactRecord`/`FactLedger` objects and production `render_human_report()` to assert:

- missing dimensions render `not_executed` semantics;
- template mode includes the three structured roles and ignores a hostile explicit chain;
- strict mode with only state supporting excludes `256Mi` and `2508` from overview/root sections;
- strict mode with all three facts supporting renders the three strict causal roles.

Run the probe twice. Expected: both iterations exit 0 with identical assertions.

- [ ] **Step 4: Run static and scope checks**

Run:

```bash
git diff --check
git status --short --branch
```

Compare scheduler-owned pre/post business-state digests and protected agent-loop manifests. Expected: only contract-allowed files differ during the worker interval; no secret, live, deploy, kubectl write, remediation, build/push, reset, clean, stash, checkout, or commit action occurred.

- [ ] **Step 5: Write the worker report and handoff**

Record inputs, files changed, every command with exit/count/duration, RED and GREEN evidence for both cycles, ConfigMap parse evidence, direct-probe evidence, risks, claim boundary, and recommended independent review action.

- [ ] **Step 6: Dispatch independent review**

Reviewer must independently rerun focused/adjacent tests, inspect the exact dirty diff, repeat both mode probes, parse ConfigMap, verify the write boundary, and return `ACCEPT`, `REWORK`, or `BLOCKED`. T003 is not done without `ACCEPT` and evidence for every criterion.
