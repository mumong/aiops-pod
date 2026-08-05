# CLAUDE.md — robusta 项目技术约定

> 此文件是 Claude Code 与项目维护者之间的"协议"，记录已确定的技术方向、架构约定和设计决策。
> 避免重复讨论或推翻已达成共识的设计。

---

## 1. 项目定位

**robusta** 是一个基于 FastAPI + HolmesGPT 的 K8s AIOps Copilot。
核心能力：接收用户问题 → 调用 LLM（tool calling）+ MCP 工具 + Runbook 知识库 → 输出诊断报告。

---

## 2. 架构总览

### 两种执行模式（并行存在）

| 模式 | 入口 | 触发条件 | 说明 |
|------|------|----------|------|
| **原有模式** | `execute_query_stream` → HolmesGPT agentic loop | `USE_WORKFLOW != true` | 单次 LLM agentic loop |
| **工作流模式** | `_execute_query_stream_workflow` → `WorkflowExecutor` | `USE_WORKFLOW=true` | 4 节点 LangGraph 工作流 |

### 工作流 4 节点

```
layer（问题定位） → [条件路由] → evidence（证据采集） → rca（根因分析） → conclusion（汇总总结）
                       ↘ HEALTHY 模式 ────────────────────────────────────→ conclusion
```

- 每个节点独立，有自己的 prompt 和 LLM 调用
- QUERY 模式（非故障查询）走 `layer → evidence → conclusion`
- HEALTHY 模式（集群健康）走 `layer → conclusion`
- 诊断模式（ABNORMAL，存在异常 Pod）走完整流程；异常分类由 pod_status_keyword / pod_abnormal_type 表达，L0-L4 层级映射已移除

### SSE 事件流

```
run_start → node_start → [thinking...] → node_complete → ... → final → run_end
```

- `thinking` 事件在 `node_start` 和 `node_complete` 之间发出
- 包含 `tool_start`, `tool_result`, `ai_message`, `iteration_end` 子类型
- text 模式用 `💭` 前缀渲染

---

## 3. 关键设计决策（已确定，不再讨论）

### 3.1 LLM 调用方式

- **统一走 `_call_with_stream_limited(messages, max_steps=N)`**
- 内部临时修改 `ai.max_steps`，调完恢复
- 底层调 `call_with_stream(ai, messages)` 收集事件

### 3.2 max_steps 可配置化

**优先级**: 环境变量 > `config.yaml` > 代码默认值

```yaml
# config.yaml
workflow:
  max_steps:
    layer: 3
    evidence: 10
    rca: 8
    conclusion: 3
```

环境变量: `WORKFLOW_MAX_STEPS_LAYER`, `WORKFLOW_MAX_STEPS_EVIDENCE`, `WORKFLOW_MAX_STEPS_RCA`, `WORKFLOW_MAX_STEPS_CONCLUSION`

通过 `HolmesService.get_node_max_steps(node_id)` 获取。

### 3.3 Thinking（推理过程）实时展示

**数据流**:
```
call_with_stream → StreamResponse.intermediate_events
    → 节点 execute() 存入 state["thinking_events"]
    → executor 在 node_complete 前 yield thinking SSE 事件
```

- `StreamResponse` 包含 `intermediate_events: List[Dict]` 字段
- 各节点 `_analyze_with_llm` 返回 `(result, thinking_events)` 元组
- 事件带 `node` 标记便于区分来源

### 3.4 config.yaml 非 Holmes 字段处理

`config_loader.py` 中 `_excluded_keys` 维护需要从 Holmes Config 验证中排除的顶级字段：
```python
_excluded_keys = {"stream_output", "sub_agents", "federation", "llm", "workflow"}
```
新增自定义顶级配置块时，**必须**加入此集合。

### 3.5 MCP 工具优先

- 内置工具集大部分关闭，由外部 MCP Server 替代
- MCP SSE 端点配置在 `mcp_servers` 块
- 只保留 `core_investigation` 和 `runbook` 两个内置工具集

---

## 4. 文件职责速查

