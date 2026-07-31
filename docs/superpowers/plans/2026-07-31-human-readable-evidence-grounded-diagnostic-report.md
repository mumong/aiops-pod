# Human-Readable Evidence-Grounded Diagnostic Report Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce concise, human-readable `/ask` reports that explain validated evidence, show every available Logging and Tracing signal, and retain the complete machine-verifiable appendix and remediation safety contract.

**Architecture:** Add a pure presentation module between validated evidence and final Markdown. It groups evidence by generic dimension, retains model prose only when it cites valid facts and introduces no unsupported exact literal, and supplies a readable deterministic fallback. `ConclusionFormatterNode` remains the orchestration boundary and continues to append immutable audit and remediation payloads.

**Tech Stack:** Python 3, Pydantic v2 `FactLedger`/`FactRecord`, Markdown, pytest.

---

## File map

- Create `app/core/workflow/report_presentation.py`: fault-agnostic evidence projection, grounded narrative filtering, and human Markdown rendering.
- Create `tests/unit/workflow/test_report_presentation.py`: focused behavior tests across unrelated Pod failures.
- Create `tests/fixtures/observability/a006_human_report_replay.json`: sanitized local replay containing canonical facts and Kubernetes previous logs.
- Modify `app/core/prompts.py`: concise conclusion contract and hidden fact-reference protocol.
- Modify `app/core/workflow/nodes/conclusion_formatter.py`: integrate the presentation module without changing the machine/remediation contracts.
- Modify `tests/unit/workflow/test_fast_paths.py`: Prompt, replay, and genericity integration coverage.
- Modify `tests/unit/workflow/test_ask_conclusion_remediation_json.py`: Fact Ledger report and remediation safety coverage.
- Create `docs/human-readable-diagnostic-reports.md` and modify `README.md`: user and extension documentation.

### Task 1: Lock the concise Prompt contract

**Files:**
- Modify: `tests/unit/workflow/test_fast_paths.py`
- Modify: `app/core/prompts.py:618-863`

- [ ] **Step 1: Add failing Prompt tests**

```python
def test_conclusion_prompt_is_human_focused_and_grounded():
    prompt = CONCLUSION_FORMATTER_PROMPT
    for heading in (
        "诊断概览", "现象描述", "关键证据", "证据关联与因果链",
        "根因结论", "修复建议", "验证步骤", "注意事项",
    ):
        assert heading in prompt
    assert "<!-- facts:fact-id[,fact-id...] -->" in prompt
    assert "Markdown 粗体" in prompt
    assert "正文不展示 Fact ID、entity ID 或 JSON" in prompt
    assert "背景证据不得升级为根因" in prompt


def test_conclusion_prompt_does_not_teach_one_fault_scenario():
    prompt = CONCLUSION_FORMATTER_PROMPT
    for scenario in ("OOMKilled", "ImagePullBackOff", "ConfigError", "TerminatingStuck"):
        assert scenario not in prompt
    assert len(prompt) < 6000
```

- [ ] **Step 2: Run the tests and verify RED**

```bash
pytest -q \
  tests/unit/workflow/test_fast_paths.py::test_conclusion_prompt_is_human_focused_and_grounded \
  tests/unit/workflow/test_fast_paths.py::test_conclusion_prompt_does_not_teach_one_fault_scenario
```

Expected: both fail because the current Prompt is 7,688 characters, contains scenario-specific text, and lacks grounded hidden refs.

- [ ] **Step 3: Replace `CONCLUSION_FORMATTER_PROMPT` with this compact contract**

```python
CONCLUSION_FORMATTER_PROMPT = """
# 任务
把已验证诊断事实写成给人看的 Markdown 报告。先回答问题，再解释证据；准确但不展示内部合同实现。

# 事实边界
- 精确值、状态、实体、来源和因果只能来自 validated FactRecords 或 source-backed observations。
- 可观测性使用本轮全部有效证据，不限于 RCA supporting facts；背景证据不得升级为根因。
- 不补算、不猜测。真实空结果写“查询完成，当前窗口未发现匹配记录”。
- 正文不展示 Fact ID、entity ID 或 JSON；机器字段留在底部附录。
- 每个事实段落末尾添加 `<!-- facts:fact-id[,fact-id...] -->`，只引用输入中存在的完整 Fact ID。
- 没有 Fact ID 的 source-backed observation 只能进入可观测性摘要，并标明真实工具来源。

# 写作
- 使用：诊断概览、现象描述、关键证据、可观测性摘要、证据关联与因果链、根因结论、修复建议、验证步骤、注意事项。
- 解释“信号说明什么”，不要逐字段抄写。
- 核心实体、状态、错误、指标和值使用 Markdown 粗体。
- 语气明确、简洁；不输出内部权威性、模型限制或合同教学。

# 安全
- 根因只使用 validated supporting facts；不同实体、时间窗口或 trace_id 不拼接。
- 未提供 typed Remediation Policy 时只给人工处理和只读验证，不生成 Kubernetes 写命令。
- 保留调用方提供的结构化修复计划合同。
"""
```

