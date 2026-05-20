# 小模型稳定化架构说明

本文用于交接和复盘：从 DeepSeek structured-output 版本开始，到当前 `qwen-before-architecture` 分支，为了让 Qwen3-32B-AWQ 这类本地小模型稳定完成 K8s Pod 异常诊断，系统做了哪些架构和实现层面的优化。

核心结论：这轮优化不是单纯改 prompt，而是把“不稳定的模型自由发挥”收敛成一套可审计的工作流合同。模型仍然负责理解问题、选择工具和生成解释，但代码层负责限定上下文、结构化边界、证据统计、runbook 范围和测试口径。

## 1. 历史时间线

| 时间点 | 提交/分支 | 主要含义 |
|---|---|---|
| 2026-05-12 | `bbaede4` `befor change articture` | 结构化架构改造前基线。仍存在 prompt JSON、长上下文、evidence plan 不稳定等问题。 |
| 2026-05-12 | `fd416af` `structoutput json deepseek` / `structured-deepseek` | DeepSeek 上验证 LangChain/Pydantic structured output。核心是证明结构化输出可以被后续节点消费。 |
| 2026-05-13 | `1040651` `qwen-before-architecture` 起点 | 为 Qwen 小模型回到更兼容的架构，并开始收敛 runbook、Pod abnormal 测试和自动 suite。 |
| 2026-05-13 | `d22af90` | 大规模小模型稳定化：工具摘要增强、evidence prompt 强化、rootcause 精确匹配测试体系、更多 manifest case。 |
| 2026-05-18 | `ecd6b03` | 继续补充 describe/yaml 关键字段、backlog 自动化 case、测试 README 和报告体系。 |

### DeepSeek 分支做了什么

`structured-deepseek` 的重点是确认“模型和网关支持结构化输出”：

- `AICall.call_structured()` 使用 LangChain `with_structured_output(schema)`。
- `LayerOutput`、`EvidencePlanOutput` 等 Pydantic schema 开始成为节点边界。
- structured call 默认关闭 streaming，避免流式中间块破坏结构化结果。
- 文本 JSON fallback 默认关闭，避免模型输出 fenced JSON 被误当作可靠合同。

这解决的是“结构化输出能不能被后续消费”的问题。

### Qwen 小模型分支做了什么

Qwen 分支解决的是“推理能力、注意力、上下文容量、工具选择都更弱时，如何仍然稳定诊断”的问题。核心变化包括：

- 限制模型思考模式，避免 Qwen 先生成大量 `<think>` 再工具调用。
- 减少跨节点大文本传递，用 `layer_handoff` 代替 `layer_full_analysis`。
- 工具原始输出落盘，回注给模型的是 bounded summary。
- runbook 不再当大知识库灌入，而是作为 guide，由 layer 确认后 evidence 阶段按需注入。
- evidence plan 由 Pydantic 生成和校验，不再从自由文本里猜计划。
- 证据完整度从“工具调用成功率”改成“计划项是否被真实工具结果满足”。
- 测试从“异常类型对不对”升级到“同一异常类型下根因是否精确匹配”。

## 2. 小模型的真实问题

这轮优化针对的是 Qwen3-32B-AWQ 这类本地模型的几个实际问题。

| 问题 | 旧表现 | 风险 |
|---|---|---|
| JSON 不稳定 | prompt 要求输出 JSON，但模型可能输出自然语言、fenced JSON、截断 JSON 或字段类型漂移 | 下游无法稳定消费，或者错误消费 |
| 注意力漂移 | 上游 layer 大段分析、runbook、工具结果全部塞给 evidence/RCA | 模型忘记当前 Pod、namespace、异常状态，开始泛化巡检 |
| 工具输出过长 | `kubectl describe/get yaml/get pods -A` 原文进入 agent loop | 小模型有效上下文被工具噪音占满 |
| 计划和执行脱节 | 模型先写 plan，但执行时不按 plan 或根本不调用工具 | evidence 完整度虚高或虚低 |
| runbook 过度展开 | runbook 列了所有可能原因，模型逐个查 PVC/PV/StorageClass，即使事件已明确是 ConfigMap 缺失 | 耗时长，且容易错判根因 |
| 负向证据误判 | `NotFound`、空 events、工具失败被当作“没采集”或普通失败 | 缺失对象类问题无法正确确认 |
| 同类异常根因混淆 | VolumeMountFailed 只判断 L0 就算对，没区分 ConfigMap/Secret/PVC/hostPath | 根因准确率虚高 |

