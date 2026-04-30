# AIOps Copilot 功能演进说明

本文按项目演进阶段梳理从早期 HolmesGPT 单节点单次诊断，到当前 AICall + LangGraph + MCP + Runbook + Federation + Context Archive + Pod 异常状态 Agent 的主要功能开发。

重点细化阶段 1-8，也就是从 HolmesGPT 单节点调用到工作流、流式输出、MCP 工具、Runbook、质量指标和 Federation 的能力建设。阶段 9 作为 AICall 架构拐点保留关键设计说明；阶段 10 之后只做简要概括。

## 1. 总体演进脉络

项目最早是一个围绕 HolmesGPT 的单次诊断服务：

```text
用户问题
  -> HolmesGPT
  -> MCP / K8s 工具
  -> 一次性返回诊断文本
```

随着能力扩展，逐步演进为当前结构：

```text
FastAPI
  -> HolmesService
  -> AICall(LangGraph)
  -> Workflow: layer -> evidence -> rca -> conclusion
  -> MCP Tools / Builtin Tools / Runbooks / Prometheus / Federation
  -> Context Archive / Metrics / Reports
```

核心变化不是简单替换模型，而是把“单次问答”改造成可观测、可拆解、可验证、可扩展的运维诊断系统。

## 2. 阶段一：HolmesGPT 单节点单次运行

时间线大致对应 2025-12 初始提交到 2026-01 初期。

### 2.1 初始目标

早期目标很直接：

- 提供一个 K8s AIOps API 服务。
- 用户输入自然语言问题。
- 后端调用 HolmesGPT。
- HolmesGPT 自主调用 Kubernetes / MCP 工具。
- 返回一个诊断答案。

当时系统更接近“单节点 Agent”：

```text
question -> HolmesGPT ask -> tool calls -> answer
```

还没有明确的 layer/evidence/rca/conclusion 多阶段职责，也没有稳定的中间状态管理。

### 2.2 FastAPI 服务入口

早期已经建立了服务外壳：

- 通过 FastAPI 暴露查询接口。
- 服务启动时加载配置。
- 使用 `deploy/k8s-simple.yaml` 部署到 Kubernetes。
- 通过 Secret / ConfigMap 提供模型和运行配置。

这一阶段的价值是把实验性质的 HolmesGPT 调用包装成一个可部署服务，而不是只在本地脚本里运行。

具体优化包括：

- 把“本地执行一次 HolmesGPT”封装成 HTTP 服务，外部调用方不需要理解 HolmesGPT CLI 或内部 Python 对象。
- 把模型地址、模型名、API Key、MCP Server 地址等从代码里移到配置，避免每次换模型或环境都改代码。
- 增加健康检查和基础日志，方便部署到 K8s 后判断服务是否正常启动。
- 将诊断请求和服务生命周期拆开，服务启动只做初始化，请求到来时再执行诊断链路。

### 2.3 HolmesGPT 适配层

早期核心适配在 `app/core/holmes/` 一类模块中逐步成形，主要职责包括：

- 加载 HolmesGPT 配置。
- 包装 HolmesGPT 调用。
- 映射 HolmesGPT 事件。
- 监听 HolmesGPT 日志。
- 将工具调用过程转换成服务可理解的输出事件。

这一步解决了一个实际问题：HolmesGPT 自己的输出和事件格式不适合直接暴露给 API 用户，需要做一层适配。

这一层做过的细化工作包括：

- 将 HolmesGPT 的日志、工具调用、中间文本统一映射成内部事件，避免 API 层直接依赖 HolmesGPT 的原始输出格式。
- 对工具执行过程做抽象，让上层可以知道“正在调用哪个工具”和“工具返回了什么”，而不只是等最终答案。
- 对异常做包装，例如 Holmes 初始化失败、工具连接失败、模型调用失败时，返回服务侧可理解的错误。
- 为后续流式输出保留事件接口，虽然早期不是完整 LangGraph 工作流，但已经开始从“一段文本”转向“事件流”。

### 2.4 MCP 工具接入

初始版本已经围绕 MCP 做工具接入：

- 配置 MCP Server 地址。
- 让 HolmesGPT 可以通过 MCP 调用外部 K8s 能力。
- 把 MCP 工具作为诊断时的真实数据来源。

这让系统从“只靠模型回答”变成“模型可以查真实集群”。

早期 MCP 接入重点解决三件事：

- 工具发现：服务启动后能识别 MCP Server 暴露了哪些工具。
- 工具调用：HolmesGPT 可以把自然语言推理转成具体 Kubernetes 查询。
- 工具结果回传：工具输出能够进入模型上下文，成为后续诊断依据。

这一阶段还没有强上下文治理，工具结果更接近原样回注，因此后续才出现 raw/structured/summary 和 budget 体系。

