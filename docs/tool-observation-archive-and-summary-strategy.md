# 工具 Observation、归档文件与摘要策略说明

本文梳理当前 AIOps 工作流中工具执行结果的处理策略、`context_archives/<run_id>` 目录结构、以及一次实际归档样本的分析结论。

样本目录：

`/data/redis/aiops-aiops-reports-pvc-pvc-ba2f85fd-f25d-4b45-9156-a9d69bbab8d7/context_archives/782989aa5954456a`

## 当前工具结果处理链路

工具执行结果进入主 Agent 前会经过 `ObservationProcessor`。

核心流程如下：

1. MCP / builtin tool 返回原始输出 `raw_content`。
2. `ObservationProcessor.process()` 根据工具名选择处理器。
3. 系统把工具输出同时写入三个归档文件。
4. 回注给 LLM 的 `ToolMessage.content` 默认是 `summary`，不是 raw，也不是完整 structured。
5. `thinking_events` 会保存 `result=summary`，同时带上 `raw_ref`、`structured_ref`、`summary_ref` 和内存态 `structured`。
6. 下游 evidence/RCA/conclusion 主要消费 `summary` 和 evidence 组织出的结构化字段。

也就是说：**LLM 当前直接看到的是 summary；structured.json 虽然落盘，也进入部分内存事件，但不会完整作为工具 observation 文本回注给主模型。**

相关代码：

- `app/core/aicall/client.py`: `_process_tool_observation()` 负责调用 processor 并把 `summary` 回写到 ToolMessage。
- `app/core/context/observation.py`: `ObservationProcessor` 负责 raw/structured/summary 的生成。
- `app/core/context/archive.py`: `ContextArchive.write_tool_artifact()` 负责落盘。
- `app/core/workflow/nodes/evidence_collector.py`: `_extract_tool_data_from_thinking()` 会把 `summary` 作为 `tool_data.data` 传给 RCA/conclusion，并携带 refs。

## 工具分类策略

当前工具按输出风险分为三类。

### Heavy Tools

这些工具通常输出较大，会做规则提取和摘要后再回注：

- `kubectl_get_by_kind_in_cluster`
- `kubectl_get_by_kind_in_namespace`
- `kubectl_get_yaml`
- `kubectl_describe`
- `kubectl_events`
- `kubernetes_jq_query`
- `kubernetes_tabular_query`

处理特点：

- raw 全量落盘。
- structured 提取关键结构化字段。
- summary 小文本回注给 LLM。
- 如果 summary 超过 `max_observation_chars` 或上下文压力达到 80%，会触发 LLM summarizer 或截断兜底。

### Medium Tools

这些工具在输出不大时直接回注：

- `kubectl_get_by_name`
- `kubectl_find_resource`
- `kubectl_lineage_children`
- `kubectl_lineage_parents`
- `execute_prometheus_instant_query`
- `get_prometheus_target`

处理特点：

- 如果 raw 长度小于 `max_observation_chars`，summary 基本等于 raw。
- structured 通常只有 `{"status": "kept_small_output"}`，信息主要在 summary/raw。

### Full Passthrough Tools

这些工具默认全量回注，除非上下文压力过高：

- `kubectl_run_image`
- `run_bash_command`
- `fetch_runbook`

处理特点：

- summary 默认等于 raw。
- 只有上下文压力达到阈值时才触发 LLM 压缩。
- 适合保留 runbook、连通性测试、bash 结果的细节。

## Archive 目录结构说明

一次 run 的归档根目录是：

`context_archives/<run_id>/`

### `tools/`

每次工具调用会生成三类文件：

- `NNN-<node>-<tool>.raw.txt`: 工具原始输出，完整落盘，不一定回注给 LLM。
- `NNN-<node>-<tool>.structured.json`: 规则提取后的结构化对象，便于后续排查、测试和潜在再注入。
- `NNN-<node>-<tool>.summary.txt`: 实际回注给主 Agent 的观察文本，通常也是 `thinking_events[].result` 的来源。

命名示例：

- `002-evidence-kubectl_get_yaml.raw.txt`
- `002-evidence-kubectl_get_yaml.structured.json`
- `002-evidence-kubectl_get_yaml.summary.txt`

### `budget/`

每个节点调用前后记录上下文预算：

- `budget/layer.json`
- `budget/evidence.json`
- `budget/rca.json`
- `budget/conclusion.json`

主要字段：

- `context_window`: 模型上下文窗口。
- `components`: system prompt、user message、tool schema、reserved output 等组成。
- `actual_context_tokens`: 估算或实际上下文 token。
- `provider_prompt_tokens`: 如果可探测到，记录供应商返回的实际 prompt token。
- `usage_ratio`: 当前估算总占用比例。

### `handoff/`

节点间交接快照：

