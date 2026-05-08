# 结构化证据采集运行复盘（2026-05-07）

---

埋点traceid，兼容langfuse可以全方位全流程的观察到agent与 ai交互的所有细节内容。

http://10.2.0.54:3001/project/cmn5ux21p0006qw07q05hy9ix/sessions/c07066e16b21437d  这是我一个tracing的详细内容。我发现rca阶段有一个工具采集摘要模块里面的证据 完整吗？我怎么感觉挺少的，这里是我全部详细的中间过程。
---


## 结论摘要

本次复盘基于实际 PV 报告目录：

```text
/data/redis/aiops-aiops-reports-pvc-pvc-d0fafec0-a0c3-41a3-841e-4c8a58670530
```

重点分析的完整运行：

```text
run_id=f5b8812a0c8b47cd
report=/data/redis/aiops-aiops-reports-pvc-pvc-d0fafec0-a0c3-41a3-841e-4c8a58670530/L3-我的集群有什么问题？_20260507_071641.md
archive=/data/redis/aiops-aiops-reports-pvc-pvc-d0fafec0-a0c3-41a3-841e-4c8a58670530/context_archives/f5b8812a0c8b47cd
```

对比参考的后续运行：

```text
run_id=6fac8822a0df4137
archive=/data/redis/aiops-aiops-reports-pvc-pvc-d0fafec0-a0c3-41a3-841e-4c8a58670530/context_archives/6fac8822a0df4137
```

总体判断：最新的 Pydantic 结构化方案已经在“计划解析、证据完整度统计、RCA 输出归一化、conclusion 使用结构化上下文”上生效，但运行时仍然没有完全达到“更快、更全面、更稳定”的目标。主要原因不是结构化 schema 本身失败，而是 evidence 执行仍然是自由 Agent Loop，模型会在计划之外继续探索；同时当前工作流仍以单个 `primary_pod` 为主线，尚未把多个异常状态拆成多个 issue group 独立诊断。

## 当前设计已生效的部分

### 1. evidence plan 已经结构化

代码侧已经新增结构化契约：

```text
app/core/workflow/schemas.py
```

核心对象包括：

```text
EvidencePlanOutput
EvidenceCollectionOutput
EvidenceMatchOutput
RCAOutput
```

在 `f5b8812a0c8b47cd` 中，evidence 输出的计划是可解析的结构化列表：

```json
{
  "plan_total": 5,
  "plan_collected": 4,
  "plan_completeness": 0.8,
  "environment_evidence_total": 5,
  "environment_evidence_collected": 4,
  "environment_evidence_completeness": 0.8
}
```

这比之前“模型输出 plan，但统计口径不一定跟 plan 对齐”的状态更稳定。最终报告中的证据完整度也显示为：

```text
证据完整度: 4/5 (80%)
```

这说明当前完整度已经主要来自结构化 evidence plan，而不是 conclusion 自己重新猜测。

### 2. 工具归档链路完整

该 run 的工具输出已经落盘为三类文件：

```text
*.raw.txt
*.structured.json
*.summary.txt
```

示例：

```text
tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt
tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json
tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt
```

三类文件语义如下：

| 文件类型 | 作用 | 给 LLM 的价值 |
|---|---|---|
| `raw.txt` | 保存工具原始完整输出 | 排查归档与审计最可靠，但通常太长，不适合直接注入 |
| `structured.json` | 保存规则提取后的结构化事实 | 最适合下游结构化读取和复盘，例如 `status_counts`、`selected_rows` |
| `summary.txt` | 保存给 LLM 的短摘要 | 适合控制上下文，但可能丢细节 |

这次 layer 的 Pod 列表工具归档中，`structured.json` 已准确提取了异常状态：

```json
{
  "row_count": 53,
  "abnormal_count": 5,
  "status_counts": {
    "ImagePullBackOff": 3,
    "Terminating": 1,
    "Running": 46,
    "ErrImagePull": 1
  },
  "selected_rows": [
    "aaa ... ImagePullBackOff ...",
    "aaa ... ImagePullBackOff ...",
    "aiops-e2e terminating-stuck 0/1 Terminating ...",
    "xnet ... ImagePullBackOff ...",
    "xnet ... ErrImagePull ..."
  ]
}
```

这说明表格异常提取逻辑在该 run 中没有漏掉 `Terminating`。

### 3. RCA 输出结构化有改善

`rca.output.json` 中已经包含结构化字段：

