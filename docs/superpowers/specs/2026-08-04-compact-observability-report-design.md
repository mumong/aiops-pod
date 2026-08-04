# Compact Observability Report Design

## Status

Approved in conversation on 2026-08-04. This design refines the accepted dual-mode
Fact Ledger report without changing its authority boundaries.

## Problem

The canonical report is locally correct but still has two presentation defects:

1. The compact conclusion prompt describes an older flat section list, while the
   deterministic renderer emits a different visual structure. Small models therefore
   spend output budget on Markdown that the postprocessor cannot use consistently.
2. `## 机器可核验附录` serializes every FactRecord, all claim Fact IDs, and every
   evidence limitation. In the representative strict-mode probe, the human body is
   2,013 characters while the appendix alone is 2,442 characters. The machine payload
   dominates the report instead of supporting it.

The desired report follows the supplied reference's information flow—overview,
phenomenon, collected evidence, evidence relationship, missing evidence, causal
analysis, conclusion, repair guidance, and verification—while remaining stable for
small models and honest about absent evidence.

## Goals

- Align `CONCLUSION_FORMATTER_PROMPT` with the supplied diagnostic-report reference.
- Guarantee the final Markdown layout in deterministic code instead of trusting the
  model to produce correct tables and box drawing.
- Replace evidence bullets with a compact, readable evidence table.
- Render a visually distinct three-role causal box without inventing a fourth role.
- Replace the full Fact Ledger appendix with a small Metrics/Logging/Tracing summary.
- Preserve default template mode, optional strict authority mode, unexecuted-dimension
  truthfulness, entity isolation, grounded prose, and diagnostic-only remediation.

## Non-goals

- Do not change Fact Ledger schemas or discard the full internal Ledger from workflow
  state. Only the user-visible appendix is reduced.
- Do not change how supporting or contradicting Fact IDs are validated.
- Do not allow free-text LLM causal chains into deterministic authority sections.
- Do not add fault-name-specific rendering branches.
- Do not change remediation authorization, live diagnosis, providers, MCP, Evidence
  ReAct, deployment, image tags, or version synchronization.
- Do not add an environment variable or deployment switch for report layout.

## Chosen Architecture

Use a hybrid prompt-and-renderer design:

1. The prompt asks for grounded semantic content in the same diagnostic order as the
   reference and requires Fact ID markers on every factual sentence.
2. The existing grounded-section parser accepts only sentences whose cited Fact IDs
   exist in the current Ledger and satisfy the section's authority rules.
3. The renderer owns all visible headings, tables, ordering, row limits, empty states,
   and causal box drawing.
4. The postprocessor appends the unchanged diagnostic-only remediation contract and a
   new compact observability appendix.

This separation lets the model improve explanations without allowing model formatting
quality to control the final report shape.

## Prompt Contract

`CONCLUSION_FORMATTER_PROMPT` will use the following semantic outline:

- `诊断概览`: answer first; state the affected object, status, confidence, and one
  evidence-backed core conclusion.
- `现象描述`: describe observed behavior and key entities using concrete values.
- `已采集证据`: translate raw results into readable evidence statements with source.
- `证据关联分析`: explain only relationships supported by cited facts.
- `缺失证据`: state what was not measured and how that limits the conclusion.
- `根因分析`: distinguish condition, state transition, and observed result.
- `修复建议` and `验证步骤`: remain diagnostic-only and prefer read-only validation.

The prompt will explicitly state that the system normalizes the final Markdown. The
model must emit concise grounded sentences rather than raw dictionaries, a machine
appendix, remediation JSON, ASCII boxes, or copied FactRecord objects. Every factual
sentence must end with an existing `<!-- facts:... -->` marker. The prompt must not
claim that an unexecuted query returned no data.

## Deterministic Human Report

The final visible order is fixed:

```text
# 🩺 K8s 诊断报告
## 📊 诊断概览
## 🔍 现象描述
### 关键实体
## 🕵️ 证据链
### 已采集证据
### 证据关联分析
### 缺失证据              (only when limitations exist)
## 🎯 根因分析
### 因果链                (only with at least two roles)
### 根因结论
## 🛠️ 修复建议
## ✅ 验证步骤
## 🧩 结构化修复计划       (existing safety contract)
## 机器可核验附录
```

