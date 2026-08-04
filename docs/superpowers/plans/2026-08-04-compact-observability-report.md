# Compact Observability Report Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a stable, reference-aligned human diagnostic report and replace the oversized full-ledger appendix with a deterministic Metrics/Logging/Tracing core summary.

**Architecture:** Keep Fact Ledger validation and the default-off strict authority switch unchanged. `report_presentation.py` projects validated records and grounded model prose into the fixed human layout; a focused `report_appendix.py` selects at most one real FactRecord per observability dimension and serializes the compact contract. `ConclusionFormatterNode` remains the integration boundary that derives limitations, preserves the diagnostic-only remediation block, and appends the compact payload.

**Tech Stack:** Python 3.12, Pydantic v2 Fact Ledger models, deterministic Markdown/JSON rendering, pytest.

---

## Execution constraints

- Work in the current `robusta` checkout. The target Python and test files contain user-owned uncommitted changes that are absent from a clean worktree.
- Do not reset, clean, stash, checkout, restore, or overwrite existing work.
- Do not commit implementation files because path-level commits would capture pre-existing user hunks. Store RED/GREEN commands and diffs in the dedicated agent-loop attempt instead.
- Do not change `VERSION`, deployment manifests, Evidence ReAct, Fact Ledger schemas, remediation authorization, providers, MCP behavior, or the existing strict-mode configuration.
- Do not make Kubernetes or topology part of the compact appendix.
- Preserve full Fact Ledgers in workflow state; only the user-visible appendix changes.

## File map

- Modify `app/core/prompts.py`: align the conclusion prompt with the approved semantic order and tell the model that deterministic code owns layout.
- Modify `app/core/workflow/report_presentation.py`: key-entity and evidence tables, visible limitations, grounded relationship prose, and display-width-aware causal cards.
- Create `app/core/workflow/report_appendix.py`: deterministic three-dimension core-fact selection and compact JSON rendering.
- Modify `app/core/workflow/nodes/conclusion_formatter.py`: pass typed limitations into the human renderer and append the new compact payload after remediation.
- Modify `tests/unit/workflow/test_fast_paths.py`: prompt contract and adjacent prompt regressions.
- Modify `tests/unit/workflow/test_report_presentation.py`: focused human layout, authority, entity isolation, and causal-card tests.
- Create `tests/unit/workflow/test_report_appendix.py`: isolated compact appendix selection and size tests.
- Modify `tests/unit/workflow/test_ask_conclusion_remediation_json.py`: end-to-end formatter integration and migration away from the old full-ledger assertions.

### Task 1: Align the conclusion prompt with the deterministic renderer

**Files:**
- Modify: `tests/unit/workflow/test_fast_paths.py` near the existing `CONCLUSION_FORMATTER_PROMPT` tests
- Modify: `app/core/prompts.py:433-466`

- [ ] **Step 1: Replace the old outline assertion with a failing ordered-contract test**

Add this test beside the current conclusion prompt assertions:

```python
def test_conclusion_prompt_uses_reference_order_and_delegates_layout():
    prompt = CONCLUSION_FORMATTER_PROMPT
    sections = [
        "诊断概览",
        "现象描述",
        "已采集证据",
        "证据关联分析",
        "缺失证据",
        "根因分析",
        "修复建议",
        "验证步骤",
    ]

    positions = [prompt.index(section) for section in sections]
    assert positions == sorted(positions)
    assert "系统会确定性生成最终标题、表格、顺序和因果框" in prompt
    assert "每个事实句末尾" in prompt
    assert "<!-- facts:fact-id[,fact-id...] -->" in prompt
    assert "不要输出机器附录、修复 JSON、ASCII/Unicode 因果框" in prompt
    assert "未执行的查询不得写成空结果" in prompt
```

- [ ] **Step 2: Run the prompt test and verify RED**

Run:

```bash
.venv/bin/python -m pytest -q \
  tests/unit/workflow/test_fast_paths.py::test_conclusion_prompt_uses_reference_order_and_delegates_layout
```

Expected: FAIL because the current prompt still uses `关键证据` / `可观测性摘要` and does not contain the deterministic-layout contract.

- [ ] **Step 3: Replace only `CONCLUSION_FORMATTER_PROMPT` with the approved semantic contract**

Use this complete prompt body while retaining the surrounding constant name and English alias:

```python
CONCLUSION_FORMATTER_PROMPT = """
# 任务
把已验证诊断事实写成简洁、自然、给人看的语义草稿。先回答问题，再解释证据；最终 Markdown 由系统统一渲染。

# 输出顺序
依次提供：诊断概览、现象描述、已采集证据、证据关联分析、缺失证据、根因分析、修复建议、验证步骤。

# 数据与事实边界
- 优先写具体数值与单位、状态、退出码、错误原文、重启次数和时延，并解释这些信号说明什么。
- 精确值、状态、实体、来源和因果只能来自 validated FactRecords 或 source-backed observations；背景证据不得升级为根因。
- 每个事实句末尾添加 `<!-- facts:fact-id[,fact-id...] -->`，且只能引用输入中存在的完整 Fact ID。
- 没有 Fact ID 的 source-backed observation 只能作为观测说明，并标明真实工具来源。
- 多实体分别总结；观测证据只做维度摘要。不同实体、时间窗口或 trace_id 不拼接；拓扑事实只描述关系，不自动证明健康或因果。
- 真实空结果可写“查询完成，当前窗口未发现匹配记录”；未执行的查询不得写成空结果。
- 数据不足时明确写缺口，不强行生成根因或因果链。

# 表达方式
- 正文使用自然语言，不展示 Fact ID、entity ID、原始字典、JSON 或 `key=value` 机器字段。
- 系统会确定性生成最终标题、表格、顺序和因果框；只输出有 Fact marker 的简洁事实句。
- 不要输出机器附录、修复 JSON、ASCII/Unicode 因果框或复制 FactRecord。
- 核心实体、状态、错误、指标和值可以使用 Markdown 粗体。

# 安全
- 根因只使用 validated supporting facts；普通观测事实只能描述现象和证据。
- 未提供 typed Remediation Policy 时只给人工处理方向和只读验证，不生成 Kubernetes 写命令。
- 保留调用方提供的结构化修复计划合同。
"""
```