| 要做什么 | 改哪里 |
|----------|--------|
| 改 Agent 诊断框架/输出模板 | `app/core/prompts.py` |
| 新增/编辑 Runbook 内容 | `knowledge_base/runbooks/*.md` |
| 改 Runbook 加载逻辑 | `app/core/runbook.py` |
| 新增 MCP 工具 | 写 MCP Server + 配置到 `config.yaml` 的 `mcp_servers` |
| 修改工作流节点逻辑 | `app/core/workflow/nodes/*.py` |
| 修改工作流图/路由 | `app/core/workflow/graph.py` |
| 修改 SSE 事件格式 | `app/core/workflow/executor.py` (工作流) / `app/core/holmes/streaming.py` (原有) |
| 修改 text 模式输出 | `app/core/service.py` → `_workflow_to_text()` |
| 修改性能指标 | `app/core/workflow/metrics.py` |
| 修改 LLM 调用包装 | `app/core/holmes/call_wrapper.py` |
| 修改配置加载 | `app/core/holmes/config_loader.py` |
| 修改 K8s 部署 | `deploy/` 目录 |

---

## 5. 编码约定

### 5.1 节点开发模式

每个节点的 `_analyze_with_llm` 方法签名约定：
```python
def _analyze_with_llm(self, ...) -> tuple:
    """Returns (result_dict, intermediate_events_list)"""
```

节点 `execute()` 方法必须：
1. 设置 `new_state["current_node"] = self.node_id`
2. 成功时：合并 thinking_events 到 state
3. 失败时：保留上游 thinking_events（`state.get("thinking_events", [])`)

### 5.2 配置约定

- 本地开发: `config/config.yaml`
- K8s 部署: `deploy/configmap/config.yaml`（嵌在 ConfigMap 里，多 4 空格缩进）
- 两份配置必须**同步更新**

### 5.3 环境变量

| 变量 | 用途 |
|------|------|
| `USE_WORKFLOW` | `true` 启用工作流模式 |
| `LLM_API_KEY` | LLM API Key |
| `LLM_MODEL` | 模型名 |
| `LLM_API_BASE` | API 代理地址 |
| `WORKFLOW_MAX_STEPS_{NODE}` | 节点 max_steps 覆盖 |

### 5.4 日志约定

- 节点开始: `📍 [node_name] ...`
- 节点完成: `✅ [node_name] ...`
- 工作流开始: `🚀`
- 工作流完成: `🎉`
- 错误: `❌`

---

## 6. 性能目标

| 指标 | 目标 |
|------|------|
| MTTR | < 10 分钟 |
| 根因准确率 | >= 80% |
| 证据完整率 | > 90% |
| Runbook 覆盖率 | > 90% |

---

## 7. 变更日志（重大决策）

