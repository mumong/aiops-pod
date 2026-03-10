# 架构与模块地图

---

## 设计原则

- **高内聚**：同一类能力（配置加载、流式输出、MCP 管理、联邦查询）放在同一模块域
- **低耦合**：主服务不依赖"本地 tools"，默认通过配置连接第三方 MCP Server
- **多集群优先**：联邦查询（Agent-to-Agent）是核心差异化能力
- **双模式**：默认 HolmesGPT agentic loop，可切换 LangGraph 四阶段工作流
- **多 LLM**：通过 litellm 支持任意 LLM 提供商，配置切换无需改代码

---

## 目录结构

```
robusta/
├── run.py                              # 启动入口
├── app/
│   ├── main.py                         # FastAPI 应用 + 生命周期
│   ├── api/
│   │   └── routes.py                   # 所有 HTTP API 端点
│   └── core/
│       ├── service.py                  # HolmesService（全局单例编排器）
│       ├── prompts.py                  # 所有 LLM 提示词
│       ├── runbook.py                  # RunbookManager
│       ├── environment.py              # 环境检测与配置路径
│       ├── paths.py                    # 项目根目录工具
│       ├── federation/                 # 联邦查询模块（多集群）
│       │   ├── __init__.py             # Coordinator + Agent 全局单例工厂
│       │   ├── registry.py             # AgentRegistry（从 config 加载子集群）
│       │   ├── client.py               # SubAgentClient（httpx 连接池）
│       │   ├── aggregator.py           # FederationAggregator（v1 并发聚合）
│       │   ├── toolset.py              # ListClustersTool + QueryClusterTool
│       │   └── agent.py                # FederationAgent（v2 智能路由）
│       ├── holmes/                     # HolmesGPT 封装层
│       │   ├── config_loader.py        # YAML 配置加载、环境变量替换
│       │   ├── query_stream.py         # 流式输出（text / sse）
│       │   ├── streaming.py            # SSE 消息封装、耗时格式化
│       │   ├── call_wrapper.py         # 流式事件收集为响应对象
│       │   ├── introspection.py        # 启动自检（工具/MCP/Runbook 摘要）
│       │   └── tool_logging_patch.py   # 工具调用日志 patch
│       ├── mcp/
│       │   └── mcp_patch.py            # MCP 工具补丁
│       ├── workflow/                   # LangGraph 工作流（USE_WORKFLOW=true）
│       │   ├── graph.py                # 工作流图构建
│       │   ├── executor.py             # 工作流执行器
│       │   ├── state.py                # 工作流状态定义
│       │   ├── metrics.py              # 工作流执行指标
│       │   └── nodes/                  # 四个工作流节点
│       │       ├── base.py             # WorkflowNode 基类
│       │       ├── layer_classifier.py # 节点1：问题定位（QUERY/L0-L4）
│       │       ├── evidence_collector.py # 节点2：证据采集
│       │       ├── root_cause_analyzer.py # 节点3：根因分析
│       │       └── conclusion_formatter.py # 节点4：报告生成
│       └── skills/
│           └── models.py               # Layer 枚举（QUERY/L0-L4）
├── knowledge_base/runbooks/            # Runbook 知识库
├── config/config.yaml                  # 本地开发配置
├── deploy/                             # K8s 部署配置
│   ├── k8s-simple.yaml                 # Deployment + Service
│   ├── configmap/config.yaml           # 生产配置（ConfigMap）
│   ├── secrets/core.yaml               # LLM Key 等敏感配置（Secret）
│   └── rbac.yaml                       # ServiceAccount + RBAC
├── reports/                            # 子集群诊断报告（运行时生成）
└── Makefile                            # 构建 & 部署命令
```

---

## API 端点

