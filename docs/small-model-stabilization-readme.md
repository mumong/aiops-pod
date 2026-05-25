# 32B 小模型稳定化研究报告

本文用于复盘从 DeepSeek 大模型/结构化输出版本切换到 Qwen3-32B-AWQ 这类本地小模型后，为了让 AIOps Copilot 稳定完成 Kubernetes Pod 异常诊断所做的体系化优化。

这不是一次简单的 prompt 调整。实际工作更接近一次“把自由生成式 Agent 改造成可审计诊断系统”的工程研究：小模型仍然负责理解用户意图、选择工具、组织解释，但系统通过工作流拆分、Pydantic 合同、上下文压缩、工具摘要、runbook 收敛、证据统计和 E2E 标注集，把模型的自由度限制在可验证、可复盘、可迭代的范围内。

## 1. 研究结论

### 1.1 核心结论

32B 小模型在 K8s 诊断 Agent 中最主要的问题不是“完全不会诊断”，而是稳定性不足：

- 长上下文下容易注意力漂移，忘记当前 Pod、namespace、异常状态。
- 工具调用 loop 中容易过度探索、重复调用、按 runbook 全量巡检。
- 结构化输出容易失败，尤其是 JSON/Pydantic schema、RCAOutput、evidence_plan 这类合同。
- 同一种 Pod 异常类型下容易只判断大类，不区分精确根因。
- 最终报告会把次要信号写成主因，例如 Terminating 场景误写 finalizer、OOMKilled、kubelet。

有效方法不是继续堆更长 prompt，而是把任务拆成多个硬边界：

```text
用户问题
  -> layer：只定位当前异常对象和异常族
  -> evidence：只围绕 layer_handoff 采集真实证据
  -> rca：只基于 evidence 做因果收敛，不重新调用工具
  -> conclusion：只渲染报告，关键指标以后端结构化结果为准
```

最终形成的有效策略可以概括为：

- 用 `layer_handoff` 替代跨节点大文本，给小模型固定注意力锚点。
- 用 raw/structured/summary 三件套治理工具输出，让模型只看短事实，完整原文落盘。
- 用 Pydantic schema 和 `response_format` 把关键节点从“写 JSON”改成“生成可校验对象”。
- 用 evidence_plan + tool_result 匹配，把“计划”和“证据”分离。
- 用 runbook guide 化，避免小模型把 runbook 当成全量 checklist。
- 用 rootcause E2E 标注集衡量精确根因，而不是只看 layer 是否正确。

### 1.2 量化结果

当前 `test/pod_rootcause_e2e` 已汇总两批稳定性测试结果：

| 数据集 | 覆盖 | 诊断次数 | 说明 |
|---|---:|---:|---|
| `testreports/pod_rootcause_suite_20260513_184055` | 7 group / 21 case | 1050 | v1-core 稳定夜间检查 |
| `testreports/pod_rootcause_suite_20260519_162052` | 3 group / 5 case | 250 | backlog-auto：terminating/sandbox/evicted |
| 合计 | 10 group / 26 case | 1300 | 当前自动化可复现根因套件 |

整体结果：

| 指标 | 当前结果 |
|---|---:|
| 根因准确率 | 82.2% |
| Runbook 覆盖率 | 99.6% |
| 平均证据率 | 90.7% |
| 平均 MTTR | 5.4m |

Group 级结果：

| Group | Case | Run | 根因准确率 | Runbook 覆盖率 | 平均证据率 | 平均 MTTR |
|---|---:|---:|---:|---:|---:|---:|
| volumemount | 5 | 250 | 98.4% | 100.0% | 91.2% | 4.2m |
| pending | 4 | 200 | 79.5% | 100.0% | 94.3% | 5.2m |
| imagepull | 3 | 150 | 78.7% | 100.0% | 82.1% | 5.5m |
| crashloop | 3 | 150 | 95.3% | 100.0% | 90.5% | 6.3m |
| configerror | 3 | 150 | 80.7% | 100.0% | 90.6% | 4.3m |
| oomkilled | 1 | 50 | 100.0% | 100.0% | 95.8% | 6.0m |
| notready | 2 | 100 | 60.0% | 95.0% | 90.5% | 7.8m |
| terminating | 3 | 150 | 56.7% | 100.0% | 95.9% | 5.5m |
| sandbox | 1 | 50 | 96.0% | 100.0% | 93.3% | 6.6m |
| evicted | 1 | 50 | 78.0% | 100.0% | 76.9% | 6.0m |

这些数据说明：小模型在工具证据充足、状态信号清晰的场景上已经可用，例如 volumemount、crashloop、oomkilled、sandbox；但在需要区分相近生命周期原因的场景上仍然薄弱，例如 terminating、notready。

## 2. 背景：为什么 32B 小模型会出问题

### 2.1 大模型到小模型的能力差异

DeepSeek 这类线上大模型对长上下文、多轮工具调用、隐式格式约束、复杂因果链更鲁棒。切换到 Qwen3-32B-AWQ 后，模型不是不能做，而是更容易在以下边界失稳：

