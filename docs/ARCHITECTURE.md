# 核心流程与模块架构

[返回 README](../README.md)。本文描述当前源码和仓库默认配置（robusta 12.0.44 起），参数以 [config.yaml](../deploy/configmap/config.yaml) 为准。部署与配置项见 [GUIDE](GUIDE.md)，单次运行排查见 [运行诊断](run-diagnostics.md)，模型/推理服务自身的问题见 [LLM 自身异常记录](llm-model-anomalies.md)。

全文以一次真实运行为例：`3c05242319a449de`（"我的集群 pod 有什么问题"，4 个异常 Pod：case-04 / 06 / 09 / 11），以及随后对这 4 组的修复。

---

## 1. 设计原则

1. **模型做判断，代码管身份、校验与边界。** 发现异常、选择工具、分析原因、制定修复由 Agent 自主完成；目标身份、分组、控制器归属、命令越界、审批与执行由代码约束，不信任模型自报。
2. **事实可追溯。** 每次工具调用的原文、结构化结果和模型可见摘要都归档；模型看摘要，需要时按 `raw_ref` 回读原文。
3. **失败如实标记，不编造。** 结构化交付无效时不做第二次模型提取、不补造目标或结论，标记 `execution_incomplete` / `partial` 并保留已有证据。
4. **通用规则，不按故障类型特判。** 护栏、恢复判定、命令策略只看工具行为和资源状态，新的异常类型不需要改代码。

## 2. 总览

```
用户 ──► /ask、/query (SSE) ──► WorkflowExecutor（每个请求重建图，节点实例不共享）
                │
                ▼
        ① request_router  意图路由（单次结构化调用，无 thinking、无工具）
                │ route
   ┌────────────┼──────────────────────┬─────────────┐
 focused     full_diagnosis          clarify      remediation（修复任务内部使用）
   │            │                      │              │
query_collect ② layer 定位（Agent，只读工具）  END          ⑦ RemediationNode
   │            │ LocationHandoff
   │            ▼
   │      ③ plan_groups 分组（纯代码）
   │            │ 1 组 ──► evidence → rca（串行）
   │            │ ≥2 组 ─► ④ parallel_evidence
   │            │             ├─ 异常组 1：evidence(Agent) → rca(结构化)
   │            │             ├─ 异常组 2：…（独立 client、独立上下文、独立归档）
   │            │             └─ 异常组 N
   │            ▼
   │      ⑤ conclusion  总览 + 各组报告原样拼接
   ▼            ▼
  END    诊断记录落盘（diagnosis-record.v2，按组）
                │ 用户点击"生成自动修复方案"
                ▼
        ⑥ POST /repair/batches → 每组一个 job → 并发规划（⑦）
                ▼
        ⑧ 执行：策略预检 → 审批/自动 → dry_run/execute/verify → ⑨ 恢复观察 → 终态 + 审计
```

## 3. 模块地图

