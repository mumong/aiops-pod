<div align="center">

# K8s AIOps Copilot

**用自然语言诊断 Kubernetes 故障 & 查询集群数据**

基于 HolmesGPT + FastAPI + MCP + 多集群联邦查询的智能运维 Agent

</div>

---

## 核心能力

| 能力 | 说明 |
|------|------|
| **智能意图识别** | 自动区分数据查询（QUERY）和故障诊断（L0-L4），走不同处理路径 |
| **分层诊断 (L0-L4)** | 五层故障分类：基础设施→集群节点→工作负载→服务网络→应用层 |
| **多集群联邦查询** | Agent-to-Agent 智能路由，支持跨集群对比和选择性查询 |
| **MCP 工具扩展** | 通过 MCP 协议接入任意外部工具（K8s、Prometheus、ES、Helm 等） |
| **Runbook 知识库** | 内置 26+ 故障手册，AI 自动匹配场景 |
| **流式输出** | SSE 实时推送工具调用和 AI 推理过程 |
| **多 LLM 提供商** | 支持 DeepSeek / Claude / GLM / OpenAI，通过配置切换 |

---

## 架构概览

```
用户（自然语言提问）
  │
  ▼
FastAPI ─────────────────────────────────────────────────
  │
  ├── /ask                    单集群查询
  ├── /federation/ask         多集群并发查询（v1）
  └── /federation/ask/v2      Agent-to-Agent 智能路由（v2）
  │
  ▼
┌─────────────────────────────────────────┐
│           HolmesService                 │
│  ┌─────────────────────────────────┐    │
│  │  模式 A：HolmesGPT Agentic Loop │◄── USE_WORKFLOW=false（默认）
│  │  LLM 自主规划 + Tool Calling    │    │
│  └─────────────────────────────────┘    │
│  ┌─────────────────────────────────┐    │
│  │  模式 B：LangGraph 工作流       │◄── USE_WORKFLOW=true
│  │  定层→采证→根因→报告（四阶段）   │    │
│  └─────────────────────────────────┘    │
│                                         │
│  Runbook 知识库（RAG 匹配）             │
│  System Prompt（诊断框架）              │
└─────────────────────────────────────────┘
  │
  ├── 内置工具集：Kubernetes、Prometheus、Helm
  └── MCP 工具集（SSE）：K8s MCP、ES MCP、自定义 MCP ...

┌──────────────────────────────────────────┐
│          联邦查询（可选）                  │
│  FederationAgent → query_cluster()       │
│    ├── 主集群 (localhost:8000)            │
│    ├── 子集群 A (10.2.0.24:30800)        │
│    └── 子集群 B (10.2.0.xx:30800)        │
└──────────────────────────────────────────┘
```

### 工作流模式（四阶段流水线）

```
问题定层(QUERY/L0-L4) → 证据采集(工具调用) → 根因分析(因果链) → 报告生成(Markdown)
        │                      │                    │                  │
  layer_classifier      evidence_collector    root_cause_analyzer  conclusion_formatter
```

- **QUERY 路径**：数据查询 → 工具采集 → 数据汇总 → 表格输出（跳过根因分析）
- **L0-L4 路径**：故障诊断 → 多维采证 → 因果链推理 → 结构化诊断报告

---

## 快速开始

### 本地运行

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置 LLM API Key
export LLM_API_KEY=sk-xxx

# 3. 启动服务
python run.py
```

服务默认监听 `http://0.0.0.0:8000`。

### K8s 部署

```bash
# 1. 修改 LLM 配置
vim deploy/secrets/core.yaml     # 填入 LLM_API_KEY、LLM_MODEL 等

# 2. 构建镜像并部署
make build push deploy-master    # 主集群（启用联邦查询）
make build push deploy-slave     # 子集群（关闭联邦查询）

# 常用运维命令
make logs                        # 查看日志
make restart                     # 重启服务
make delete                      # 删除部署（保留 namespace）
```

---

## API 参考

### 端点总览