- [ ] **Step 4: Verify GREEN and adjacent prompt invariants**

Replace the body of `test_conclusion_prompt_is_human_focused_and_grounded()` with:

```python
def test_conclusion_prompt_is_human_focused_and_grounded():
    prompt = CONCLUSION_FORMATTER_PROMPT
    for heading in (
        "诊断概览",
        "现象描述",
        "已采集证据",
        "证据关联分析",
        "缺失证据",
        "根因分析",
        "修复建议",
        "验证步骤",
    ):
        assert heading in prompt
    assert "<!-- facts:fact-id[,fact-id...] -->" in prompt
    assert "Markdown 粗体" in prompt
    assert "不展示 Fact ID、entity ID、原始字典、JSON" in prompt
    assert "背景证据不得升级为根因" in prompt
```

Change the `conclusion_phrases` list in
`test_rca_and_conclusion_prompts_require_verbatim_per_pod_observability()` to:

```python
conclusion_phrases = [
    "多实体分别总结",
    "观测证据只做维度摘要",
    "核心实体、状态、错误、指标和值可以使用 Markdown 粗体",
    "每个事实句末尾添加",
    "根因只使用 validated supporting facts",
]
```

Change `conclusion_phrases` in
`test_prompts_refine_runbooks_after_live_evidence_and_preserve_topology_semantics()`
to remove the obsolete claim that raw topology is preserved in the machine appendix:

```python
conclusion_phrases = [
    "拓扑事实只描述关系，不自动证明健康或因果",
    "只能引用输入中存在的完整 Fact ID",
    "不要输出机器附录",
]
```

Run:

```bash
.venv/bin/python -m pytest -q \
  tests/unit/workflow/test_fast_paths.py::test_conclusion_prompt_uses_reference_order_and_delegates_layout \
  tests/unit/workflow/test_fast_paths.py -k 'conclusion_prompt or prompt_contract'
```

Expected: the new test and all selected adjacent prompt tests pass without weakening entity, topology, grounding, or safety assertions.

- [ ] **Step 5: Record the checkpoint**

Run `git diff --check -- app/core/prompts.py tests/unit/workflow/test_fast_paths.py`; expected exit code 0. Save the exact RED and GREEN outputs in the worker report; do not commit these dirty paths.

### Task 2: Render the fixed human report structure and visible evidence tables

**Files:**
- Modify: `tests/unit/workflow/test_report_presentation.py`
- Modify: `app/core/workflow/report_presentation.py`

- [ ] **Step 1: Add failing structure, row-limit, and limitation tests**

Import `EvidenceLimitation` and add:

```python
from app.core.workflow.schemas import EvidenceLimitation, FactLedger, FactRecord


def test_human_report_has_fixed_tables_and_optional_missing_evidence():
    config_fact, state_fact, metric_fact = causal_test_facts()
    extra = [
        fact(
            fact_id=f"fact-log{i:08d}",
            dimension="logging",
            fact_type="log",
            source_system="elasticsearch",
            attribute="log.message",
            value={"message": f"line-{i}"},
        )
        for i in range(6)
    ]
    current_ledger = ledger([config_fact, state_fact, metric_fact, *extra])
    limitations = [
        EvidenceLimitation(
            code="sampled_interval_unknown",
            applies_to=(metric_fact.fact_id,),
            statement="指标只证明离散采样时刻，采样间瞬时值未知。",
            source_basis=(metric_fact.fact_id,),
        ),
        EvidenceLimitation(
            code="availability_unmeasured",
            applies_to=("availability",),
            statement="当前事实未直接测量服务可用性，不声明服务不可用。",
        ),
    ]

    report = render_human_report(
        model_content="""## 证据关联分析
重启次数为 **2508**，可作为当前状态变化的观测结果。 <!-- facts:fact-metric02 -->
""",
        ledgers=[current_ledger],
        validated_claim=diagnosed_claim(
            supporting_fact_ids=[state_fact.fact_id]
        ),
        dimensions=build_dimension_presentations([current_ledger]),
        limitations=limitations,
    )

    headings = [
        "## 📊 诊断概览",
        "## 🔍 现象描述",
        "### 关键实体",
        "## 🕵️ 证据链",
        "### 已采集证据",
        "### 证据关联分析",
        "### 缺失证据",
        "## 🎯 根因分析",
        "### 根因结论",
        "## 🛠️ 修复建议",
        "## ✅ 验证步骤",
    ]
    assert [report.index(item) for item in headings] == sorted(
        report.index(item) for item in headings
    )
    assert "| 类型 | Namespace | 名称 | 当前状态/关键信号 |" in report
    assert "| # | 证据类型 | 数据来源 | 关键数据 | 说明 |" in report
    evidence = report.split("### 已采集证据", 1)[1].split(
        "### 证据关联分析", 1
    )[0]
    assert sum(line.startswith("| ") for line in evidence.splitlines()) == 7
    assert "重启次数为 **2508**" in report
    assert "| 指标采样间隔 | 指标只证明离散采样时刻" in report
    assert "| 服务可用性 | 当前事实未直接测量服务可用性" in report
    assert "fact-metric02" not in report
    assert "source_basis" not in report


def test_human_report_omits_missing_evidence_without_limitations():
    state_fact = fact(
        fact_id="fact-state007",
        dimension="kubernetes",
        fact_type="state",
        source_system="kubernetes",
        attribute="container.state",
        value={"state": "Running"},
    )
    current_ledger = ledger([state_fact])

    report = render_human_report(
        model_content="",
        ledgers=[current_ledger],
        validated_claim=diagnosed_claim(
            supporting_fact_ids=[state_fact.fact_id]
        ),
        dimensions=build_dimension_presentations([current_ledger]),
    )

    assert "### 缺失证据" not in report
```