| 模块 | 文件 | 职责 |
|---|---|---|
| HTTP/SSE | [routes.py](../app/api/routes.py)、[service.py](../app/core/service.py) | 接收请求、加载配置与 MCP 工具、启动工作流、SSE 输出 |
| 修复 API | [repair_routes.py](../app/api/repair_routes.py) | 批次/任务/反馈/取消、策略查询与模式切换、审计 |
| 工作流 | [graph.py](../app/core/workflow/graph.py)、[executor.py](../app/core/workflow/executor.py) | 条件路由、事件流、计时、取消、节点归档 |
| 意图路由 | [request_router.py](../app/core/workflow/nodes/request_router.py) | `RequestContract`：route/task/scope/对象/时间 |
| 轻量查询 | [query_answer.py](../app/core/workflow/nodes/query_answer.py) | focused 路由：工具循环内直接提交 `QueryAnswer` |
| 深度诊断节点 | [autonomous_diagnosis.py](../app/core/workflow/nodes/autonomous_diagnosis.py) | layer / evidence / rca 三个阶段 |
| 分组与并发 | [autonomous_parallel.py](../app/core/workflow/nodes/autonomous_parallel.py)、[group_runner.py](../app/core/workflow/group_runner.py) | 按定位目标分组、lane 调度与隔离、并发上限 |
| 交接契约 | [diagnosis_contract.py](../app/core/workflow/diagnosis_contract.py)、[case_result.py](../app/core/workflow/case_result.py)、[case_report.py](../app/core/workflow/case_report.py) | 定位交接、证据交接、单组报告、总览与拼接 |
| 流式契约 | [stream_contract.py](../app/core/workflow/stream_contract.py)、[fact_contract.py](../app/core/workflow/fact_contract.py) | lane 事件打标、工具→维度映射 |
| 模型循环 | [client.py](../app/core/aicall/client.py)、[structured_transport.py](../app/core/aicall/structured_transport.py)、[working_context.py](../app/core/aicall/working_context.py) | Agent 循环、护栏、结构化交付、上下文压缩 |
| 观测处理 | [observation.py](../app/core/context/observation.py)、[observability_projection.py](../app/core/context/observability_projection.py)、[lifecycle_core.py](../app/core/context/lifecycle_core.py) | 工具结果解析、投影、摘要、归档引用 |
| 预算与归档 | [budget.py](../app/core/context/budget.py)、[archive.py](../app/core/context/archive.py)、[builtin_tools.py](../app/core/aicall/builtin_tools.py) | token 预算、归档、`fetch_runbook` / `read_context_archive` |
| 提示词 | [prompts.py](../app/core/prompts.py)、`app/core/prompt_catalog/` | 全部模型指令的唯一入口 |
| 修复规划 | [remediation.py](../app/core/workflow/nodes/remediation.py)、[ownership.py](../app/core/remediation/ownership.py)、[group_context.py](../app/core/remediation/group_context.py) | `RepairDraft` 契约、控制器链、按组截取诊断 |
| 修复执行 | [jobs.py](../app/core/remediation/jobs.py)、[pod_executor.py](../app/core/remediation/pod_executor.py)、[policy.py](../app/core/remediation/policy.py)、[approval.py](../app/core/remediation/approval.py)、[recovery.py](../app/core/remediation/recovery.py)、[settings.py](../app/core/remediation/settings.py)、[audit.py](../app/core/remediation/audit.py)、[records.py](../app/core/remediation/records.py) | 任务编排、命令策略、审批、执行、恢复观察、模式开关、审计、不可变记录 |
| 运行诊断 | `app/core/diagnostics/` | `run_report`、ledger、工程异常发现 |
| A2A | [a2a_adapter](../a2a_adapter/) | 标准 A2A 协议封装，独立容器，见 [A2A](a2a.md) |

MCP 工具服务（mcpstander）和前端在独立仓库。

## 4. 诊断生命周期

### 4.1 请求入口

- 前端调用 `/ask`（SSE）。生成 `run_id`；会话身份为 64 位哈希（owner），之后访问修复记录必须使用同一会话身份。
- 事件类型：`run_start`、`node_start/complete`、`thinking`（`ai_reasoning` 思考、`ai_token` 输出、`tool_start/tool_result`、`runtime_status` 状态文案）、`final`。
- 并发 lane 的事件经 `LaneQueue` 打上 `parallel_group_id` 与 `lane_stage`（evidence/rca），工具事件另带 `evidence_context`（维度、所属实体），前端据此把思考、输出和工具结果分发到各组卡片。

### 4.2 ① 意图路由（request_router）

- 内部调用：关闭 thinking，采样 temperature 0.7 / top_p 0.8 / top_k 20，输出上限 1200 token。
- 输出 `RequestContract`（禁止多余字段）：`route`（full_diagnosis / focused / clarify / remediation）、`task`、`scope`（cluster / namespace / pod）、`namespaces`、`pod_names`、`requested_outputs`、`time_range`。
- 边界：
  - 用户未指定时间时 `time_range=null`，不自动补窗口。
  - full_diagnosis 表示深度，不表示扩大到全集群。
  - 路由只校验结构，不按关键词或对象数量改写模型决定。
  - 路由失败按类别（HTTP、连接、超时、格式）给出脱敏提示，不暴露服务商响应正文与凭证，不清空已有会话。
  - 带修复上下文的请求直接走 remediation，不调用模型（修复任务中路由耗时为 0）。
- 路由结果：
  - focused：`query_collect → END`。查询 Agent 在同一工具循环内提交 `QueryAnswer`，不再调用总结模型。
  - clarify：返回澄清问题并保存会话。
- 实例：`full_diagnosis / diagnose / cluster`，2.0 秒。

### 4.3 ② 定位（layer）

- 提示词：`DEEP_LAYER_PROMPT`（唯一职责：定位对象和异常现象）+ 定位交接契约 + 工具指南 + Runbook 目录 + Pod 异常判定准则。
- Agent 循环：开启 thinking；只开放只读工具（写工具在调用层直接屏蔽）；`workflow.max_steps.layer=48` 个图步；每轮输出上限 `llm.output_tokens.agent=4000`。
- **怎样在集群里找出异常由 Agent 自主决定**，代码不做全量扫描兜底。
- 清单投影：`query_pod_lifecycle` 的列表结果经 `inventory_view` 处理。需要关注的 Pod 保留完整生命周期记录；当前正常的 Pod 只按命名空间列成名单。真实 73 个 Pod 的一页从约 15.8k token 降到约 1.9k；归档里仍保留全部 Pod。名单不等于健康结论。
- 输出 `LocationOutput`：
  ```
  analysis
  handoff:
    targets[]: target_id（唯一）, entity{kind, namespace, name, uid},
               issue（≤320 字，只写现象）,
               status: investigate | assessed | deferred | excluded,
               status_reason（deferred/excluded 必填）, evidence_refs（≤3）
    coverage: complete | partial | unknown, coverage_note
  ```