| 端点 | 方法 | 参数 | 说明 |
|------|------|------|------|
| `/ask` | GET/POST | `q`(必填), `stream`(true), `format`("text"), `max_steps`(20) | 单集群查询 |
| `/q/{question}` | GET | `stream`, `format`, `max_steps` | 路径参数方式查询 |
| `/federation/ask` | GET/POST | `q`, `max_steps`(30), `conclusion_max_tokens`(8192) | 多集群并发查询 |
| `/federation/ask/v2` | GET/POST | `q`, `max_steps`(30) | A2A 智能路由 |
| `/reports` | GET | `cluster`(可选过滤), `limit`(50) | 子集群报告列表 |
| `/reports/{filename}` | GET | — | 查看报告内容 |
| `/health` | GET | — | 健康检查 |
| `/tools` | GET | — | 工具列表 |
| `/tools/detail` | GET | — | 工具详情（按 toolset 分组） |
| `/runbooks` | GET | — | Runbook 列表 |
| `/artifacts/{id}` | GET | — | 被截断的大输出全文 |

---

## 请求链路

### 单集群查询（`/ask`）

```
用户 → /ask?q=Pod重启&max_steps=20
       ↓
  routes.py: ask_get/ask_post
       ↓
  ┌─ USE_WORKFLOW=false ─────────────────────┐
  │  HolmesService.execute_query_stream()    │
  │       ↓                                   │
  │  HolmesGPT agentic loop                  │
  │    ├─ System Prompt (SYSTEM_PROMPT)       │
  │    ├─ Runbook 匹配                       │
  │    └─ LLM Tool Calling → 生成结论        │
  └──────────────────────────────────────────┘
  ┌─ USE_WORKFLOW=true ──────────────────────┐
  │  WorkflowExecutor.execute()              │
  │       ↓                                   │
  │  ①定层 → ②采证 → ③根因 → ④报告         │
  │  (每个节点独立调用 LLM + 工具)            │
  └──────────────────────────────────────────┘
       ↓
  流式文本 / SSE 返回
```

### 工作流模式数据流

```
layer_classifier (LAYER_CLASSIFIER_PROMPT)
  输入: question
  输出: layer(QUERY/L0-L4), confidence, key_entities
       ↓
evidence_collector (EVIDENCE_COLLECTOR_PROMPT)
  输入: question, layer
  输出: evidence_summary, evidence_details[], tools_used[]
  行为: QUERY→直接采集数据 | L0-L4→多维故障采证
       ↓
root_cause_analyzer (ROOT_CAUSE_ANALYZER_PROMPT)
  输入: question, layer, evidence
  输出: root_cause, confidence, causal_chain[]
  行为: QUERY→仅汇总数据(无工具) | L0-L4→因果链推理
       ↓
conclusion_formatter (CONCLUSION_FORMATTER_PROMPT)
  输入: question, layer, evidence, root_cause
  输出: 最终 Markdown 报告
  行为: QUERY→数据表格 | L0-L4→完整诊断报告
```

### Agent-to-Agent 联邦查询（`/federation/ask/v2`）

```
用户 → /federation/ask/v2?q=查询 cluster-24 的 CPU
       ↓
  FederationAgent.ask_stream()
       ↓
  litellm.completion (FEDERATION_AGENT_PROMPT)
       ↓
  Tool Calling 循环:
    ① LLM → list_clusters()          → 获取可用集群列表
    ② LLM → query_cluster("cluster-24", "CPU 使用率")
              ↓
         SubAgentClient → POST http://10.2.0.24:30800/ask
              ↓
         子集群执行诊断并返回结果
    ③ LLM → 生成最终汇总报告
       ↓
  流式文本返回
```

---

## 核心模块说明

### 1. HolmesService（`app/core/service.py`）

全局单例编排器，负责：
- 读取 config.yaml → 解析 LLM 配置（优先级：Secret > config > 默认值）
- 创建 HolmesGPT AI 实例
- 加载 Runbook 知识库
- 条件性初始化 FederationCoordinator 和 FederationAgent
- 提供 `execute_query()` 和 `execute_query_stream()` 方法