| 维度 | 大模型常见表现 | 32B 小模型常见表现 |
|---|---|---|
| 长上下文 | 能从长工具输出里抓重点 | 被 describe/yaml/events 噪声冲散 |
| 工具选择 | 能按目标挑选关键工具 | 容易重复查、泛化查、查错资源 |
| 结构化输出 | 更容易遵守 JSON/schema | 容易输出自然语言、字段漂移、结构缺失 |
| 多阶段记忆 | 能记住上游意图 | 下游 evidence/RCA 可能忘记 layer 的主对象 |
| runbook 使用 | 能选择性参考 | 容易把 runbook 每条都当 checklist |
| 因果排序 | 更能区分主因/次因 | 容易把任何出现过的错误都当根因 |

根本原因是小模型的有效注意力、指令遵循、复杂状态管理和结构化生成能力都更弱。Agent 诊断链路又天然包含长上下文、多工具、多阶段状态、多格式输出，因此小模型的问题会被放大。

### 2.2 实际暴露的问题

这轮优化中暴露过的典型问题包括：

| 问题 | 真实表现 | 影响 |
|---|---|---|
| evidence_plan 不稳定 | prompt 要求先写计划，但模型直接调用工具，或计划 JSON 不可解析 | 证据完整度无法可靠计算 |
| RCA 结构化失败 | evidence 已经采集成功，但 RCAOutput 没返回合法 Pydantic 对象 | RCA 走低置信度兜底 |
| 工具摘要缺关键字段 | describe summary 没暴露 `preStop`、`terminationGracePeriodSeconds`、`finalizers` | Terminating 根因误判 |
| 表格输出替代 YAML | 模型计划检查 finalizers/deletionTimestamp，却实际调用普通 get 表格 | 关键字段不可见 |
| runbook 过度执行 | VolumeMountFailed 明明事件显示 configmap not found，模型还继续查 PVC/PV/StorageClass | 耗时增加，根因漂移 |
| 中文语义匹配漏判 | 报告写“配置文件不存在”，自动 signature 只匹配 `not found` | 评测低估真实准确率 |
| 次要信号盖过主因 | Terminating 场景中看到 Exit Code 137 或 Killing，就写 OOM/kubelet/finalizer | 根因准确率下降 |
| 最终报告幻觉 | 工具输出 `finalizers: <none>`，conclusion 却写“存在 finalizers” | 用户结论错误 |

这些问题说明：如果只依赖“更详细 prompt”，小模型仍会在工具选择、证据排序和结构化合同上不稳定。

## 3. 研究方法

### 3.1 实验对象

研究对象是 `/ask` 诊断链路和 Pod rootcause E2E 套件。

主链路：

```text
layer -> evidence -> rca -> conclusion
```

测试对象：

- Pod 异常类型：VolumeMountFailed、Pending、ImagePull、CrashLoop、ConfigError、OOMKilled、NotReady、Terminating、Sandbox、Evicted。
- 精确根因：ConfigMap 不存在、Secret 不存在、PVC 不存在、hostPath 错误、nodeSelector 不匹配、CPU/Memory 不足、镜像不存在、pull secret 缺失、preStop 卡住、RuntimeClass handler 无效等。

### 3.2 评价指标

评价不再只看“有没有说对异常类型”，而是看精确根因：

| 指标 | 含义 |
|---|---|
| 根因准确率 | 最终报告 root cause 是否命中 case 的 `root_cause_signature` |
| Runbook 覆盖率 | 是否使用了期望 runbook |
| 平均证据率 | evidence plan/tool_result 的实际覆盖情况 |
| 平均 MTTR | 单次诊断端到端耗时 |

`pod_rootcause_e2e` 与旧的 `pod_abnormal_e2e` 区别：

- `pod_abnormal_e2e`：判断异常大类，例如 L0 VolumeMountFailed。
- `pod_rootcause_e2e`：判断同类异常下的具体根因，例如 ConfigMap 不存在、Secret 不存在、PVC 不存在。

### 3.3 研究路径

这轮工作不是一次完成，而是经历了多轮探索：

| 阶段 | 探索方向 | 结果 |
|---|---|---|
| DeepSeek structured-output | 验证 Pydantic structured output 能不能作为节点边界 | 可行，形成 `call_structured()` 和 schema 思路 |
| Qwen 小模型迁移 | 发现同样 prompt 在小模型下 JSON、工具调用、注意力都更不稳定 | 需要架构约束，而不是只改 prompt |
| 上下文治理 | 去掉 `layer_full_analysis` 下游传递，改为 `layer_handoff` | 下游更稳定，实体和异常状态不易漂移 |
| 工具摘要治理 | raw 落盘，summary 回注，structured 提取关键字段 | 大幅减少工具噪声 |
| evidence 结构化 | 用 EvidencePlanOutput / EvidenceCollectionOutput 约束采证 | 计划、工具、证据统计可审计 |
| runbook 收敛 | runbook 变成 guide，不再让模型全量巡检 | 工具调用减少，根因更聚焦 |
| rootcause E2E | 用 26 个 case、1300 次诊断做量化 | 暴露 terminating/notready 等剩余薄弱点 |

## 4. 架构优化一：四节点职责拆分

### 4.1 旧问题

旧链路更接近“一个 Agent 自己查、自己想、自己写报告”。这对大模型还能勉强工作，但对小模型会产生几个问题：

- 上游定位、证据、根因和报告混在一起，模型容易提前下结论。
- layer 阶段拿到的大段工具结果继续传给 evidence/RCA/conclusion。
- evidence 阶段既要规划、又要执行、又要总结，格式和工具调用互相干扰。
- RCA 阶段如果继续调工具，会重新展开排查，甚至推翻 evidence。

