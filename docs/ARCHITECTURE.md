# 架构与开发参考

---

## 目录结构

```
robusta/
├── run.py                              # 启动入口
├── app/
│   ├── main.py                         # FastAPI 应用 + 生命周期
│   ├── api/routes.py                   # 所有 HTTP API 端点
│   └── core/
│       ├── service.py                  # HolmesService（全局单例编排器）
│       ├── prompts.py                  # 所有 LLM 提示词
│       ├── runbook.py                  # RunbookManager
│       ├── federation/                 # 联邦查询模块（多集群）
│       │   ├── __init__.py             # Coordinator + Agent 全局单例工厂
│       │   ├── registry.py             # 子集群配置注册
│       │   ├── client.py               # httpx 异步调用子集群
│       │   ├── aggregator.py           # v1 并发聚合
│       │   ├── toolset.py              # list_clusters + query_cluster 工具
│       │   └── agent.py                # v2 Agent-to-Agent 智能路由
│       ├── holmes/                     # HolmesGPT 封装层
│       │   ├── config_loader.py        # YAML 配置加载、环境变量替换
│       │   ├── query_stream.py         # 流式输出（text / sse）
│       │   ├── streaming.py            # SSE 消息封装
│       │   ├── call_wrapper.py         # 流式事件收集
│       │   └── introspection.py        # 启动自检
│       ├── workflow/                   # LangGraph 工作流（USE_WORKFLOW=true）
│       │   ├── graph.py                # 工作流图构建
│       │   ├── executor.py             # 执行器
│       │   └── nodes/                  # 四个工作流节点
│       │       ├── layer_classifier.py
│       │       ├── evidence_collector.py
│       │       ├── root_cause_analyzer.py
│       │       └── conclusion_formatter.py
│       └── skills/models.py            # Layer 枚举（QUERY/L0-L4）
├── knowledge_base/runbooks/            # Runbook 知识库
├── config/config.yaml                  # 本地开发配置
├── deploy/                             # K8s 部署配置
│   ├── k8s-simple.yaml                 # Deployment + Service
│   ├── configmap/config.yaml           # 生产配置（ConfigMap）
│   ├── secrets/core.yaml               # LLM Key 等敏感配置
│   └── rbac.yaml                       # ServiceAccount + RBAC
└── Makefile                            # 构建 & 部署命令
```

---

## 请求链路

### 单集群查询（`/ask`）

```
用户 → /ask?q=Pod重启&max_steps=20
       ↓
  ┌─ USE_WORKFLOW=false ─────────────────────┐
  │  HolmesGPT agentic loop                  │
  │    ├─ System Prompt (SYSTEM_PROMPT)       │
  │    ├─ Runbook 匹配                       │
  │    └─ LLM Tool Calling → 生成结论        │
  └──────────────────────────────────────────┘
  ┌─ USE_WORKFLOW=true ──────────────────────┐
  │  LangGraph 四阶段工作流                    │
  │  ①定层 → ②采证 → ③根因 → ④报告         │
  └──────────────────────────────────────────┘
       ↓
  流式文本 / SSE 返回
```

### Agent-to-Agent 联邦查询（`/federation/ask/v2`）

```
用户 → /federation/ask/v2?q=查询 cluster-24 的 CPU
       ↓
  FederationAgent (litellm Tool Calling 循环)
    ① list_clusters()          → 获取集群列表
    ② query_cluster("cluster-24", "CPU 使用率")
         ↓
       SubAgentClient → POST http://子集群:30800/ask
         ↓
       子集群返回诊断结果
    ③ LLM 生成汇总报告（流式输出）
```

---

## 提示词参考

所有提示词统一管理在 `app/core/prompts.py`，修改后需重新构建镜像。