| 日期 | 决策 | 说明 |
|------|------|------|
| 2025-xx | 工作流模式 POC | 4 节点 LangGraph，与原有模式并行 |
| 2025-xx | QUERY 条件路由 | 非故障查询走 evidence 取数后再 conclusion，HEALTHY 直接到 conclusion |
| 2025-xx | 节点级 max_steps | 每个节点独立控制 LLM 迭代上限 |
| 2026-03-23 | max_steps 可配置化 | 环境变量 > config.yaml > 默认值 |
| 2026-03-23 | thinking 实时展示 | SSE thinking 事件 + text 💭 模式 |
| 2026-03-24 | threading + queue 实时 thinking | executor 用后台线程跑 LangGraph，主线程通过 queue 实时 yield thinking 事件 |
| 2026-03-24 | 节点基类 _call_llm | 统一 streaming + metrics + thinking，所有节点共用 |
| 2026-03-24 | kubectl_top 工具层面禁用 | service.py 初始化后从 tools_by_name 中删除 kubectl_top_nodes/pods |
| 2026-03-24 | 证据数据流修复 | evidence_analysis 包含 tool_data（MCP 工具真实输出）+ llm_analysis |
| 2026-03-24 | conclusion 纯文本生成 | conclusion 节点用 litellm 直接调用（不带工具），避免 LLM 调工具不写报告 |
| 2026-03-24 | RCA 不重复采集 | RCA prompt 动态注入"不要重复采集数据"指令，基于已有证据分析 |
| 2026-03-24 | 联邦查询实时流式 | federation/ask/v2 并发查询子集群，实时转发 thinking 输出 |
| 2026-03-24 | 联邦查询并发执行 | 多个 query_cluster 用多线程并发，共享 queue 按到达顺序输出 |
| 2026-03-24 | Runbook 从 thinking 检测 | 从 thinking_events 的 fetch_runbook 结果中提取 runbook 标题 |
| 2026-03-24 | 置信度保底 80% | 有工具证据+有结论 → 保底 80%（prompt + executor 后置修正） |
| 2026-03-24 | 性能统计简化 | 各节点百分比以总耗时为分母（加起来≈100%），去掉 LLM/工具百分比 |
| 2026-04-08 | layer_full_analysis 数据流修复 | 两阶段架构中阶段1完整分析文本（含工具输出）被阶段2精简JSON丢弃，导致下游evidence/rca"证据不足"。新增 `layer_full_analysis` state 字段传递完整数据 |
| 2026-08-04 | conclusion 第一性原理精简 | conclusion 节点从 8697 行重写为 ~660 行：恢复 main 分支人类可读富模板 `CONCLUSION_FORMATTER_PROMPT`（📊概览/🔍现象/🕵️证据链/🎯根因/🛠️修复/📋验证），单次 `call_simple` 纯文本生成；删除 fact 标记语义草稿协议、`report_presentation.py` 确定性渲染器、12 步正则矫正链、kubectl 写命令语义授权引擎。格式稳定性靠富模板而非事后矫正（小模型友好） |
| 2026-08-04 | 真实工具数据升级为报告核心 | conclusion 的工具数据段改用 thinking 事件的完整 `result`（observation 摘要，单条 1500 字符、最多 24 条），不再是 300 字符 preview；用户消息固定 5 段：问题/阶段1定位/阶段2证据摘要/阶段3根因/工具真实数据 + REMEDIATION_PLAN_PROMPT |
| 2026-08-04 | 删除 report-authority 指纹机制 | `evaluate_report_authority`/`attach_internal_report_authority`/`select_authoritative_fact_ledgers` 及指纹绑定全部移除；`tool_item_allows_fact_ledger_projection` 退化为纯结构校验。fact ledger 可信度由 normalize/validate 保证 |
| 2026-08-04 | 删除 RCA limitations 措辞重写 | `validate_rca_claims` 不再对 logging-gap/trace-gap 措辞做正则重写（~500 行），limitations 保持 LLM 原文，事实可信度由 fact-id 校验保证 |
| 2026-08-04 | 死代码清理 | 删除：`skills/{engine,rules,evidence}.py`（规则引擎，无人引用）、`context/usage_probe.py`（全部调用点禁用）、`mcp/mcp_patch.py`、`holmes/tool_logging_patch.py`（HolmesGPT 工具链已被 AICall 取代）、evidence 的 `plan_match_adjudicator`（从未接线）、schemas 中 `ConclusionOutput`/`EvidenceMatch*`/`ReportAuthorityDecision`/`EvidenceLimitation` |
| 2026-08-04 | 证据表带类型列 | 报告模板"已采集证据+证据关联分析"合并为"真实采集证据结果"：每行标注类型（Metric/Logging/Tracing/Topology/K8s Event/K8s State/K8s Config），Metric/Logging/Tracing 采到必须逐条入表 |
| 2026-08-04 | 补证归属 agent 自主（架构决策） | 补采**不做代码层控制**：evidence agent 在 ReAct 循环内根据真实工具结果自主决定是否继续补证（prompt："补证由上一轮真实结果驱动"），硬约束只有 max_steps 与上下文预算。plan 只作参考与完整度统计口径，不主导采集。曾实现过代码驱动的补采外层循环，同日按此决策移除 |
| 2026-08-04 | 移除 L0-L4 层级映射 | layer 节点只判定 `HEALTHY / ABNORMAL` + 异常 Pod 状态分析（pod_status_keyword/pod_abnormal_type）；状态→层级映射表、compatible_layers、层级展示全部移除。Layer 枚举保留 L0-L4 仅作历史输入兼容（解析时归一化为 ABNORMAL）。报告概览显示"Pod 异常状态"而非"问题层级" |
| 2026-08-05 | 工具数据去重键修复 | `_build_tool_data_section` 去重键从"工具名+结果前80字符"改为"工具名+调用参数+结果前缀"：可观测性工具结果共享相同 OBSERVABILITY_QUERY 契约头，旧键把补采结果（trace_id 定向 span、range 趋势）误判为重复丢弃 |
| 2026-08-05 | 集成 pod-anomaly-cases 测试库 | aiopsdata 的 c01-c11 异常 case 库拷入 `test/pod-anomaly-cases/`；Makefile 新增 case-list/case-deploy/case-validate/case-ask/case-deploy-all/case-clean。c07 config-error 非 OOM 场景实测通过：正确排除 OOM、根因"缺失关键配置"95% 置信度，报告含全五维真实数据与 trace_id |
| 2026-08-05 | 可观测性真实值结构化直通（第一性原理） | conclusion 的可观测性工具数据改从 `ev[structured].facts` 结构化提取真实值（`_render_observability_structured`），而非拍平文本盲截断：metric 渲染 `name=value unit（趋势）`、tracing 渲染 `请求→响应码 src→dst trace_id`、logging 渲染日志原文；QUERY DSL 噪声丢弃，截断只丢整条低价值事实、绝不砍值；coverage=empty 如实呈现。修复了 metric 数值(302)被截断、tracing flow 未进 summary 而只显示 coverage/query_succeeded 元状态的问题。干净环境 c06/c09 实测：`restarts_total=4 count`、`GET /work→200 trace_id=...` 真实值进证据表 |

