# Observability 工具链验收合同

## 目标

在 32K 上下文的 Qwen Agent 中，保留 Agent 自主选择和组织查询工具的能力，同时保证大体积可观测性结果不会挤爆上下文，也不会因为确定性压缩变成不可回查的单一事实源。

目标数据流：

```text
Agent 自主调用通用工具
  -> MCP 在请求安全边界内完整返回
  -> RAW 响应完整归档
  -> AIOps 生成有损但可审计的 evidence-first ToolMessage
  -> Qwen 判断证据是否充分并按 raw_ref 或通用工具继续调查
```

确定性代码只负责规范化、去重、计数、模式抽样、上下文预算和回查引用，不选择要调用的观测工具，也不在规则层判断根因。

## 术语边界

“MCP 全量返回”指在 Agent 声明的时间窗、`max_records`、最大 series/采样点等查询安全边界内，MCP 最终序列化阶段不再隐藏删除记录或字段。它不表示无限读取整个后端。

超出查询边界的数据允许不进入本次响应，但必须通过 `counts`、`truncation.stages`、`reasons` 和可用时的 `next_cursor` 明确说明。`serialization.response_truncated` 必须准确描述 MCP 最终响应层是否又做了裁剪。

“高价值召回”不等于只保留 ERROR。它指不同语义模式至少有一个代表证据进入模型工作上下文，包括异常证据、正常负向证据、零值、`empty/absent` 和未知业务属性。未进入工作上下文的完整响应必须能够通过 `raw_ref` 回查。

## 四层通过条件

| 层级 | 必须通过的检查 |
| --- | --- |
| MCP 完整性 | Logs 请求边界内记录、Metrics series、Flow 和 Span、Topology 关系的规范记录召回率为 100%；长字段逐字保持；响应可超过旧 6 KiB；`counts` 与实际数组一致；源端限制原因明确。 |
| AIOps 投影 | Metrics 保留值/单位/时间/容器/控制标签/统计和趋势；Logs 解析 JSON 并保留原始关键信息、身份与 raw reference；Trace 区分 Flow/Span 并统一时间；不同模式、HTTP 200、INFO、零值、`empty/absent` 和未知标量可见；省略计数准确。 |
| ToolMessage 传递 | `ToolMessage.content` 与归档 `summary.txt` 完全一致；RAW 与 structured 不直接进入模型；`aiops_raw_ref` 指向完整 MCP 响应；`read_context_archive` 可分页读取；summary 不超过配置预算且不携带完整 PromQL/DSL/SQL。 |
| Qwen 行为 | 使用真实模型端点和真实注册工具 schema；能够复述核心事实、标出信息缺口、理解 coverage/truncation；需要续查时只能选择存在的工具并给出合理参数意图；不把压缩视图误报为完整事实。 |

## 失败条件

以下任一情况均视为未完成：

- 查询边界内存在无声明的记录或字段丢失；
- `matched/retrieved/returned/dropped` 与真实数组不一致；
- 任一不同语义模式在 summary 中零召回且没有可用 `raw_ref`；
- 正常 HTTP 200、INFO、零值或 `empty/absent` 被错误关键词策略删除；
- Agent 实际看到 RAW、structured 或错误的 summary 文件；
- 回查工具无法读取 `raw_ref` 或分页元数据错误；
- Qwen 虚构未注册工具、把缺失信息当成已确认事实，或忽略明确的截断状态。

## 验收样本

最低覆盖四类：

1. 启动前故障：Metrics 能分类，Logs `empty`、Trace `absent`，模型应要求 Kubernetes Event/status 证据。
2. OOM/运行时退出：状态、重启、趋势、日志、Flow/Span 可形成跨维证据链。
3. Readiness/依赖失败：零就绪、HTTP 503、依赖错误日志及 Trace 关联。
4. Liveness/Terminating：HTTP 200、正常 INFO 等负向证据仍有价值，模型不得因其“正常”而丢弃。

每次发布应分别记录本地确定性测试、历史 RAW 回放、已部署 MCP 实测和真实 Qwen 盲测结果，不能用其中一层替代另一层。

## 2026-08-21 验收记录

| 验收层 | 结果 | 证据 |
| --- | --- | --- |
| MCP 本地实现 | 通过 | 133 tests + 26 subtests；Logs 20/20、Metrics 12/12、Trace 10 Flow + 3 Span、超过 6 KiB 和 7,000 字符长证据均保持完整。 |
| AIOps 投影与工作流回归 | 通过 | 618 tests；另有实验脚本 3 tests；`py_compile` 与两个仓库 `git diff --check` 通过。 |
| 历史真实 RAW 生产投影回放 | 通过 | 68 个响应、96 条 evidence、91 条直接可见、5 条外置；81/81 个语义模式有代表证据；query 泄漏、raw_ref 失败、选择计数错误均为 0；最大 summary 2,987 字符。 |
| AICall ToolMessage/回查 | 通过 | 20 条约 20 KiB 日志响应；ToolMessage 与 summary 逐字一致、RAW 逐字归档、完整 DSL 不进入模型；offset 分页可读。 |
| 真实 Qwen | 通过 | Qwen3.6-35B-A3B 覆盖 c08/c02/c10/c09；精确读出异常和正常负向证据；c02 function call 为合法 `kubectl_describe` 且参数通过真实 schema；未虚构工具。 |
| 已部署 MCP | 未通过/尚未更新 | 当前运行中的同标签旧 Pod 对 c08 `max_records=50` 仍只返回 1 fact/1 sample，且无新合同的 `counts/truncation/serialization`。必须构建新镜像并滚动后重新验收。 |

本记录中的“本地通过”不代表线上生效。发布门槛是新 MCP 与 AIOps 镜像部署后，再用在线 c02/c08/c09/c10 重跑 MCP 完整性、ToolMessage 和 Qwen 三段链路。