### 2.5 Runbook 初步接入

早期 `deploy/configmap/runbooks.yaml` 开始承载运维知识。

初始 runbook 更偏少量案例，例如：

- 磁盘满。
- CrashLoop。
- 端口冲突或依赖异常。

这一阶段的 runbook 主要承担提示词增强作用：让模型知道常见问题应该查什么、如何判断。

当时的优化重点不是“runbook 管理系统”，而是先验证知识注入是否有价值：

- 把常见故障的排查步骤写成稳定文本。
- 在 prompt 中提示模型优先参考这些排查路径。
- 用 case manifest 验证模型是否会查正确对象。
- 逐步沉淀出“现象 -> 应查证据 -> 根因判断 -> 修复建议”的模板。

### 2.6 JSON 输出和报告可读性

2025-12 中后期开始优化输出格式：

- 让模型按 JSON 或结构化格式返回。
- 优化 prompt，减少纯自然语言发散。
- 加入示例 case 文件用于验证。
- 改善部署权限和 RBAC。

这些优化为后续工作流拆分做了基础准备，因为多节点流转必须依赖可解析的结构化输出。

这部分的实际收益很大：

- 降低了从最终文本里正则抽取字段的难度。
- 让服务端可以稳定拿到 layer、confidence、evidence、root cause 等字段。
- 为 E2E accuracy 统计提供机器可读输入。
- 为后续 LangGraph state 设计提供了字段基础。

## 3. 阶段二：代码结构重组与 Holmes 适配模块化

时间线大致对应 2026-01 中旬。

### 3.1 从散乱核心代码到模块分层

早期代码逐渐拆出：

- `app/core/holmes/`
- `app/core/mcp/`
- `app/core/skills/`
- `app/core/paths.py`
- `app/core/prompts.py`
- `app/core/runbook.py`

这个阶段的核心价值是把“服务入口、Holmes 适配、MCP 管理、知识库、提示词”分开。

拆分前的问题是：一个请求从 API 到模型、工具、prompt、报告输出之间耦合较重，排查问题时很难判断是配置问题、模型问题、工具问题还是 prompt 问题。

拆分后的收益：

- 服务入口只负责请求处理和响应。
- Holmes 模块只负责 HolmesGPT 生命周期与事件适配。
- MCP 模块只负责工具服务连接。
- Runbook 和 prompt 模块只负责知识与指令。
- Skills 模块尝试承载诊断领域对象。

### 3.2 Holmes 目录的职责

`app/core/holmes/` 曾经承担的职责包括：

- `call_wrapper.py`：封装 HolmesGPT 调用。
- `config_loader.py`：加载 HolmesGPT 相关配置。
- `event_mapper.py` / `event_schema.py`：把 HolmesGPT 事件转成内部事件。
- `query_stream.py`：处理流式查询。
- `streaming.py`：输出流控制。
- `introspection.py`：导出和查看 Holmes 内置工具。
- `artifacts.py`：处理长输出或中间产物。

这套适配层后续被 AICall 替代，但它在早期解决了“外部框架不可直接控”的问题。

从演进角度看，这一层的价值有两点：

- 它把 HolmesGPT 变成了一个可替换的后端，而不是让整个业务系统直接长在 HolmesGPT 上。
- 它暴露出 HolmesGPT 后续难以满足的需求，例如 prompt 控制权、工具调用控制权、结构化输出稳定性和上下文管理。

### 3.3 MCP Manager 模块化

早期 `mcp_manager.py` 被整理到 `app/core/mcp/manager.py`，形成更明确的 MCP 管理边界。

主要优化点：

- MCP 配置从业务逻辑中抽离。
- 工具连接和服务初始化解耦。
- 后续可替换 MCP Server，不影响工作流层。

### 3.4 Skills 模块

`app/core/skills/` 早期用于沉淀诊断规则、证据模型和格式化逻辑：

- `models.py`：定义 Layer、Evidence 等基础模型。
- `evidence.py`：证据相关结构。
- `rules.py`：规则判断。
- `engine.py`：技能执行入口。
- `formatter.py` / `gate.py`：输出与门控逻辑。

虽然其中部分代码后来被清理，但这一阶段推动了“诊断不是一段 prompt，而是一组可建模对象”的方向。

### 3.5 E2E 故障场景起步

这一阶段开始出现 `test/e2e`：

- namespace manifest。
- L0/L2/L3/L4 示例故障。
- `run_all.sh` 部署场景。
- `validate.sh` 检查场景。
- `test_scenarios.sh` 调用服务验证。

这让项目从“主观觉得模型答得对”变成“有可复现故障环境”。

早期 E2E 的设计目标比较务实：

