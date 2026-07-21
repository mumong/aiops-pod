# 面向小模型的自主可观测性查询 Runbook 设计

## 1. 目标

在不改变 Robusta 四节点工作流、不把 MCP 变成故障规则引擎的前提下，
精简 Pod 异常 Runbook，使其成为 Qwen 的“查询方法与证据边界”参考。

Agent 获得 Kubernetes、Metrics、Logging、Tracing 等基础工具后，应能够根据
当前 Pod 状态自主决定：

- 当前还需要回答哪些诊断问题。
- 应查询哪个可观测性维度。
- 应选择哪些指标、关键词、过滤条件和时间窗口。
- 是否需要根据前一轮结果继续补证。
- 何时已有足够证据并停止查询。

Runbook 不应预先规定完整工具调用计划、固定 PromQL、固定日志查询或固定
ClickHouse SQL。MCP 不应按 OOM、ConfigError、ImagePullBackOff 等异常类型
选择查询。

## 2. 当前问题

### 2.1 Prometheus collector 偏向 OOM

当前 `collect_aiops_case` 对所有 Pod 固定查询：

- `container_memory_working_set_bytes`
- `kube_pod_container_status_restarts_total`
- `kube_pod_container_status_last_terminated_reason`
- `kube_pod_status_phase`
- `kube_pod_container_resource_limits{resource="memory"}`

历史 range query 和 Agent-facing highlight 也只围绕内存。`scenario` 没有参与
Prometheus 指标选择。因此：

- OOM 可以获得内存趋势和 Limit。
- ConfigError 会收到与根因无关的内存数据。
- ImagePullBackOff 会在容器尚未启动时查询不存在的容器资源序列。
- Terminating、Pending、ProbeFailed 等场景缺少直接相关指标。

### 2.2 Runbook 偏向固定执行清单

现有场景 Runbook 普遍包含：

- 固定的 Step 1、Step 2 排查命令。
- 完整 kubectl 命令和推荐执行顺序。
- “必查项”形式的静态 checklist。
- 预先写好的根因分支和修复建议。

这种内容适合人工操作手册，但会让 Qwen 机械执行全部步骤，降低根据真实结果
进行二次决策的空间。

### 2.3 提示词限制与目标冲突

当前 QUERY direct 提示词要求 Prometheus 查询前读取 Runbook，并在存在模板时
逐字复用标准 PromQL，同时禁止模型自主构造替代表达式。这适用于节点级固定
报表查询，不适合 Pod 异常的动态诊断补证。

后续必须区分：

- 固定报表型 QUERY：可以继续使用稳定模板。
- Pod 异常诊断：Runbook 只给方法，由 Agent 自主选择查询。

### 2.4 完全自由查询也不够稳定

隔离动态 PromQL 实验已经证明 Qwen 能根据两个真实 Case 选择不同查询：

- OOM 选择容器内存 range query。
- ConfigError 选择 terminated reason、exit code 和 restart increase。

同时也暴露出：

- OOM 查询遗漏 memory limit。
- 原始 Prometheus series 约 16.8KB，第二轮输入达到 10,646 tokens。
- 重复 scraper 和历史容器 series 产生噪声。
- 小模型可能把合理推断写成直接事实。

因此动态查询适合作为 Agent 能力，但必须由 MCP 提供作用域、数据量和结果
规范化约束。

## 3. 设计原则

### 3.1 Agent 决策，MCP 执行

Qwen 负责：

- 提出待验证问题。
- 选择可观测性维度。
- 选择 Prometheus 指标和 PromQL。
- 选择日志关键词、字段、容器和时间范围。
- 选择 Flow、Span、Trace ID、Pod IP、状态码等链路过滤条件。
- 根据返回结果决定继续查询或停止。

MCP 负责：

- 校验 namespace、Pod、Pod UID、IP、Node 和时间范围。
- 拒绝无作用域、超长、超时或高基数查询。
- 生成安全的 ES DSL 和 ClickHouse SQL。
- 执行受约束 PromQL。
- 去重重复 scraper、限制 series 和采样点。
- 返回结构化统计、真实样本、coverage 和 directness。

MCP 不负责：

- 根据异常类型选择指标。
- 判断根因。
- 生成修复建议。
- 将无数据自动替换成其他无关指标。