所以优化目标不是“让 prompt 更详细”，而是让模型每一步都被结构、上下文和统计口径约束。

## 3. 总体架构收敛

当前 `/ask` 仍然是四节点：

```text
用户问题
  -> layer
      识别当前异常、异常组、runbook、实体、状态分布
  -> evidence
      基于 layer_handoff 生成 Pydantic evidence_plan，并调用真实工具采证
  -> rca
      不再调工具，只基于 evidence 做因果收敛
  -> conclusion
      面向用户输出 Markdown 报告，证据统计以后端结构化值为准
```

`/query` 被切成快路径：

```text
用户查询
  -> layer(query direct)
  -> conclusion(render QueryResult)
```

这个拆分很重要。查询类问题不再进入 evidence/RCA，避免“PromQL 查询失败”被小模型误解释成集群故障。

## 4. 模型 transport 层优化

配置位置：

- `deploy/configmap/config.yaml`
- `app/core/aicall/client.py`
- `tests/unit/aicall/test_event_loop_safety.py`

### 4.1 Qwen `enable_thinking=false`

当前 ConfigMap 中配置：

```yaml
llm:
  extra_body:
    chat_template_kwargs:
      enable_thinking: false
      # enable_thinking: true
```

这不是“隐藏 think 输出”，而是传给 Qwen chat template 的生成策略。关闭后，模型少生成一段 reasoning token，通常会更快进入最终回答或 tool call。

对诊断链路的价值：

- 减少每个节点的首 token 等待。
- 降低 `<think>` 混入 JSON/structured output 的概率。
- 减少 agent loop 中 AI message 的累计上下文。
- 对工具调用型任务更稳定，因为诊断依据来自真实工具结果，而不是长思考。

保留注释 `enable_thinking: true` 是为了未来需要观察推理过程时能快速开启。

### 4.2 结构化输出禁用 streaming

`AICall._call_native_structured()` 创建模型时传 `disable_streaming=True`。

原因：

- structured output 要一次性拿到完整对象。
- 流式输出中可能包含中间块、reasoning 块或不完整 JSON。
- 小模型网关对 streaming + structured 的兼容性更差。

### 4.3 文本 JSON fallback 默认关闭

`AICall.call_structured()` 默认只接受原生 structured output：

```python
use_native = True
allow_text_fallback = False
```

如果模型或网关不支持原生 structured output，就返回 `None`，而不是偷偷从自然语言里解析 JSON。

这个决策牺牲了短期兼容性，但换来边界可信：

- 不把模型随手写的 fenced JSON 当作合同。
- 不让“看起来像 JSON”的文本污染后续节点。
- 让不支持 structured output 的模型尽早暴露问题。

## 5. Pydantic 结构化边界

核心文件：

- `app/core/workflow/schemas.py`
- `app/core/aicall/client.py`
- `app/core/workflow/structured_runtime.py`

关键 schema：

| Schema | 作用 |
|---|---|
| `LayerOutput` | layer 的结构化结论，包含层级、异常 Pod、异常类型、场景、QueryResult |
| `LayerHandoff` | 下游真正消费的紧凑交接对象 |
| `IssueGroup` | 多异常组表达，例如 ImagePull、Terminating 同时存在 |
| `EvidencePlanOutput` | evidence 采证计划 |
| `EvidenceCollectionOutput` | evidence 采集结果、完整度、未采集原因 |
| `RCAOutput` | 根因、因果链、限制项 |
| `QueryResult` | `/query` 结果表格 |
| `ContextCompactionSummary` | evidence 运行时上下文压缩摘要 |

设计原则：

- prompt 描述语义，Pydantic 约束结构。
- LLM 可以字段不稳定，但下游只消费 Pydantic 校验后的对象。
- state 中保留 JSON 字符串是兼容旧前端和归档，节点内部优先用 Pydantic 对象或校验后的 dict。

## 6. `layer_handoff`：小模型注意力锚点

核心文件：

- `app/core/workflow/nodes/layer_classifier.py`