- 每个故障场景都有一个可部署 manifest。
- 每个 manifest 尽量制造单一明确故障，避免一个 case 同时触发多个根因。
- 脚本负责创建 namespace、部署故障、等待状态、调用接口、清理资源。
- 验证脚本只检查核心结果，例如是否命中预期层级、是否出现关键 runbook、是否识别核心异常对象。

这为后续 accuracy、MTTR、runbook 覆盖率、证据完整率等指标提供了测试底座。

## 4. 阶段三：LangGraph 四节点工作流

时间线大致对应 2026-01 下旬到 2026-02 初。

这是项目第一次从“单节点 Agent”升级为“多阶段诊断工作流”。

### 4.1 四节点架构

新增 `app/core/workflow/`：

```text
workflow/
  graph.py
  executor.py
  metrics.py
  state.py
  nodes/
    base.py
    layer_classifier.py
    evidence_collector.py
    root_cause_analyzer.py
    conclusion_formatter.py
```

正式形成四节点：

```text
layer -> evidence -> rca -> conclusion
```

### 4.2 layer：问题定位和分层

早期 layer 节点职责是广义运维分层：

- 判断问题属于 L0-L4 哪一层。
- 抽取关键实体。
- 给出可能场景。
- 输出后续节点需要的定位信息。

L0-L4 当时更偏“运维层级”：

- L0：存储/容量/节点资源。
- L1：节点/调度。
- L2：工作负载/容器。
- L3：网络/服务访问。
- L4：应用/依赖/配置。

这一步解决了单节点 Agent 经常“边查边跳”的问题，先让模型明确问题域。

layer 的早期优化点包括：

- 要求先输出结构化分类，而不是直接开始写结论。
- 抽取 namespace、pod、node、service、deployment 等关键实体，减少后续节点重新猜对象。
- 将用户原始问题和已识别实体一起传给 evidence，避免 evidence 丢失上下文。
- 引入 confidence，让低置信度分类能在报告里暴露风险。

### 4.3 evidence：证据链采集

evidence 节点开始承担“让模型不要直接下结论，先采集证据”的职责。

早期能力包括：

- 根据 layer 输出制定 evidence plan。
- 调用工具采集证据。
- 记录证据项。
- 计算证据完整度。
- 将工具结果传给 RCA。

这一步是系统从“会回答”到“能给证据”的关键转变。

evidence 节点早期经历过几轮重要优化：

- 从“模型自由调用工具”改为“先规划要收集哪些证据”。
- 从“工具调用成功就算证据”改为“工具结果要能匹配 planned evidence”。
- 从“所有证据都必须采完”改为“critical/important 证据满足后可以动态提前停止”。
- 从“只把工具原文塞给 RCA”改为“提取 evidence_items、facts、conflicts、missing_evidence”。

这些改动是为了降低重复调用、减少无关工具噪声，并让 RCA 看到的是证据结构而不是工具日志堆叠。

### 4.4 rca：根因分析

RCA 节点用于把证据收敛为因果链：

- 根因是什么。
- 直接原因是什么。
- 传播机制是什么。
- 用户看到的现象是什么。
- 还有哪些限制和未验证项。

这让最终报告不只是工具输出摘要，而是具备“因果解释”。

RCA 的设计重点是约束模型不要跳步：

- 必须引用 evidence 中已经验证的事实。
- 必须区分直接现象、触发因素、根因和影响范围。
- 必须标记缺失证据，不能把未验证猜测写成事实。
- 必须输出置信度，并解释置信度来源。

后续 lite 模式也是在这个基础上形成：RCA 不再读取所有历史工具全文，而是读取压缩后的事实集合。

### 4.5 conclusion：最终报告

conclusion 节点用于把前三阶段结果整理成用户可读报告。

优化点包括：

- 按模板输出。
- 尽量引用真实证据。
- 把修复建议和验证步骤分开。
- 避免把 raw JSON 直接贴给用户。

conclusion 的优化方向是“给人看”，而不是“给模型继续推理”：

- 删除中间推理噪声。
- 把诊断结论前置。
- 把证据链和修复建议分开。
- 对命令类建议强调验证步骤，避免只给一个修复动作。
- 对置信度不足的情况明确说明还缺哪些证据。

### 4.6 WorkflowState

`WorkflowState` 成为节点间数据板。

核心字段逐步包括：

- `question`
- `layer`
- `layer_analysis`
- `key_entities`
- `possible_scenarios`
- `evidence_items`
- `evidence_analysis`
- `evidence_completeness`
- `root_cause`
- `causal_chain`
- `rca_analysis`
- `conclusion`
- `thinking_events`

这一阶段的核心设计思想是：节点通过结构化 state 交接，而不是靠大段文本互相复制。

### 4.7 WorkflowExecutor

`executor.py` 负责：

- 初始化工作流。
- 按节点执行。
- 推送节点开始/完成事件。
- 汇总最终报告。
- 记录耗时和 metrics。
- 捕获错误并输出失败信息。