```json
{
  "root_cause": "镜像地址 docker.io/bitnami/redis:5.0.7-debian-10-r32 不存在或标签错误...",
  "has_causal_chain": true,
  "confidence": 0.85
}
```

RCA 的 `causal_chain`、`evidence_inventory`、`alternative_causes`、`limitations` 等字段都能被后续 conclusion 使用。这个方向是正确的：RCA 不应该重新采集工具，而应该基于 evidence 的结构化事实做推理。

## 问题 1：evidence 很慢

### 现象

完整报告性能统计：

```text
总耗时: 11.4m
问题定位: 43.8s (6%)
证据链采集: 467.6s (68%)
根因分析: 75.7s (11%)
汇总总结: 97.4s (14%)
LLM 调用: 4 次
工具调用: 17 次
```

evidence 单阶段耗时 467.6 秒，占总耗时 68%。这是当前最主要的性能瓶颈。

### 直接证据

evidence 原始计划只有 5 项：

```text
e1 kubectl_get_by_name
e2 kubectl_events
e3 kubectl_get_yaml
e4 kubectl_get_by_kind_in_namespace
e5 run_bash_command
```

但工具归档里实际出现了 15 个 evidence 工具文件：

```text
001-evidence-kubectl_get_by_name
002-evidence-kubectl_events
003-evidence-kubectl_get_yaml
004-evidence-kubectl_get_by_kind_in_namespace
005-evidence-run_bash_command
006-evidence-kubectl_get_by_kind_in_namespace
007-evidence-run_bash_command
008-evidence-run_bash_command
009-evidence-run_bash_command
010-evidence-run_bash_command
011-evidence-run_bash_command
012-evidence-run_bash_command
013-evidence-run_bash_command
014-evidence-run_bash_command
015-evidence-run_bash_command
```

其中多个额外工具失败或超时：

```text
docker: command not found
crictl: command not found
命令执行超时 (60秒)
命令执行超时 (60秒)
```

这说明慢不是因为 evidence plan 太长，而是因为 plan 后面的自由 Agent Loop 继续探索，且探索中包含慢命令和无效命令。

### 根因判断

当前设计是“结构化计划 + 自由执行”：

```text
LLM 输出 evidence_plan
↓
Agent Loop 继续逐步调用工具
↓
LLM 自己判断是否继续
↓
最后再把实际工具结果映射回 evidence_plan
```

这个模式的优点是灵活，真实复杂故障时模型可以补查；缺点是性能不可控，尤其小模型会出现：

```text
思考一次 → 调一个工具 → 再思考 → 再调一个工具
```

每次工具后都要新增一次模型交互，LLM latency 会迅速放大。该 run 中工具自身并不都是慢的，但 ReAct 多轮思考加上两个 60 秒超时，最终把 evidence 拉长到 7 分钟以上。

### 当前设计是否有效

部分有效。

有效点：

```text
evidence plan 可解析
完整度按 plan 统计
失败项能进入 missing_reasons
```

未完全有效点：

```text
工具执行没有严格受 plan 约束
计划外工具会继续膨胀
慢工具没有被及时止损
Agent Loop 没有转成批量执行
```

## 问题 2：分析不够全面，漏掉 Terminating Pod

### 现象

最终报告只分析了：

```text
ImagePullBackOff / ErrImagePull
```

但同一次 layer 工具扫描已经发现：

```text
aiops-e2e terminating-stuck 0/1 Terminating ... pod_abnormal_type=TerminatingStuck
```

### 直接证据

layer 工具摘要明确包含：

```text
status_counts={'ImagePullBackOff': 3, 'Terminating': 1, 'Running': 46, 'ErrImagePull': 1}
```

异常行也包含：

```text
aiops-e2e     terminating-stuck     0/1     Terminating     0     8d
```

但 `layer/handoff.json` 只输出了 L3：

```json
{
  "layers": ["L3"],
  "primary_pod": {
    "name": "test1-redis-master-0",
    "namespace": "aaa"
  },
  "abnormal_pods": [
    {"name": "test1-redis-master-0", "namespace": "aaa", "status": "ImagePullBackOff"},
    {"name": "test1-redis-slave-0", "namespace": "aaa", "status": "ImagePullBackOff"},
    {"name": "test1-redis-master-0", "namespace": "xnet", "status": "ImagePullBackOff"},
    {"name": "test1-redis-slave-0", "namespace": "xnet", "status": "ErrImagePull"}
  ]
}
```

也就是说，漏诊不是工具提取不到 `Terminating`，而是 layer 的最终结构化交接没有保留该异常。

后续 run `6fac8822a0df4137` 已有改善：