### 3.2 Runbook 是参考，不是计划

Runbook 提供：

- 当前场景需要回答的诊断问题。
- 各维度可以提供什么类型的证据。
- 可考虑的指标族、日志语义和链路条件。
- 正向证据、反向证据和证据边界。
- 无数据时的正确解释。
- 停止扩展条件。

Runbook 不提供：

- 必须逐字执行的完整 PromQL。
- 完整 ES DSL 或 ClickHouse SQL。
- 固定工具调用次数。
- 不考虑真实返回值的统一调用顺序。
- 预先填好的 root cause。

### 3.3 维度存在不等于维度有价值

不同 Pod 生命周期阶段天然具有不同可观测性：

- 容器尚未创建：通常没有应用日志、容器资源指标和应用 Trace。
- 应用启动后立即退出：可能有 previous logs，但 Trace 可能未及时导出。
- 应用运行期间异常：Metrics、Logs、DeepFlow、Tempo 才可能形成完整关联。
- 镜像拉取失败：Kubernetes Events 是决定性证据，Node runtime metrics 只是背景。

Agent 必须允许维度返回 `empty` 或 `absent`，不能为了凑齐三维数据而查询无关
内容或编造结论。

## 4. Runbook 信息架构

每个 Pod 场景 Runbook 统一精简为以下结构。

### 4.1 场景识别

只描述用于选择 Runbook 的强信号和排除项。例如：

- 当前 waiting reason。
- last terminated reason 和 exit code。
- deletion timestamp。
- Warning Event 的关键 reason。

### 4.2 需要回答的诊断问题

每个 Runbook 保留三到五个问题。问题描述目标，不指定工具。例如：

- 这是容器 cgroup OOM，还是 Node MemoryPressure/Evicted？
- 容器根本没有启动，还是启动后因配置校验失败退出？
- ImagePullBackOff 是镜像不存在、认证失败，还是网络/TLS 问题？

### 4.3 可选观测维度

按价值说明 Kubernetes、Metrics、Logging、Tracing 能提供什么，不要求全部查询。

每个维度标记：

- `direct`：可直接支持当前 Pod 的状态或原因。
- `supporting`：只能作为趋势或关联背景。
- `not_expected`：当前生命周期阶段通常不存在。

### 4.4 查询构造原则

只给通用构造方法和候选指标族，不给必须逐字复用的完整语句。

Metrics 示例：

```text
当前状态使用 instant query。
趋势和重启变化使用 bounded range query。
所有 Pod 级查询必须精确限定 namespace 和 pod。
资源使用应与 request/limit 在相同 namespace/pod/container 维度比较。
Node 级指标必须标记 related_context，不能冒充 Pod 直接证据。
```

Runbook 可以提供可替换的查询模式，帮助小模型理解 PromQL 组合方式，但不得要求
逐字执行。例如：

```text
当前状态:
  <state_metric>{namespace="<namespace>",pod="<pod>",<optional filters>}

时间窗口内是否发生:
  max_over_time(<state_metric>{namespace="<namespace>",pod="<pod>"}[<window>])

计数器增量:
  increase(<counter_metric>{namespace="<namespace>",pod="<pod>"}[<window>])

资源峰值与限制:
  max_over_time(<usage_metric>{namespace="<namespace>",pod="<pod>",
  container="<container>"}[<window>])
  与相同 namespace/pod/container 维度的 <limit_metric> 比较
```

尖括号内容必须由 Agent 根据当前实体、问题和可用指标替换。候选指标只是知识，
不是待执行清单。

Logging 示例：

```text
优先限定 Pod UID，其次 namespace + pod + container。
时间窗围绕最近一次失败、重启或 Warning Event。
先查决定性错误关键词，再根据 trace ID、错误码或配置键展开。
优先 previous container；没有启动过的容器不应反复查询应用日志。
```

Tracing 示例：

```text
先通过 Pod IP、namespace、service 或 workload 查目标流量。
发现 trace ID 后再按 trace ID 获取完整 flow/span。
优先错误响应、长延迟和故障时间窗口内的调用。
DeepFlow flow 只能证明网络调用；应用 span 属性才能说明业务操作。
```

### 4.5 证据边界