旧问题是 `layer_full_analysis` 太大，下游 evidence 和 RCA 会在上游长文本里漂移。现在 layer 生成完整分析后落盘，下游默认只拿 `layer_handoff`。

`layer_handoff` 重点字段：

```json
{
  "layer": "L1",
  "abnormal_pods": [
    {"namespace": "aiops-e2e", "name": "rc-terminating-finalizer", "status": "Terminating"}
  ],
  "abnormal_groups": [],
  "issue_groups": [],
  "current_abnormal_summary": {
    "status_counts": {"Terminating": 1},
    "selected_rows": []
  },
  "pod_status_keyword": "Terminating",
  "pod_abnormal_type": "TerminatingStuck",
  "active_entities": [],
  "active_signals": [],
  "matched_runbooks": ["pod-terminating-stuck.md"],
  "must_verify": [],
  "do_not_change": []
}
```

它对小模型的价值：

- 直接告诉模型当前有哪些异常 Pod，不让模型从长文本里找。
- 用 `current_abnormal_summary.status_counts` 锚定“当前异常状态分布”。
- 用 `issue_groups` 告诉 evidence：主异常组完整验证，非主异常组最小验证。
- 用 `matched_runbooks` 告诉 evidence：只使用 layer 已确认的 runbook，不重新选择。
- 用 `must_verify` 和 `do_not_change` 限制 namespace、Pod、Node、状态不漂移。

## 7. 工具输出治理：raw/structured/summary 三件套

核心文件：

- `app/core/context/observation.py`
- `app/core/context/archive.py`
- `app/core/aicall/client.py`

每次工具调用后系统做三件事：

```text
raw.txt        保存完整原始输出，供人工复盘
structured.json 保存规则提取出的结构化事实
summary.txt    回注给 LLM 的短摘要
```

关键点：不是只在日志里压缩，而是把 LangChain agent loop 里的 `ToolMessage.content` 也替换成 summary。否则模型下一轮仍会看到完整 describe/yaml，注意力继续被冲散。

### 7.1 `kubectl describe pod` 增强

当前 describe 摘要会提取：

- `Name / Namespace / Node / Status`
- `Termination Grace Period`
- `Controlled By`
- `QoS Class`
- `Node-Selectors / Tolerations`
- `Containers` 中的 `Image / Command / State / Reason / Exit Code / Restart Count`
- `Volumes` 中的 `ConfigMapName / SecretName / ClaimName / HostPath`
- `Events` 中的 Warning、Failed、Killing、BackOff、probe failed 等

这次修复 Terminating 场景时，重点就是让 summary 不再丢失 `Termination Grace Period`、`Command`、`Exit Code`、`Events` 这些高价值字段。

### 7.2 `kubectl get pod -o yaml` 增强

Pod YAML 摘要会提取：

- `metadata.deletionTimestamp`
- `metadata.finalizers`
- `deletionGracePeriodSeconds`
- `spec.terminationGracePeriodSeconds`
- `spec.nodeName`
- `spec.imagePullSecrets`
- `spec.containers[].command/args/lifecycle/resources`
- `spec.volumes` 中的 ConfigMap/Secret/PVC 引用
- `status.phase/reason/message`
- `status.conditions`
- `containerStatuses` 中的 waiting/terminated/lastTerminated/exitCode

这个增强是为了让模型不用读完整 YAML，也能判断：

- Terminating 是否 finalizer 卡住。
- preStop 是否存在。
- grace period 是否仍在正常窗口。
- ImagePull 是否缺 secret。
- VolumeMount 是否引用 ConfigMap/Secret/PVC。
- OOM/CrashLoop 是否有 Last State 和 exitCode。

## 8. Prompt 管理和注意力控制

核心文件：

- `app/core/prompts.py`
- `app/core/workflow/nodes/evidence_collector.py`

这轮重要调整是把 evidence 运行时拼接 prompt 收敛到 `prompts.py`，同时区分 system prompt 和 user prompt。

原则：

- system prompt 放稳定职责、格式、安全边界。
- 业务上下文放 user prompt，例如 `layer_handoff`、当前异常摘要、已确认 runbook 上下文。
- 不把 archive 路径当证据。
- 不把 runbook 当真实环境证据。
- 不把计划或工具名当证据。