### 4.2 最终方案

把工作流拆成四个节点：

| 节点 | 只做什么 | 不做什么 |
|---|---|---|
| layer | 扫描当前异常 Pod、识别异常族、匹配 runbook、生成 handoff | 不做深度采证，不写最终报告 |
| evidence | 按 handoff 和 runbook guide 采集真实证据 | 不泛化巡检，不把计划/runbook/archive 当证据 |
| rca | 基于 evidence 做因果链和根因收敛 | 默认不再调用工具 |
| conclusion | 渲染 Markdown 报告 | 不自行计算证据率、runbook 覆盖率 |

这等于把小模型的任务从“全栈自由诊断”降解成多个局部任务。每个局部任务的输入更短、职责更窄、输出更容易校验。

### 4.3 为什么有效

小模型最怕同时处理多种目标。拆分后：

- layer 不需要写修复建议，只要找当前异常。
- evidence 不需要决定最终根因，只要验证事实。
- RCA 不需要调用工具，只要基于已采证据排序。
- conclusion 不需要重新推理指标，只负责表达。

这使每一步的错误面变小，也让错误更容易定位。

## 5. 架构优化二：`layer_handoff` 注意力锚点

### 5.1 旧问题

旧的 `layer_full_analysis` 会把 layer 阶段完整分析和工具原始输出继续传给下游。对小模型来说，这会造成注意力漂移：

- evidence 忘记主 Pod，去查其他 namespace。
- RCA 被历史 event 影响，把已恢复的对象当当前故障。
- conclusion 把 runbook 里的典型原因当真实原因。

### 5.2 最终方案

`layer` 节点生成 `layer_handoff`，下游默认只消费这个紧凑结构：

```json
{
  "diagnosis_scope": "question_scope",
  "layer": "L1",
  "abnormal_pods": [
    {"name": "rc-terminating-prestop", "namespace": "aiops-e2e", "status": "Terminating"}
  ],
  "current_abnormal_summary": {
    "status_counts": {"Terminating": 1},
    "selected_rows": []
  },
  "pod_status_keyword": "Terminating",
  "pod_abnormal_type": "TerminatingStuck",
  "matched_runbooks": ["pod-terminating-stuck.md"],
  "must_verify": [],
  "do_not_change": []
}
```

关键字段：

| 字段 | 对小模型的作用 |
|---|---|
| `abnormal_pods` | 明确当前要诊断的 Pod，不让模型从长文本里找 |
| `current_abnormal_summary.status_counts` | 固定当前异常分布，避免遗漏多异常组 |
| `pod_status_keyword` | 锚定状态，例如 Pending、Terminating、CrashLoopBackOff |
| `pod_abnormal_type` | 锚定异常族，例如 TerminatingStuck、VolumeMountFailed |
| `matched_runbooks` | 告诉 evidence 使用已确认 runbook，不重新选择 |
| `must_verify` | 明确必须验证的事实 |
| `do_not_change` | 禁止模型替换 Pod、namespace、Node 或把历史事件当当前故障 |

### 5.3 为什么有效

`layer_handoff` 的本质是把“从文本中寻找诊断目标”变成“读取固定字段”。这对小模型很重要，因为小模型在长文本检索和多实体保持上明显弱于大模型。

## 6. 架构优化三：工具输出 raw/structured/summary 三件套

### 6.1 旧问题

K8s 工具输出很长：

- `kubectl get pods -A` 可能几十到几百行。
- `kubectl describe pod` 包含 annotations、conditions、events、volumes、containers。
- `kubectl get pod -o yaml` 包含完整 spec/status。

如果这些内容原样进入 Agent loop，小模型会：

- 被无关字段占满上下文。
- 忽略关键 event。
- 把历史信息当当前事实。
- 在后续轮次重复携带完整工具输出，越来越慢。

### 6.2 最终方案

每个工具结果都被 `ObservationProcessor` 处理成三类产物：

```text
raw.txt         完整原始输出，供人工复盘
structured.json 规则提取出的结构化事实
summary.txt     回注给 LLM 的短摘要
```

关键点：不是只在日志里保存 summary，而是把 LangChain agent loop 里的 `ToolMessage.content` 也替换成 bounded summary。这样下一轮模型看到的是压缩后的事实，而不是完整工具输出。

### 6.3 重型工具处理

当前重点处理的重型工具包括：

- `kubectl_get_by_kind_in_cluster`
- `kubectl_get_by_kind_in_namespace`
- `kubectl_get_yaml`
- `kubectl_describe`
- `kubectl_events`
- `kubernetes_jq_query`
- `kubernetes_tabular_query`

处理策略：

| 工具类型 | 摘要策略 |
|---|---|
| Pod 表格 | 提取异常行、状态统计、样例行 |
| describe | 提取 Name、Namespace、Node、Status、Container、Volume、Events、Warning |
| yaml | 解析 Pod metadata/spec/status 高价值字段 |
| events | 优先保留 Warning、Failed、BackOff、x509、Killing 等诊断行 |
| logs | 保留错误行、尾部关键日志 |
| 空结果 | 明确标记为空/负向观察，不能当作异常已验证 |

### 6.4 Terminating 场景的具体收益