- [ ] **Step 4: Run Step 2 and verify `2 passed`**

- [ ] **Step 5: Commit**

```bash
git add app/core/prompts.py tests/unit/workflow/test_fast_paths.py
git commit -m "refactor: focus conclusion prompt on human reports"
```

### Task 2: Build a fault-agnostic display projection

**Files:**
- Create: `app/core/workflow/report_presentation.py`
- Create: `tests/unit/workflow/test_report_presentation.py`

- [ ] **Step 1: Write failing mixed-provider tests**

```python
def test_real_signal_wins_over_empty_provider_coverage():
    rows = build_dimension_presentations([ledger([
        fact(dimension="logging", fact_type="coverage", source_system="elasticsearch",
             value={"coverage": "empty"}),
        fact(dimension="logging", fact_type="log", source_system="kubernetes",
             attribute="container.previous_log",
             value={"message": "required configuration is missing"}),
    ])])
    row = rows["logging"]
    assert row.state == "partial"
    assert row.sources == ("kubernetes",)
    assert "required configuration is missing" in row.signals[0]
    assert "未获取到" not in row.render_markdown()


def test_deepflow_is_visible_when_tempo_is_empty():
    rows = build_dimension_presentations([ledger([
        fact(dimension="tracing", fact_type="flow", source_system="deepflow",
             attribute="l7_flow", value={"request_type": "GET",
             "request_resource": "/healthz", "response_code": 200,
             "duration_us": "26577"}),
        fact(dimension="tracing", fact_type="coverage", source_system="tempo",
             value={"coverage": "empty"}),
    ])])
    row = rows["tracing"]
    assert row.state == "partial"
    assert "**GET /healthz**" in row.signals[0]
    assert "**200**" in row.signals[0]
```

Add one parameterized test using `OOMKilled`, `CreateContainerConfigError`, and `ErrImagePull` as ordinary fact values. Assert all three use identical headings and call paths.

- [ ] **Step 2: Run `pytest -q tests/unit/workflow/test_report_presentation.py` and verify import failure**

- [ ] **Step 3: Implement the pure public API**

```python
@dataclass(frozen=True)
class DimensionPresentation:
    dimension: str
    label: str
    state: str
    sources: tuple[str, ...]
    signals: tuple[str, ...]
    evidence_refs: tuple[str, ...]

    def render_markdown(self) -> str:
        source = "、".join(self.sources) or "已执行的数据源"
        signal = "<br>".join(self.signals) or "查询完成，当前窗口未发现匹配记录"
        state = {"present": "已有数据", "partial": "部分数据", "empty": "查询完成"}[self.state]
        return f"| **{self.label}** | {source} | {state} | {signal} |"


def build_dimension_presentations(
    ledgers: Sequence[FactLedger],
    observations: Sequence[Mapping[str, object]] = (),
) -> dict[str, DimensionPresentation]:
    """Build display rows by evidence dimension, never by fault name."""
```

Implementation rules:

- any non-coverage record is a substantive signal;
- records plus empty/error/weak provider coverage produce `partial`, and `empty` is used only with no substantive signal;
- visible sources are providers that supplied substantive signals;
- a Kubernetes log observation is accepted only when `semantic_success is True`, its tool is an existing log tool, and `structured.selected_lines` is non-empty;
- cap each dimension at three signals and 600 visible characters;
- render generic entity, attribute, unit, log `message`, request method/resource, response code, duration, and trace ID fields; never inspect a fault name to select output.

- [ ] **Step 4: Run the new module tests and verify GREEN**

- [ ] **Step 5: Commit**

```bash
git add app/core/workflow/report_presentation.py tests/unit/workflow/test_report_presentation.py
git commit -m "feat: add generic diagnostic evidence presentation"
```

### Task 3: Keep only fact-grounded AI narrative

**Files:**
- Modify: `app/core/workflow/report_presentation.py`
- Modify: `tests/unit/workflow/test_report_presentation.py`

- [ ] **Step 1: Add failing narrative tests**

```python
def test_grounded_paragraph_is_kept_and_hidden_refs_removed():
    text = "容器状态为 **ErrImagePull**。 <!-- facts:fact-state -->"
    result = keep_grounded_narrative(
        text,
        records={"fact-state": state_record},
        allowed_fact_ids={"fact-state"},
    )
    assert "ErrImagePull" in result
    assert "fact-state" not in result
    assert "<!--" not in result


def test_unknown_ref_or_exact_value_is_rejected():
    assert keep_grounded_narrative(
        "峰值为 **999Mi**。 <!-- facts:fact-metric -->",
        records={"fact-metric": metric_record},
        allowed_fact_ids={"fact-metric"},
    ) == ""
    assert keep_grounded_narrative(
        "状态已确认。 <!-- facts:fact-unknown -->",
        records={"fact-state": state_record},
        allowed_fact_ids={"fact-state"},
    ) == ""
```