- 代码边界：
  - 目标 ID 或实体重复视为无效。
  - 交接无效时 `targets=[]`、`coverage=partial`、记 `execution_incomplete`，不做二次提取。
  - `assess_delivery` 用实际工具事件核对交接。
  - namespace 由 API Server 补全。
- 实例：3 轮、10 次工具调用、118 秒（第 1 轮 71 秒用满 4000 token），交出 4 个 investigate 目标。

### 4.4 ③ 分组（plan_groups，纯代码）

- 每个 `investigate` 的 Pod 目标生成一组 `g1…gN`，界面显示为"异常组 N"，问题取目标的 `issue`。
- 只要存在非 Pod 目标，就整体走串行诊断，避免丢失。
- 分组计划归档到 `parallel/plan.json`。
- 路由（`after_location`）：
  - 判定为 healthy/inconclusive 且没有待调查目标 → 总结；
  - 组数大于 1 → 并发诊断；
  - 否则 → 串行 evidence → rca。
- 分组出错时降级为单路诊断，并提示"分组暂不可用"，不丢弃诊断结果。
- 定位没有交出目标（例如全部正常，或定位阶段失败）时走串行诊断，RCA 以"请求范围"作为身份交付（`request_scope_target`），健康结论用 `outcome=healthy`，不会再因缺少目标身份被判无效（run 354362a291394218）。
- 多卡片是否出现取决于 layer 是否交出多个目标。分组本身是确定性的，有几个目标就开几组。

### 4.5 ④ 并发诊断（parallel_evidence）

**调度**：`resolve_lane_workers` 取值顺序为 `workflow.evidence.parallel.max_workers`（当前 10）> 环境变量 `AIOPS_AUTONOMOUS_PARALLEL_WORKERS` > 默认 3，限制在 1 到 16。修复规划使用同一上限。

**lane 隔离**：
- 每组使用独立的 `AICall` client，工作记忆和压缩策略都不共享。
- `request_contract` 收窄为本组 Pod（scope=pod），问题改写为"只针对 ns/pod"。
- 父任务的原始问题保留在 `original_question`。
- layer 已读的 Runbook 以引用形式共享。
- 归档在 `<run_id>-gN/`。

**lane 工具面**（17 个）：`execute_pod_promql`、`query_pod_logs`、`query_pod_tracing`、`query_pod_topology`、`query_pod_lifecycle`、本 Pod 的 describe / events / yaml / get_by_name、当前 / previous / 容器日志、通用 Prometheus 即时 / 区间查询、`fetch_runbook`、`read_context_archive`。集群列表、grep 类工具和 TodoWrite 不在 lane 内。

**每组依次运行两个阶段**：

| 阶段 | 方式 | 输出契约 | 失败处理 |
|---|---|---|---|
| evidence（取证） | Agent 循环，开启 thinking，最多 48 步 | `EvidenceStageOutput`：`analysis`、`key_facts`（≤8，每条带真实 `evidence_refs`）、`unresolved`（≤6）、`runbook_refs` | 交接置空，unresolved 写"证据结构化交接无效"，记 `execution_incomplete` |
| rca（根因） | 无工具的单次结构化交付，输出上限 `delivery=10000` | `DiagnosisCaseOutput`：`outcome`（abnormal / recovered / healthy / inconclusive）、`summary`、`cause`、`certainty`（unknown/hypothesis/supported/confirmed）、`key_facts`、`unresolved`、`report` | 原文存入 `cases/invalid-output.txt`；用 evidence 阶段的真实事实生成兜底报告（注明"不构成根因结论"），标记 partial |

**RCA 交付后的代码处理**（`bind_case_result`）：
1. 组 ID、目标身份、归档路径由代码绑定，模型不能改写，也不能注入修复命令。
2. 修复被二次转义的段落换行，代码和日志原文不动。
3. 删除"待核实…"小节；未确认项保留在 `unresolved` 中继续交接。
4. 给"关键证据"表的来源列加 **Kubernetes / Metrics / Logging / Tracing** 标签，按工具名统一映射；单元格已写明维度的不再重复。
5. 写 `cases/result.json`、`cases/evidence-index.json`（本组全部工具结果的索引）。