| 端点 | 方法 | 说明 |
|------|------|------|
| `/ask` | GET / POST | 单集群查询（主入口） |
| `/q/{问题}` | GET | 路径参数方式查询（简洁 URL） |
| `/federation/ask` | GET / POST | 多集群并发查询（v1，查询所有集群） |
| `/federation/ask/v2` | GET / POST | Agent-to-Agent 智能路由（v2，按需选择集群） |
| `/health` | GET | 健康检查 |
| `/tools` | GET | 可用工具列表 |
| `/tools/detail` | GET | 工具详情（按 toolset 分组，含参数 schema） |
| `/runbooks` | GET | Runbook 知识库列表 |
| `/reports` | GET | 子集群诊断报告列表（支持 `cluster`、`limit` 过滤） |
| `/reports/{filename}` | GET | 查看具体报告内容 |
| `/artifacts/{artifact_id}` | GET | 获取被截断的大输出全文 |

---

### 1. `/ask` — 单集群查询（最常用）

用自然语言向当前集群提问，支持故障诊断和数据查询。

**参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `q` | string | **必填** | 问题内容（中文需 URL 编码，推荐用 `--data-urlencode`） |
| `stream` | bool | `true` | 是否流式输出。`true`=实时推送，`false`=等全部完成后一次返回 |
| `format` | string | `"text"` | 流式输出格式：`text`（纯文本流）或 `sse`（结构化事件流，适合前端解析） |
| `max_steps` | int | `20` | LLM 最大工具调用轮数（范围 1-100）。简单查询可设小值加快返回，复杂诊断建议调大 |

**使用示例：**

```bash
# ============================================================
# 基本用法（GET + 流式输出，最常用的方式）
# ============================================================

# 故障诊断：Pod 为什么一直重启
curl -G "http://10.2.0.48:30800/ask" \
  --data-urlencode "q=payment-service 的 Pod 为什么一直重启"

# 数据查询：查看集群 CPU 使用率
curl -G "http://10.2.0.48:30800/ask" \
  --data-urlencode "q=集群 CPU 使用率是多少"

# 查看某个 namespace 下的 Pod 状态
curl -G "http://10.2.0.48:30800/ask" \
  --data-urlencode "q=查看 namespace kube-system 下所有 Pod 状态"

# ============================================================
# 调整参数
# ============================================================

# 加快返回：简单查询只需要少量工具调用，把 max_steps 设小
curl -G "http://10.2.0.48:30800/ask" \
  --data-urlencode "q=集群有多少个节点" \
  --data-urlencode "max_steps=5"

# 深度诊断：复杂问题需要更多工具调用轮数
curl -G "http://10.2.0.48:30800/ask" \
  --data-urlencode "q=分析 production namespace 下所有异常 Pod 的根因" \
  --data-urlencode "max_steps=50"

# 非流式输出：等待全部完成后一次性返回（适合脚本调用）
curl -G "http://10.2.0.48:30800/ask" \
  --data-urlencode "q=列出所有 CrashLoopBackOff 的 Pod" \
  --data-urlencode "stream=false"

# SSE 格式输出：返回结构化事件流（适合前端 EventSource 解析）
curl -G "http://10.2.0.48:30800/ask" \
  --data-urlencode "q=磁盘使用率" \
  --data-urlencode "format=sse"

# ============================================================
# POST 方式（表单提交，适合长问题或脚本集成）
# ============================================================

curl -X POST "http://10.2.0.48:30800/ask" \
  -d "q=查看 namespace kube-system 下所有 Pod 状态" \
  -d "max_steps=30"

# ============================================================
# 路径参数方式（最简洁的 URL，适合英文或简单问题）
# ============================================================

curl "http://10.2.0.48:30800/q/check+cluster+health"
```

---

### 2. `/federation/ask` — 多集群并发查询（v1）

向所有已配置的子集群并发发送同一问题，汇总后由 LLM 合成统一结论。适合"哪个集群 XX 最高"这类需要对比所有集群的场景。

**参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `q` | string | **必填** | 问题内容 |
| `max_steps` | int | `30` | 每个子集群的最大工具调用步数 |
| `conclusion_max_tokens` | int | `8192` | 每个子集群结论的最大 token 数。设为 `0` 表示不限制（返回完整报告） |

**使用示例：**

```bash
# 查询所有集群的 CPU 使用率，自动对比
curl -G "http://10.2.0.48:30800/federation/ask" \
  --data-urlencode "q=哪个集群 CPU 利用率最高"

# 限制每个子集群的结论长度（加快汇总速度）
curl -G "http://10.2.0.48:30800/federation/ask" \
  --data-urlencode "q=所有集群的节点状态" \
  --data-urlencode "conclusion_max_tokens=4096"

# 简单查询减少步数
curl -G "http://10.2.0.48:30800/federation/ask" \
  --data-urlencode "q=所有集群各有多少个 Pod" \
  --data-urlencode "max_steps=10"

# 不限制结论长度，获取完整报告
curl -G "http://10.2.0.48:30800/federation/ask" \
  --data-urlencode "q=对比所有集群的内存使用情况" \
  --data-urlencode "conclusion_max_tokens=0"
```