| 常量名 | 使用场景 | 使用者 |
|--------|----------|--------|
| `SYSTEM_PROMPT` | 默认模式（HolmesGPT agentic loop） | `service.py` |
| `LAYER_CLASSIFIER_PROMPT` | 工作流节点 1 — 问题定位（QUERY/L0-L4） | `layer_classifier.py` |
| `EVIDENCE_COLLECTOR_PROMPT` | 工作流节点 2 — 证据采集 | `evidence_collector.py` |
| `ROOT_CAUSE_ANALYZER_PROMPT` | 工作流节点 3 — 根因分析 | `root_cause_analyzer.py` |
| `CONCLUSION_FORMATTER_PROMPT` | 工作流节点 4 — 报告生成 | `conclusion_formatter.py` |
| `FEDERATION_AGENT_PROMPT` | A2A 联邦查询智能路由 | `federation/agent.py` |
| `FEDERATION_SYNTHESIS_PROMPT` | 联邦查询 v1 报告合成 | `federation/aggregator.py` |

### 提示词路由

```
用户请求
  ├── USE_WORKFLOW=false ──→ SYSTEM_PROMPT
  ├── USE_WORKFLOW=true  ──→ LAYER_CLASSIFIER → EVIDENCE_COLLECTOR → ROOT_CAUSE_ANALYZER → CONCLUSION_FORMATTER
  ├── /federation/ask    ──→ FEDERATION_SYNTHESIS_PROMPT
  └── /federation/ask/v2 ──→ FEDERATION_AGENT_PROMPT
```

---

## 配置参考

### LLM 配置优先级

```
Secret 环境变量（LLM_API_KEY / LLM_MODEL / LLM_API_BASE）
    ↓ 为空则回退
config.yaml llm 块
    ↓ 为空则回退
默认值（model = "deepseek/deepseek-chat"）
```

### 支持的 LLM 提供商

| 提供商 | LLM_MODEL | LLM_API_BASE |
|--------|-----------|--------------|
| DeepSeek | `deepseek/deepseek-chat` | 留空 |
| Claude | `anthropic/claude-sonnet-4-6` | `https://terminal.pub` |
| GLM 智谱 | `openai/glm-4` | `https://open.bigmodel.cn/api/paas/v4` |
| OpenAI | `openai/gpt-4o` | 留空 |

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `LLM_API_KEY` | — | LLM API Key |
| `LLM_MODEL` | `deepseek/deepseek-chat` | litellm 模型 ID |
| `LLM_API_BASE` | — | API 端点覆盖 |
| `USE_WORKFLOW` | `false` | 启用 LangGraph 工作流 |
| `BASH_TOOL_UNSAFE_ALLOW_ALL` | `false` | 允许所有 bash 命令 |
| `CONFIG_FILE` | 自动检测 | 配置文件路径 |

所有 Secret 环境变量均为 `optional: true`，缺失不会导致 Pod 启动失败。

### 联邦查询配置

```yaml
# 主集群 — deploy/configmap/config.yaml
federation:
  enabled: true
  sub_agents:
    - name: "main"
      url: "http://localhost:8000"      # 容器内端口，不能用 NodePort
      description: "主集群"
      enabled: true
    - name: "cluster-24"
      url: "http://10.2.0.24:30800"    # 子集群 NodePort
      description: "子集群 24"
      enabled: true

# 子集群
federation:
  enabled: false
```

### 工具集配置

```yaml
# 内置工具集
toolsets:
  kubernetes/core:
    enabled: true
  prometheus/metrics:
    enabled: true
    config:
      prometheus_url: "http://prometheus:9090"

# MCP 远程工具
mcp_servers:
  elasticsearch:
    description: "工具描述（AI 据此判断何时调用）"
    config:
      url: "http://mcp-server:8088/sse"
      mode: "sse"
    enabled: true
```

---

## 速查表

| 你要做的事 | 改哪里 |
|---|---|
| 切换 LLM 提供商 | `deploy/secrets/core.yaml` |
| 改默认模式诊断行为 | `app/core/prompts.py` → `SYSTEM_PROMPT` |
| 改工作流节点提示词 | `app/core/prompts.py` → 对应 `*_PROMPT` |
| 改 A2A 路由行为 | `app/core/prompts.py` → `FEDERATION_AGENT_PROMPT` |
| 新增/编辑 Runbook | `knowledge_base/runbooks/*.md` + `catalog.json` |
| 新增 MCP 工具 | 写 MCP Server + 配置 `mcp_servers` 块 |
| 配置子集群 | `deploy/configmap/config.yaml` → `federation.sub_agents` |
| 增加新 API | `app/api/routes.py` |
