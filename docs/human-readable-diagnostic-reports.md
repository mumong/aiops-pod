# 人类可读、以真实数据为核心的诊断报告

`/ask` 的最终报告由 conclusion 节点单次 LLM 调用生成：
system prompt 是 `app/core/prompts.py` 中的 `CONCLUSION_FORMATTER_PROMPT` 富模板，
用户消息注入前三个阶段的分析结果和工具采集的真实可观测性数据。
报告的结构稳定性来自这份富模板本身，不再依赖任何事后正则矫正或确定性重渲染。

> 历史说明：早期版本采用「LLM 语义草稿 + `<!-- facts:id -->` 标记 +
> `report_presentation.py` 确定性渲染 + 12 步正则矫正链」的架构，
> 对小模型不友好且输出不稳定，已于 2026-08-04 移除。

## 报告模板

`CONCLUSION_FORMATTER_PROMPT` 固定输出以下章节（Markdown）：

1. `## 📊 诊断概览` — Pod 异常状态、分类、置信度、证据完整度表格
2. `## 🔍 现象描述` — 用户报告 + 关键实体表格
3. `## 🕵️ 证据链` — "真实采集证据结果"表（每行标注类型：Metric / Logging / Tracing / Topology / K8s Event / K8s State / K8s Config，含**原始数据列**）+ 紧跟的证据关联分析 + 缺失证据（同样带类型列）
4. `## 🎯 根因分析` — ASCII 因果链 + 引用证据编号的根因结论
5. `## 🛠️ 修复建议` — 可直接执行的命令，按优先级排序
6. `## 📋 验证步骤` — 命令 + 预期结果表格
7. `## ⚠️ 注意事项`
8. `## 🧩 结构化修复计划` — 由 `REMEDIATION_PLAN_PROMPT` 约定的 JSON block，
   供 post-diagnosis remediation executor 解析（`app/core/remediation/plans.py`）

## 真实数据如何进入报告

conclusion 的用户消息固定 5 段（`conclusion_formatter.py`）：

| 段落 | 来源 | 说明 |
|------|------|------|
| 用户问题 | `state["question"]` | 报告必须开头直接回答 |
| 阶段1：问题定位 | `layer_handoff`（回退 `layer_analysis`） | 异常状态/实体/场景 |
| 阶段2：证据采集摘要 | `evidence_analysis` JSON 压缩 | 完成度、清单、缺失项 |
| 阶段3：根因分析 | `rca_analysis` JSON 压缩 | 根因、因果链、置信度（经 fact-id 校验） |
| 工具采集的真实数据 | `thinking_events` 中 `tool_result` 事件 | **可观测性工具**从 `ev[structured].facts` 结构化提取真实值（metric `name=value unit（趋势）`、tracing `请求→响应码 + trace_id`、logging 日志原文；QUERY DSL 噪声丢弃，超限只丢整条事实、绝不砍值，`coverage=empty` 如实呈现）；**K8s 等工具**用 `result` 文本头尾保护截断（单条 ≤1500 字符）；总量最多 24 条 |

防幻觉边界由三层保证（都不修改 LLM 散文）：

1. **采集层**：`ObservationProcessor` 把工具原始输出压缩为有界真实摘要并归档，
   可观测性工具产出标准 `FactRecord`/`FactLedger`。
2. **RCA 层**：`validate_rca_claims`（`fact_contract.py`）校验根因引用的 fact-id
   必须真实存在，无效引用会把结论降级为 inconclusive。
3. **模板层**：`CONCLUSION_FORMATTER_PROMPT` 明确要求"只用真实数据、缺就写缺"，
   证据链原始数据列只能摘自输入的工具真实数据。

## 快速路径与回退

- HEALTHY：确定性健康摘要，不调 LLM。
- QUERY direct：直接渲染上游 `query_result` 结构化表格，不调 LLM。
- QUERY（LLM 路径）：短 JSON schema（`QueryConclusionOutput`）总结查询结果。
- 诊断路径 LLM 失败或返回空：`_format_with_template` 确定性回退，
  直接展示三个阶段的真实结果。

## 修复安全合同

`REMEDIATION_PLAN_PROMPT` 要求所有写动作 `requires_human_approval=true`，
executor 在执行前中断等待审批（`workflow.remediation.mode: review`）。
不适合自动修复时输出 `"remediation_available": false` 和空 actions。

## 回归验证

```bash
pytest -q \
  tests/unit/workflow \
  tests/unit/remediation/test_plans.py
```