---

### 3. `/federation/ask/v2` — Agent-to-Agent 智能路由（v2，推荐）

主 Agent 先理解用户意图，智能决定查询哪些集群、对每个集群发送什么问题。支持：
- **选择性查询**：只查指定的集群，不浪费时间查无关集群
- **跨集群对比**：同时查多个集群不同指标，然后合成对比
- **不同问题路由**：对不同集群问不同的问题

**参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `q` | string | **必填** | 问题内容 |
| `max_steps` | int | `30` | Agent 最大执行步数（包含集群查询 + 合成推理） |

**使用示例：**

```bash
# 查询指定集群的指标（Agent 自动只查 main 和 cluster-24）
curl -G "http://10.2.0.48:30800/federation/ask/v2" \
  --data-urlencode "q=我想要知道 main 的内存使用率和 cluster-24 的 CPU 使用率"

# 查询单个集群（Agent 智能路由，只查 cluster-24）
curl -G "http://10.2.0.48:30800/federation/ask/v2" \
  --data-urlencode "q=查询 cluster-24 的内存使用情况"

# 对比两个集群
curl -G "http://10.2.0.48:30800/federation/ask/v2" \
  --data-urlencode "q=对比 main 和 cluster-24 的 CPU 使用率"

# 跨集群故障排查
curl -G "http://10.2.0.48:30800/federation/ask/v2" \
  --data-urlencode "q=检查所有集群是否有 Pod 处于异常状态"

# 增加步数以支持更复杂的多集群分析
curl -G "http://10.2.0.48:30800/federation/ask/v2" \
  --data-urlencode "q=分析 main 集群的磁盘告警和 cluster-24 的内存告警" \
  --data-urlencode "max_steps=50"
```

---

### 4. 辅助端点

```bash
# 健康检查
curl "http://10.2.0.48:30800/health"

# 查看所有可用工具（AI 能调用的工具列表）
curl "http://10.2.0.48:30800/tools"

# 查看工具详情（含参数 schema，按 toolset 分组）
curl "http://10.2.0.48:30800/tools/detail"

# 查看已加载的 Runbook 知识库
curl "http://10.2.0.48:30800/runbooks"

# 查看子集群诊断报告列表
curl "http://10.2.0.48:30800/reports"

# 按集群名过滤报告
curl "http://10.2.0.48:30800/reports?cluster=cluster-24&limit=10"

# 查看具体报告内容
curl "http://10.2.0.48:30800/reports/cluster-24_20260309_143000.md"

# 获取被截断的大输出全文（artifact_id 来自流式输出中的链接）
curl "http://10.2.0.48:30800/artifacts/{artifact_id}"
```

---

### 5. `/ask` vs `/federation/ask` vs `/federation/ask/v2` 怎么选？

| 场景 | 推荐端点 | 说明 |
|------|----------|------|
| 查询当前集群的状态/指标 | `/ask` | 直接查，速度最快 |
| 诊断当前集群的故障 | `/ask` | 单集群深度诊断 |
| 对比所有集群的某个指标 | `/federation/ask` | 并发查所有集群，自动汇总 |
| 只查指定的 1-2 个集群 | `/federation/ask/v2` | Agent 智能路由，不查无关集群 |
| 对不同集群问不同问题 | `/federation/ask/v2` | Agent 自动拆分问题并路由 |
| 跨集群对比分析 | `/federation/ask/v2` | 最灵活，推荐多集群场景首选 |

### 参数调优建议

| 参数 | 场景 | 建议值 |
|------|------|--------|
| `max_steps` | 简单状态查询（Pod 列表、节点数量） | `5-10` |
| `max_steps` | 常规指标查询（CPU、内存使用率） | `10-20`（默认） |
| `max_steps` | 深度故障诊断（根因分析、多维采证） | `30-50` |
| `max_steps` | 复杂多集群分析 | `50+` |
| `conclusion_max_tokens` | 快速概览 | `2048-4096` |
| `conclusion_max_tokens` | 完整报告 | `0`（不限制） |
| `stream` | 交互式使用（终端/浏览器） | `true`（默认） |
| `stream` | 脚本/程序集成 | `false` |
| `format` | 终端查看 | `text`（默认） |
| `format` | 前端 EventSource 解析 | `sse` |