**故障隔离**：一组失败只把该组标为 partial，已采集的证据保留，其他组继续。只有"模型流式连接中断"才取消全部 lane。

**实例**（4 组同时启动）：

| 组 | evidence 各轮（秒 / 输出 token / 工具调用数） | 总耗时 | 结果 |
|---|---|---|---|
| 1（04） | 102 / 4000 / 0（思考过长，未调用工具） | 127 秒 | partial，兜底报告 |
| 2（06） | 20/688/3、15/598/3、9/359/2、31/1309/6、35/1296/0 | 159 秒 | completed |
| 3（09） | 28/1032/5、60/2405/0 | 139 秒 | completed |
| 4（11） | 共 7 轮，最后一轮 70/3801/0 | 259 秒 | completed，supported |

每组最后一个"0 次工具调用"的轮次是 evidence 的结构化交接；RCA 每组另需 45 到 50 秒。

### 4.6 工具调用链路（所有 Agent 循环相同）

```
模型发出 tool_calls
 ├─ 护栏（llm.agent_guards）
 │   · 写工具不在名单内 → 拒绝
 │   · 单轮最多执行 16 个调用（max_tool_calls_per_turn）
 │   · 同一工具同参数再次出现：不执行，返回"结果未变化"提示；
 │     首次结果被截断的，返回原文下一段（repeat_page_chars=3000）；
 │     超过 max_identical_calls=3 → 停止本阶段并收卷
 │   · 一整轮全是已回答过的调用（≥2 个）→ 视为已完成，收卷交付（finalize_on_idle_round）
 │   · 流式拼接损坏的工具参数在发送前修复或丢弃，避免整轮 HTTP 400
 ├─ 执行 MCP 工具
 ├─ ObservationProcessor：三种表示归档到 tools/NNN-<node>-<tool>.{raw,structured,summary}
 │   · raw：Agent 实际收到的响应（不等于数据源全部数据）
 │   · structured：规范化的实体、事实、计数、覆盖、来源
 │   · summary：有预算的模型可见投影
 │   按工具处理：
 │   · query_pod_lifecycle → 核心字段 / 清单视图（字段需由模型点名）
 │   · Prometheus / 日志 / Tracing → 确定性可观测性投影：按信息量排序、按模式轮换选取，
 │     预算约 3000 字符（observation_summary.max_chars），保留统计、来源、覆盖与遗漏计数
 │     （例：日志 28903 → 3151 字符，12 条中选 4 条，省略 8 条可回读）
 │   · kubectl describe / yaml 等大结果 → 关键行 +"未展示不代表不存在"+ raw_ref
 │   · fetch_runbook / read_context_archive → 原文透传
 │   · semantic_success：成功但为空 ≠ 失败 ≠ 正常
 └─ 模型看 summary；需要更多时 read_context_archive(raw_ref, offset, length) 分段回读
    （路径限定在归档根目录内，不会自动重新采集）
    前端收到 tool_result（带维度、实体、raw_ref），卡片按维度显示徽标
```

### 4.7 上下文预算与压缩

策略"重前期"（2026-10-19）：决定性事实大多在前中期取得，触发压缩时只留最近 1-2 次交互原文，预算主要给承载早期事实的工作记忆；摘要提示词（`CONTEXT_SUMMARY_PROMPT`）按"决定性事实 → 出处 → 空/失败 → 推测 → 未解决"的优先级、按对象分节输出，并要求原样保留工具结构化字段的键与值。

当前真正生效的是"请求预算触发的工作上下文压缩"（[working_context.py](../app/core/aicall/working_context.py)），触发点由硬输入上限决定：

```
硬输入上限 = min(窗口 × hard_guard_input_ratio, 窗口 − 本轮输出预留 − safety_tokens) − 256（估算误差）
窗口 54000：min(48600, 54000 − 4000 − 2000) − 256 ≈ 47744 token
```

| 项 | 当前值 | 是否随窗口变化 |
|---|---|---|
| 触发 | 单次请求输入超过上述硬上限（约 47.7k） | 是（比例 0.90 + 绝对预留） |
| 近期原文保留 | 最近 `recent_keep_interactions`=2 次完整交互；最新一次 ≤ 窗口 15%，其余合计 ≤ `recent_keep_ratio`=6% | 是 |
| 较早历史 | 按段整理成工作记忆，单段输入 ≤ 窗口 × 72%；≥3 段时最多 3 路并行，按原顺序合并 | 是 |
| 工作记忆长度 | `summary_output_ratio`=8% × 窗口（54K≈4320，30K≈2400，70K≈5600）；分段证据卡为其 60% | 是 |
| 每轮输出预留 | agent 4000 / delivery 10000 / compaction 3000 / router 1200 | 否（绝对值） |
| 单条工具摘要 | `observation_summary.max_chars`=3000 字符 | 否（绝对值） |
| 不拆分 | 工具调用与其响应不拆开 | — |
| 失败 | 摘要为空、截断、超预算或分段失败都不替换原历史，如实报告 | — |
| 证据回执 | `evidence_receipts` 在压缩后保留工具/对象/状态/引用的轻量记录 | — |
| 前端 | "压缩上下文中…" → "上下文压缩完成，继续调查" | — |
| 归档 | `compactions/<node>-NNN.before/after.json` | — |

