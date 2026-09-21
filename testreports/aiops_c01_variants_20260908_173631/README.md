# c01 Pending 多根因实测与人工审查

## 结论

8 次请求均完成；单独测试每次发现 1/1 个目标，组合测试每次发现 3/3 个目标。**能区分多个 Pending 对象，但不能据此认定具体根因分析已经可靠：CPU 场景反复出现错误或解释不充分。**

内存请求过大、PVC 缺失的主根因识别正确；组合测试的内存报告有明显单位换算错误。CPU 问题同时涉及程序摘要丢字段、模型单位理解错误和 Runbook 判定粒度过粗，并非只是测试脚本误判。

本次未修改 Agent 主程序、Runbook 或正式评分规则。结束时 `runner.json.status=completed`、`cleanup_errors=[]`；工作进程 4000739 已退出，aiops-case-v01/v02/v03 已删除。

## 测试方法

- 问题始终为：**我的集群有什么问题？** 不向模型提供目标 Pod、命名空间或预期根因。
- `c01-cpu`、`c01-memory`、`c01-pvc` 分别部署，各问两次；随后同时部署三个场景，再问两次。组间清理。
- 每次请求前验证 Pod 状态、对应 UID 的故障事件，并保存请求前后 Pod/Events；所有目标的请求前后 UID 一致。
- CPU 注入 `requests.cpu=100000`，Kubernetes 返回为 `100k`，即 **100,000 核**，不是 100m 或 0.1 核。
- 内存注入 `requests.memory=1Pi`，即 **1,125,899,906,842,624 bytes（2^50 bytes）**。
- PVC 注入对当前命名空间中不存在的 `unavailable-claim` 的引用。
- 请求串行、超时 1200 秒、每次只尝试一次。组内两次共用同一批 Pod，故不是独立重新注入的统计样本。
- 复用已有部署/验收、SSE 请求、证据归档与清理函数。执行记录见 [run_c01.py](run_c01.py)、[runner.json](runner.json)。

本次验证的是“**相同 Pending 症状、多个独立 Pod 分别具有不同根因**”，不是一个 Pod 同时具有三个故障。

## 逐次结果

以下为人工审查主根因及重要矛盾，不以关键词命中代替诊断质量，也不另行生成正式质量分数。

| 部署方式 | 次数 | 耗时 | 人工结论 | Run ID / 原文 |
|---|---:|---:|---|---|
| CPU 单独 | 1 | 89.1s | 部分正确：识别 CPU 不足并列出 100k，但未明确定位请求配置过大，停留于集群资源不足 | [975be492d402435e](01-cpu/run-01/report.md) |
| CPU 单独 | 2 | 98.4s | 前后矛盾：根因段写出请求过大，但概览声称 48 核远大于 100k，因果链归为耗尽/碎片化 | [e77dd8bed7714b10](01-cpu/run-02/report.md) |
| 内存单独 | 1 | 44.8s | 主根因正确：1Pi 请求过大；单位名称和空指标解释有瑕疵 | [8297c09aa26a44d5](02-memory/run-01/report.md) |
| 内存单独 | 2 | 54.2s | 主根因正确：1Pi 请求超过节点容量 | [a145fa1e5f25422b](02-memory/run-02/report.md) |
| PVC 单独 | 1 | 45.1s | 主根因正确：引用的 PVC 不存在；另有无充分依据的排除性陈述 | [3f3587c72a6a4e9d](03-pvc/run-01/report.md) |
| PVC 单独 | 2 | 70.5s | 主根因正确：引用的 PVC 不存在；单点指标及小请求值被过度解释 | [e03e6b6b46444c00](03-pvc/run-02/report.md) |
| 三场景同时 | 1 | 100.5s | 找全 3/3。CPU 错归集群耗尽（100k 被解释为 0.1 核）；内存/PVC 主根因正确，内存把 1Pi 错换成 16 EiB | [2a4e3ebf60c140c2](04-combined/run-01/report.md) |
| 三场景同时 | 2 | 80.9s | 找全 3/3。CPU 因果链仍归集群耗尽，未定位请求异常；内存/PVC 主根因正确，内存把 1Pi 错换成 1Ti 对应的字节数 | [d038e25aac5148e6](04-combined/run-02/report.md) |

8 次平均请求耗时 **72.94 秒**，不含部署、验收、归档与清理；这是诊断响应耗时，不代表自动修复耗时。每种条件只有两次，不应当作稳定质量估计。

## 问题定位：不是单一原因

### 1. 已确定的代码问题：Describe 摘要按文本去重，破坏了字段上下文

首轮 CPU 的 `005-evidence-kubectl_describe.raw.txt`：

```text
Limits:
  cpu: 100k
  memory: 32Mi
Requests:
  cpu: 100k
  memory: 8Mi
```

同次 `.summary.txt`：

```text
Limits:
  cpu: 100k
  memory: 32Mi
Requests:
  memory: 8Mi
```

`app/core/context/observation.py` 的 `_extract_describe_containers`（约 1519 行）和 `_extract_describe_pod_sections`（约 1414 行）对摘要调用 `_dedupe_lines`。后者（约 2386 行）只按去空白后的文本判断重复，不区分 Limits、Requests 或容器作用域。

**同值并不等于同一事实。** 此处 Requests 的 CPU 被误删；结构化结果仍正确保留 requests 和 limits。原文仅 1370 字符、摘要 958 字符，已使用归档原文在本地确定性复现，结果与保存的摘要一致，不需要调用 LLM，也不是上下文太长才发生。

影响已进入实际推理：该次 `node_inputs/rca.input.json` 中 Evidence 分析写出了“无 cpu requests”“Pod 没有设置 cpu requests”。同次 YAML 原文及结构化结果也有 100k，但 `_extract_yaml` 的文本摘要没有输出容器 resources，未提供有效的摘要层纠错。