---

## 配置

### LLM 提供商配置

**优先级**：Secret 环境变量 > config.yaml `llm` 块 > 默认值

#### 方式一：通过 Secret（推荐，适合 K8s 部署）

修改 `deploy/secrets/core.yaml`：

```yaml
stringData:
  # DeepSeek（默认）
  LLM_API_KEY: "sk-xxx"
  LLM_MODEL: "deepseek/deepseek-chat"
  LLM_API_BASE: ""                      # 留空使用默认端点

  # Claude（取消注释切换）
  # LLM_API_KEY: "sk-xxx"
  # LLM_MODEL: "anthropic/claude-sonnet-4-6"
  # LLM_API_BASE: "https://terminal.pub"

  # GLM 智谱（OpenAI 兼容）
  # LLM_API_KEY: "xxx"
  # LLM_MODEL: "openai/glm-4"
  # LLM_API_BASE: "https://open.bigmodel.cn/api/paas/v4"
```

#### 方式二：通过 config.yaml

在 `deploy/configmap/config.yaml`（K8s）或 `config/config.yaml`（本地）中配置：

```yaml
llm:
  model: "deepseek/deepseek-chat"    # litellm 模型 ID
  # api_key: "sk-xxx"                # 留空则从 LLM_API_KEY 环境变量读取
  # api_base: ""                     # 留空使用默认端点
```

**litellm 模型 ID 格式**：`提供商/模型名`，如 `deepseek/deepseek-chat`、`anthropic/claude-sonnet-4-6`、`openai/gpt-4o`、`openai/glm-4`

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| **LLM 配置** | | |
| `LLM_API_KEY` | — | LLM API Key（必填） |
| `LLM_MODEL` | `deepseek/deepseek-chat` | litellm 模型 ID，格式 `提供商/模型名` |
| `LLM_API_BASE` | — | API 端点覆盖（用于代理或兼容端点，留空使用默认） |
| **服务配置** | | |
| `API_HOST` | `0.0.0.0` | 服务监听地址 |
| `API_PORT` | `8000` | 服务监听端口 |
| `CONFIG_FILE` | 自动检测 | 指定配置文件路径（绝对或相对路径） |
| **功能开关** | | |
| `USE_WORKFLOW` | `false` | 启用 LangGraph 四阶段工作流模式 |
| `BASH_TOOL_UNSAFE_ALLOW_ALL` | `false` | 允许执行所有 bash 命令（生产环境建议 false） |
| `MCP_AUTO_START_LOCAL` | `false` | 是否自动启动本地 MCP 子进程（开发环境用） |
| `HOLMES_INIT_TIMEOUT_SECONDS` | `0` | HolmesGPT 初始化超时秒数（0=无限等待） |

> **配置优先级**：环境变量（Secret） > `config.yaml` 中的 `llm` 块 > 默认值
>
> 配置文件自动检测：K8s 环境 → `config/config.k8s.yaml`，本地环境 → `config/config.yaml`

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
  bash:
    enabled: true
  helm/core:
    enabled: true

# MCP 工具集（SSE 远程连接）
mcp_servers:
  elasticsearch:
    description: "Elasticsearch - 查询日志索引"
    config:
      url: "http://mcp-server-manager.mcp.svc.cluster.local:8088/sse"
      mode: "sse"
    enabled: true
```

### 联邦查询（多集群）配置

在 `deploy/configmap/config.yaml` 的 `federation` 块中配置：

```yaml
federation:
  enabled: true                    # 主集群 true，子集群 false
  max_tokens_per_agent: 0          # 子集群报告压缩阈值（0=不压缩）
  synthesis_timeout: 300            # 等待子集群响应超时（秒）
  sub_agents:
    - name: "main"
      url: "http://localhost:8000"   # 主集群用容器内端口
      description: "主集群"
      enabled: true
    - name: "cluster-24"
      url: "http://10.2.0.24:30800"  # 子集群用 NodePort
      description: "子集群 24"
      enabled: true
```

**注意**：主集群 URL 必须用 `http://localhost:8000`（容器内端口），不能用 NodePort。