- [ ] **Step 2: Run the two node IDs and verify missing-function failures**

- [ ] **Step 3: Implement the hidden-ref and exact-literal validator**

```python
FACT_MARKER = re.compile(r"<!--\s*facts:([^>]+)\s*-->")
EXACT_LITERAL = re.compile(
    r"`[^`]+`|\b\d+(?:\.\d+)?(?:Mi|Gi|Ki|ms|us|s|%|bytes?)?\b|\b[0-9a-f]{16,64}\b",
    re.IGNORECASE,
)


def keep_grounded_narrative(text, *, records, allowed_fact_ids):
    match = FACT_MARKER.search(text or "")
    if not match:
        return ""
    cited = {item.strip() for item in match.group(1).split(",") if item.strip()}
    if not cited or not cited <= allowed_fact_ids or not cited <= records.keys():
        return ""
    visible = FACT_MARKER.sub("", text).strip()
    inventory = " ".join(
        json.dumps(records[item].model_dump(mode="json"), ensure_ascii=False)
        for item in sorted(cited)
    )
    if any(token.strip("`") not in inventory for token in EXACT_LITERAL.findall(visible)):
        return ""
    return visible
```

Observation prose may cite every valid Ledger fact. Causal/root-cause prose may cite only `claim_validation.valid_supporting_fact_ids`. Narrative never authorizes remediation.

- [ ] **Step 4: Run `pytest -q tests/unit/workflow/test_report_presentation.py` and verify GREEN**

- [ ] **Step 5: Commit**

```bash
git add app/core/workflow/report_presentation.py tests/unit/workflow/test_report_presentation.py
git commit -m "feat: validate fact-grounded report narrative"
```

### Task 4: Integrate the human body and preserve machine contracts

**Files:**
- Modify: `app/core/workflow/nodes/conclusion_formatter.py:206-430`
- Modify: `app/core/workflow/nodes/conclusion_formatter.py:4302-5255`
- Modify: `tests/unit/workflow/test_ask_conclusion_remediation_json.py`

- [ ] **Step 1: Add failing end-to-end assertions**

Create a diagnosed Fact Ledger report with valid model hidden refs and background Logging/Tracing facts:

```python
for phrase in (
    "权威结论仅由", "未验证的模型叙述",
    "当前可核验现象仅见", "本节不保留模型生成",
):
    assert phrase not in report
assert "**CrashLoopBackOff**" in report
assert "**required configuration is missing**" in report
body, appendix = report.split("## 机器可核验附录", 1)
assert "fact-" not in body
assert '"attribute"' not in body
assert "fact-ledger-authoritative-v1" in appendix
```

Add a second test whose model output invents an exact value. Assert that sentence is absent and a generic readable fallback is present.

- [ ] **Step 2: Run the two new tests and verify RED**

- [ ] **Step 3: Pass source-backed observations into the contract**

```python
def _apply_fact_ledger_report_contract(
    cls,
    content: str,
    *,
    ledgers: List[FactLedger],
    validated_claim: Dict[str, Any],
    observations: Sequence[Mapping[str, object]] = (),
) -> str:
```

Parse `evidence_analysis` once at the `execute()` call site and pass its `tool_data` list. Do not read archive files during rendering; observations must already be in state and have `semantic_success=True`.

- [ ] **Step 4: Replace the machine-like shell with the presentation builder**

```python
dimensions = build_dimension_presentations(ledgers, observations)
human_report = render_human_report(
    model_content=content,
    ledgers=ledgers,
    validated_claim=validated_claim,
    dimensions=dimensions,
)
safe_report = cls._render_fact_ledger_diagnostic_remediation(
    human_report, ledgers=ledgers, validated_claim=validated_claim,
)
appendix = cls._render_fact_ledger_appendix(
    diagnostic_status=status, records=referenced_records,
)
return cls._neutralize_unstructured_kubectl_writes(
    safe_report.rstrip() + "\n\n---\n\n" + appendix + "\n"
)
```

Keep appendix rendering, remediation normalization, entity-scope validation, and claim validation unchanged. Remove the human-facing call sites of `_format_deterministic_fact_report_shell`, `_enforce_fact_ledger_diagnosis_overview`, and `_enforce_fact_ledger_phenomenon` after migration.

- [ ] **Step 5: Run focused safety suites**

```bash
pytest -q \
  tests/unit/workflow/test_report_presentation.py \
  tests/unit/workflow/test_ask_conclusion_remediation_json.py \
  tests/unit/remediation/test_plans.py