---

## 8. 关键架构决策（已确定）

### 8.1 实时 Thinking 架构

```
executor.execute_stream()
  │
  ├── WorkflowNode.set_event_queue(queue)
  ├── threading.Thread → workflow.stream(initial_state)
  │     │
  │     └── 节点 _call_llm() → call_with_stream_and_queue()
  │           │
  │           └── 每个 stream event → queue.put(("thinking", event))
  │
  └── 主线程 while loop:
        queue.get() → yield thinking/node_start/node_complete
```

- thinking 事件到达时自动补发 node_start（修复时序）
- finally 块中 clear_event_queue + worker.join

### 8.2 节点数据流

```
layer → state["layer_analysis"] (JSON, 结构化分类结果)
  │     state["layer_full_analysis"] (阶段1完整分析文本，含工具输出)
  │
  │  ⚠️ 重要：下游节点必须优先使用 layer_full_analysis（含 kubectl describe/logs 等原始数据）
  │     layer_analysis 只是精简的 JSON（layer, confidence, reasoning），不含工具输出！
  │
evidence → state["evidence_analysis"] (JSON, 含 tool_data + llm_analysis)
  │         state["thinking_events"] (所有节点的工具调用记录)
  │         读取: state.get("layer_full_analysis", "") or state.get("layer_analysis", "{}")
  │
rca → state["rca_analysis"] (JSON, 含 llm_raw_analysis)
  │   读取: state.get("layer_full_analysis", "") or state.get("layer_analysis", "")
  │   prompt 动态注入已有数据 + "不要重复采集"
  │
conclusion → litellm 直接调用（不带工具）
             从 thinking_events 提取工具真实数据传给 LLM
```

#### ⚠️ layer 两阶段架构数据流约定（不可破坏）

layer 节点使用两阶段架构：
- 阶段1: HolmesGPT agentic loop → 调用工具收集数据，输出自然语言分析（enriched_text）
- 阶段2: litellm 提取 → 从分析文本中提取结构化 JSON（layer, confidence, reasoning 等）

**关键约定**：阶段2 的 extracted dict 中必须注入 `full_analysis = enriched_text`，
然后在 execute() 中 `pop("full_analysis")` 存入 `state["layer_full_analysis"]`。
下游 evidence/rca 必须优先读取 `layer_full_analysis`，回退到 `layer_analysis`。

涉及文件：
- `layer_classifier.py`: `_analyze_with_llm()` 注入 full_analysis，`execute()` pop 到 state
- `evidence_collector.py`: `execute()` 读取 layer_full_analysis
- `root_cause_analyzer.py`: `execute()` 读取 layer_full_analysis
- `state.py`: WorkflowState 类型定义
- `executor.py`: state 初始化包含 layer_full_analysis

### 8.3 联邦查询实时流式

```
federation/ask/v2 → FederationAgent.ask_stream()
  │
  ├── LLM Tool Calling 决定查哪些集群
  │
  └── _execute_tools_streaming()
        │
        ├── 多线程并发查询子集群（每个子集群一个线程）
        ├── 共享 queue 收集所有 chunk
        ├── 主线程按到达顺序实时 yield
        └── 收集完整文本 → extract_final_answer → 给 LLM 合成
```

### 8.4 工具禁用机制

- `service.py` 初始化后调用 `_disable_tools(["kubectl_top_nodes", "kubectl_top_pods"])`
- 直接从 `ai.tool_executor.tools_by_name` 中删除
- prompt 层面也有 `⛔⛔⛔ 绝对禁止` 双重保障

### 8.5 质量指标产生位置

| 指标 | 代码位置 |
|------|----------|
| MTTR | `metrics.py` → `total_duration_seconds` |
| 根因置信度 | `executor.py:536-611` → 4 层提取 + 后置修正（保底 80%） |
| 证据完整率 | `executor.py:504-507` → `evidence_collected / evidence_planned` |
| Runbook | `executor.py:616-660` → thinking_events + state 文本 + log_listener |
| 格式化输出 | `metrics.py:format_stats_block()` + `format_metrics_block()` |