Terminating 场景曾经暴露出工具摘要缺字段的问题。后来针对 `describe` 和 `yaml` 做了增强：

`kubectl_describe` 摘要保留：

- `Termination Grace Period`
- `Command`
- `Args`
- `State`
- `Last State`
- `Reason`
- `Exit Code`
- `Restart Count`
- `Events: Killing / Stopping container`
- `Volumes`

`kubectl_get_yaml` 摘要保留：

- `metadata.deletionTimestamp`
- `metadata.finalizers`
- `deletionGracePeriodSeconds`
- `spec.terminationGracePeriodSeconds`
- `spec.containers[].lifecycle.preStop`
- `spec.containers[].command/args`
- `status.containerStatuses[].waiting/terminated/lastTerminated/exitCode`

这使模型不用读完整 YAML，也能区分：

- finalizer 卡住
- preStop hook 卡住
- terminationGracePeriodSeconds 过长
- Node/kubelet 不可达
- volume detach/unmount 卡住

## 7. 架构优化四：Pydantic 结构化合同

### 7.1 旧问题

最早的方式是 prompt 要求模型输出 JSON，例如：

```text
请输出 JSON，包含 layer、confidence、root_cause...
```

这对小模型不稳定，常见失败包括：

- 输出 fenced JSON。
- JSON 前后夹自然语言。
- 字段名不一致。
- list/dict 类型漂移。
- 输出被 `<think>` 或工具调用打断。
- RCA 阶段直接自然语言分析，没有合法 RCAOutput。

### 7.2 最终方案

关键节点使用 Pydantic schema：

| Schema | 作用 |
|---|---|
| `LayerOutput` | layer 结构化结果 |
| `LayerHandoff` | layer 到下游的紧凑交接对象 |
| `IssueGroup` | 多异常组 |
| `EvidencePlanOutput` | evidence 采证计划 |
| `EvidenceCollectionOutput` | evidence 采集结果 |
| `EvidenceMatchOutput` | plan/tool 对齐裁判 |
| `RCAOutput` | RCA 根因结果 |
| `QueryResult` | `/query` 结果 |
| `ContextCompactionSummary` | evidence 运行时上下文压缩 |

### 7.3 response_format 使用方式

系统里有两种结构化路径：

第一种是无工具结构化调用：

```python
parsed, raw = ai_call.call_structured(
    system_prompt=prompt,
    question=user_message,
    schema=RCAOutput,
    allow_text_fallback=True,
)
```

第二种是 Agent 工具 loop 内的结构化输出：

```python
create_agent(
    model=agent_model,
    tools=tools,
    system_prompt=system_prompt,
    response_format=ToolStrategy(schema=EvidenceCollectionOutput),
)
```

这两种方式解决的问题不同：

| 路径 | 适合场景 | 优点 |
|---|---|---|
| `call_structured()` | RCA、提取、压缩等不需要工具的节点 | 输入短，合同清晰 |
| Agent `response_format=ToolStrategy` | layer/evidence 这种需要先调用工具再产出结构化结果的节点 | 工具调用和结构化结果在同一轮 agent 内闭环 |

### 7.4 为什么 Pydantic 不是万能的

Pydantic 只能保证“返回后能校验”，不能保证模型一定返回。

真实 RCA 失败就是这个问题：

```text
RCA 节点 evidence 已经采集到了有效 tool_data，
但 RCAOutput structured object 没生成合法对象，
于是 parsed=None，
系统进入低置信度兜底：
当前无法基于 LLM 输出确定根本原因。
```

这不是 evidence 没有结构化，而是 RCA 是一次单独的结构化推理边界。它不再调用工具，也没有确定性规则兜底。只要这次 RCAOutput 失败，就会进入 fallback。

后来 RCA 开启 `allow_text_fallback=True`，让 native structured 失败后还能尝试解析 JSON 文本，并在 prompt 中强化 RCAOutput JSON 结构。这能提高兼容性，但根因仍是：小模型/网关对结构化输出的稳定性不足。

## 8. 架构优化五：Evidence plan 从“提示词愿望”变成“执行协议”

### 8.1 旧问题

Prompt 要求 evidence 先生成计划，但小模型可能：

- 只输出计划，不调用工具。
- 直接调用工具，不输出计划。
- 输出计划但字段名不合规。
- 计划检查 YAML 字段，却实际调用表格工具。
- 计划和实际工具不匹配，证据完整度失真。

### 8.2 最终方案

Evidence 被拆成三个对象：

```text
evidence_plan       模型计划要验证什么
tool_result         真实工具返回了什么
evidence_inventory  计划项是否被真实工具满足
```

核心原则：

- 计划不是证据。
- runbook 不是证据。
- archive 不是证据。
- 只有真实 tool_result 才是环境证据。
- `NotFound`、空 events、命令失败如果回答了检查目的，可以是负向证据。
- 有 plan 时，完整度按 plan item 是否被真实工具满足计算。

### 8.3 执行协议

Evidence prompt 明确：

1. 采证计划由 `EvidencePlanOutput` Pydantic schema 生成。
2. 执行阶段只按既有计划调用必要工具。
3. 必须调用至少一个 critical/important 真实只读工具。
4. 没有 tool_result 禁止写采集结论。
5. 工具失败、空事件、NotFound 记录为负向/冲突证据。
6. critical/important 证据满足后停止，不重复调用相同工具。