```json
{
  "layers": ["L3", "L1"],
  "abnormal_pods": [
    {"name": "test1-redis-master-0", "namespace": "aaa", "status": "ImagePullBackOff"},
    {"name": "test1-redis-slave-0", "namespace": "aaa", "status": "ImagePullBackOff"},
    {"name": "test1-redis-master-0", "namespace": "xnet", "status": "ImagePullBackOff"},
    {"name": "test1-redis-slave-0", "namespace": "xnet", "status": "ImagePullBackOff"},
    {"name": "terminating-stuck", "namespace": "aiops-e2e", "status": "Terminating"}
  ]
}
```

但它仍然选择 ImagePull pod 作为 `primary_pod`，因此 evidence 仍主要围绕 ImagePull 主线采集。

### 根因判断

当前工作流本质上仍是单主线诊断：

```text
layer 识别多个异常
↓
选择一个 primary_pod
↓
evidence 围绕 primary_pod 采证
↓
RCA 围绕 primary_pod 下根因
↓
conclusion 输出一个主根因报告
```

这种结构适合“单一故障主线”，但不适合“我的集群有什么问题？”这种整体健康问题。整体健康问题可能同时存在多个独立异常状态，例如：

```text
ImagePullBackOff / ErrImagePull
Terminating
Pending
CrashLoopBackOff
```

如果只选一个 primary_pod，其他异常即使在 layer 中被识别，也可能在 evidence/RCA/conclusion 中被弱化或丢失。

### 不建议的解决方式

不建议增加硬编码逻辑，例如：

```text
if status == Terminating:
    fetch pod-terminating-stuck.md
```

这会让系统变成规则驱动，违背当前设计目标，也难以扩展到更多异常类型。

### 推荐方向

推荐把“多个异常状态”提升为结构化问题组，而不是只靠一个 `primary_pod`：

```json
{
  "issue_groups": [
    {
      "group_id": "g1",
      "status_keywords": ["ImagePullBackOff", "ErrImagePull"],
      "pod_abnormal_type": "ImagePullFailed",
      "compatible_layers": ["L3"],
      "primary_entities": [
        {"kind": "Pod", "namespace": "aaa", "name": "test1-redis-master-0"},
        {"kind": "Pod", "namespace": "aaa", "name": "test1-redis-slave-0"}
      ],
      "evidence_plan": []
    },
    {
      "group_id": "g2",
      "status_keywords": ["Terminating"],
      "pod_abnormal_type": "TerminatingStuck",
      "compatible_layers": ["L1"],
      "primary_entities": [
        {"kind": "Pod", "namespace": "aiops-e2e", "name": "terminating-stuck"}
      ],
      "evidence_plan": []
    }
  ]
}
```

这个方案仍然可以由大模型做语义分组，不需要写死某个异常类型的处理逻辑。区别是下游不再只接收单个 `primary_pod`，而是接收多个 issue group。

## 问题 3：context_budget 指标怎么看

### 现象

日志中会看到类似：

```text
[context_budget] node=evidence window=32000 input_tokens=5342 input_usage=17% reserved_tokens=10096 budget_tokens=26600 budget_usage=83%
[context_budget.top] node=evidence tool_schema=unknown(11%) ai_messages=unknown(17%) ...
```

用户容易疑惑：

```text
为什么 input_usage 只有 17%，budget_usage 却有 83%？
unknown 为什么还能有百分比？
input 是否一直递增？
```

### 字段解释

| 字段 | 含义 | 准确性 |
|---|---|---|
| `provider_prompt_tokens` | provider 返回的实际 prompt token 数 | 最可信 |
| `provider_input_usage_ratio` | `provider_prompt_tokens / context_window` | 最可信 |
| `actual_context_tokens` | 本地按组件估算的输入上下文 token | 估算 |
| `reserved_tokens` | 为输出、scratchpad、工具循环预留的 token | 配置值 |
| `estimated_total` | `actual_context_tokens + reserved_tokens` | 风险估算 |
| `usage_ratio` / `budget_usage` | `estimated_total / context_window` | 容量风险指标 |
| `unknown(x%)` | token 数值不精确，但根据 chars/3 等启发式估算出占窗口比例 | 粗估 |

以 evidence 为例：

```json
{
  "provider_prompt_tokens": 5342,
  "provider_input_usage_ratio": 0.1669,
  "actual_context_tokens": 16504,
  "reserved_tokens": 10096,
  "estimated_total": 26600,
  "usage_ratio": 0.83125
}
```