- `handoff/layer-to-evidence.json`
- `handoff/evidence-to-rca.json`
- `handoff/rca-to-conclusion.json`

用途：

- 证明上游传给下游的结构化内容是什么。
- 排查“哪个节点引入了历史噪音或错误结论”。
- 支持后续离线复盘。

### `node_inputs/`

节点调用 LLM 前构造出的输入：

- `node_inputs/evidence.input.json`
- `node_inputs/conclusion.input.json`

用途：

- 检查 prompt 和 user_message 是否包含预期字段。
- 排查 runbook catalog、archive refs、handoff 是否正确注入。

### `node_outputs/`

节点执行后的输出快照：

- `node_outputs/layer.output.json`
- `node_outputs/evidence.output.json`
- `node_outputs/rca.output.json`
- `node_outputs/conclusion.output.json`

用途：

- 查看工作流 state 中该节点新增了哪些字段。
- 对比 handoff 与 final state 是否一致。

### `layer/`

layer 节点额外保留：

- `layer/full_analysis.md`: layer 阶段完整分析文本，包括工具观察摘要。
- `layer/handoff.json`: layer 给 evidence 的结构化 handoff。

## 样本 run 的文件规模

本次样本总大小约 `504K`，其中：

- `tools/`: 约 `248K`
- `node_inputs/`: 约 `80K`
- `handoff/`: 约 `68K`
- `node_outputs/`: 约 `60K`
- `budget/`: 约 `24K`
- `layer/`: 约 `20K`

工具文件压缩比摘要：

| 工具文件前缀 | raw | structured | summary | summary/raw | structured/raw |
|---|---:|---:|---:|---:|---:|
| `001-layer-kubectl_get_by_kind_in_cluster` | 15616 | 1143 | 1067 | 6.8% | 7.3% |
| `002-evidence-kubectl_get_yaml` | 4813 | 1131 | 344 | 7.1% | 23.5% |
| `003-evidence-kubectl_events` | 39 | 51 | 103 | 264.1% | 130.8% |
| `004-evidence-kubectl_get_by_name` | 411 | 35 | 411 | 100.0% | 8.5% |
| `001-evidence-fetch_runbook` | 2405 | 33 | 2405 | 100.0% | 1.4% |

结论：

- 表格类和 YAML 类工具的 summary 压缩非常明显，通常只保留 7% 左右。
- YAML 的 structured 通常比 summary 更丰富，但仍远小于 raw。
- runbook 当前是 full passthrough，summary 等于 raw。
- `kubectl_get_by_name` 小输出会 passthrough，summary 等于 raw。

## 样本中发现的信息缺口

本次诊断对象是 `aiops-e2e/terminating-stuck`，异常类型是 `TerminatingStuck`。

Runbook 对该类型的关键判定项是：

- `metadata.deletionTimestamp` 是否存在。
- `metadata.finalizers` 是否非空。
- Pod 当前是否仍然存在。
- Node 是否 Ready。
- describe/events 是否显示 Killing、FailedKillPod、volume unmount/detach 等事件。

样本中的 `kubectl_get_yaml.raw.txt` 包含关键字段：

- `metadata.deletionTimestamp: "2026-04-29T06:56:00Z"`
- `metadata.finalizers: ["aiops.e2e/hold"]`
- labels/annotations 中包含 e2e 期望状态和 runbook 信息。

但当前 `structured.json` 只包含：

- kind/name/namespace
- ownerReferences
- serviceAccountName
- nodeName
- imagePullSecrets
- containers/initContainers
- volumes
- phase/reason/message
- containerStatuses

当前 `summary.txt` 只包含：

- kind/name/namespace
- serviceAccountName/nodeName
- imagePullSecrets
- phase
- containers
- containerStatuses
- volumes

所以本次存在明确缺口：

**TerminatingStuck 最关键的 `deletionTimestamp` 和 `finalizers` 在 raw 中存在，但 structured 和 summary 都没有提取。**

这会导致 LLM 虽然能看到 Pod `phase=Running`、容器 `reason=Error`，但看不到“删除已触发且 finalizer 阻塞”的最关键事实。对 TerminatingStuck 这种场景，summary 可能不足以支持高质量判断。

## 是否应该把 structured 增强回注给 LLM

建议做，但要受控。

不建议直接把完整 raw 回注给 LLM，因为：

- YAML raw 很容易包含大量 annotations、last-applied-configuration、managedFields、网络状态等噪音。
- 多次工具调用会快速膨胀上下文。
- conclusion 阶段本身输出很长，继续塞 raw 风险更高。

建议采用“summary + compact structured facts”的回注策略。

### 推荐策略

对 heavy tools，回注内容从：

```text
summary
```

升级为：