如果模型第一轮只返回 plan，没有有效工具结果，系统会拒绝并重试：

```text
上一轮 evidence_plan 已有效，本轮不要重新输出 evidence_plan；
请直接按既有计划调用至少一个 critical 或 important 级真实工具。
```

这解决了“小模型以为写完计划就完成采证”的问题。

### 8.4 YAML 工具纠偏

Terminating、ImagePullSecret、资源配置等场景必须看 YAML。系统增加了工具归一化：

- 如果 command 包含 `kubectl get ... -o yaml`，必须使用 `kubectl_get_yaml`。
- 如果 purpose 要检查 `finalizers/deletionTimestamp/preStop/lifecycle/terminationGracePeriodSeconds/spec/status`，必须用 YAML 工具。
- 普通 `kubectl_get_by_name` 表格不能冒充 YAML 证据。
- `tool_args` 是建议参数，不是禁止模型选择正确工具的硬约束。

这点来自真实问题：模型计划写了 `kubectl get pod -o yaml`，但实际使用表格工具，导致 finalizers、preStop、lifecycle 等字段根本不可见。

## 9. 架构优化六：Runbook 从知识库变成诊断分流 guide

### 9.1 旧问题

Runbook 内容越全，小模型越容易把它当 checklist。例如 VolumeMountFailed runbook 可能列出：

- ConfigMap 不存在
- Secret 不存在
- PVC 不存在
- StorageClass 异常
- CSI 异常
- NFS 权限问题
- subPath 错误

如果事件已经明确：

```text
MountVolume.SetUp failed for volume ... configmap "xxx" not found
```

小模型仍可能继续查 PVC/PV/StorageClass，甚至最终把根因写成存储问题。

### 9.2 最终方案

Runbook 只作为 guide：

- layer 阶段根据异常类型 fetch 明显匹配的 runbook。
- evidence 阶段优先使用 layer 已确认的 `matched_runbooks`。
- runbook 不算真实证据。
- 如果当前错误原文已经命中明确分支，只验证该分支，不展开所有典型原因。

runbook 中也写入原则：

```text
证据计划优先覆盖“当前已经出现的错误文本”，不要把典型原因列表全部变成 evidence_plan。
Runbook 是 guide，不是全量巡检清单。
```

### 9.3 为什么有效

这相当于把 runbook 从“让模型看更多知识”改成“让模型少走弯路”。对小模型来说，知识越多不一定越好；如果没有明确优先级，长 runbook 会扩大搜索空间，降低根因精度。

## 10. 架构优化七：上下文预算和运行时压缩

### 10.1 旧问题

Evidence 是最容易上下文膨胀的节点：

- AI messages 会累计多轮思考。
- Tool observations 会累计多次工具结果。
- describe/yaml/events 可能重复出现。
- 小模型上下文窗口虽然可能标称较大，但有效注意力会随着噪声下降。

### 10.2 最终方案

系统为每次 LLM 调用写入 context budget：

- system prompt
- user message
- tool schema
- tool observations
- ai messages
- final output
- context summaries

Evidence 节点启用运行时压缩：

```yaml
workflow:
  context_compaction:
    enabled: true
    nodes:
      - evidence
    max_context_window: 35000
    trigger_ratio: 0.70
    max_compactions_per_call: 1
    summary_max_tokens: 1200
```

触发后使用 `ContextCompactionSummary` Pydantic schema，把中间思考和工具输出压缩成：

- 过程摘要
- 已完成证据
- 未完成证据
- 关键事实
- 负向事实
- 冲突
- 下一步焦点
- discarded_noise

同时保留原始 `evidence_plan` 消息，避免计划解析失效。

### 10.3 为什么有效

这解决的是“Agent 越查越糊”的问题。小模型不是单次工具不会用，而是在多轮工具返回后上下文越来越脏。压缩后，模型继续看到的是当前证据状态，而不是大量历史文本。

## 11. 架构优化八：RCA lite 与兜底机制

### 11.1 为什么 RCA 要 lite

RCA 默认配置：

```yaml
workflow:
  rca_mode: lite
```

RCA 不再调用工具，只消费 evidence 结果。

原因：

- RCA 如果继续调工具，会重复采证，增加耗时。
- RCA 可能跳出 evidence 边界，重新泛化巡检。
- RCA 可能看到更多噪声后推翻已经验证的主因。

### 11.2 RCA 正常路径

正常路径是：

```text
evidence 产出 evidence_items/evidence_analysis/tool_data
  -> RCA 构建 compact evidence_summary
  -> call_structured(schema=RCAOutput)
  -> parsed != None
  -> 写入 root_cause / causal_chain / rca_analysis
  -> conclusion 使用 RCA 结果
```

RCA 输入会包含：

- `layer_handoff`
- evidence item 摘要
- `evidence_facts`
- `evidence_conflicts`
- `missing_evidence`
- `tool_data` 中的真实工具摘要

### 11.3 RCA 兜底路径

如果模型没有返回合法 `RCAOutput`：

```text
parsed is None
  -> _build_llm_fallback()
  -> root_cause = "[Lx层] 当前无法基于 LLM 输出确定根本原因"
  -> confidence = 0.1
  -> causal_chain = LLM 未生成可靠因果链
```

这会导致：