### 8.1 Runbook 注入方式

当前逻辑：

1. layer 阶段可以 `fetch_runbook`。
2. layer 输出 `matched_runbooks`。
3. evidence 阶段只读取这些已确认 runbook 的关键上下文。
4. runbook 内容注入 evidence user prompt，而不是无限扩大 system prompt。

这样避免两个问题：

- 代码侧盲目注入所有 runbook，导致上下文过大。
- evidence 阶段重新选错 runbook，导致计划偏离当前异常。

### 8.2 Runbook 是 guide，不是 checklist

prompt 明确要求：

- 先看高价值当前证据，例如 describe/events/logs/yaml。
- 如果错误原文已经命中明确分支，就只验证该分支，不展开所有典型原因。
- VolumeMountFailed 先看 Pod Events 和 volume 类型；只有事件或 spec 指向 PVC/PV 时才查 PVC/PV/StorageClass。
- Terminating 优先查 `deletionTimestamp/finalizers`。
- CrashLoop/OOM 优先 describe + previous logs。
- Pending 优先 FailedScheduling 原文。

这解决了小模型“看到 runbook 很多方向就全部查一遍”的问题。

## 9. Evidence plan 和证据统计口径

核心文件：

- `app/core/workflow/nodes/evidence_collector.py`
- `app/core/workflow/schemas.py`
- `app/core/prompts.py`

当前 evidence 分成两个概念：

```text
evidence_plan       模型计划要验证什么
tool_result         真实工具返回了什么
evidence_inventory  计划项是否被真实工具满足
```

重要原则：

- 计划不是证据。
- runbook 不是证据。
- archive 不是证据。
- `NotFound`、空 events、命令失败如果正好回答检查目的，可以是负向证据。
- 实际执行但没有匹配计划的工具是补充证据，不自动抬高 plan 完整度。

### 9.1 取消自动补全计划

之前系统会根据 abnormal_groups 自动追加 plan item。这个策略容易让完整度变成代码猜测，而不是 LLM 真实计划。

当前改法：

- 不再自动补全 evidence_plan。
- 异常组覆盖通过 prompt 强约束和后续统计呈现。
- 如果 plan 没覆盖某异常组，报告中体现缺失，而不是代码悄悄帮模型补。

这让测试结果更真实，也能暴露小模型计划能力不足的问题。

### 9.2 计划归一化，不改变诊断意图

虽然不自动补计划，但会做必要的工具参数归一化：

- `kubectl get ... -o yaml` 计划必须归一化为 `kubectl_get_yaml`。
- 普通 `kubectl_get_by_name` 表格不能冒充 YAML 证据。
- `tool_args` 和 `command/purpose/evidence_type` 冲突时，优先满足诊断意图。
- 如果模型漏掉 MCP 必填字段，例如 `kind`，可从 command 中补齐 `kind/name/namespace`，避免 schema validation 失败。

这不是补计划，而是把模型已经表达出来的意图转成可执行 MCP 参数。

### 9.3 完整度公式

报告中同时保留两个口径：

| 字段 | 含义 |
|---|---|
| `plan_total` | Pydantic evidence plan 项数 |
| `plan_collected` | 已被真实工具结果满足的计划项 |
| `plan_completeness` | `plan_collected / plan_total` |
| `environment_evidence_total` | 环境证据总项，包含部分 layer_verified |
| `environment_evidence_collected` | 已采集环境证据 |
| `executed_tool_count` | 实际工具调用数 |
| `matched_tool_count` | 匹配计划的工具数 |
| `unplanned_tool_count` | 执行了但不匹配计划的工具数 |

这解释了为什么 `4/7 = 57%`：计划项是 7 个，真实匹配到 4 个，`4 / 7 = 0.5714`，展示为 57%。如果另外 3 个是未采集或没有匹配上，完整度就不能算 100%。

## 10. RCA 和 conclusion 收敛

核心文件：

- `app/core/workflow/nodes/root_cause_analyzer.py`
- `app/core/workflow/nodes/conclusion_formatter.py`
- `app/core/prompts.py`

### 10.1 RCA lite

当前默认：

```yaml
workflow:
  rca_mode: lite
```

RCA 不再调工具，只消费 evidence 结构化事实。