这让服务端可以流式展示工作流进度，而不是长时间无响应。

Executor 的细化职责后来不断增加：

- 串联节点输入输出。
- 将节点结果写回 state。
- 将 thinking events 转给流式响应。
- 记录每个阶段耗时。
- 在节点失败时保留已有上下文，尽量输出可诊断的失败结果。
- 为 reporter、metrics、context archive 提供统一数据来源。

## 5. 阶段四：输出体验和流式进度优化

时间线大致对应 2026-01 下旬到 2026-03。

### 5.1 从一次性输出到流式输出

早期接口倾向一次性返回完整结果。随着诊断链变长，用户会长时间看不到进展。

后续逐步加入：

- 节点开始提示。
- 节点完成提示。
- 工具调用提示。
- 工具结果摘要。
- 最终报告。

终端体验类似：

```text
🚀 开始诊断
📍 [问题定位] 执行中...
💭 [证据链采集] 调用工具: kubectl_describe
💭 [证据链采集] 工具结果: ...
✅ [根因分析] 完成
```

这项优化解决的是实际可用性问题：诊断链路可能持续几十秒甚至数分钟，如果接口一直不返回内容，用户无法判断是模型慢、工具卡住、服务异常还是网络断开。

流式输出后，用户至少可以看到：

- 当前进入哪个节点。
- 模型是否已经开始行动。
- 正在调用哪个工具。
- 工具是否成功返回。
- 哪一步耗时异常。

### 5.2 text 与 SSE 双格式

接口逐步支持：

- `format=text`：适合 curl / 终端直接看。
- `format=sse`：适合前端或程序消费。

这解决了两个场景：

- 运维人员用 curl 直接诊断。
- Web UI 或其他系统消费事件流。

### 5.3 thinking 事件

系统开始记录和转发 `thinking_events`：

- `ai_message`
- `ai_token`
- `tool_start`
- `tool_result`
- `iteration_end`

这些事件既用于用户可见流式输出，也用于后续 metrics、reporter、context archive。

这套事件后来成为多个功能的共同数据源：

- 终端实时输出。
- Langfuse 或日志里的模型行为分析。
- 工具调用次数统计。
- evidence 证据匹配。
- context archive 工具轨迹落盘。
- 重复工具调用分析。

### 5.4 `<think>` 展示策略

本地推理模型会输出 `<think>` 内容。项目后来支持三种展示模式：

- `full`：完整展示。
- `truncated`：只展示前 N 字符。
- `hidden`：不展示。

这解决了两个冲突需求：

- 调试时希望看模型推理过程。
- 正式报告不应该暴露冗长或不稳定的内部推理。

### 5.5 报告可读性优化

在多次迭代中，最终报告从原始模型文本逐步优化为：

- 先回答用户核心问题。
- 再展示诊断概览。
- 再展示证据链。
- 再展示根因因果链。
- 最后给修复建议和验证命令。

这让报告从“模型聊天回答”变成“运维诊断报告”。

## 6. 阶段五：MCP / Kubernetes 工具体系完善

时间线大致对应 2026-02。

### 6.1 外部 MCP Server 协作

系统逐步从内置调用转向 MCP Server 协作：

- K8s 工具通过 MCP 暴露。
- AIOps 服务作为 Agent 调用 MCP 工具。
- MCP Server 独立部署和演进。

这带来的好处：

- AIOps 服务不直接塞满所有工具实现。
- 工具服务可以独立扩展。
- 多工具、多集群能力更容易组合。

### 6.2 Kubernetes 工具能力

逐步支持和使用的 K8s 工具包括：

- `kubectl_get_by_kind_in_cluster`
- `kubectl_get_by_kind_in_namespace`
- `kubectl_get_by_name`
- `kubectl_describe`
- `kubectl_get_yaml`
- `kubectl_events`
- `kubectl_find_resource`
- `kubectl_lineage_children`
- `kubectl_lineage_parents`
- `kubernetes_jq_query`
- `kubernetes_tabular_query`
- `kubernetes_count`
- `kubectl_run_image`

这些工具覆盖了：

- 集群级扫描。
- namespace 内筛选。
- 单资源详情。
- YAML 配置。
- 事件。
- 资源拓扑。
- 临时 Pod 验证网络/DNS/镜像。

工具体系的演进重点是从“能查资源”扩展到“能围绕故障闭环排查”：

- `get` 类工具负责发现异常对象。
- `describe` 类工具负责拿事件和状态原因。
- `yaml` 类工具负责看 spec/status 细节。
- `events` 类工具负责补充时间线。
- `lineage` 类工具负责从 Pod 反查 Deployment/ReplicaSet/Job。
- `run_image` 类工具负责主动验证 DNS、网络、镜像仓库等运行时条件。