- workflow 继续走 conclusion，不会中断。
- 最终报告可能仍由 conclusion 根据 evidence 写出看似合理内容。
- 但 `rca_analysis` 本身是低置信度兜底。
- 指标上 RCA 结构化成功率会下降，根因结论更依赖 conclusion 自己理解 evidence。

### 11.4 真实问题说明

你之前看到过这种情况：

```text
evidence 已采集：
- kubectl_get_yaml 显示 finalizers: <none>
- lifecycle.preStop: sleep 21600
- terminationGracePeriodSeconds: 21600
- describe 显示 Killing / Stopping container
- node1 Ready

但 RCA 节点输出：
当前无法基于 LLM 输出确定根本原因
原因：LLM 返回结果不符合 RCA 结构化输出合同
```

这说明 evidence 结构化成功不等于 RCA 结构化一定成功。RCA 是另一个独立的模型调用边界。Pydantic 能校验结果，但不能保证小模型一定生成合法结果。

后续优化方向：

- RCA `allow_text_fallback=True`，native structured 失败后解析 JSON 文本。
- RCA prompt 明确给出 JSON 字段示例，贴合 `RCAOutput`。
- RCA 输入中提高真实工具输出优先级，禁止 conclusion/RCA 覆盖 `finalizers: <none>` 这类事实。
- 对高频场景补确定性 RCA 规则兜底，例如 OOMKilled、ImagePull、VolumeMount、Terminating。

## 12. 架构优化九：Conclusion 只渲染，不重新计算事实

### 12.1 旧问题

最终报告是用户看到的内容。如果 conclusion 自己重新计算或重新解释，很容易出现：

- evidence 说 3/3，报告写 100%，但实际 plan 只有 2 项满足。
- 工具输出 finalizers 为空，报告写 finalizers 未清理。
- RCA fallback，报告却写高置信度根因。
- runbook 覆盖率由模型口述，不等于实际引用。

### 12.2 最终方案

Conclusion 仍然输出 Markdown，因为报告需要可读性。但关键统计以后端为准：

- 证据完整度来自 `EvidenceCollectionOutput.collection_summary`。
- root cause 优先来自 `RCAOutput.root_cause`。
- Runbook 覆盖率由 reporter 从 thinking_events、tool_result、rca/conclusion 文本中归一化统计。
- MTTR 由测试脚本实际测量。

Prompt 中强调：

- 工具输出事实优先级最高。
- 如果 `finalizers: <none>`，禁止写 finalizer 未清理。
- 如果 Node Ready，不要把 kubelet/节点不可达作为主因。
- 如果存在 preStop/sleep/Termination Grace Period/Killing，应优先考虑 preStop 或 grace period。

## 13. 测试体系：从“异常识别”升级到“精确根因”

### 13.1 为什么要新建 rootcause E2E

只测异常大类会掩盖问题。例如所有这些都可能表现为 VolumeMountFailed：

- ConfigMap 不存在
- Secret 不存在
- ConfigMap key 缺失
- PVC 不存在
- hostPath 路径错误

如果只判断 L0/VolumeMountFailed，模型说哪个都可能看起来“差不多对”。但真实运维需要知道具体修复什么。

所以 `pod_rootcause_e2e` 用 `root_cause_signature` 做精确匹配：

- `include_all`
- `include_any`
- `exclude_any`

### 13.2 人工语义修正带来的启发

你发现过一个典型问题：

```text
预期关键词：not found
模型报告：配置文件不存在
```

自动评测没有匹配 `not found`，但语义上“文件不存在”是正确根因。

这说明根因评测本身也需要工程化：

- 不能只用英文关键词。
- 要补中文同义词，例如 `不存在`、`未找到`、`缺失`。
- 要区分根因段落与背景段落，避免全报告误命中。
- 要保留人工复核入口，发现评测误判后回写 signature。

这不是“手工改分”，而是评测体系从关键词匹配向语义匹配迭代。

### 13.3 当前覆盖状态

当前自动化可复现 10 个 group、26 个 case：

| Group | 覆盖场景 |
|---|---|
| volumemount | ConfigMap/Secret/ConfigMap key/PVC/hostPath |
| pending | nodeSelector/CPU/Memory/PVC |
| imagepull | invalid registry/image not found/missing pull secret |
| crashloop | 非零退出码/命令不存在/配置文件缺失 |
| configerror | env 缺失/ConfigMap key 缺失/Secret key 缺失 |
| oomkilled | memory limit 过低 |
| notready | readiness/liveness probe |
| terminating | finalizer/preStop/long grace |
| sandbox | RuntimeClass handler 无效 |
| evicted | ephemeral-storage/emptyDir 驱逐 |

仍不适合默认夜跑的场景：

| Group | 原因 |
|---|---|
| unknown | 需要停 kubelet、隔离节点或制造 NodeLost |
| sandbox 扩展 | CNI/IPAM/container runtime 故障依赖真实环境 |
| evicted 扩展 | DiskPressure/MemoryPressure/PIDPressure 会影响节点稳定性 |
| terminating 扩展 | Node 不可达、CSI/NFS detach/unmount 依赖破坏性故障 |

## 14. 典型失败与修复案例

### 14.1 VolumeMountFailed: ConfigMap 不存在

失败模式：