Runbook 明确哪些结论不能仅靠单一维度得到。例如：

- exit code 78 不能单独证明具体缺失配置项。
- memory 峰值低于 Limit 不能证明从未触及 Limit。
- Node pull-image error 不能单独归因到目标 Pod。
- 没有 Trace 不代表网络一定正常。
- Kubernetes waiting reason 能证明当前状态，但不一定包含底层错误原因。

### 4.6 停止扩展条件

满足以下任一条件应停止无关查询：

- 已有两类相互一致的直接证据。
- 决定性 Kubernetes Event 或日志原文已指出明确原因，补查不会改变结论。
- 当前生命周期阶段决定某维度不可能存在。
- 连续查询为空且作用域、时间窗已经验证正确。
- 剩余查询只能增加背景，不能区分候选根因。

## 5. 三个首批场景

### 5.1 OOMKilled

#### 诊断问题

- Kubernetes 是否真实记录 `OOMKilled` 或 exit code 137？
- 内存使用是否持续增长、周期上升或逼近 Limit？
- 内存峰值、最近终态和重启是否在时间上相关？
- 是否存在 Node MemoryPressure、Evicted 或 Node OS OOM 的反向证据？
- 日志或 Trace 是否能说明由哪个请求或业务操作驱动内存增长？

#### Metrics 候选

- 容器 memory working set、RSS、usage 趋势。
- memory request/limit 和使用率。
- OOM event、memory failure。
- restart increase。
- last terminated reason、exit code 和 timestamp。
- Node MemoryPressure 仅作为 related context。

Agent 不应默认查询 CPU、磁盘或无关 namespace 指标。

#### Logging 方法

- 时间窗覆盖最近一次容器启动到 OOM 终止。
- 优先 previous container 和集中日志。
- 搜索 allocation、heap、GC、memory、cache、batch、payload 等业务语义。
- 保留真实数值、配置项、错误码、trace ID 和请求路径。

#### Tracing 方法

- 查询 OOM 前访问目标 Pod 的请求。
- 优先高延迟、错误响应、较大 payload 或明确分配操作。
- 发现 trace ID 后关联 DeepFlow flow、Tempo span 和日志。
- Trace 说明触发路径；OOMKilled 终态仍以 Kubernetes 为准。

#### 停止条件

Kubernetes 终态、内存趋势和至少一个业务触发证据形成时间一致链路，或已经明确
只能诊断到资源耗尽但无法定位业务触发来源。

### 5.2 ConfigError

#### 首先区分

- `CreateContainerConfigError` / `CreateContainerError`：容器未启动。
- `CrashLoopBackOff + Error`：应用已启动后因配置校验或初始化失败退出。

#### 诊断问题

- 容器是否曾成功启动？
- 当前是 Kubernetes 配置引用错误，还是应用内部配置校验失败？
- 重启是否持续发生，退出码和终态是什么？
- 决定性日志或 Event 指向哪个 ConfigMap、Secret、key、env 或参数？
- 应用是否在退出前执行过初始化调用或依赖访问？

#### Metrics 候选

- waiting reason。
- last terminated reason、exit code、timestamp。
- restart increase。
- ready/running 状态。
- Pod phase 和 start time。

除非日志或状态提示资源问题，否则不查询内存 working set 和 memory limit。

#### Logging 方法

- 对未启动容器，以 Kubernetes Events 为主，不反复查询应用日志。
- 对启动后退出容器，优先 previous logs。
- 搜索 missing、required、config、secret、env、validation、bootstrap、parse。
- 保留具体配置键和完整错误原文。

#### Tracing 方法

- 仅当应用实际启动且存在服务流量时查询。
- 优先初始化依赖、配置中心、数据库、消息系统或启动探针调用。
- 如果应用在 telemetry flush 前退出，Trace 为空应标记为证据限制。

#### 停止条件

Event 或日志已明确指出配置对象/键/校验失败，且生命周期指标证明该失败持续导致
容器无法启动或反复退出。

### 5.3 ImagePullBackOff

#### 诊断问题

- 当前是否仍为 ImagePullBackOff/ErrImagePull？
- 失败的具体 image、tag 或 digest 是什么？
- Event 表明镜像不存在、认证失败、DNS、TLS、超时还是限流？
- 所在 Node 是否同时出现 pull-image runtime errors？
- 该问题是否只影响一个 Pod/镜像，还是同一 Node 上多个拉取操作？