- [ ] **Step 2: Run both tests and verify RED**

Run:

```bash
.venv/bin/python -m pytest -q \
  tests/unit/workflow/test_report_presentation.py::test_human_report_has_fixed_tables_and_optional_missing_evidence \
  tests/unit/workflow/test_report_presentation.py::test_human_report_omits_missing_evidence_without_limitations
```

Expected: the first test fails because `limitations` is not accepted and the fixed tables/headings do not exist.

- [ ] **Step 3: Add deterministic labels and bounded record selectors**

Add these constants and helpers near `_template_core_records()`:

```python
_FACT_TYPE_LABELS = {
    "configuration": "配置",
    "state": "状态",
    "event": "事件",
    "log": "日志",
    "measurement": "指标",
    "span": "Trace",
    "flow": "流量",
}
_LIMITATION_LABELS = {
    "sampled_interval_unknown": "指标采样间隔",
    "representative_trace_only": "Trace 代表性",
    "availability_unmeasured": "服务可用性",
    "capacity_policy_missing": "容量策略",
    "topology_relation_only": "拓扑关系边界",
    "partial_coverage": "证据覆盖范围",
}


def fact_signal(record: FactRecord) -> str:
    """Public readable projection shared by human and appendix renderers."""
    return _fact_signal(record)


def _evidence_records(records: Sequence[FactRecord]) -> list[FactRecord]:
    return [
        record
        for record in records
        if record.fact_type != "coverage"
        and record.dimension != "topology"
        and record.directness != "related_context"
        and record.confidence not in {"low", "weak"}
    ][:6]


def _evidence_explanation(record: FactRecord) -> str:
    if record.fact_type in {"configuration", "state", "event", "log"}:
        return "已采集的直接状态或上下文信号，不单独扩大为根因。"
    return "用于描述当前观测结果，不单独扩大为根因。"


def _deduplicated_limitations(
    limitations: Sequence[EvidenceLimitation],
) -> list[EvidenceLimitation]:
    seen: set[tuple[str, str]] = set()
    result: list[EvidenceLimitation] = []
    for item in limitations:
        key = (item.code, item.statement)
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
        if len(result) == 3:
            break
    return result
```

Also import `EvidenceLimitation` from `app.core.workflow.schemas`.

- [ ] **Step 4: Extend `render_human_report()` and replace the current evidence bullets/table**

Add `limitations: Sequence[EvidenceLimitation] = ()` to the function signature. Build `display_records = _evidence_records(non_coverage)` and render these exact blocks in order:

```python
lines.extend(["", "## 🔍 现象描述", ""])
if model_sections["phenomenon"]:
    lines.extend(f"- {item}" for item in model_sections["phenomenon"])
elif first:
    lines.append(f"- {_fact_signal(first)}。")
else:
    lines.append("- 当前诊断已完成证据收集，具体信号见下方证据链。")

if entity_groups:
    lines.extend([
        "",
        "### 关键实体",
        "",
        "| 类型 | Namespace | 名称 | 当前状态/关键信号 |",
        "|---|---|---|---|",
    ])
    for _label, entity_records in entity_groups:
        representative = next(
            (
                record
                for record in entity_records
                if record.fact_type != "coverage"
                and record.dimension != "topology"
            ),
            entity_records[0],
        )
        lines.append(
            f"| {_cell(representative.entity_kind)} | "
            f"{_cell(representative.namespace)} | "
            f"{_cell(representative.entity_name)} | "
            f"{_fact_signal(representative)} |"
        )

lines.extend([
    "",
    "## 🕵️ 证据链",
    "",
    "### 已采集证据",
])

def append_evidence_table(
    table_records: Sequence[FactRecord],
    *,
    start_index: int,
) -> int:
    lines.extend([
        "",
        "| # | 证据类型 | 数据来源 | 关键数据 | 说明 |",
        "|---|---|---|---|---|",
    ])
    for index, record in enumerate(table_records, start=start_index):
        lines.append(
            f"| {index} | {_FACT_TYPE_LABELS.get(record.fact_type, '观测')} | "
            f"{_cell(record.source_system)} | {_fact_signal(record)} | "
            f"{_evidence_explanation(record)} |"
        )
    return start_index + len(table_records)

if len(entity_groups) > 1:
    next_index = 1
    for label, entity_records in entity_groups:
        scoped = [record for record in display_records if record in entity_records]
        if not scoped:
            continue
        lines.extend(["", f"#### **{_cell(label)}**"])
        next_index = append_evidence_table(scoped, start_index=next_index)
else:
    append_evidence_table(display_records, start_index=1)
if not display_records:
    lines.append("| 1 | 未验证 | 本轮未执行 | 当前没有可展示的核心证据 | 需要继续采集。 |")

lines.extend(["", "### 证据关联分析", ""])
relationship_items = [
    *model_sections["evidence"],
    *model_sections["causal"],
]
lines.extend(
    [f"- {item}" for item in relationship_items]
    or ["- 当前仅展示结构化数据关联，未额外生成因果推断。"]
)

visible_limitations = _deduplicated_limitations(limitations)
if visible_limitations:
    lines.extend([
        "",
        "### 缺失证据",
        "",
        "| 缺失项 | 影响 |",
        "|---|---|",
    ])
    for item in visible_limitations:
        lines.append(
            f"| {_LIMITATION_LABELS[item.code]} | {_cell(item.statement)} |"
        )
```