```text
summary

structured_facts:
<经过白名单筛选后的关键 structured 字段>

refs:
raw_ref=...
structured_ref=...
summary_ref=...
```

注意不是完整 structured 全量回注，而是按工具类型选择关键字段。

### `kubectl_get_yaml` 建议增强字段

Pod YAML 应补充提取并回注：

- `metadata.creationTimestamp`
- `metadata.deletionTimestamp`
- `metadata.deletionGracePeriodSeconds`
- `metadata.finalizers`
- `metadata.labels`
- `metadata.annotations` 中以 `aiops.` 开头的诊断相关字段。
- `spec.nodeName`
- `spec.terminationGracePeriodSeconds`
- `spec.tolerations`
- `spec.affinity`
- `spec.nodeSelector`
- `spec.restartPolicy`
- `status.conditions`
- `status.containerStatuses[*].state`
- `status.containerStatuses[*].lastState`
- `status.containerStatuses[*].restartCount`
- `status.containerStatuses[*].ready`

其中 TerminatingStuck 必须确保 summary/structured_facts 明确出现：

```text
deletionTimestamp: <value>
finalizers: [...]
deletionGracePeriodSeconds: <value>
```

### `kubectl_describe` 建议增强字段

Pod describe 应优先保留：

- Name/Namespace/Node/Status
- Controlled By
- Finalizers
- Conditions
- Containers state/last state/reason/exit code
- Events 中 Warning/Killing/FailedKillPod/MountVolume/FailedMount/BackOff/OOMKilled/ImagePull 相关行

### `kubectl_get_by_kind_in_cluster` 建议增强字段

当前表格摘要基本可用，但有一个问题：

- `Completed` 被异常行选中了。

Pod 异常扫描场景下建议把 `Completed/Succeeded` 视为正常终态，不应计入异常行，除非用户明确查询 Job/Completed Pod。

### `fetch_runbook`

当前 full passthrough 是合理的。runbook 本身就是“外置知识”，压缩会降低可解释性。只有当上下文压力达到 80% 时再压缩。

## 对 RCA 和 Conclusion 的影响

当前链路中：

- evidence 的 `tool_data.data` 是 summary。
- RCA 的 `_extract_tool_data_for_rca()` 只取 `tool_data.data[:500]`。
- conclusion 的 `_build_tool_data_section()` 只取 `result_preview[:300]`。

因此，即使 `structured.json` 落盘更完整，RCA/conclusion 默认也不一定能看到。

更稳的做法是：

- evidence 阶段把 compact structured facts 进入 `evidence_facts`。
- RCA 只基于 `evidence_facts + evidence_conflicts + compact tool_data` 推理。
- conclusion 不调用工具，不读 raw，只消费 evidence/RCA 已确认的事实和引用。

## 建议后续改造

### 第一阶段：修补 Pod YAML 提取缺口

优先修改 `ObservationProcessor._extract_pod_yaml()`：

- structured 增加 metadata lifecycle 字段。
- summary 增加 deletion/finalizer/conditions 等关键事实。

这是最小且收益最高的改动。

### 第二阶段：工具 observation 回注 structured facts

新增一个受控 formatter，例如：

```python
def _format_observation_for_llm(summary, structured, refs, tool_name):
    return summary + compact_structured_facts + refs
```

只对 heavy tools 启用，且字段白名单按工具类型控制。

### 第三阶段：RCA/conclusion 消费 evidence_facts

把从 structured 提取出的关键事实写入 `evidence_facts`，避免 conclusion 再读 raw。

### 第四阶段：异常类型驱动字段白名单

根据 `pod_abnormal_type` 增强字段选择：

- `TerminatingStuck`: deletionTimestamp/finalizers/nodeName/events。
- `ImagePullFailed`: image/imagePullSecrets/Secret type/events/registry connectivity。
- `OOMKilled`: resources limits/requests/lastState.terminated.exitCode/reason/restartCount。
- `PendingUnschedulable`: nodeSelector/affinity/tolerations/PVC/scheduler events。
- `VolumeMountFailed`: volumes/PVC/PV/FailedMount events。
- `NotReadyProbeFailed`: readiness/liveness/startup probes/events/logs。

## 结论

当前摘要策略已经有效降低了上下文：例如 `kubectl_get_yaml` 从 4813 字符压缩到 344 字符，只回注约 7.1%。但这个压缩对部分 Pod 异常类型过于激进。

本次样本证明：`structured.json` 确实比 `summary.txt` 更完整，而 raw 中还存在 structured 未提取的关键字段。对 TerminatingStuck 来说，`deletionTimestamp/finalizers` 是核心证据，当前没有进入 summary，是需要优先修复的缺口。

推荐方向不是回退到 raw 全量回注，而是：

**保留 raw 落盘，增强 structured 提取，把关键 structured facts 追加回注给 LLM。**