边界：该缺陷不能解释全部误诊，因为结构化事实还在，且其他轮次模型明确读到了正确数值。

### 2. 已确定的模型问题：正确数值进入 RCA 后仍误读单位

CPU 第二次 `e77dd8bed7714b10`：

- `012-evidence-execute_prometheus_instant_query` 原始返回和摘要均返回目标 CPU request **100000**，单位 core。
- 后续节点查询返回 allocatable **18、18、12 核**，也保留在 RCA 输入中。
- Evidence 却写出 `100k = 0.0001 core`；最终报告一处承认请求过大，另一处声称 `48 core` 远大于 `100k`，并推测碎片化。

两次组合运行的 Evidence 都把 `100k` 解释为 `0.1 核`。内存主根因虽对，报告分别出现 `1Pi≈16 EiB` 和 `1Pi≈1099511627776 bytes` 的错误。原始配置只提供 `1Pi`，这些错误换算由模型引入。

因此不能认定为 Prometheus 或 Kubernetes 返回了错误资源数值，也不能认为增加工具调用就一定解决。当前资源 canonical fact 保留 Kubernetes quantity 字符串，缺少此路径上的确定性数值归一化与比较校验。

### 3. Runbook 有知识，但粗粒度判定使模型过早结束调查

本次各目标报告都引用了 `pod-pending-unschedulable`。运行时完整 Runbook 快照见 [runbook-snapshot.json](runbook-snapshot.json)，哈希在 runner.json 中。

Runbook 涉及 CPU/内存不足、PVC、资源 requests 与节点 allocatable 对比，不属于“完全没有知识来源”。但其判定表将 `FailedScheduling + Insufficient cpu/memory` 直接对应为高置信度“资源不足导致 Pod Pending”，没有强制继续区分“请求配置过大”和“正常请求遇到节点余量不足”。

组合第二次 CPU 的 Evidence 明确写道：根据 Runbook，`FailedScheduling + Insufficient cpu` 已足以得出高置信结论，因此没有再查询节点容量。

另外，`_extract_runbook_plan_context` 注入 Evidence 的是筛选后的章节，不是完整 Runbook；Pending 的完整约 4102 字符变为约 969 字符，本例主要是章节筛选，不是达到 2500 字符上限后硬截断。补证提示和判定规则仍在，但不能把它等同于全部诊断细节均注入。

### 4. 个别工具调用错误存在，但不是 CPU 误诊的充分解释

- 组合第二次 Layer 调用了当前阶段不存在的 `kubectl_describe_pod`，被明确拒绝。
- 同轮一次查 `workload` 没带 namespace，实际落到默认命名空间，返回 NotFound；后续对正确命名空间的调用成功。
- 同轮节点内存 custom-columns 查询语法错误，命令失败。
- CPU 单独第一轮还查询了并非该 Pod 所引用的 `workload-pvc`，返回 NotFound。

部分命令失败文本被外层事件记为 `status=success`。**工具事件成功不等于查询获得有效数据**，人工审查必须看返回正文。NotFound 也应结合查询对象判断，不能一概视为服务失效。

这些调用没有导致漏掉目标，且正确的 Pod 配置和调度事件已取得；CPU 单独第二轮没有上述失败文本，仍发生单位误判，故不能将问题都归因于工具错误。

### 5. 报告语义约束不足

已检查的组合第一轮 CPU `claim_validation.output.json` 记录 `enabled=false`、`skipped=true`。该次不能宣称经过发布前事实绑定与验证；即使引用有效，也不意味着单位换算和因果推论得到验证。

其他常见错误：

- `Insufficient cpu` 表示节点不能满足**这次请求**，不等于 CPU 使用率满载或资源余量为零。
- “无可抢占受害者”不能推出整个集群完全饱和，更不是“没有可抢占的节点”。
- 单次 Pending=1 / Running=0 不能证明历史上从未运行、一直 Pending 或永久失败。
- 请求值很小不能单独排除节点资源不足；缺少应用日志/trace 对未启动容器可以是预期，但不能泛化为全部可观测数据均不存在。

## 建议优先级（本次未实施）

1. 修复结构化摘要跨字段去重，确保 requests/limits 与容器作用域不丢失；YAML 摘要保留诊断所需 resources。
2. 为 Kubernetes quantity 增加确定性归一化，保留原值及标准单位值；调度按每个候选节点比较有效请求与可用资源，不能只比较集群总和。
3. Pending Runbook 明确分开请求异常、节点资源占用、PVC/调度约束，避免看到 Insufficient 就宣布具体根因已确认。
4. 区分调用完成、命令执行成功和有效观测；禁止把错误正文当作正常证据。
5. 增加报告中单位、数值比较、对象范围、时间范围的校验；无法确定时保留不确定性，不自动生成错误的“真实原始结果”。

先修复确定性摘要问题，再用相同场景回归，才能分清程序修复收益与模型推理波动。

## 证据位置

- 每次目录：`report.md`、`events.json`、`raw.sse`、`evidence.archive.json`、`before.json`、`after.json`。
- 节点容量快照：[node-capacity.json](node-capacity.json)。
- 完整工具和节点归档位于宿主机：`/data/redis/aiops-aiops-reports-pvc-pvc-52d8916d-bd02-4ad3-9c91-ea2e59356b51/context_archives/`。
- 单独运行 lane 为 `<run_id>-g1`；组合第一轮为 `2a4e3ebf60c140c2-g1-p1/p2/p3`；组合第二轮为 `d038e25aac5148e6-g1/g2/g3`。
- lane 下 `tools/` 可对照同次 `.raw.txt/.summary.txt/.structured.json`；`node_inputs/rca.input.json` 可查看错误解释何时进入 RCA。