Update `_grounded_model_sections()` so headings containing `已采集证据` map to `evidence`, and headings containing `证据关联分析` map to `causal`. Check `证据关联分析` before the broader evidence heading checks.

- [ ] **Step 5: Add the explicit root subsection and keep strict authority unchanged**

In the root block, emit `### 因果链` only when `causal_box` is non-empty, then always emit `### 根因结论`. Keep strict selection as `selected_records = supporting`; keep template selection as `_template_core_records(non_coverage)`; do not consume incoming or claim-embedded free-text chains.

```python
lines.extend(["", "## 🎯 根因分析", ""])
if causal_box:
    lines.extend(["### 因果链", "", *causal_box, ""])
lines.extend(["### 根因结论", ""])
```

Move the existing grounded strict/root fallback under this subsection without changing its supporting-only conditions.

- [ ] **Step 6: Verify GREEN and current renderer authority tests**

Run:

```bash
.venv/bin/python -m pytest -q tests/unit/workflow/test_report_presentation.py
```

Expected: all tests pass after updating old heading assertions to the fixed layout. Confirm the existing template/strict, unsupported literal, unexecuted dimension, and multi-entity expectations remain assertions rather than being removed.

- [ ] **Step 7: Record the checkpoint**

Run `git diff --check -- app/core/workflow/report_presentation.py tests/unit/workflow/test_report_presentation.py`; expected exit code 0. Save RED/GREEN evidence; do not commit dirty implementation paths.

### Task 3: Replace the flat causal text with aligned Unicode cards

**Files:**
- Modify: `tests/unit/workflow/test_report_presentation.py`
- Modify: `app/core/workflow/report_presentation.py`

- [ ] **Step 1: Add failing alignment and omission tests**

Add:

```python
import unicodedata


def _display_width_for_test(value: str) -> int:
    return sum(
        2 if unicodedata.east_asian_width(char) in {"W", "F"} else 1
        for char in value
    )


def test_causal_cards_are_framed_and_display_width_aligned():
    config_fact, state_fact, metric_fact = causal_test_facts()
    current_ledger = ledger([config_fact, state_fact, metric_fact])

    report = render_human_report(
        model_content="",
        ledgers=[current_ledger],
        validated_claim=diagnosed_claim(
            supporting_fact_ids=[
                config_fact.fact_id,
                state_fact.fact_id,
                metric_fact.fact_id,
            ]
        ),
        dimensions=build_dimension_presentations([current_ledger]),
        strict_report_authority=True,
    )
    causal = report.split("### 因果链", 1)[1].split(
        "### 根因结论", 1
    )[0]
    borders = [
        line for line in causal.splitlines()
        if line.startswith(("┌", "│", "└"))
    ]

    assert causal.count("┌") == 3
    assert causal.count("↓") == 2
    assert "根本原因" in causal
    assert "传导机制" in causal
    assert "最终表现" in causal
    assert len({_display_width_for_test(line) for line in borders}) == 1
    assert "**" not in causal


def test_single_causal_role_omits_causal_heading_and_box():
    state_fact = fact(
        fact_id="fact-state008",
        dimension="kubernetes",
        fact_type="state",
        source_system="kubernetes",
        attribute="container.state",
        value={"state": "CrashLoopBackOff"},
    )
    current_ledger = ledger([state_fact])
    report = render_human_report(
        model_content="",
        ledgers=[current_ledger],
        validated_claim=diagnosed_claim(
            supporting_fact_ids=[state_fact.fact_id]
        ),
        dimensions=build_dimension_presentations([current_ledger]),
        strict_report_authority=True,
    )

    assert "### 因果链" not in report
    assert "┌" not in report
    assert "### 根因结论" in report
```

- [ ] **Step 2: Run both tests and verify RED**

Run the two exact node IDs above. Expected: the current `[标签] value` block fails the border and alignment assertions.

- [ ] **Step 3: Implement standard-library display width helpers**

Import `unicodedata` and add:

```python
def _display_width(value: str) -> int:
    return sum(
        2 if unicodedata.east_asian_width(char) in {"W", "F"} else 1
        for char in value
    )


def _plain_card_text(value: Any) -> str:
    text = re.sub(r"[*_`]", "", _cell(value))
    return re.sub(r"\s+", " ", text).strip()


def _wrap_display(value: str, width: int) -> list[str]:
    rows: list[str] = []
    current = ""
    current_width = 0
    for char in value:
        char_width = 2 if unicodedata.east_asian_width(char) in {"W", "F"} else 1
        if current and current_width + char_width > width:
            rows.append(current)
            current = ""
            current_width = 0
        current += char
        current_width += char_width
    if current or not rows:
        rows.append(current)
    return rows


def _pad_display(value: str, width: int) -> str:
    return value + " " * max(0, width - _display_width(value))


def _framed_card(label: str, value: str, *, width: int = 58) -> list[str]:
    inner = width - 2
    content = [f"{label}", *_wrap_display(_plain_card_text(value), inner)]
    return [
        "┌" + "─" * inner + "┐",
        *(f"│{_pad_display(row, inner)}│" for row in content),
        "└" + "─" * inner + "┘",
    ]