### Diagnostic overview

Keep the current table and vocabulary:

| Item | Source |
|---|---|
| 影响对象 | entity-scoped FactRecords |
| 诊断状态 | validated claim status |
| 结论置信度 | bounded validated claim confidence |
| 核心结论 | mode-selected deterministic core FactRecord |

No unavailable layer name, issue category, or evidence-completeness percentage is
invented merely to match the reference template.

### Phenomenon and key entities

The phenomenon remains a short grounded narrative. A `### 关键实体` table follows it
when at least one entity exists:

```markdown
| 类型 | Namespace | 名称 | 当前状态/关键信号 |
|---|---|---|---|
```

Rows are grouped by entity and limited to one representative signal per entity. A
multi-entity report keeps separate rows and separate evidence subsections; entities are
never combined into one causal chain.

### Collected evidence table

Replace the current bullet list with:

```markdown
| # | 证据类型 | 数据来源 | 关键数据 | 说明 |
|---|---|---|---|---|
```

At most six rows are shown. Coverage and topology records do not occupy evidence rows.
Template mode may show all eligible high-quality core facts. Strict mode may also show
non-supporting facts in this observation table, but the `说明` wording must not promote
them to root-cause authority. Root and causal sections continue to use only validated
supporting facts in strict mode.

Evidence rows use deterministic labels and `_fact_signal()` output. Grounded model
evidence sentences may appear in `### 证据关联分析`; they do not rewrite raw fact values.

### Missing evidence

Move the human-readable part of `derive_evidence_limitations()` out of the machine
appendix and into an optional visible table:

```markdown
| 缺失项 | 影响 |
|---|---|
```

Show at most three limitations, deduplicated by `(capability, statement)` while
preserving their first-seen order. The stable human label for `capability` becomes the
`缺失项`; the limitation statement becomes the `影响`. Do not expose Fact IDs,
`applies_to`, or `source_basis` in the body. Omit the subsection when there are no
limitations.

### Causal box

Keep the already accepted three semantic roles:

- Template: `关键条件` -> `状态变化` -> `观测结果`.
- Strict: `根本原因` -> `传导机制` -> `最终表现`.

Render each present role as a framed monospace card and connect cards with a centered
down arrow. At least two roles are required. A single role produces no causal box.
Box contents are generated only from the selected FactRecords; incoming and
claim-embedded free-text chains remain ignored.

The renderer strips Markdown emphasis before placing text inside the monospace frame.
It wraps by terminal display width, treating East Asian wide characters as two cells,
so borders remain aligned for Chinese text. This uses the Python standard library and
adds no runtime dependency.

### Root conclusion

Always include `### 根因结论`. In strict mode it contains only supporting-fact prose.
In template mode it is explicitly a structured data association, not a validated root
cause. If evidence is insufficient, use the existing inconclusive wording and do not
force a causal statement.

## Compact Machine Appendix

Replace `fact-ledger-authoritative-v1` in the user-visible appendix with
`observability-core-summary-v1`:

````markdown
## 机器可核验附录
> 仅保留本轮 Metrics、Logging、Tracing 三个维度的核心证据摘要。

```json
{
  "contract": "observability-core-summary-v1",
  "dimensions": [
    {
      "dimension": "metrics",
      "state": "present",
      "source": "prometheus",
      "fact_id": "fact-metric02",
      "signal": "example 的 restart_count 为 2508",
      "evidence_ref": "prometheus:restart:1"
    },
    {
      "dimension": "logging",
      "state": "not_executed"
    },
    {
      "dimension": "tracing",
      "state": "not_executed"
    }
  ]
}
```
````

The appendix has exactly three dimension entries in this order: `metrics`, `logging`,
`tracing`.

For each dimension:

- Always include `dimension` and `state`.
- Include at most one core FactRecord.
- When a core fact exists, include one `source`, `fact_id`, plain-text `signal`, and
  first `evidence_ref` when present.
- When completed-empty coverage exists, include its real source and the truthful
  `empty` state, but no fabricated core fact.
- When neither facts nor coverage exist, emit only `dimension` and
  `state: not_executed`.

Core-fact selection is deterministic. Prefer, in order:

1. an existing validated supporting Fact ID in that dimension;
2. direct over related-context evidence;
3. strong/high evidence over weaker evidence;
4. the newest valid timestamp (a missing/invalid timestamp sorts after every valid
   timestamp);
5. lexical Fact ID as the final tie breaker.

Coverage records are never selected as a core fact. The signal is derived through the
existing readable fact formatter, stripped of Markdown markers, normalized to one
line, and capped at 160 Unicode characters. Truncation uses a single terminal ellipsis.

The appendix never contains:

- Kubernetes or topology dimensions;
- full FactRecord dictionaries;
- entity IDs or metadata;
- a global claim Fact ID list;
- limitations, `applies_to`, or `source_basis`;
- more than one evidence reference per dimension.

The canonical three-fact fixture must render an appendix no longer than 1,200 Unicode
characters and shorter than its human body. The full internal Fact Ledger remains
available in workflow state for validators and future machine consumers.

## Data Flow

```text
Fact Ledgers + validated claim + observations
                  |
                  +--> dimension presentations
                  |       |--> visible observability table
                  |       +--> compact appendix states/sources
                  |
                  +--> mode-selected FactRecords
                  |       |--> core conclusion
                  |       +--> causal roles and box
                  |
                  +--> eligible core facts
                          |--> evidence table (max 6)
                          +--> appendix selector (max 1 per observability dimension)
```

The diagnostic-only remediation payload remains between the human report and machine
appendix. Its marker and parser behavior are unchanged.

## Error and Boundary Handling

- Invalid or missing claim data remains inconclusive.
- Missing dimensions render `not_executed`/`未验证`; they never use query-completed
  language.
- Completed-empty coverage preserves the actual provider and `empty` state.
- A real signal wins over empty coverage provenance.
- An invalid/nonexistent ID listed as supporting is never dereferenced. Appendix
  selection then continues with eligible facts that actually exist in the Ledger;
  strict root selection remains supporting-only and therefore becomes inconclusive
  when no valid supporting Fact ID remains.
- Large or structured fact values are reduced through the existing readable formatter;
  raw JSON is not copied into the report.
- Multiple entities retain separate evidence and disable merged causal synthesis.
- Appendix reduction does not authorize deletion of the internal Ledger.

## Verification Strategy

Implementation follows strict RED -> GREEN cycles.

1. Prompt contract tests prove the reference-aligned semantic order, Fact marker rule,
   and prohibition on model-generated machine appendices/boxes.
2. Renderer tests prove exact heading order, key-entity table, evidence table, optional
   missing-evidence table, framed causal cards, and single-role omission.
3. Appendix tests prove exactly three ordered dimensions, deterministic one-fact
   selection, truthful empty/not-executed states, forbidden-field absence, 160-character
   signal cap, 1,200-character fixture cap, and appendix-shorter-than-body relation.
4. Existing template/strict negative authority, multi-entity isolation, grounded prose,
   machine remediation, and unexecuted-dimension tests remain green.
5. A production direct-render probe runs twice and records byte-identical output plus
   section order and size measurements.
6. Focused and adjacent regression suites run fresh, followed by independent review.

## Compatibility and Rollout

The visible appendix contract intentionally changes from a full authoritative payload
to a compact summary. Repository search found no application consumer that parses its
`facts`, `claim_fact_ids`, or `limitations`; existing references are formatter tests.
The remediation parser relies on the separate `remediation_contract` payload and is not
changed. Tests that previously treated the appendix as a full Ledger must migrate to
assert the new compact contract and confirm that full facts remain in workflow state.

No feature flag is added. This is the canonical presentation for both report authority
modes; only fact selection for core/root sections remains mode-dependent.