### 6.3 Prometheus 工具

随着 `/query` 和指标查询需求增加，系统接入 Prometheus 能力：

- 查询 metric names。
- 查询 label values。
- 查询 series。
- instant query。
- target 查询。
- rules 查询。

这让系统可以回答：

- 节点 CPU 使用率。
- 节点内存使用率。
- Pod/container 指标。
- Prometheus target 是否存在。

### 6.4 Bash / run image 工具

项目也引入了更通用的排查工具：

- `run_bash_command`
- `kubectl_run_image`

典型用途：

- 在集群内起临时 Pod 测试 DNS。
- 测试 registry 访问。
- 执行只读 shell 命令获取环境信息。

后续又针对这类工具做了上下文保护，避免全量输出撑爆小模型上下文。

### 6.5 工具日志和可观测性

早期通过 Holmes 适配层记录工具日志，后续在 AICall 中记录：

- 工具名。
- 参数。
- 成功/失败。
- raw 长度。
- summary 长度。
- processor 类型。
- raw/structured/summary 归档路径。

这让“模型到底查了什么”可以被复盘。

工具可观测性后续直接支撑了几类问题排查：

- 为什么模型重复调用同一个工具。
- 工具 raw 里是否有关键字段，但 summary 丢失了。
- 某个 processor 是否错误压缩了输出。
- 小模型是否因为上下文不足只看到了摘要。
- 某次诊断实际调用了几个工具，而不是只看最终报告猜测。

## 7. 阶段六：Runbook 体系扩展

时间线大致对应 2026-02 到 2026-04。

### 7.1 从 3 个案例到 L0-L4 runbook

早期 runbook 只有少量示例，后来扩展为 L0-L4 体系。

典型 runbook 包括：

- `l0-volume-limit`
- `l1-taint-node`
- `l2-oomkilled`
- `l3-imagepull-failed`
- `l4-config-bootstrap-fail`

这些 runbook 让模型在不同问题类型下有明确排查步骤。

### 7.2 Runbook catalog

`runbooks.yaml` 中不只是 markdown 内容，还包含 catalog：

- `id`
- `type`
- `layer`
- `update_date`
- `description`
- `link`
- `operations`

catalog 被注入 prompt，让模型先知道有哪些 runbook 可选。

catalog 的设计目的是“先给索引，不给全文”：

- 模型先基于 id、layer、description 判断是否需要某个 runbook。
- 真正需要时再通过 `fetch_runbook` 读取正文。
- 这样可以减少 system prompt 中固定知识的体积。
- 也能在日志里看到模型到底选择了哪个 runbook。

### 7.3 fetch_runbook 工具

后续引入 `fetch_runbook` 这类能力，让模型可以按需读取 runbook，而不是一次把所有 runbook 全量塞进上下文。

价值：

- 降低 system prompt 长度。
- 让模型按当前异常选择知识。
- 让运行时可观测“模型实际参考了哪个 runbook”。

### 7.4 Runbook 覆盖率

随着质量指标引入，runbook 不再只是提示词增强，还成为可评估对象。

系统会统计：

- 核心 Runbook。
- 参考 Runbook。
- 实际 fetch 过的 runbook。
- 是否命中场景预期 runbook。

这让 runbook 体系能进入 E2E 准确率评价。

覆盖率统计的意义不是要求模型机械引用 runbook，而是判断：

- 预期故障是否能触发对应知识。
- 模型有没有绕开关键排查路径。
- runbook 描述是否足够清晰，能被模型选中。
- 新增 runbook 是否对准确率产生正向影响。

### 7.5 Runbook 收敛

后期发现泛化 runbook 太多会导致模型漂移，因此逐步收敛：

- `/ask` 主链只暴露当前诊断主线相关 runbook。
- query PromQL 参考和诊断 runbook 分离。
- private/reference 类 runbook 不默认进入主链。

这是后续 Pod 异常状态 Agent 的基础。

## 8. 阶段七：质量指标和 E2E 评测体系

时间线大致对应 2026-03 到 2026-04。

### 8.1 性能统计

系统加入 `WorkflowMetrics`，记录：

- 总耗时。
- 每个节点耗时。
- LLM 调用次数。
- 工具调用次数。
- 工具调用耗时。

报告中可以看到：

```text
总耗时
问题定位耗时
证据采集耗时
根因分析耗时
汇总总结耗时
LLM 调用次数
工具调用次数
```

这让诊断链路性能可量化。

### 8.2 MTTR

项目中的 MTTR 被定义为“本次诊断从请求到报告输出的端到端耗时”。

它不是生产事故恢复时间，而是诊断响应速度指标。

实现口径：

```text
mttr_seconds = workflow_total_duration_seconds
```

### 8.3 证据完整率