```

- [ ] **Step 4: Rewrite `_causal_box()` to compose cards**

Keep the existing mode-specific labels, sentinel filtering, and two-role minimum. Replace only the final assembly:

```python
width = 58
box = ["```text"]
for index, (label, value) in enumerate(rows):
    box.extend(_framed_card(label, value, width=width))
    if index < len(rows) - 1:
        box.append(" " * ((width - 1) // 2) + "↓")
box.append("```")
return box
```

- [ ] **Step 5: Verify GREEN and both authority modes**

Run:

```bash
.venv/bin/python -m pytest -q tests/unit/workflow/test_report_presentation.py \
  -k 'causal or template_mode or strict_mode'
```

Expected: all selected tests pass; template labels remain `关键条件/状态变化/观测结果`, strict labels remain `根本原因/传导机制/最终表现`, and a single role produces no box.

- [ ] **Step 6: Record the checkpoint**

Run `git diff --check -- app/core/workflow/report_presentation.py tests/unit/workflow/test_report_presentation.py`; expected exit code 0.

### Task 4: Build the compact observability appendix as an isolated renderer

**Files:**
- Create: `app/core/workflow/report_appendix.py`
- Create: `tests/unit/workflow/test_report_appendix.py`
- Modify: `app/core/workflow/report_presentation.py` only for the public `fact_signal()` wrapper introduced in Task 2

- [ ] **Step 1: Write the failing compact-contract tests**

Create `tests/unit/workflow/test_report_appendix.py` with local FactRecord/DimensionPresentation fixtures and these contracts:

```python
import json
from typing import Any

from app.core.workflow.report_appendix import render_compact_observability_appendix
from app.core.workflow.report_presentation import DimensionPresentation
from app.core.workflow.schemas import FactRecord


def make_record(
    *,
    fact_id: str,
    dimension: str,
    source_system: str,
    value: Any,
    fact_type: str = "measurement",
    evidence_refs: list[str] | None = None,
    directness: str = "direct",
    confidence: str = "high",
    strength: str = "strong",
    timestamp: str | None = None,
) -> FactRecord:
    return FactRecord.model_validate({
        "fact_id": fact_id,
        "entity_id": "k8s.pod:demo/example:uid-1",
        "entity_kind": "Pod",
        "namespace": "demo",
        "entity_name": "example",
        "dimension": dimension,
        "fact_type": fact_type,
        "attribute": f"{dimension}.signal",
        "value": value,
        "source_system": source_system,
        "directness": directness,
        "confidence": confidence,
        "strength": strength,
        "timestamp": timestamp,
        "evidence_refs": evidence_refs or [f"ref:{fact_id}"],
    })


def dimension_rows(
    *,
    metrics_state: str = "not_executed",
    logging_state: str = "not_executed",
    tracing_state: str = "not_executed",
    metrics_sources: tuple[str, ...] = (),
) -> dict[str, DimensionPresentation]:
    states = {
        "metrics": metrics_state,
        "logging": logging_state,
        "tracing": tracing_state,
    }
    return {
        dimension: DimensionPresentation(
            dimension=dimension,
            label=dimension.title(),
            state=state,
            sources=(metrics_sources if dimension == "metrics" else ()),
            signals=(),
            evidence_refs=(),
        )
        for dimension, state in states.items()
    }


def standard_three_dimension_records() -> list[FactRecord]:
    return [
        make_record(
            fact_id="fact-metric0010",
            dimension="metrics",
            source_system="prometheus",
            value=2508,
        ),
        make_record(
            fact_id="fact-logging010",
            dimension="logging",
            fact_type="log",
            source_system="elasticsearch",
            value={"message": "required configuration is missing"},
        ),
        make_record(
            fact_id="fact-tracing010",
            dimension="tracing",
            fact_type="span",
            source_system="tempo",
            value={
                "name": "GET /healthz",
                "trace_id": "0123456789abcdef0123456789abcdef",
            },
        ),
    ]


def _payload(rendered: str) -> dict:
    fenced = rendered.split("```json\n", 1)[1].split("\n```", 1)[0]
    return json.loads(fenced)


def test_appendix_has_exact_three_dimensions_and_forbidden_fields_absent():
    metric = make_record(
        fact_id="fact-metric0001",
        dimension="metrics",
        source_system="prometheus",
        value=42,
    )
    topology = make_record(
        fact_id="fact-topology01",
        dimension="topology",
        fact_type="relationship",
        source_system="kubernetes",
        value={"relation": "owned_by"},
    )
    rendered = render_compact_observability_appendix(
        records=[metric, topology],
        dimensions=dimension_rows(metrics_state="present"),
        supporting_fact_ids=[metric.fact_id, "fact-does-not-exist"],
    )
    payload = _payload(rendered)

    assert payload["contract"] == "observability-core-summary-v1"
    assert [item["dimension"] for item in payload["dimensions"]] == [
        "metrics", "logging", "tracing"
    ]
    assert payload["dimensions"][0]["fact_id"] == metric.fact_id
    assert payload["dimensions"][1] == {
        "dimension": "logging", "state": "not_executed"
    }
    assert "topology" not in rendered
    for forbidden in (
        "facts", "claim_fact_ids", "limitations", "entity_id",
        "metadata", "applies_to", "source_basis",
    ):
        assert f'"{forbidden}"' not in rendered


def test_appendix_selector_prefers_support_then_quality_then_newest():
    older_support = make_record(
        fact_id="fact-metric0002",
        dimension="metrics",
        source_system="prometheus",
        value="supported",
        timestamp="2026-08-01T00:00:00Z",
    )
    newer_direct = make_record(
        fact_id="fact-metric0003",
        dimension="metrics",
        source_system="prometheus",
        value="newer",
        timestamp="2026-08-03T00:00:00Z",
    )
    selected = _payload(render_compact_observability_appendix(
        records=[newer_direct, older_support],
        dimensions=dimension_rows(metrics_state="present"),
        supporting_fact_ids=[older_support.fact_id],
    ))["dimensions"][0]

    assert selected["fact_id"] == older_support.fact_id

    derived_newer = make_record(
        fact_id="fact-metric0004",
        dimension="metrics",
        source_system="prometheus",
        value="derived-newer",
        directness="derived",
        timestamp="2026-08-04T00:00:00Z",
    )
    direct_older = make_record(
        fact_id="fact-metric0005",
        dimension="metrics",
        source_system="prometheus",
        value="direct-older",
        timestamp="2026-08-02T00:00:00Z",
    )
    selected = _payload(render_compact_observability_appendix(
        records=[derived_newer, direct_older],
        dimensions=dimension_rows(metrics_state="present"),
    ))["dimensions"][0]
    assert selected["fact_id"] == direct_older.fact_id

    same_quality_old = make_record(
        fact_id="fact-metric0006",
        dimension="metrics",
        source_system="prometheus",
        value="old",
        timestamp="2026-08-01T00:00:00Z",
    )
    same_quality_new = make_record(
        fact_id="fact-metric0007",
        dimension="metrics",
        source_system="prometheus",
        value="new",
        timestamp="2026-08-03T00:00:00Z",
    )
    selected = _payload(render_compact_observability_appendix(
        records=[same_quality_old, same_quality_new],
        dimensions=dimension_rows(metrics_state="present"),
    ))["dimensions"][0]
    assert selected["fact_id"] == same_quality_new.fact_id

    lexical_first = make_record(
        fact_id="fact-metric0008a",
        dimension="metrics",
        source_system="prometheus",
        value="a",
    )
    lexical_second = make_record(
        fact_id="fact-metric0008b",
        dimension="metrics",
        source_system="prometheus",
        value="b",
    )
    selected = _payload(render_compact_observability_appendix(
        records=[lexical_second, lexical_first],
        dimensions=dimension_rows(metrics_state="present"),
    ))["dimensions"][0]
    assert selected["fact_id"] == lexical_first.fact_id


def test_appendix_preserves_empty_provider_and_caps_plain_signal():
    long_log = make_record(
        fact_id="fact-logging001",
        dimension="logging",
        fact_type="log",
        source_system="elasticsearch",
        value={"message": "故障" * 100},
        evidence_refs=["log:first", "log:second"],
    )
    rows = dimension_rows(
        metrics_state="empty",
        metrics_sources=("prometheus",),
        logging_state="present",
    )
    payload = _payload(render_compact_observability_appendix(
        records=[long_log],
        dimensions=rows,
        supporting_fact_ids=[],
    ))

    metrics, logging, _tracing = payload["dimensions"]
    assert metrics == {
        "dimension": "metrics",
        "state": "empty",
        "source": "prometheus",
    }
    assert "**" not in logging["signal"]
    assert "\n" not in logging["signal"]
    assert len(logging["signal"]) == 160
    assert logging["signal"].endswith("…")
    assert logging["evidence_ref"] == "log:first"


def test_standard_appendix_is_bounded_and_deterministic():
    records = standard_three_dimension_records()
    rows = dimension_rows(
        metrics_state="present",
        logging_state="present",
        tracing_state="present",
    )
    first = render_compact_observability_appendix(
        records=records,
        dimensions=rows,
        supporting_fact_ids=[records[0].fact_id],
    )
    second = render_compact_observability_appendix(
        records=list(reversed(records)),
        dimensions=rows,
        supporting_fact_ids=[records[0].fact_id],
    )

    assert first == second
    assert len(first) <= 1200
```

- [ ] **Step 2: Run the new file and verify RED**

Run:

```bash
.venv/bin/python -m pytest -q tests/unit/workflow/test_report_appendix.py
```

Expected: collection fails with `ModuleNotFoundError` because `report_appendix.py` does not exist.

- [ ] **Step 3: Create the compact renderer with deterministic selection**

Create `app/core/workflow/report_appendix.py` with this implementation shape:

```python
from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Mapping, Sequence

from app.core.workflow.report_presentation import (
    DimensionPresentation,
    fact_signal,
)
from app.core.workflow.schemas import FactRecord


OBSERVABILITY_DIMENSIONS = ("metrics", "logging", "tracing")
_DIRECTNESS_RANK = {"direct": 0, "derived": 1, "related_context": 2}
_STRENGTH_RANK = {"critical": 0, "strong": 1, "supporting": 2, "context": 3}
_CONFIDENCE_RANK = {"high": 0, "medium": 1, "low": 2, "weak": 3}


def _timestamp_rank(record: FactRecord) -> tuple[int, float]:
    raw = record.timestamp or record.end or record.start
    if not raw:
        return (1, 0.0)
    try:
        value = datetime.fromisoformat(raw.replace("Z", "+00:00")).timestamp()
        return (0, -value)
    except (TypeError, ValueError):
        return (1, 0.0)


def _select_core_fact(
    records: Sequence[FactRecord],
    *,
    dimension: str,
    supporting_fact_ids: set[str],
) -> FactRecord | None:
    candidates = [
        record for record in records
        if record.dimension == dimension and record.fact_type != "coverage"
    ]
    if not candidates:
        return None
    return min(candidates, key=lambda record: (
        0 if record.fact_id in supporting_fact_ids else 1,
        _DIRECTNESS_RANK[record.directness],
        _STRENGTH_RANK.get(record.strength or "context", 3),
        _CONFIDENCE_RANK[record.confidence],
        *_timestamp_rank(record),
        record.fact_id,
    ))


def _plain_signal(record: FactRecord) -> str:
    value = re.sub(r"[*_`]", "", fact_signal(record))
    value = re.sub(r"\s+", " ", value).strip()
    return value if len(value) <= 160 else value[:159].rstrip() + "…"


def render_compact_observability_appendix(
    *,
    records: Sequence[FactRecord],
    dimensions: Mapping[str, DimensionPresentation],
    supporting_fact_ids: Sequence[str] = (),
) -> str:
    supporting = set(supporting_fact_ids)
    entries: list[dict[str, str]] = []
    for dimension in OBSERVABILITY_DIMENSIONS:
        row = dimensions.get(dimension)
        record = _select_core_fact(
            records,
            dimension=dimension,
            supporting_fact_ids=supporting,
        )
        if record is not None:
            entry = {
                "dimension": dimension,
                "state": row.state if row is not None else "present",
                "source": record.source_system,
                "fact_id": record.fact_id,
                "signal": _plain_signal(record),
            }
            if record.evidence_refs:
                entry["evidence_ref"] = record.evidence_refs[0]
        else:
            state = row.state if row is not None else "not_executed"
            entry = {"dimension": dimension, "state": state}
            if state == "empty" and row is not None and row.sources:
                entry["source"] = row.sources[0]
        entries.append(entry)

    payload = {
        "contract": "observability-core-summary-v1",
        "dimensions": entries,
    }
    return "\n".join([
        "## 机器可核验附录",
        "> 仅保留本轮 Metrics、Logging、Tracing 三个维度的核心证据摘要。",
        "",
        "```json",
        json.dumps(payload, ensure_ascii=False, indent=2),
        "```",
    ])
```

- [ ] **Step 4: Complete the local test fixtures and verify GREEN**

Run the new test file. Expected: four tests pass, the standard output is byte-identical regardless of input record order, and its length is at most 1,200 Unicode characters.

- [ ] **Step 5: Record the checkpoint**

Run:

```bash
git diff --check -- \
  app/core/workflow/report_appendix.py \
  app/core/workflow/report_presentation.py \
  tests/unit/workflow/test_report_appendix.py
```

Expected: exit code 0. Do not commit; the worker handoff is the checkpoint.

### Task 5: Wire limitations and the compact appendix through the canonical postprocessor

**Files:**
- Modify: `app/core/workflow/nodes/conclusion_formatter.py:6540-6614`
- Modify: `tests/unit/workflow/test_ask_conclusion_remediation_json.py`

- [ ] **Step 1: Add a JSON appendix parser and failing end-to-end contract test**

Add this helper near `_diagnosis_report()`:

```python
def _machine_appendix_payload(report: str) -> dict:
    appendix = report.split("## 机器可核验附录", 1)[1]
    fenced = appendix.split("```json\n", 1)[1].split("\n```", 1)[0]
    return json.loads(fenced)
```

Add an integration test using one Metrics fact, one Logging fact, no Tracing fact, and a coverage record showing `tracing=empty` from Tempo:

```python
def test_canonical_report_uses_compact_appendix_after_remediation():
    entity_id = "k8s.pod:demo/api:uid-api"
    metric = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="api",
        dimension="metrics",
        fact_type="measurement",
        attribute="cpu.usage",
        value=0.42,
        unit="ratio",
        source_system="prometheus",
        evidence_ref="metric:cpu-real",
    )
    log = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="api",
        dimension="logging",
        fact_type="log",
        attribute="log.message",
        value={"message": "required configuration is missing"},
        source_system="elasticsearch",
        evidence_ref="log:config-real",
    )
    trace_coverage = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="api",
        dimension="coverage",
        fact_type="coverage",
        attribute="tracing.coverage",
        value={"dimension": "tracing", "coverage": "empty"},
        source_system="tempo",
        evidence_ref="coverage:tempo-empty",
    )
    records = [metric, log, trace_coverage]
    claim = _rca_claim(
        diagnostic_status="diagnosed",
        root_cause_summary="same-entity candidate",
        hypotheses=[{
            "hypothesis_id": "hyp-api",
            "entity_id": entity_id,
            "summary": "same-entity candidate",
            "supporting_fact_ids": [log["fact_id"]],
            "contradicting_fact_ids": [],
            "unknowns": [],
            "confidence": 0.9,
        }],
        supporting_fact_ids=[log["fact_id"]],
    )
    node = _node_with_response(_diagnosis_report(root_text="ignored model root"))
    report = node.execute({
        "question": "为什么 api Pod 异常？",
        "layer": Layer.L2,
        "layer_analysis": "{}",
        "evidence_analysis": _fact_evidence(
            _ledger("case-compact", [entity_id], records)
        ),
        "rca_analysis": claim,
        "thinking_events": [],
    })["conclusion"]
    payload = _machine_appendix_payload(report)

    assert report.index("## 🧩 结构化修复计划") < report.index(
        "## 机器可核验附录"
    )
    assert payload["contract"] == "observability-core-summary-v1"
    assert payload["dimensions"][0]["fact_id"] == metric["fact_id"]
    assert payload["dimensions"][1]["fact_id"] == log["fact_id"]
    assert payload["dimensions"][2] == {
        "dimension": "tracing", "state": "empty", "source": "tempo"
    }
    assert "### 缺失证据" in report
    assert '"remediation_contract": "fact-ledger-diagnostic-only-v1"' in report