### 2. Holmes 子模块（`app/core/holmes/`）

| 模块 | 职责 |
|------|------|
| `config_loader.py` | YAML 配置加载、环境变量替换、排除非 Holmes 字段 |
| `query_stream.py` | `execute_query_stream_text()` / `_sse()` 流式输出 |
| `call_wrapper.py` | 流式事件收集为响应对象 |
| `streaming.py` | SSE 消息封装、耗时格式化 |
| `introspection.py` | 启动时输出工具集/MCP/Runbook 加载摘要 |

### 3. 联邦查询（`app/core/federation/`）

| 模块 | 职责 |
|------|------|
| `registry.py` | 从 config 加载子集群列表 |
| `client.py` | httpx 异步调用子集群 `/ask` 端点 |
| `aggregator.py` | v1 并发查询所有集群 + LLM 合成报告 |
| `toolset.py` | `list_clusters()` + `query_cluster()` 工具定义 |
| `agent.py` | v2 litellm Tool Calling 循环（智能路由） |

### 4. 工作流（`app/core/workflow/`）

LangGraph 四阶段流水线，通过 `USE_WORKFLOW=true` 启用：

| 节点 | 文件 | 提示词 | 职责 |
|------|------|--------|------|
| layer | `layer_classifier.py` | `LAYER_CLASSIFIER_PROMPT` | 判断 QUERY/L0-L4 层级 |
| evidence | `evidence_collector.py` | `EVIDENCE_COLLECTOR_PROMPT` | 调用工具采集证据 |
| rca | `root_cause_analyzer.py` | `ROOT_CAUSE_ANALYZER_PROMPT` | 根因分析 |
| conclusion | `conclusion_formatter.py` | `CONCLUSION_FORMATTER_PROMPT` | 生成报告 |

### 5. 提示词（`app/core/prompts.py`）

详见 [提示词参考文档](./PROMPTS.md)。

| 常量 | 用途 |
|------|------|
| `SYSTEM_PROMPT` | 默认模式 HolmesGPT 系统提示词 |
| `LAYER_CLASSIFIER_PROMPT` | 工作流节点 1 - 问题定位 |
| `EVIDENCE_COLLECTOR_PROMPT` | 工作流节点 2 - 证据采集 |
| `ROOT_CAUSE_ANALYZER_PROMPT` | 工作流节点 3 - 根因分析 |
| `CONCLUSION_FORMATTER_PROMPT` | 工作流节点 4 - 报告生成 |
| `FEDERATION_AGENT_PROMPT` | A2A 智能路由 |
| `FEDERATION_SYNTHESIS_PROMPT` | v1 多集群合成 |

---

## "我该改哪个文件？"速查表

| 你要做的事 | 去改哪里 |
|---|---|
| 切换 LLM 提供商 | `deploy/secrets/core.yaml`（LLM_API_KEY / LLM_MODEL / LLM_API_BASE） |
| 改默认模式诊断行为 | `app/core/prompts.py` → `SYSTEM_PROMPT` |
| 改工作流节点提示词 | `app/core/prompts.py` → 对应 `*_PROMPT` |
| 改 A2A 路由行为 | `app/core/prompts.py` → `FEDERATION_AGENT_PROMPT` |
| 新增/编辑 Runbook | `knowledge_base/runbooks/*.md` + `catalog.json` |
| 新增 MCP 工具 | 写 MCP Server + 配置 `mcp_servers` 块 |
| 改流式输出格式 | `app/core/holmes/query_stream.py` |
| 增加新 API | `app/api/routes.py` |
| 改服务启动流程 | `app/main.py` |
| 配置子集群 | `deploy/configmap/config.yaml` → `federation.sub_agents` |
| 改 QUERY/L0-L4 分类规则 | `app/core/workflow/nodes/layer_classifier.py` |