证据完整率基于 `evidence_items`：

```text
collected / planned
```

早期有无 plan 模式兜底：

- 有 plan：按 plan item 匹配工具结果。
- 无 plan：从成功工具调用反向构造证据项。

后续又进一步强化：

- plan 必须先输出。
- plan 后必须调用真实工具。
- 失败工具、空摘要、意图不匹配不能算正向采集。

这使证据完整率从“工具调用数量”逐步接近“关键证据覆盖率”。

### 8.4 根因置信度

`quality_scorer.py` 引入根因置信度评分。

评分会结合：

- 证据强度。
- RCA 输出。
- runbook 匹配。
- deterministic decision。
- LLM 自评。
- layer confidence。

这避免只依赖模型说“confidence=0.9”。

### 8.5 Runbook 覆盖率

E2E 中会检查报告是否引用预期 runbook。

来源包括：

- 核心 Runbook。
- 参考 Runbook。
- thinking_events 中实际 fetch 的 runbook。
- RCA JSON 中声明的 primary runbooks。

### 8.6 E2E accuracy

`test/e2e/test_accuracy.py` 用于多次请求统计：

- 层级准确率。
- Runbook 覆盖率。
- 证据采集率。
- MTTR。

支持：

- 单场景单次。
- 单场景多次。
- 并发压测。
- 全场景矩阵。
- 自定义问题。

这套评测体系让后续改 prompt、改 runbook、改工具摘要策略时可以做回归：

- 如果准确率下降，可以定位是 layer 分类变差、evidence 不完整、runbook 未命中还是 RCA 失败。
- 如果 MTTR 上升，可以定位是某个节点慢还是工具调用次数增加。
- 如果证据完整率下降，可以检查 evidence plan 和工具匹配逻辑。
- 如果 runbook 覆盖率下降，可以检查 catalog 注入和 fetch_runbook 调用。

### 8.7 故障注入矩阵

早期场景逐步扩展，包括：

- L0 存储/驱逐。
- L1 调度失败。
- L2 OOMKilled。
- L3 ImagePullBackOff。
- L4 配置启动失败。

后续又扩展到 11 类 Pod 异常状态。

## 9. 阶段八：Federation / A2A 多集群能力

时间线大致对应 2026-03。

### 9.1 多集群注册

新增 `app/core/federation/`：

- `registry.py`
- `client.py`
- `aggregator.py`
- `agent.py`
- `toolset.py`
- `report_parser.py`

主集群可以配置多个子集群：

```yaml
federation:
  enabled: true
  sub_agents:
    - name: main
      url: http://localhost:8000
    - name: cluster-24
      url: http://10.2.0.24:30800
```

多集群注册解决的是“主服务如何知道有哪些子集群可用”的问题。

这一阶段的优化点包括：

- 子集群名称、地址、启用状态通过配置声明。
- 主集群启动时加载 federation registry。
- 每个子集群保持独立 AIOps 服务，不把所有 kubeconfig 和工具都集中到主集群。
- 主集群只做路由和聚合，子集群仍负责本集群诊断。

### 9.2 广播式 federation

第一类联邦能力是广播式：

```text
主集群收到问题
  -> 对所有 enabled 子集群发送同一个问题
  -> 收集每个子集群结果
  -> 聚合输出
```

对应接口：

- `/federation/ask`
- `/federation/query`

适合：

- 所有集群统一巡检。
- 对比每个集群是否有异常。
- 收集多集群 CPU/内存指标。

广播式 federation 的设计比较简单，但很实用：

- 用户不需要指定集群。
- 主集群把同一个问题发给所有子集群。
- 每个子集群独立返回结果。
- 主集群按 cluster name 聚合。

它适合“巡检”和“横向对比”，不适合复杂的跨集群推理。

### 9.3 Agent-to-Agent federation

第二类是 A2A：

```text
用户问题
  -> 主 Agent 判断要查哪些子集群
  -> 主 Agent 调用子 Agent
  -> 子 Agent 独立执行 ask/query
  -> 主 Agent 汇总
```

对应接口：

- `/federation/ask/v2`
- `/federation/query/v2`

适合：

- 用户明确点名集群。
- 不同集群需要不同查询。
- 主 Agent 需要根据中间结果决定下一步。

A2A 相比广播式的优化点在于“选择性调用”：

- 主 Agent 可以先理解用户问题。
- 再决定调用哪个子 Agent。
- 子 Agent 对自己的集群拥有完整工具链。
- 主 Agent 只聚合子 Agent 的诊断结论，不直接替子集群执行底层 kubectl。

这保持了职责边界，也避免主集群承担所有集群的凭据和工具执行风险。

### 9.4 Federation toolset

federation toolset 把子集群封装成工具能力，让主 Agent 可以像调用普通工具一样调用子 Agent。