```

Expected: all pass; no-policy output still parses as `manual_only`, `requires_human_approval=true`, `actions=[]`.

- [ ] **Step 6: Commit**

```bash
git add app/core/workflow/nodes/conclusion_formatter.py tests/unit/workflow/test_ask_conclusion_remediation_json.py
git commit -m "feat: render human-readable fact ledger reports"
```

### Task 5: Reproduce A006 offline without agent-loop dependencies

**Files:**
- Create: `tests/fixtures/observability/a006_human_report_replay.json`
- Modify: `tests/unit/workflow/test_fast_paths.py`
- Modify: `app/core/workflow/report_presentation.py`

- [ ] **Step 1: Create the sanitized fixture**

Include only canonical Kubernetes/Prometheus/DeepFlow facts, ES Logging `coverage=empty`, a successful `kubectl_previous_logs` observation with `structured.selected_lines` and archive refs, and the validated claim. Do not include `data/agent-loop` paths, evaluator labels, or expected-answer fields.

- [ ] **Step 2: Add the failing replay test**

```python
def test_a006_replay_shows_previous_logs_and_deepflow_in_human_body():
    report = render_replay(load_json_fixture("observability/a006_human_report_replay.json"))
    body, appendix = report.split("## 机器可核验附录", 1)
    logging = table_row(body, "Logging")
    tracing = table_row(body, "Tracing")
    assert "kubectl_previous_logs" in logging
    assert "2 MiB" in logging
    assert "未获取到" not in logging
    assert "DeepFlow" in tracing
    assert "GET" in tracing and "/allocate" in tracing and "200" in tracing
    assert "未获取到" not in tracing
    assert "fact-" not in body
    assert "fact-" in appendix
```

- [ ] **Step 3: Run the replay node ID and verify RED**

- [ ] **Step 4: Adjust only generic observation normalization until GREEN**

Production logic may inspect tool class, dimension, source, coverage, structured fields, and evidence refs. It may not inspect the fixture name, workload name, endpoint, OOM token, or error string.

- [ ] **Step 5: Run tests and genericity scan**

```bash
pytest -q tests/unit/workflow/test_report_presentation.py \
  tests/unit/workflow/test_fast_paths.py::test_a006_replay_shows_previous_logs_and_deepflow_in_human_body
rg -n "if .*OOM|elif .*OOM|match .*OOM|trace-oom|a006" \
  app/core/workflow/report_presentation.py app/core/prompts.py
```

Expected: tests pass and the production scan returns no match.

- [ ] **Step 6: Commit**

```bash
git add tests/fixtures/observability/a006_human_report_replay.json \
  tests/unit/workflow/test_fast_paths.py app/core/workflow/report_presentation.py
git commit -m "test: replay mixed-source human observability report"
```

### Task 6: Document and verify the completed feature

**Files:**
- Create: `docs/human-readable-diagnostic-reports.md`
- Modify: `README.md`

- [ ] **Step 1: Document the extension contract**

Explain the human-body/machine-appendix boundary, mixed-provider precedence, hidden Fact refs, generic evidence attributes, background-versus-causal evidence, and unchanged manual-only remediation behavior. Link the document from the README.

- [ ] **Step 2: Check documentation**

```bash
git diff --check
rg -n "T[B]D|TO[D]O|PLACE[H]OLDER" docs/human-readable-diagnostic-reports.md README.md
```

Expected: whitespace check succeeds and placeholder scan has no match.

- [ ] **Step 3: Run the extended regression**

```bash
pytest -q \
  tests/unit/workflow/test_report_presentation.py \
  tests/unit/workflow/test_fact_contract.py \
  tests/unit/workflow/test_fast_paths.py \
  tests/unit/workflow/test_ask_conclusion_remediation_json.py \
  tests/unit/remediation/test_plans.py \
  tests/unit/aicall/test_observation_processing.py
```

Expected: exit code 0.

- [ ] **Step 4: Render and inspect the offline replay**

Write the derived report under a directory created by `mktemp -d`, inspect readability and appendix completeness, then leave it uncommitted. Do not create or modify `data/agent-loop` artifacts.

- [ ] **Step 5: Audit all eleven design acceptance items**

Record command or rendered-output evidence for prohibited phrases, mixed-source Logging, partial Tracing, bold values, no machine IDs in the body, causal separation, remediation safety, fallback behavior, three unrelated failures, and A006 replay.

- [ ] **Step 6: Commit documentation**

```bash
git add README.md docs/human-readable-diagnostic-reports.md
git commit -m "docs: explain evidence-grounded human reports"
```

- [ ] **Step 7: Verify branch state**

```bash
git status --short --branch
git log -8 --oneline --decorate
```

Expected: no uncommitted project changes; only the planned report commits are ahead of the remote branch.