#### Metrics 候选

- waiting reason。
- ready/running 状态。
- Pod phase 和创建时间。
- container image/image_spec。
- 所在 Node 的 kubelet pull-image operation error 和 duration。

Node runtime 指标必须标记为 `related_context`。它们不能单独证明目标 Pod 的具体
失败原因。

#### Logging 方法

- 应用容器尚未启动时，不期待应用日志。
- kubelet/container runtime 日志只有在工具允许且 Events 不足时按 Node 补查。
- 不应查询业务错误关键词或 previous application logs。

#### Tracing 方法

- Pod IP 尚不存在或应用未启动时，不期待 Pod 级 DeepFlow/Tempo 数据。
- 镜像拉取由 Node runtime 发起，Pod IP 作用域的 flow 查询通常无法覆盖。
- 只有在提供 Node runtime 网络作用域时，registry 流量才能作为 related context。

#### 停止条件

当前 waiting reason、image spec 和 Event 原文已经确定失败类别；Node 指标只在
需要判断是否为节点范围问题时补查。

## 6. 基础工具合同

### 6.1 Kubernetes

继续复用现有只读工具：

- get/get_yaml/describe。
- events。
- current/previous logs。
- Pod、owner、Node、ConfigMap、Secret、PVC 等只读查询。

### 6.2 Metrics

提供受约束 Pod PromQL 工具：

```text
execute_pod_promql(
  namespace,
  pod,
  promql,
  query_type,
  start?,
  end?,
  step?,
  purpose?
)
```

约束：

- PromQL 必须包含精确 namespace 和 pod matcher。
- 单条长度不超过 2,000 字符。
- range 不超过两小时。
- series 和每条 series 的采样点有上限。
- 对重复 scraper series 做语义去重。
- 返回 query、scope、coverage、current/min/max/last/delta 和少量代表性样本。

Node 级查询后续使用独立作用域合同，不允许伪装成 Pod 级查询。

### 6.3 Logging

Agent 不直接编写完整 ES DSL，而是提供查询意图：

```text
query_pod_logs(
  namespace,
  pod,
  pod_uid?,
  container?,
  start,
  end,
  keywords?,
  levels?,
  trace_id?,
  fields?,
  max_records?,
  purpose?
)
```

MCP 构造 ES DSL，优先 Pod UID，并返回：

- 命中数量。
- 时间范围。
- 去重后的决定性日志样本。
- 保留字段和裁剪说明。
- coverage 和查询条件。

### 6.4 Tracing

Agent 选择查询条件，MCP 构造 DeepFlow SQL 或 Tempo 请求：

```text
query_pod_flows(namespace, pod, pod_ip?, start, end,
                protocol?, response_codes?, min_duration_us?,
                peer_ip?, trace_id?, max_records?, purpose?)

query_pod_spans(namespace, pod, service?, start, end,
                trace_id?, status?, operation?, max_records?, purpose?)

get_trace_by_id(trace_id)
```

返回必须区分：

- DeepFlow network flow。
- DeepFlow eBPF syscall/L7 context。
- Tempo application span。
- direct Pod evidence 与 related topology context。

## 7. Agent 提示词

Evidence 节点提示词应改为：

1. Runbook 用于提出待验证问题，不是固定执行计划。
2. 先读取 Kubernetes 当前状态，再决定需要哪些可观测性维度。
3. 每次工具调用必须说明 `purpose`，即希望区分哪些候选解释。
4. 收到结果后执行 reconciliation，再决定是否补查。
5. 真实工具结果优先于 Runbook、Pod 名称和模型经验。
6. 不要求每个 Case 都有 Metrics、Logs、Tracing。
7. 某维度在当前生命周期阶段不应存在时，应记录限制并停止。
8. 只查询能够改变根因判断或置信度的证据。
9. 不得因为 Runbook 列出候选指标而全部执行。

删除或限定以下要求：

- Pod 异常诊断中必须逐字复用 Runbook PromQL。
- 禁止模型自主构造 PromQL。
- 固定先后顺序的工具 checklist。