这不是矛盾，而是两个口径：

```text
provider_input_usage_ratio = 本次真实输入占窗口比例
usage_ratio/budget_usage = 本地估算输入 + 预留输出/工具空间后的风险比例
```

因此 `input_usage=17%` 说明当前实际 prompt 没有爆窗口；`budget_usage=83%` 说明如果继续多轮工具和长输出，剩余空间风险较高。

### input 递增是否正常

正常。Agent Loop 每调一次工具，下一轮 LLM 输入都会包含更多历史消息和工具 observation，所以 provider prompt tokens 会逐步增长。evidence 的输入增长尤其明显，因为它包含：

```text
runbook catalog
system prompt
user/handoff
tool schema
AI messages
tool observations
reserved scratchpad/output
```

本次 evidence 的 top components 显示：

```text
tool_schema: 3536 tokens
ai_messages: 5363 tokens
tool_observations: 2882 tokens
```

这说明多轮 Agent Loop 自身会快速膨胀上下文，慢和上下文增长是同一个设计问题的两个表现。

### unknown 是否表示数据不可用

不是。`unknown` 表示“token 数不是精确 tokenizer 计算出来的”，但系统仍用 `chars/3` 等启发式估算百分比。这个百分比适合作为风险信号，不适合作为精确计费或精确窗口判断。

如果要追求更准确，应优先看：

```text
provider_prompt_tokens
provider_input_usage_ratio
context_usage.actual
```

本地 `context_budget` 更适合做：

```text
是否需要压缩上下文
哪个组件最占空间
是否接近窗口风险
```

## 对“最新修改是否符合新设计”的判断

### 符合的部分

```text
Pydantic schema 已接入
evidence plan 可以结构化解析
evidence completeness 可以按 plan 输出
RCA 可以结构化校验并归一化
conclusion 已能使用结构化上下文生成报告
工具输出 raw/structured/summary 三类归档完整
```

### 不符合或未完成的部分

```text
evidence 执行仍是 Agent Loop，不是 plan-driven batch execution
计划外工具仍会大量出现
慢工具没有被统一止损
多异常状态仍没有被提升为多 issue group
报告仍以单 primary_pod 根因为中心
context_budget 的工具耗时维度不足，duration_s 多处为 0，不能准确解释 wall-clock 慢在哪里
```

## 建议的后续优化路线

### 短期：保持 Agent Loop，但收紧运行时可观测性

不改诊断策略，只增强可观测：

```text
记录每个工具真实 wall time
记录每轮 LLM call 的 prompt_tokens/completion_tokens/duration
记录 planned vs unplanned 工具比例
记录 timeout 工具数量
在报告性能统计里区分 LLM 耗时和工具耗时
```

这样可以量化回答：

```text
慢是模型慢、工具慢、还是工具超时慢？
模型是否在计划外扩散？
每次改动后 planned coverage 是否提升？
```

### 中期：增加可配置执行模式

建议保留当前模式，同时新增可配置模式：

```text
agent_loop: 当前模式，最灵活，但慢且不可控
planned_batch: LLM 只产出计划，系统按计划批量执行工具，最快最稳定
hybrid: 先批量执行计划，再允许 LLM 最多补查 N 个工具
```

这个不是硬编码业务逻辑，而是执行框架能力。异常类型和工具选择仍然由 LLM 的结构化 plan 决定。

推荐默认顺序：

```text
测试/开发环境: agent_loop 和 hybrid 都打开，便于比较
生产/演示环境: hybrid 或 planned_batch，减少 10 分钟级长尾
```

### 中期：多 issue group 结构

对“我的集群有什么问题？”这类问题，应从单主线改为多问题组：

```text
layer 输出 issue_groups
evidence 按 issue_group 生成轻量 plan
RCA 按 issue_group 输出 root cause 或 limitation
conclusion 汇总多个异常状态
```

这样可以自然覆盖：

```text
ImagePullBackOff 组
Terminating 组
CrashLoopBackOff 组
Pending 组
```

而不需要写死任何状态分支。

### 长期：把运行质量量化

建议围绕运维 Agent 建立以下指标：