注意：旧的"运行时压缩"路径（代码默认 `max_context_window=35000` / `trigger_ratio=0.70`，已从部署配置删除）只在模型窗口 ≤ 35000 时生效，当前窗口 54000 下不会触发；`AIOPS_EVIDENCE_VIEW_MODE` 未开启，按证据预算的压缩也不生效。实测最近 1110 轮请求输入中位数约 14k、P90 约 23k、最大约 49k，压缩很少触发。

### 4.8 结构化交付与收卷

- **交付方式**：结果 schema 作为工具挂进工具列表，`tool_choice=auto`（`llm.structured_tool_choice`），服务端用 Pydantic 校验（[structured_transport.py](../app/core/aicall/structured_transport.py)）。不用指名 tool_choice，原因是 vLLM 的语法约束解码会让 Qwen3.6 不转义内层引号，字段在第一个引号处被截断。
- **循环内 tool_choice**：`create_agent` 带 ToolStrategy 时每轮强制 `tool_choice=any`（网关 `required`），小模型收尾时会复制上一条调用而不是调交卷工具。`llm.loop_tool_choice`（字符串或按节点映射，默认 `auto`）用 `AutoToolChoiceChatOpenAI` 改为 `auto`：一轮可以文本结束，再由收卷交付给出结构化结果。A/B 数据见 [llm-model-anomalies.md](llm-model-anomalies.md) §1.1。
- **校验失败**：把错误反馈给模型重试，最多 `structured_validation_retries=2` 次。
- **`finish_reason=length` 一律拒收**：LangChain 会把截断的参数补成不完整的字典，不能当作有效结果。
- **被拒回复归档**：`structured/<node>-rejected-NNN.json`，含实际参数、结束原因和错误。
- **收卷**：步数、时限或重复上限用尽，或模型以纯文本结束时，用本阶段的工具结果和分析做一次无工具、无 thinking 的结构化调用。材料里每条观测都带工具名与参数；被截断的草稿替换为标记，不作为依据。交付为空时以更大预留重试一次。
- **思考回传**：`llm.history_reasoning_field=reasoning`，只给当前工具循环内的 assistant 轮附带 reasoning，避免模型反复发出上一轮的调用。

### 4.9 ⑤ 总结（conclusion）

- **总览**：一次小的结构化调用，模型只看各组索引（组 ID、目标、状态、一句话摘要、确定程度），看不到报告全文与工具正文。
- **拼接**：`诊断对象：N 组；完整交付 X 组；未完整交付 Y 组` + 总览 + 每组 `## 异常组 N · ns/pod` + 该组报告原文。
- **总览失败时**：写"总览生成失败；独立诊断结果已保留"，各组报告照常展示。
- **结束后**：诊断记录 `diagnosis-record.v2` 按组落盘，供修复使用；同时生成 `run_report.md` 与 `ledger/*.json`。
- **实例**：总结 2.1 秒，总耗时 381 秒。

## 5. 修复与执行生命周期

修复节点（内部 id `remediation`）只负责**已有异常的修复**：制定变更方案 → 高危命令规则 → 人工审批（或 auto 模式）→ 执行 → 恢复观察。

**执行请求**（用户给出明确对象和动作："卸载 default/cloud-server"、"用 helm 部署 xx"、"删除/重启 xx"、"执行 kubectl/helm 命令"）不进修复节点，由路由器标为 `focused / operate`，在轻量路由上直接执行（[operate_tools.py](../app/core/workflow/operate_tools.py)）：写工具（`run_bash_command`、`kubectl_run_image`、`helm_install/upgrade/uninstall/rollback`）在调用前过同一套高危规则——bash 里的 kubectl 命令走 `CommandPolicy`，任何 shell 命令按 `denied_executables` 逐个可执行位置检查——命中即不执行并返回规则名；执行与拦截都写入修复审计（`command_executed` / `execution_denied`，含调用者、命令、结果摘要）。不审批、不做恢复观察。设计依据：run 3453c7ecdddc40bf 把 "helm delete" 送进修复节点，被 RepairDraft 的 group_id / kubectl-only 契约连续打回。