```

- [ ] **Step 2: Run the integration test and verify RED**

Run the exact node ID above. Expected: FAIL because the report still emits `fact-ledger-authoritative-v1` and does not pass limitations into the human renderer.

- [ ] **Step 3: Replace the old appendix integration**

Import the new renderer:

```python
from app.core.workflow.report_appendix import (
    render_compact_observability_appendix,
)
```

Inside `_apply_fact_ledger_report_contract()`, derive limitations once, pass them to `render_human_report()`, retain the remediation call, then append the compact payload:

```python
limitations = derive_evidence_limitations(ledgers)
result = render_human_report(
    model_content=content,
    ledgers=ledgers,
    validated_claim=validated_claim,
    dimensions=dimensions,
    causal_chain=causal_chain,
    strict_report_authority=strict_report_authority,
    limitations=limitations,
)
result = cls._render_fact_ledger_diagnostic_remediation(
    result,
    ledgers=ledgers,
    validated_claim=validated_claim,
    display_values=[
        signal
        for dimension in dimensions.values()
        for signal in dimension.signals
    ],
)
validation = (
    validated_claim.get("claim_validation")
    if isinstance(validated_claim.get("claim_validation"), dict)
    else {}
)
supporting_fact_ids = validation.get("valid_supporting_fact_ids") or []
all_records = list({
    record.fact_id: record
    for ledger in ledgers
    for record in ledger.records
}.values())
appendix = render_compact_observability_appendix(
    records=all_records,
    dimensions=dimensions,
    supporting_fact_ids=supporting_fact_ids,
)
final_report = result.rstrip() + "\n\n---\n\n" + appendix + "\n"
return cls._neutralize_unstructured_kubectl_writes(final_report)
```

Delete the now-unused `_render_fact_ledger_appendix()` classmethod. Do not alter `_render_fact_ledger_diagnostic_remediation()` or its parser contract.

- [ ] **Step 4: Migrate old full-ledger expectations without weakening safety tests**

In these existing tests, replace assertions about every FactRecord dictionary, entity ID, metadata, `claim_fact_ids`, `limitations`, and `fact-ledger-authoritative-v1` with `_machine_appendix_payload()` assertions for exactly three dimensions and at most one Fact ID per dimension:

- `test_fact_ledger_report_renders_validated_facts_and_appendix_deterministically`
- `test_fact_ledger_report_keeps_two_pod_facts_in_their_own_sections`
- `test_fact_ledger_report_replaces_all_root_cause_sections_with_one_canonical_section`
- `test_fact_ledger_report_has_human_body_and_separate_machine_appendix`
- every remaining old-contract assertion listed by this exact command:

```bash
rg -n 'fact-ledger-authoritative-v1|claim_fact_ids|"facts"|entity_id.*appendix' \
  tests/unit/workflow/test_ask_conclusion_remediation_json.py \
  tests/unit/workflow/test_fast_paths.py