固定节点报表型 QUERY 仍可保留标准 PromQL，不与 Pod 诊断混用。

## 8. 结果和上下文控制

### 8.1 结果预算

- 单个 Metrics 调用目标不超过 6KB。
- 单个 Logging/Tracing 调用目标不超过 6KB。
- 每次动态补证最多三到四条独立查询。
- 原始全量数据保存在 MCP 侧 evidence store，通过 ref 按需读取。

### 8.2 压缩原则

MCP 先做确定性压缩：

- 去重 scraper、相同日志和重复 flow。
- 指标返回 min/max/last/delta，而不是全部采样点。
- 日志优先错误原文、配置键、请求路径和 trace ID。
- Trace 优先错误、长延迟和跨服务关键 hop。

LLM 压缩只用于历史 observation 接近上下文阈值时，不替代 MCP 的结构化压缩。

### 8.3 证据记录

每次动态查询生成结构化 Fact：

```text
fact_id
source_system
dimension
entity_scope
query
purpose
observed_value
timestamp/window
directness
coverage
evidence_ref
```

RCA 只能引用当前 Case 的真实 Fact。

## 9. 低侵入实施边界

Robusta：

- 精简 `deploy/configmap/runbooks.yaml` 中首批三个场景。
- 调整 Evidence 提示词中的 Runbook 和动态查询规则。
- 保留 Layer/Evidence/RCA/Conclusion 四节点。
- 自主查询模式只暴露 Kubernetes、Metrics、Logging、Tracing 基础工具，不要求
  `collect_aiops_case`，也不把它作为 mandatory 入口。
- 旧 `collect_aiops_case` 只作为默认关闭的兼容回退保留；不参与自主查询验收，
  后续可独立移除。
- 通过 Robusta MCP 配置开关在“现有粗粒度模式”和“自主基础工具模式”之间切换，
  两种模式不同时作为 Agent 的首选入口。

mcpstander：

- 复用已验证的 `execute_pod_promql` 实验实现。
- 在现有 Logging/DeepFlow/Tempo collector 上增加结构化查询参数。
- 不复制 `data` 脚本。
- 不加入场景判断分支。

不在本轮范围：

- 图数据库。
- RAG。
- 自动执行修复。
- 重构现有工作流。
- 为所有 Pod 异常一次性编写完整 Runbook。

## 10. 测试设计

### 10.1 模块测试

完成一组模块后集中测试：

- Runbook 结构和体积测试。
- 提示词不再要求 Pod 诊断逐字复用 PromQL。
- PromQL 作用域、范围、series 和采样限制。
- Logging/Tracing 参数验证和查询生成。
- Fact 记录与 evidence ref。

### 10.2 真实 Qwen 对照测试

首批使用真实：

- OOMKilled。
- 应用级 ConfigError。
- ImagePullBackOff。

每个场景至少重复三次，并保存：

- Qwen 收到的 Runbook。
- 每轮 tool call 和参数。
- MCP 原始结果和 Agent-facing 结果。
- 最终 RCA 和 evidence refs。
- token、耗时和上下文压缩记录。

### 10.3 验收指标

- 三个场景选择的 Prometheus 查询集合明显不同。
- 有效 PromQL 比例不低于 90%。
- OOM 至少两次查询内存趋势和 memory limit。
- ConfigError 至少两次优先查询生命周期和日志，不默认查询内存。
- ImagePullBackOff 三次都优先使用 waiting reason/Event，不虚构应用日志或 Trace。
- Qwen 至少在一个场景中根据第一次结果自主发起第二次补证。
- 无无作用域 PromQL、无超范围查询、无大于约 6KB 的单次 Agent-facing 结果。
- 最终报告引用真实指标值、日志原文或 Trace，并明确不存在或不足的维度。

## 11. 成功定义

本设计完成后，系统不是“根据异常类型执行预设查询”，而是：

```text
Runbook 提供诊断问题与查询方法
  -> Qwen 根据真实状态选择查询
  -> MCP 安全执行并压缩真实结果
  -> Qwen 根据结果继续补证或停止
  -> RCA 引用当前 Case 的真实证据
```

扩展新场景时，优先新增或精简 Runbook 的诊断问题和证据边界，而不是修改 MCP
collector 的异常类型分支。