### 5.1 ⑥ 发起（三种入口，同一种按组批次）

入口：报告下的按钮（`POST /repair/batches`）、`/ask ... repair=plan`（诊断完成后自动建批次）、同一会话里的对话请求（"修复刚刚的问题"）。**auto 模式下诊断结束后自动建批次**（等同 `repair=plan`，不需要点击；方案自动执行，只有命中高危规则的任务停在 blocked 等人工反馈）。对话请求在会话已有分组诊断时，由 `RemediationNode._group_dispatch` 直接转成批次，不再让一个 Agent 处理整份诊断；点名的 Pod 只选它所在的组；诊断全部 healthy/recovered 时直接答复"无需修复"。API / A2A 带 `repair=plan` 且会话没有诊断时，路由改为先深度诊断、再自动建批次；网页对话（不带该参数）在会话没有诊断时仍由单个 Agent 现场规划（见 [API 待办](api.md#8-待办已记录未实现)）。只有结论为 abnormal / inconclusive 的组会生成任务。

```
"生成自动修复方案" → POST /repair/batches {diagnosis_run_id}
 · 校验会话身份（owner）
 · 每个诊断一个批次 batch-<run_id>（幂等：重复点击不会重复执行写操作）
 · 每个异常组一个 job（planning）
 · 后台并发规划，上限同诊断 lane；各 job 独立完成、独立更新状态：planning → planned → 执行线程
```

实例（当时上限仍为 3）：3 个 job 于 06:42:10 同时规划，分别用时 207、228、241 秒；第 4 个 job 到 06:45:37 才开始。12.0.44 起 4 组同时开始。

### 5.2 ⑦ 规划（RemediationNode，每组一个独立 Agent）

**输入**（`scoped_diagnosis` 只截取本组）：
- 本组历史报告、关键事实、未确认项与引用，并附说明"不是执行授权，生成方案前可自主核实"；
- 收窄后的 `request_contract`；
- **控制器链**（有诊断时取诊断目标，否则取请求中的 Pod）：代码用只读 `kubectl get -o json` 沿 `ownerReferences` 走到顶层（如 Pod → ReplicaSet → Deployment，最多 6 层）。

**Agent**：只读工具（写工具屏蔽），最多 `max_steps.remediation=64` 步，自行读取要修改对象的当前配置（必要时分页）。节点不依赖上游诊断：没有诊断时，修复对象和控制器链取自请求中的 namespace/Pod。

**输出 `RepairDraft`**（schema 按本次控制器链绑定）：
```
targets[]:     namespace, pod, pod_uid, group_id, owner_kind/name/uid（用集群事实覆盖模型填写）
actions[]:     id, group_id, description, risk, dry_run_command, execute_command,
               verify_command, rollback_advice, configuration_change, verification_conditions
assessments[]: group_id, status ∈ ready | needs_input | not_actionable | needs_evidence, reason, missing
answer:        给人看的方案说明
```

**代码校验**（不通过则反馈重试；最终仍无效，job 失败且不执行任何命令）：

| 规则 | 防止的问题 |
|---|---|
| 命令只能作用于本组 Pod 或其已核实的控制器 | 改到其他对象 |
| 写在被管理的中间层（ReplicaSet、Job）上 → 拒绝，并指出应改的顶层控制器 | 修改被上层覆盖、看似成功实际无效 |
| 命令中的控制器名与核实结果不一致 → 拒绝 | 把 ReplicaSet 名当作 Deployment 名使用 |
| 每个 target 要么有动作，要么在 assessments 中说明原因 | 命令写在正文、动作为空 |
| ready 必须有动作，其他状态不能带动作 | 状态与动作不一致 |
| 正文出现 kubectl 写命令而 actions 为空 → 拒绝 | 只有说明、没有可执行方案 |

规划结果以不可变记录（带版本号）保存；前端修复工作区展示修复对象、异常原因、命令、风险与回滚建议。规划过程（每次工具调用的参数、状态、结果摘要，以及模型思考）由 [progress.py](../app/core/remediation/progress.py) 有界记录在任务上（`planning_progress`），工作区按"规划 → 审批 → 执行 → 恢复观察 → 结果"展示当前阶段并实时显示规划过程。

### 5.3 ⑧ 执行（PodRepairExecutor）

1. **生效模式**：配置 `remediation.mode`（review / auto）加上管理员临时覆盖（`PUT /repair/policy/mode`，需 `X-AIOps-Admin-Token`，带 TTL，持久化，到期自动恢复）。`enabled=false` 时终态为 execution_disabled。
2. **策略预检**：在申请任何审批之前，检查所有动作的所有阶段：
   - 传输：只允许单条 kubectl 命令，不允许 shell 管道或重定向；
   - `denied_operations`：taint cp port-forward proxy attach auth certificate edit（2026-10-20 收窄：delete / apply / patch / scale / rollout 等常规修复动作放行，仍受范围校验）
   - `denied_flags`：--all --all-namespaces -A（批量）
   - `denied_resource_kinds`：node CRD PV storageclass clusterrole(binding) webhook（写拒绝，读不限）
   - `denied_executables`（容器内执行）：dd mkfs* fdisk sfdisk parted wipefs blkdiscard shred shutdown reboot halt poweroff。mcpstander bash 工具的 `BASH_BLOCKED_COMMANDS` 为这份名单加上 rm，Agent 的工具一律执行不了它们
   - `approval_required`（需人工审批）：drain、写 namespace、Pod 内 rm。规则判为"允许但需审批"：修复方案中可出现，执行前**强制人工审批，自动执行模式也一样**，审批卡片标注高危命令；对话执行（轻量路由）仍拦截。执行走后端执行器，不经过 MCP
   - `bulk_selector_on_write`：写操作禁止批量选择器。

   命中任一条：审计记 `command_denied`（含规则名），终态为 **blocked**，并说明"本计划尚未执行任何命令"。
3. **范围检查**：目标超出用户请求范围 → 拒绝。
4. **Pod 范围锁**：同一 Pod 已有待审批或执行中的方案 → 拒绝。
5. **基线**：执行前记录一次目标状态，供恢复判定使用。
6. **逐个动作执行**（整个任务限时 `max_duration_seconds=900`，超时为 timeout）：
   - review：每个动作单独审批（`approval_timeout_seconds=600`）；批准则继续，拒绝为 rejected，超时为 timeout（"600 秒内未批准，未执行"）。
   - auto：普通动作直接执行；含 `approval_required` 命令的动作照常等待人工审批，执行事件的 `approval` 记审批 ID 而不是 auto。
   - auto：不等审批，记 `approval=auto`。
   - 依次执行 dry_run → execute → verify：按参数列表执行，不经过 shell，单条命令有超时。
   - verify 失败不立即判失败，交给恢复观察作最终判断（模型写的验证命令只是启发式）。
   - 取消或方案被替代 → cancelled / superseded；已执行的动作不会自动回滚。

### 5.4 ⑨ 恢复观察（RecoveryWatch）

- 只读状态，每 5 秒一次（`recovery.poll_seconds`），最多 180 秒（`timeout_seconds`）。
- 判定规则只看状态，不针对具体故障：

| 观察到 | 判定 |
|---|---|
| 原 Pod 原本在删除中，现已不存在 | recovered（Terminating 类） |
| 仍有 deletionTimestamp | pending |
| Succeeded | recovered |
| 未 Ready | pending |
| 修复后同一 Pod 的重启次数仍在增加 | pending，稳定计时重新开始 |
| Running 且 Ready，持续 20 秒（`settle_seconds`） | recovered |

- 原 Pod 被替换时，按控制器的 selector 找到最新、未在删除中的 Pod 继续观察。
- 终态：recovered，或 not_recovered（"已执行，但 180 秒内未观察到恢复；请复查，未自动回滚"）。全程记入审计（`GET /repair/audit`）。

### 5.5 对话调整方案

`POST /repair/jobs/{id}/feedback`：带上旧方案和意见重新规划，生成 v+1。旧版本审批立即失效（superseded）。用户反馈被视为"人的决定"，不视为集群事实；涉及状态时模型仍需核实。


## 6. 多集群模式

只在挂载了多集群配置（`AIOPS_CLUSTERS_CONFIG`，见 `deploy-edge/clusters.mc.yaml`）时生效；没有该配置时，路由 schema、提示词、工具 schema、工具结果和 kubectl 调用与单集群完全相同。设计、边界与验收见 [多集群设计](multi-cluster-design.md)、[验收方案](multi-cluster-acceptance.md)，SDD 产物在 [specs/008-multi-cluster](../specs/008-multi-cluster/spec.md)。

| 环节 | 多集群下的行为 | 代码 |
|---|---|---|
| ① 路由 | 扩展契约增加 `cluster_mode`、`clusters`、`cluster_labels`；集群名由代码按注册表解析；没说范围、范围不在用户原话或会话中、集群不存在，一律反问；修复只针对一个集群 | `app/core/multicluster.py`、`request_router.py` |
| 工具 | 节点入口与并行通道按本次范围绑定 `cluster`：单个集群强制注入，多个集群校验在范围内；通道用自己组的集群 | `multicluster.scoped_tools`、`graph._bind_cluster_scope`、`autonomous_parallel` |
| MCP | 每次调用激活集群上下文：VictoriaMetrics 查询附加 `extra_label`；victoria 后端的"日志"是 K8s 事件（标注 `k8s_events`/`partial`），链路为 `capability_missing`；远端 kubectl 经垫片转发 | mcpstander `servers/cluster_scope.py` |
| ② 定位 | 涉及多个集群时，每个集群各跑一次定位（并行），合并为带集群前缀的目标与带集群的分组；单个集群失败只影响该集群 | `app/core/workflow/multicluster_location.py` |
| ⑤ 总结 | 各组标题带集群 | `case_report.py` |
| ⑧ 执行 | 远端集群的执行阶段作为 runner 异步任务（幂等键 `run:action:stage`，审批 ID 随任务传给 runner）；读操作与恢复观察经垫片；集群不可达时等待，不执行；结果无法确认时标记"结果未知"，不重新提交 | `pod_executor.py`、`aiops_edge/jobs_client.py` |
| 边缘 | 唯一的边缘组件 `aiops-edge-runner`：校验签名，用中心同一份命令规则再检查一遍，reader / writer 两个身份 | `aiops_edge/runner/`、`deploy-edge/runner.yaml` |

中心到边缘只经过 xnet 隧道 `/proxy` 与 runner；运行时没有任何边缘 kubeconfig（验收 X3 检查）。

## 7. 需求与边界对照

| 需求 | 边界 | 处理 |
|---|---|---|
| S1 从诊断进入修复 | 历史诊断不代表当前状态 | 规划材料注明"非授权、可核实"，模型用只读工具复查 |
| S1 展示对象/原因/命令 | 命令写在正文里 | schema 强制 actions + assessments，正文出现写命令即拒收 |
| S1 对话调整 | 旧审批误执行 | 新版本生成时旧审批失效 |
| S2 黑名单 | 规则要先于审批生效 | 审批前预检所有阶段，命中即 blocked 并给出规则名 |
| S2 审批与自动开关 | 临时切换需能自动失效 | 配置 + 管理员 TTL 覆盖 + 审计 |
| S3 结果与超时 | 命令成功不等于恢复 | 恢复观察看实际状态；审批 600 秒 / 整体 900 秒 / 观察 180 秒，各有明确终态 |
| 改中间层无效 | ReplicaSet/Job 会被覆盖 | 控制器链 + 写到中间层即拒绝 |
| 并发安全 | 同一 Pod 被两个方案同时修改 | Pod 范围锁、批次幂等 |
| 证据真实 | 编造引用 | 引用必须是真实归档路径；evidence-index 由代码生成 |
| lane 隔离 | 一组失败拖垮全部 | lane 故障局部化；只有模型断连才全部取消 |

## 8. 归档布局

报告根目录由 `AIOPS_CONTEXT_ARCHIVE_ROOT` 指定（部署在 PVC：`/tmp/aiops/reports/context_archives`）。

| 路径 | 内容 |
|---|---|
| `<run_id>/` | 主请求：路由、定位、分组、总结 |
| `<run_id>-gN/` | 各组 evidence / rca |
| `tools/NNN-<node>-<tool>.{call.json,raw.txt,structured.json,summary.txt}` | 一次工具调用的参数与三种表示 |
| `node_inputs/`、`node_outputs/` | 节点交接输入输出 |
| `requests/<node>-NNN.json` | 每轮模型请求轨迹（消息结构、`reasoning_tail`、重复调用计数） |
| `structured/<node>-rejected-NNN.json` | 被拒的结构化交付 |
| `budget/`、`compactions/` | 预算与压缩记录 |
| `parallel/plan.json`、`parallel/results.json` | 分组计划与各 lane 结果 |
| `cases/result.json`、`cases/evidence-index.json` | 单组结论与证据索引 |
| `ledger/`、`run_report.{json,md}` | 运行账本与工程异常发现（`GET /runs/{id}/report.md`） |

引用是容器内路径，不是浏览器 URL。归档可能包含业务日志和内部地址，需要控制权限与保留周期。

## 9. 已知限制

1. 发现阶段依赖 Agent 找全异常（设计选择）；漏找时不会出现多卡片。
2. 单轮思考用满 4000 token 且未调用工具时，不会自动重试，直接走兜底（见 [LLM 自身异常记录](llm-model-anomalies.md) 第 2 条）。
3. 重复调用会拿到原文下一段，等于奖励重复。
4. 结果为空的可观测性查询不在报告中展示。
5. 压缩相关参数多为绝对值，调整网关窗口时需要同步修改（见 4.7）。
6. 模型可能给出不成立的推断（如把删除时的 137 退出归因于 Readiness 失败），报告的 `certainty` 字段用于区分确定程度。