```

After migration the command must return no assertion that requires the old user-visible
appendix. References used to construct internal RCA claims or validate the internal
Fact Ledger remain unchanged.

Use this shared invariant in each migrated test:

```python
payload = _machine_appendix_payload(conclusion)
assert payload["contract"] == "observability-core-summary-v1"
assert [item["dimension"] for item in payload["dimensions"]] == [
    "metrics", "logging", "tracing"
]
assert all(
    set(item) <= {
        "dimension", "state", "source", "fact_id", "signal", "evidence_ref"
    }
    for item in payload["dimensions"]
)
```

Keep all existing assertions for deterministic output, no invented values, strict supporting-only root authority, multi-entity body isolation, diagnostic-only remediation, unexecuted truthfulness, and unsafe command neutralization.

- [ ] **Step 5: Verify GREEN for the integration file**

Run:

```bash
.venv/bin/python -m pytest -q \
  tests/unit/workflow/test_ask_conclusion_remediation_json.py
```

Expected: all tests pass. Record count, warning count, duration, and exit code.

- [ ] **Step 6: Record the checkpoint**

Run `git diff --check -- app/core/workflow/nodes/conclusion_formatter.py tests/unit/workflow/test_ask_conclusion_remediation_json.py`; expected exit code 0.

### Task 6: Prove goal-level behavior and perform independent review

**Files:**
- Verify all files in the file map
- Write execution evidence only under the dedicated agent-loop attempt paths

- [ ] **Step 1: Run focused renderer and appendix suites fresh**

Run:

```bash
.venv/bin/python -m pytest -q \
  tests/unit/workflow/test_report_presentation.py \
  tests/unit/workflow/test_report_appendix.py