---

## 五层诊断模型 + QUERY

```
QUERY  直接查询    数据查询、状态查看、使用率统计（非故障场景）
 L4   应用层      业务逻辑错误、配置错误、依赖服务不可用
 L3   服务网络层  Service/Ingress 配置、DNS 解析、NetworkPolicy
 L2   工作负载层  Pod 生命周期、镜像拉取、资源限制、探针
 L1   集群节点层  Node 状态、kubelet、容器运行时、调度
 L0   基础设施层  磁盘、内存、CPU、内核、文件系统
```

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
│       ├── federation/                 # 联邦查询模块
│       │   ├── __init__.py             # Coordinator + Agent 全局单例
│       │   ├── registry.py             # 子集群配置注册
│       │   ├── client.py               # httpx 异步调用子集群
│       │   ├── aggregator.py           # v1 并发聚合
│       │   ├── toolset.py              # list_clusters + query_cluster 工具
│       │   └── agent.py                # v2 Agent-to-Agent 路由
│       ├── holmes/                     # HolmesGPT 封装层
│       │   ├── config_loader.py        # YAML 配置加载
│       │   ├── query_stream.py         # 流式输出
│       │   └── streaming.py            # SSE 消息封装
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
├── deploy/                             # K8s 部署
│   ├── k8s-simple.yaml                 # Deployment + Service
│   ├── configmap/config.yaml           # 生产配置（ConfigMap）
│   ├── secrets/core.yaml               # LLM Key 等敏感配置
│   └── rbac.yaml                       # ServiceAccount + RBAC
└── Makefile                            # 构建 & 部署命令
```

---

## 扩展指南

### 添加新工具（MCP 方式）

1. 实现一个 MCP Server（HTTP/SSE）
2. 配置到 `mcp_servers`：
```yaml
mcp_servers:
  my-tool:
    description: "工具描述（AI 用此判断何时调用）"
    config:
      url: "http://my-mcp-server:8099/sse"
      mode: "sse"
    enabled: true
```
3. 重启服务生效

### 添加 Runbook

1. 在 `knowledge_base/runbooks/` 创建 `.md` 文件
2. 在 `catalog.json` 中注册 title + description
3. 重启服务，AI 自动匹配

### 修改提示词

所有 LLM 提示词集中在 `app/core/prompts.py`，详见 [架构与开发参考](docs/ARCHITECTURE.md)。

### 切换 LLM 提供商

修改 `deploy/secrets/core.yaml` 中的 `LLM_API_KEY` / `LLM_MODEL` / `LLM_API_BASE`，重新 `make deploy` 即可。

---

## 详细文档

| 文档 | 说明 |
|------|------|
| [架构与开发参考](docs/ARCHITECTURE.md) | 目录结构、请求链路、提示词参考、配置详解 |
| [部署与使用指南](docs/GUIDE.md) | 部署步骤、API 使用、常见问题 |

## 技术栈

- **API 框架**：[FastAPI](https://fastapi.tiangolo.com/)
- **AI 引擎**：[HolmesGPT](https://github.com/robusta-dev/holmesgpt)（Tool Calling 框架）
- **工作流编排**：[LangGraph](https://github.com/langchain-ai/langgraph)（工作流模式）
- **LLM 路由**：[litellm](https://github.com/BerriAI/litellm)（多提供商统一接口）
- **工具协议**：[MCP](https://modelcontextprotocol.io/)（Model Context Protocol）
- **LLM**：DeepSeek / Claude / GLM / OpenAI（通过 litellm 支持任意提供商）


 可量化 — 每个指标都有具体数字

  ┌────────────┬─────────────────┬────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
  │    指标    │    量化方式     │                                                          数据来源                                                          │
  ├────────────┼─────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ MTTR       │ 精确到秒的耗时  │ 从 run_start 到 run_end 的时间差                                                                                           │
  ├────────────┼─────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ 根因置信度 │ 0-100% 的百分比 │ 4 层逐级提取：① 确定性规则引擎打分 → ② RCA JSON 的 confidence 字段 → ③ 从 LLM 输出正则提取"置信度: XX%" → ④ 层级判定置信度 │
  ├────────────┼─────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ 证据完整率 │ 已采集/计划总数 │ 工作流模式：从 evidence_items 的 collected 标记统计；默认模式：从 tool_result 事件的 success/total 统计                    │