```text
事件已经显示 configmap not found，
但模型继续查 PVC/PV/StorageClass，
最终报告泛化为存储挂载问题。
```

修复策略：

- describe/events 摘要优先保留 `MountVolume.SetUp failed`。
- runbook 明确：如果 Events 已命中 ConfigMap/Secret，不展开 PVC/PV。
- rootcause signature 要求命中 ConfigMap + not found/不存在。

效果：

```text
volume-mount-missing-configmap: 50/50，根因准确率 100.0%
```

### 14.2 CrashLoop: 配置文件缺失

失败模式：

```text
日志里写中文“配置文件不存在”，
自动匹配只看 not found，
导致根因准确率被低估。
```

修复策略：

- 扩展 signature 同义词。
- 允许中文语义表达，例如“不存在”“缺失”“未找到”。
- 优先抽取 root cause 段落，降低背景误判。

效果：

```text
crashloop-config-file-missing: 根因准确率修正后 86.0%
crashloop group 总准确率 95.3%
```

### 14.3 Terminating: preStop 卡住

失败模式：

```text
工具实际返回：
finalizers: <none>
lifecycle.preStop: sleep 21600
terminationGracePeriodSeconds: 21600
Events: Killing / Stopping container
Node Ready

但报告写：
finalizers 未清理导致删除卡住。
```

根因：

- describe/yaml 摘要曾经没有足够暴露 lifecycle/preStop/grace period。
- conclusion 没有把 `finalizers: <none>` 作为强排除事实。
- RCA 结构化失败时，conclusion 自己根据通用 Terminating runbook 补了 finalizer 解释。

修复策略：

- YAML summary 提取 `finalizers`、`lifecycle.preStop`、`terminationGracePeriodSeconds`。
- describe summary 提取 `Termination Grace Period`、`Command`、`Events`。
- prompt 强化：`finalizers: <none>` 必须排除 finalizer 主因。
- evidence plan 强化：检查 Terminating 必须用 `kubectl_get_yaml`。

当前结果：

```text
terminating-prestop-stuck: 66.0%
terminating-long-grace-period: 30.0%
terminating group: 56.7%
```

这个 group 仍是当前薄弱点，说明生命周期类场景需要更强的 RCA 排序和确定性规则兜底。

### 14.4 Sandbox: RuntimeClass handler 无效

失败模式：

最初直接创建不存在 RuntimeClass 的 Pod，会被 API Server admission 拒绝，suite 直接 apply 失败，无法进入诊断。

修复策略：

- manifest 同时创建 RuntimeClass 对象。
- RuntimeClass 存在，但 handler 指向不存在 runtime handler。
- Pod 能被 API Server 接收，随后 kubelet sandbox 创建失败。

效果：

```text
sandbox-runtimeclass-invalid: 96.0%
```

这个例子说明：E2E 场景本身也要精心设计。为了测试 Agent，需要让故障进入“可观察状态”，而不是在 apply 阶段被 Kubernetes 直接拒绝。

## 15. 哪些方法最后被证明有效

### 15.1 有效方法清单

| 方法 | 是否有效 | 原因 |
|---|---|---|
| 单纯加长 prompt | 有限 | 能改善单点行为，但不能保证结构、工具和上下文稳定 |
| 关闭/控制 thinking | 有效但需按模型选择 | 减少 `<think>` 干扰和首 token 延迟；当前配置保留开关，实际值按 Qwen/DeepSeek 实验切换 |
| `layer_handoff` | 很有效 | 下游不再读长文本找对象 |
| raw/structured/summary | 很有效 | 保留可审计性，同时降低模型可见噪声 |
| Pydantic schema | 很有效但非万能 | 能校验边界，但不能保证模型一定返回 |
| Agent `response_format` | 有效 | 工具 loop 内结构化结果更可控 |
| evidence_plan 执行协议 | 很有效 | 防止只写计划不采证，防止计划和证据混淆 |
| runbook guide 化 | 很有效 | 缩小搜索空间，减少泛化巡检 |
| RCA lite | 有效但有边界 | 避免重复采证，但结构化失败时需要 fallback |
| rootcause E2E | 很有效 | 真实暴露小模型精确根因能力，而不是只看大类 |

### 15.2 最关键的方法论

最终证明最有效的方法不是某一条 prompt，而是三层收敛：

第一层：收敛输入。

```text
不要把所有信息都给模型。
只给当前节点完成任务所需的最小事实。
完整原文落盘，不进入默认 prompt。
```

第二层：收敛输出。

```text
关键节点使用 Pydantic。
计划、证据、根因、查询结果都要有 schema。
下游只消费校验后的对象。
```

第三层：收敛评价。

```text
用 E2E signature 测具体根因。
不只看模型说得像不像。
把低准确率 case 反向用于修 prompt、修工具摘要、修评测口径。
```

## 16. 当前仍然存在的问题

### 16.1 RCA 结构化稳定性

RCA 当前仍是单次结构化推理边界。如果小模型没有生成合法 `RCAOutput`，就会 fallback。Evidence 已经有 Pydantic 输出，并不意味着 RCA 一定成功。

后续建议：

- 给 RCA 增加确定性规则兜底。
- 对高频 Pod 异常建立 rule-based RCA candidate ranking。
- RCA prompt 中持续保留 schema 示例和禁止覆盖工具事实规则。

### 16.2 Terminating / NotReady 细粒度原因