| 指标 | 含义 | 目标 |
|---|---|---|
| 当前异常召回率 | 当前集群真实异常中，被报告覆盖的比例 | 越高越好 |
| 主根因准确率 | 报告主根因是否与人工标注一致 | 越高越好 |
| 证据完整率 | 已采集证据 / 计划证据 | 越高越好 |
| 证据有效率 | 有效工具结果 / 全部工具结果 | 越高越好 |
| 计划外工具比例 | unplanned tools / all tools | 越低越好 |
| 平均诊断耗时 | end-to-end latency | 越低越好 |
| P95 诊断耗时 | 长尾 latency | 越低越好 |
| 冲突证据识别率 | NotFound、历史事件污染、状态不一致是否被识别 | 越高越好 |
| Runbook 使用率 | 有匹配 runbook 的场景中实际 fetch 的比例 | 越高越好 |
| Token 增长率 | 每轮 Agent Loop 输入增长速度 | 越低越好 |

这些指标比“调用了多少工具”更能说明系统质量。工具调用越多不等于越好，关键是：

```text
是否覆盖了必要证据维度
是否减少无效工具
是否能识别多异常
是否能在合理时间内稳定输出
```

## 本次运行的最终判断

本次运行说明新设计已经解决了“输出结构不稳定、证据完整度口径混乱、RCA/conclusion 难以消费结构化信息”的一部分问题，但还没有解决“Agent Loop 太慢”和“单 primary_pod 导致多异常漏报”的架构问题。

当前最值得优先处理的是两个方向：

```text
1. 为 evidence 增加 plan-driven/hybrid 执行模式，降低 10 分钟级长尾。
2. 为整体健康类问题引入 issue_groups，让多个异常状态都能进入 evidence/RCA/conclusion。
```

这两个方向都不需要写死某个 Pod 状态的业务规则，仍然可以保持“LLM 负责语义判断，系统负责结构化执行和质量约束”的设计边界。

## 2026-05-07 后续实现更新

### 1. layer_handoff 增加 issue_groups

当前实现已在 `layer_handoff` 中增加通用 `issue_groups` 字段。该字段不是硬编码诊断逻辑，而是对当前异常 Pod 列表做结构化保留，避免下游只看到一个 `primary_pod`。

示例结构：

```json
{
  "issue_groups": [
    {
      "group_id": "g1",
      "status_keywords": ["ImagePullBackOff", "ErrImagePull"],
      "pod_abnormal_type": "ImagePullFailed",
      "compatible_layers": ["L3"],
      "primary_entities": [
        {"kind": "Pod", "namespace": "aaa", "name": "redis-master-0"},
        {"kind": "Pod", "namespace": "aaa", "name": "redis-slave-0"}
      ],
      "is_primary": true,
      "evidence_plan": []
    },
    {
      "group_id": "g2",
      "status_keywords": ["Terminating"],
      "pod_abnormal_type": "TerminatingStuck",
      "compatible_layers": ["L1"],
      "primary_entities": [
        {"kind": "Pod", "namespace": "aiops-e2e", "name": "terminating-stuck"}
      ],
      "is_primary": false,
      "evidence_plan": []
    }
  ]
}
```

这样 evidence 仍可以优先深挖主问题组，但不会完全丢掉其他当前异常状态。

### 2. evidence prompt 精简归档上下文

之前 evidence user message 会注入一长串本地归档文件路径，例如：

```text
budget/layer.json
budget/evidence.json
tools/*.raw.txt
tools/*.structured.json
node_outputs/layer.output.json
```

这会带来两个问题：

```text
1. prompt 变长，增加上下文占用。
2. 模型容易把“读取本地归档”当成采证动作，注意力从当前环境工具偏移到历史文件。
```

现在 evidence 只保留紧凑引用：

```text
context_archive_ref: <run_root>
归档内容不是当前环境证据
默认基于 layer_handoff 与真实环境工具采证
```

示例中 evidence user message 从约 6K+ 字符降到约 2.4K 字符，同时不再包含 `budget/layer.json`、`tools/`、`read_context_archive` 等强牵引词。

### 3. 减少 evidence 重复输出 plan

之前如果首轮只输出 `evidence_plan` 但没有执行工具，系统会进入 strict retry，而 strict retry 仍要求第一条消息重新输出 `evidence_plan`，因此流式输出里容易看到两份 plan。

现在逻辑改为：

```text
首轮 plan 有效但没有工具结果
↓
第二轮沿用首轮 plan
↓
提示模型不要重新输出 evidence_plan
↓
直接按既有 plan 调用真实工具
```

这不会阻止“工具调用前必须有 plan”的协议，但能减少你看到的重复 plan，也减少一次无意义重规划。

### 4. 验证结果

已通过相关单测：

```text
80 passed, 1 deselected, 1 warning
```

其中 deselected 的测试是旧的 `primary_pod NotFound` 特判类测试，按当前设计要求不再启用硬编码特判。