这让多集群不再只是固定广播，而是进入 agentic routing。

### 9.5 联邦报告解析

`report_parser.py` 用于从子集群文本报告中提取可聚合内容。

解决的问题：

- 子集群输出是自然语言/Markdown。
- 主集群需要结构化汇总。
- 需要从报告里抽取最终答案、诊断结论、指标结果。

这一步的本质是把“子 Agent 的人类可读报告”再转成“主 Agent 可聚合的数据”。

如果没有这层解析，多集群输出会变成多个完整报告拼接，可读性差，也无法统计每个集群的异常状态、指标值或根因摘要。

### 9.6 联邦部署模式

部署层支持：

- `make deploy-master`
- `make deploy-slave`

主集群开启 federation，子集群关闭 federation。

这降低了多集群部署复杂度。

## 10. 阶段九：AICall 迁移，摆脱 HolmesGPT 调用层

时间线大致对应 2026-04-09 到 2026-04-15。

这一阶段是架构上的关键拐点：从 HolmesGPT 适配层迁移到自研 `AICall`。

### 10.1 迁移动机

HolmesGPT 方案的问题：

- system prompt 前面会注入 HolmesGPT 固定模板。
- 用户自定义 prompt 被稀释。
- JSON 输出约束不稳定。
- 工具调用优先级难以控制。
- PromQL/query 类专业指令容易被通用指令淹没。
- Holmes 适配层带来额外复杂度。

### 10.2 AICall 模块

新增 `app/core/aicall/`：

- `client.py`：核心 LLM 调用。
- `types.py`：AICallResult / ThinkingEvent。
- `streaming.py`：事件推送。
- `tools.py`：MCP 到 LangChain Tool 适配。
- `builtin_tools.py`：内置工具，例如 runbook/context archive。

### 10.3 两种调用模式

AICall 提供：

- `call()`：带工具的 agent loop。
- `call_simple()`：无工具直接 LLM。
- `call_simple_json()`：无工具 JSON 提取。

对应节点：

- layer/evidence 可用 `call()` 自主调工具。
- rca/conclusion 可用 `call_simple()` 或 lite 模式。

### 10.4 LangChain / LangGraph agent loop

AICall 使用 LangChain ChatOpenAI + LangGraph agent loop。

核心能力：

- 绑定 MCP 工具。
- 接收 AIMessage。
- 执行 tool_call。
- 把 ToolMessage 回注给模型。
- 记录 thinking_events。
- 支持 max_steps / recursion_limit。

### 10.5 MCP Tool Adapter

`load_mcp_tools()` 从配置加载 MCP SSE 工具。

这让模型调用的工具从 HolmesGPT 工具体系切到 LangChain 工具体系。

### 10.6 工作流节点迁移

节点基类 `_call_llm()` 改为调用 AICall。

迁移范围包括：

- layer classifier。
- evidence collector。
- root cause analyzer。
- conclusion formatter。
- executor。
- service 初始化。

### 10.7 Reporter 拆分

`workflow/reporter.py` 从 executor 中拆出。

职责包括：

- 保存报告。
- 提取 metrics。
- 归一化 runbook。
- 生成诊断追踪。

这减少了 executor 的职责膨胀。

### 10.8 service.py 精简

service 层逐步收敛为协调器：

- 加载配置。
- 初始化 AICall。
- 加载 MCP 工具。
- 加载 runbook。
- 初始化 federation。
- 分发 ask/query。

### 10.9 事件和流式兼容

AICall 保留了原先用户可见的流式体验：

- tool_start。
- tool_result。
- ai_message。
- iteration_end。
- final。

这让底层从 HolmesGPT 切到 AICall 后，接口体验可以保持稳定。

## 11. 阶段十：/ask 与 /query 分流

阶段 9 之后的工作不再展开到每个 commit，只做简要概括。

系统将诊断和查询拆成两条正式入口：

- `/ask`：完整诊断链，走 `layer -> evidence -> rca -> conclusion`。
- `/query`：直接查询链，主要走 `layer(query direct) -> conclusion(render)`。

这一变化解决了一个关键问题：指标查询不应该被迫走证据链和 RCA，否则慢且容易过度诊断。

## 12. 阶段十一：上下文管理与小模型适配

为适配本地 32B / 32K 上下文模型，系统加入上下文治理：

- context budget 日志。
- provider actual usage 记录。
- context archive。
- 工具 raw/structured/summary 三份落盘。
- observation processor。
- rule / ai summary 策略。
- PVC 持久化归档。
- layer_handoff 替代 layer_full_analysis。
- node_inputs / node_outputs / handoff 落盘。
- read_context_archive 工具。
- 工具重复调用去重。
- session id 透传到模型调用 metadata。

这一阶段解决的是“小模型长上下文漂移”和“排查时看不到实际输入输出”的问题。