目的：

- 避免 RCA 重新展开工具调用，拖慢流程。
- 避免 RCA 跳出 evidence 边界，重新泛化巡检。
- 让“采证”和“推理”职责分离。

### 10.2 conclusion 只负责渲染

conclusion 默认输出 Markdown，不强制 Pydantic。原因是最终报告是面向人的文本，过强 schema 会削弱表达。

但关键统计不让 conclusion 自己算：

- 证据完整度以后端 `EvidenceCollectionOutput` 为准。
- runbook 覆盖率以后端 reporter 为准。
- root cause 优先来自 RCAOutput。

这样避免模型在最后报告里把 `1/3` 写成 `100%`。

## 11. Runbook 体系优化

核心文件：

- `deploy/configmap/runbooks.yaml`
- `app/core/aicall/builtin_tools.py`
- `tests/unit/runbook/test_runtime_catalog.py`

优化方向：

- Pod abnormal 主线只暴露与当前支持异常相关的 runbook。
- runbook 内容从“泛化知识库”改成“诊断分流 guide”。
- 每个 runbook 写清楚状态识别、必查项、关键证据、判定规则。
- 对同一状态的不同根因给出优先级，例如 VolumeMountFailed 先看 Events 原文，再决定查 ConfigMap/Secret/PVC/hostPath。

当前覆盖的异常族包括：

- Evicted
- VolumeMountFailed
- PendingUnschedulable
- TerminatingStuck
- OOMKilled
- CrashLoopBackOffRuntime
- ImagePullFailed
- SandboxCreateFailed
- ConfigError
- NotReadyProbeFailed
- NodeLostOrUnknown

## 12. 测试体系从“层级准确”升级到“根因准确”

核心目录：

- `test/pod_abnormal_e2e`
- `test/pod_rootcause_e2e`

### 12.1 pod_abnormal_e2e

这个套件验证：

- 异常类型是否识别正确。
- layer 是否正确。
- runbook 是否覆盖。
- evidence 完整度是否达到阈值。

小模型阈值已经按实际情况降到 60%，避免单次 evidence 少采一个非关键项就导致整轮失败。

### 12.2 pod_rootcause_e2e

这个套件验证更细：

- 同样是 VolumeMountFailed，要区分 ConfigMap 不存在、Secret 不存在、ConfigMap key 不存在、PVC 不存在、hostPath 错误。
- 同样是 Pending，要区分 nodeSelector、CPU 不足、Memory 不足、PVC 缺失。
- 同样是 CrashLoop，要区分非零退出码、命令不存在、配置文件缺失。

每个 case 有 `root_cause_signature`：

- `include_all`
- `include_any`
- `exclude_any`

最终统计根因准确率时，不再只看 layer=L0/L1/L2，而是看最终报告根因部分是否命中该 case 的关键语义。

当前自动化覆盖 10 个 group、26 个 case。详见：

- `test/pod_rootcause_e2e/README.md`
- `test/pod_rootcause_e2e/cases.yaml`

## 13. 两个具体例子

### 13.1 VolumeMountFailed 缺失 ConfigMap

旧行为风险：

```text
Pod 是 ContainerCreating/FailedMount
runbook 里有 PVC/PV/StorageClass/NFS/CSI/Secret/ConfigMap
小模型可能直接去查 PVC，甚至把根因说成 PVC 问题
```

当前约束：

- prompt 强调 describe/events 原文优先。
- `kubectl_describe` summary 保留 `MountVolume.SetUp failed ... configmap ... not found`。
- runbook 说明如果 Events 已命中 ConfigMap/Secret，不要继续泛化 PVC。
- rootcause E2E 通过 signature 要求最终根因命中 `configmap` 和 `not found`，否则失败。

### 13.2 Terminating finalizer 卡住

旧行为风险：

```text
describe 里出现 Exit Code 137
小模型把 137/OOMKilled 当成 Terminating 根因
忽略 finalizers/deletionTimestamp
```

当前约束：

- runbook 要求 Terminating 必查 `kubectl get pod -o yaml`。
- evidence prompt 明确 `finalizers/deletionTimestamp` 必须用 `kubectl_get_yaml`，不能用表格型 `kubectl_get_by_name` 替代。
- YAML summary 提取 `deletionTimestamp`、`deletionGracePeriodSeconds`、`finalizers`。
- describe summary 也保留 `Termination Grace Period`、`Command`、`Events`，用于区分 preStop、grace period、kubelet 停止流程。