这两类问题不是异常状态难识别，而是精确原因容易混淆：

- Terminating: finalizer、preStop、grace period、kubelet、volume detach 都会表现为 Terminating。
- NotReady: readiness/liveness/startupProbe、应用端口、依赖服务、容器重启可能互相影响。

当前结果也证明了这一点：

```text
terminating group 根因准确率 56.7%
notready group 根因准确率 60.0%
```

后续应重点补“主因排序规则”，而不是只补更多工具。

### 16.3 评测语义匹配

关键词 signature 已经可用，但仍需迭代：

- 中英文同义词。
- 否定表达。
- 根因段落优先。
- 排除候选原因误命中。
- 对“已排除 finalizer”这种文本不能算命中 finalizer 根因。

### 16.4 当前配置需要按实验模型切换

`deploy/configmap/config.yaml` 中保留了 Qwen thinking 控制开关：

```yaml
llm:
  extra_body:
    chat_template_kwargs:
      # enable_thinking: false
      enable_thinking: true
```

对 Qwen 小模型稳定性实验，推荐关闭 thinking 以减少 `<think>` 干扰；对 DeepSeek 对比实验或需要观察推理过程时，可以临时打开。文档不能假设当前值永远是某一个，因为你正在做模型对比实验。

## 17. 文件索引

| 主题 | 文件 |
|---|---|
| 模型调用、structured output、Agent tool loop | `app/core/aicall/client.py` |
| Pydantic schema | `app/core/workflow/schemas.py` |
| layer handoff 和异常组 | `app/core/workflow/nodes/layer_classifier.py` |
| evidence plan、执行协议、完整度统计 | `app/core/workflow/nodes/evidence_collector.py` |
| RCA lite 和 fallback | `app/core/workflow/nodes/root_cause_analyzer.py` |
| conclusion 报告渲染 | `app/core/workflow/nodes/conclusion_formatter.py` |
| prompt 统一管理 | `app/core/prompts.py` |
| 工具 raw/structured/summary | `app/core/context/observation.py` |
| context archive | `app/core/context/archive.py` |
| context budget | `app/core/context/budget.py` |
| 部署配置 | `deploy/configmap/config.yaml` |
| runtime runbook | `deploy/configmap/runbooks.yaml` |
| rootcause E2E cases | `test/pod_rootcause_e2e/cases.yaml` |
| rootcause E2E README | `test/pod_rootcause_e2e/README.md` |

## 18. 复现和验证命令

查看当前 rootcause 覆盖：

```bash
sed -n '1,220p' test/pod_rootcause_e2e/README.md
```

运行核心夜间套件：

```bash
cat > /tmp/rootcause_core.txt <<'EOF'
group:volumemount
group:pending
group:imagepull
group:crashloop
group:configerror
group:oomkilled
group:notready
EOF

nohup .venv/bin/python test/pod_rootcause_e2e/run_rootcause_suite.py \
  --scenarios-file /tmp/rootcause_core.txt \
  -n 50 -c 2 \
  --question "我的集群有什么问题" \
  --url http://10.2.0.48:30800 \
  > testreports/pod_rootcause_nightly.log 2>&1 &
```

运行自动化 backlog 场景：

```bash
printf "group:terminating\ngroup:sandbox\ngroup:evicted\n" > /tmp/rootcause_backlog_auto.txt

.venv/bin/python test/pod_rootcause_e2e/run_rootcause_suite.py \
  --scenarios-file /tmp/rootcause_backlog_auto.txt \
  -n 50 -c 2 \
  --settle-seconds 25 \
  --timeout 1200 \
  --question "我的集群有什么问题" \
  --url http://10.2.0.48:30800
```

查看最新报告：

```bash
latest_dir="$(ls -td testreports/pod_rootcause_suite_* | head -1)"
sed -n '1,220p' "$latest_dir/suite_summary.md"
```

查看某次诊断上下文归档：

```bash
kubectl -n aiops exec deploy/aiops-copilot -- \
  ls -R /tmp/aiops/reports/context_archives/<run_id>

kubectl -n aiops exec deploy/aiops-copilot -- \
  cat /tmp/aiops/reports/context_archives/<run_id>/handoff/evidence-to-rca.json
```

## 19. 最终总结

这轮小模型稳定化的核心工作量体现在三件事：

第一，重新定义了小模型 Agent 的工作边界。小模型不再被要求一次性完成“查全量上下文、理解所有 runbook、规划证据、调用工具、判断根因、写报告”的全流程，而是在四节点工作流中完成局部任务。

第二，建立了可审计的数据合同。工具结果有 raw/structured/summary，节点输出有 Pydantic schema，跨节点传递有 layer_handoff，评测有 rootcause signature。这样模型的每一步都可以被复盘，而不是只看最终自然语言。

第三，用真实 E2E 数据驱动迭代。1300 次诊断结果表明，工程约束能让 32B 小模型在多数 Pod 异常根因诊断中达到可用水平；同时也清楚暴露了 Terminating、NotReady、RCA 结构化稳定性这些剩余短板。

所以，这项工作的本质不是“把 prompt 写得更长”，而是把小模型放进一个受控诊断系统中：让它做擅长的语义理解和解释，让代码承担结构、上下文、证据、统计和可审计性。这样才能在小模型能力有限的情况下获得稳定输出。