## 13. 阶段十二：Pod 异常状态专用 Agent

最新主线从“泛 L0-L4 运维分层”切换为“Pod 异常状态优先”。

当前支持 11 类 Pod 异常：

- Evicted
- VolumeMountFailed
- PendingUnschedulable
- NodeLostOrUnknown
- TerminatingStuck
- OOMKilled
- CrashLoopBackOffRuntime
- ImagePullFailed
- SandboxCreateFailed
- ConfigError
- NotReadyProbeFailed

L0-L4 仍保留，但成为兼容字段，不再是第一判断对象。

新的主线是：

```text
先识别异常 Pod
  -> pod_status_keyword
  -> pod_abnormal_type
  -> derived_layer
  -> evidence/RCA/conclusion
```

对应 runbook 和 E2E manifest 也已围绕 Pod 异常状态重建。

## 14. 当前能力清单

### 14.1 API 能力

- `/ask` 单集群诊断。
- `/query` 单集群查询。
- `/federation/ask` 多集群广播诊断。
- `/federation/query` 多集群广播查询。
- `/federation/ask/v2` Agent-to-Agent 诊断。
- `/federation/query/v2` Agent-to-Agent 查询。
- `/health` 健康检查。
- `/tools` 工具列表。
- `/runbooks` runbook 列表。
- `/reports` 报告查看。

### 14.2 工作流能力

- 四节点诊断工作流。
- QUERY direct 快路径。
- HEALTHY 快路径。
- RCA lite 模式。
- evidence plan 协议。
- evidence 动态提前停止。
- 工具调用事件记录。
- final report 后处理。

### 14.3 工具能力

- Kubernetes get/describe/yaml/events。
- Kubernetes jq/tabular/count。
- Kubernetes lineage。
- Prometheus metric/query/target/rules。
- Bash 只读命令。
- 临时 Pod 镜像运行测试。
- Runbook fetch。
- Context archive 读取。

### 14.4 可观测能力

- 节点耗时。
- LLM 调用次数和耗时。
- 工具调用次数。
- provider usage tokens。
- context budget。
- raw/structured/summary 归档。
- node input/output 归档。
- handoff 归档。
- Langfuse session id 透传。

### 14.5 测试能力

- 单元测试覆盖 AICall、workflow、runbook、context、federation、API。
- E2E manifest 故障注入。
- accuracy 多轮统计。
- Pod abnormal runbook 和 manifest 对齐测试。

## 15. 关键设计取舍

### 15.1 为什么保留四节点

单节点 Agent 容易混合“发现问题、采集证据、推理根因、生成报告”四件事。

四节点的价值是：

- layer 钉住问题对象。
- evidence 只负责找证据。
- rca 只负责因果收敛。
- conclusion 只负责组织输出。

这比单节点更慢，但更可控、更容易排查。

### 15.2 为什么从 HolmesGPT 迁移到 AICall

核心原因是 prompt 控制权。

运维诊断需要严格结构化输出、工具调用顺序约束和节点职责边界。HolmesGPT 的内置模板会干扰这些约束。AICall 让系统完全掌握 system prompt、tool loop、事件记录和上下文处理。

### 15.3 为什么 `/query` 不走 evidence/RCA

查询类问题的目标是拿数据，不是解释故障。

如果查询 CPU/内存也走完整诊断链，会导致：

- 延迟变高。
- 输出过度分析。
- 模型可能偏离用户要的数据。

所以 `/query` 走 direct 查询和渲染。

### 15.4 为什么做 context archive

不能把所有 raw 工具输出都塞给小模型。

但又必须保留全量信息供排查，因此采用：

```text
模型看到 summary
磁盘保留 raw/structured/summary
必要时通过 read_context_archive 再读取
```

### 15.5 为什么 L0-L4 变成兼容字段

早期 L0-L4 过于泛化，容易把 Pod 异常带到网络层、应用层、基础设施层的大范围巡检。

当前目标更明确：先诊断异常 Pod 状态。

因此 L0-L4 保留给历史报告、质量指标和 runbook 兼容，但主判断对象变为 `pod_abnormal_type`。

## 16. 总结

这个项目的演进可以概括为四次关键升级：

1. 从 HolmesGPT 单次问答升级为可部署 K8s AIOps 服务。
2. 从单节点 Agent 升级为 LangGraph 四节点诊断工作流。
3. 从单集群诊断升级为多集群 federation / A2A。
4. 从 HolmesGPT 调用层升级为自研 AICall，并围绕小模型建立上下文治理和 Pod 异常状态专用诊断能力。

当前系统已经不只是“调用大模型诊断 K8s”，而是一套围绕真实工具、runbook、证据链、质量指标、归档可观测和多集群协作构建的运维诊断平台。