仍需注意：如果 RCA 看到 `Exit Code 137` 后权重判断错误，仍可能把 OOMKilled 写得过重。这个属于证据排序和 RCA prompt/ranking 的后续优化点。

## 14. 当前仍然存在的边界

这些不是部署错误，而是小模型链路仍需继续优化的地方：

- 如果 OpenAI-compatible 网关不支持 `with_structured_output` 或 agent `response_format`，结构化输出仍可能失败。
- Qwen 关闭 thinking 后速度更快，但复杂推理可能更依赖工具证据质量和 prompt 边界。
- RCA 仍可能误用次要信号，例如 Terminating 场景中过度解释 `Exit Code 137`。
- evidence plan 现在不自动补全，因此计划漏项会真实暴露为完整度下降。
- 工具参数归一化只能修复已表达出的 command 意图，不能替模型创造缺失计划。
- rootcause signature 依赖关键词/语义匹配，仍需要按实际报告迭代同义词，例如 `not found` 与 `不存在`。

## 15. 重新部署前检查清单

重新部署验证前建议检查：

```bash
git status --short
.venv/bin/python -m pytest tests/unit/workflow/test_evidence_dynamic_stop.py -q
.venv/bin/python -m py_compile app/core/workflow/nodes/evidence_collector.py app/core/context/observation.py app/core/prompts.py
```

部署后确认：

```bash
kubectl get pods,deploy,svc -n aiops -o wide
kubectl logs deployment/aiops-copilot -n aiops --tail=300
```

重点看日志：

- `MODEL_CONTEXT_WINDOW` 是否正确。
- `enable_thinking=false` 是否仍在 ConfigMap。
- `context_budget` 是否显示 evidence 输入没有异常膨胀。
- `kubectl_describe 摘要` 是否包含 Pod 关键区块。
- evidence 阶段是否真正调用 `kubectl_get_yaml`，而不是用 `kubectl_get_by_name` 代替 YAML。
- evidence 统计中 `plan_total / plan_collected / environment_evidence_total` 是否合理。

## 16. 文件索引

| 主题 | 文件 |
|---|---|
| 模型调用、structured output、工具 agent loop | `app/core/aicall/client.py` |
| Pydantic schema | `app/core/workflow/schemas.py` |
| layer handoff 和异常组 | `app/core/workflow/nodes/layer_classifier.py` |
| evidence plan、匹配、完整度 | `app/core/workflow/nodes/evidence_collector.py` |
| RCA lite | `app/core/workflow/nodes/root_cause_analyzer.py` |
| conclusion 后处理和证据统计强制替换 | `app/core/workflow/nodes/conclusion_formatter.py` |
| prompt 统一管理 | `app/core/prompts.py` |
| 工具 raw/structured/summary | `app/core/context/observation.py` |
| context archive | `app/core/context/archive.py` |
| context budget | `app/core/context/budget.py` |
| Qwen thinking 配置 | `deploy/configmap/config.yaml` |
| Pod abnormal runbooks | `deploy/configmap/runbooks.yaml` |
| 异常类型 E2E | `test/pod_abnormal_e2e` |
| 精确根因 E2E | `test/pod_rootcause_e2e` |

## 17. 总结

这轮小模型适配的本质是把诊断系统从“模型自己读长上下文并自由组织 JSON”改造成“模型在受控上下文中调用真实工具，代码用 Pydantic 和证据统计收口”。

具体收益：

- 小模型不用在长文本里找当前对象，`layer_handoff` 已经给出锚点。
- 小模型不用读完整工具输出，summary 保留关键字段，raw 落盘可审计。
- 小模型不用手写结构化 JSON，Pydantic 负责边界。
- 小模型不会把 runbook 当事实，runbook 只是 guide。
- 小模型的计划漏项、工具漏调、根因误判都能通过 E2E 统计暴露，而不是被自动补全掩盖。

这套机制不能让小模型变成大模型，但能把它的自由度限制在可验证、可复盘、可迭代的诊断闭环里。