```

Expected: all tests pass with exit code 0.

- [ ] **Step 2: Run prompt and end-to-end adjacent regressions**

Run:

```bash
.venv/bin/python -m pytest -q \
  tests/unit/workflow/test_fast_paths.py \
  tests/unit/workflow/test_ask_conclusion_remediation_json.py
```

Expected: all tests pass with exit code 0. Do not hide pre-existing failures; record any unrelated baseline failure separately with its exact node ID and evidence.

- [ ] **Step 3: Run syntax and whitespace checks**

Run:

```bash
.venv/bin/python -m py_compile \
  app/core/prompts.py \
  app/core/workflow/report_presentation.py \
  app/core/workflow/report_appendix.py \
  app/core/workflow/nodes/conclusion_formatter.py
git diff --check
```

Expected: both commands exit 0.

- [ ] **Step 4: Capture deterministic size evidence**

Run the standard three-dimension appendix test twice with `pytest -vv` and record the rendered appendix length from the test artifact. Run the canonical end-to-end fixture twice and record:

```text
first == second
appendix_length <= 1200
appendix_length < human_body_length
heading positions are strictly increasing
```

If the existing integration fixture does not yet assert `appendix_length < human_body_length`, add that exact assertion to `test_canonical_report_uses_compact_appendix_after_remediation` before declaring GREEN.

- [ ] **Step 5: Dispatch an independent reviewer**

The reviewer reads only the approved spec, this plan, the task contract, worker handoff, changed files, and fresh logs. It must return `ACCEPT`, `REWORK`, or `BLOCKED` and explicitly check:

```text
- default template mode remains default-off strict validation
- strict core/root/causal sections use only valid supporting Fact IDs
- incoming free-text causal chains never enter deterministic authority sections
- human heading order and row limits match the spec
- Unicode card borders align for Chinese display width
- limitations are visible, bounded, deduplicated, and absent from machine JSON
- appendix has exactly Metrics/Logging/Tracing and at most one core Fact each
- empty and not_executed remain truthful
- full internal Ledgers and diagnostic-only remediation remain intact
- no unrelated dirty file was overwritten or committed
```

- [ ] **Step 6: Integrate review feedback and close the loop**

For `REWORK`, create a new immutable attempt and rerun the affected RED/GREEN checks plus the complete Task 6 suite. Mark the task done only after an `ACCEPT` handoff cites evidence for every acceptance criterion. Update the dedicated board, metrics, lessons, and final handoff; do not alter the pre-existing `structured-context-hard-budget` loop workspace.
