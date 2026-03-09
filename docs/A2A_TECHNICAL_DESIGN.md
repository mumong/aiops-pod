# Agent-to-Agent (A2A) 技术设计文档

## 概述

Agent-to-Agent 是多集群联邦查询的核心能力，通过 `/federation/ask/v2` 端点暴露。与 v1（`/federation/ask`）的"查询所有集群再合成"不同，A2A 由 LLM 智能决定查询哪些集群、发送什么问题。

---

## 核心架构

### 技术选型

| 组件 | 技术 | 说明 |
|------|------|------|
| LLM 调用 | litellm | 支持 DeepSeek、OpenAI 等多种提供商 |
| Tool Calling | OpenAI Function Calling 格式 | 行业标准 |
| HTTP 客户端 | httpx（共享连接池） | 调用子集群 |
| 工具接口 | holmes.core.tools.Tool | 复用 HolmesGPT 接口定义 |
| 并发控制 | ThreadPoolExecutor | 多工具并发执行 |

### 为什么不使用 HolmesGPT Agent 循环

- A2A 只需要 2 个工具（`list_clusters` + `query_cluster`），不需要 K8s 工具集
- 避免与 HolmesGPT 内部逻辑冲突
- 需要更简单、可控的循环逻辑（如并发工具执行、流式最终输出）

---

## 数据流向与响应流向

### 完整请求链路

```
用户 ─── curl /federation/ask/v2?q="查询集群1、3、5的CPU" ───→ FastAPI
                                                                │
                                                        routes.py
                                                                │
                                                    FederationAgent.ask_stream()
                                                                │
                           ┌────────────────────────────────────┘
                           ▼
                  ╔═══════════════════╗
                  ║  Tool Calling     ║
                  ║  循环             ║
                  ╚═══════════════════╝
                           │
            Step 1: litellm.completion(stream=False)
                           │
                    LLM 返回: tool_calls=[list_clusters()]
                           │
                    执行 ListClustersTool → 返回集群列表
                           │
            Step 2: litellm.completion(stream=False)
                           │
                    LLM 返回: tool_calls=[
                        query_cluster("cluster-1", "CPU利用率"),
                        query_cluster("cluster-3", "CPU利用率"),  ← 一次返回多个
                        query_cluster("cluster-5", "CPU利用率"),
                    ]
                           │
              ╔════════════╩════════════════════════╗
              ║  单线程 + asyncio.gather 并发        ║
              ║  共享 httpx 连接池                   ║
              ╠════════════════════════════════════╣
              ║                                     ║
              ║  gather:                            ║
              ║    query_cluster-1 ──→ POST /ask    ║
              ║    query_cluster-3 ──→ POST /ask    ║
              ║    query_cluster-5 ──→ POST /ask    ║
              ║                                     ║
              ║  耗时 = max(子集群1, 3, 5)            ║
              ║  而非 sum(子集群1, 3, 5)              ║
              ╚════════════╦════════════════════════╝
                           │
                    每个成功的结果 → 保存到 reports/ 目录
                           │
            Step 3: litellm.completion(stream=True)  ← 流式最终输出
                           │
                    LLM 无 tool_calls → 生成结构化诊断报告
                           │
                    逐 chunk yield 给用户 ← 用户立即看到输出
```

### 响应流向

```
子集群 Agent                    主集群 FederationAgent              用户
────────────                    ──────────────────────            ────
     │                                    │                        │
     │  ←── POST /ask (stream=false) ──── │                        │
     │                                    │                        │
     │ ──── 完整诊断报告 ──────────────→   │                        │
     │                                    │                        │
     │                           保存报告到 reports/                │
     │                                    │                        │
     │                           合并结果 → LLM 合成                │
     │                                    │                        │
     │                                    │ ── chunk1 ──────────→  │
     │                                    │ ── chunk2 ──────────→  │
     │                                    │ ── chunk3 ──────────→  │
     │                                    │ ── ...    ──────────→  │
```

---

## 并发优化详解

### 优化前（串行）

```
query_cluster("cluster-1")  ──── 60s ────→
                                          query_cluster("cluster-3")  ──── 60s ────→
                                                                                    query_cluster("cluster-5")  ──── 60s ────→
总耗时: 180s
```

### 优化后（并发）

```
query_cluster("cluster-1")  ──── 60s ────→ ┐
query_cluster("cluster-3")  ──── 60s ────→ ├─ 并发执行，总耗时 = max = 60s
query_cluster("cluster-5")  ──── 60s ────→ ┘
```

### 实现机制

1. **LLM 返回多个 tool_calls 时**，`_execute_tools()` 检测到多个 `query_cluster`，调用 `_batch_query_clusters()`
2. **`_batch_query_clusters()`** 将所有查询打包，通过单个线程 + `asyncio.run()` + `asyncio.gather()` 并发执行
3. **`SubAgentClient.batch_query()`** 在同一个 `httpx.AsyncClient` 内并发发送所有 HTTP 请求，共享连接池
4. **避免事件循环冲突**，所有并发查询共用同一个 `asyncio.run()` 创建的事件循环
5. **最终回答流式输出**，不带 `tools` 参数重新调用 LLM（`stream=True`），用户立即看到输出

### 性能对比

| 场景 | 优化前 | 优化后 | 提升 |
|------|--------|--------|------|
| 查询 3 个集群 | ~180s + LLM ~10s | ~60s + LLM 即时流式 | **3x** |
| 查询 1 个集群 | ~60s + LLM ~10s | ~60s + LLM 即时流式 | 首 token 更快 |
| LLM 最终回答 | 等完整生成 ~10s | 流式逐 token 输出 | 首 token ~0.5s |

---

## 报告保存机制

### 保存时机

| 来源 | 触发点 | 标记 |
|------|--------|------|
| `/federation/ask` (v1) | `FederationAggregator._save_reports()` | 无特殊标记 |
| `/federation/ask/v2` (v2) | `QueryClusterTool._save_report()` | `来源: Agent-to-Agent (v2)` |

### 保存位置

```
reports/
├── cluster-24_20260309_143000.md
├── cluster-24_20260309_150000.md
├── main_20260309_143000.md
└── ...
```

- **目录**：主集群运行目录下的 `reports/`（容器内为 `/app/reports/`）
- **文件名格式**：`{集群名}_{时间戳}.md`
- **内容格式**：Markdown，包含生成时间、来源、耗时、完整诊断报告

### 查看报告 API

```bash
# 列出所有报告
curl "http://HOST:30800/reports"

# 按集群过滤
curl "http://HOST:30800/reports?cluster=cluster-24&limit=10"

# 查看具体报告
curl "http://HOST:30800/reports/cluster-24_20260309_143000.md"
```

---

## 与 v1 FederationCoordinator 的对比

| 特性 | v1 (`/federation/ask`) | v2 (`/federation/ask/v2`) |
|------|----------------------|--------------------------|
| 实现 | FederationCoordinator + Aggregator | FederationAgent (Tool Calling) |
| 路由策略 | 固定：查询所有已启用集群 | 智能：LLM 决定查询哪些 |
| 并发方式 | `asyncio.gather()` 所有集群并发 | `ThreadPoolExecutor` 同步并发 |
| 问题分解 | 不支持（所有集群同一问题） | 支持（不同集群不同问题） |
| 报告合成 | 独立 LLM 调用 + `FEDERATION_SYNTHESIS_PROMPT` | Agent 自身生成（`FEDERATION_AGENT_PROMPT`） |
| 输出格式 | 结构化 Markdown（合成 prompt 控制） | 结构化 Markdown（agent prompt 控制） |
| 适用场景 | 全局对比（如"哪个集群 CPU 最高"） | 选择性查询（如"查询集群 1 和 3"） |

---

## 部署

### 前提条件

- Docker + K8s 集群
- 主集群和子集群的网络互通（子集群 30800 端口可达）
- DeepSeek API Key（环境变量 `DEEPSEEK_API_KEY`）

### 配置文件

**主集群** — `deploy/configmap/config.yaml`：

```yaml
federation:
  enabled: true
  sub_agents:
    - name: "main"
      url: "http://localhost:8000"
      description: "主集群"
      enabled: true
    - name: "cluster-24"
      url: "http://10.2.0.24:30800"
      description: "子集群 24"
      enabled: true
    - name: "cluster-48"
      url: "http://10.2.0.48:30800"
      description: "子集群 48"
      enabled: true
```

**关键注意**：主集群 URL 必须用 `http://localhost:8000`（容器内应用端口），**不是** `http://localhost:30800`（NodePort 在宿主机上，容器内不可达）。子集群使用 NodePort `30800` 是因为跨节点访问走宿主机 IP。

**子集群** — `deploy/configmap/config.yaml`：

```yaml
federation:
  enabled: false
```

### 部署命令

```bash
cd /root/huhu/agent/combine-aiops-mcp/robusta

# 主集群（启用联邦查询）
make master

# 子集群（禁用联邦查询）
make slave

# 查看日志
make logs

# 重启
make restart
```

### 验证部署

```bash
# 健康检查
curl http://10.2.0.48:30800/health

# 查看已注册工具
curl http://10.2.0.48:30800/tools
```

---

## API 使用示例

### 指定集群查询

```bash
curl -G "http://10.2.0.48:30800/federation/ask/v2" \
  --data-urlencode "q=查询 cluster-24 的 CPU 利用率"
```

### 多集群对比

```bash
curl -G "http://10.2.0.48:30800/federation/ask/v2" \
  --data-urlencode "q=对比 main 和 cluster-24 的内存使用情况"
```

### 全局查询（所有集群）

```bash
curl -G "http://10.2.0.48:30800/federation/ask/v2" \
  --data-urlencode "q=所有集群的健康状态"
```

### 不同集群不同问题

```bash
curl -G "http://10.2.0.48:30800/federation/ask/v2" \
  --data-urlencode "q=查询 main 的内存和 cluster-24 的 CPU"
```

### POST 方式

```bash
curl -X POST "http://10.2.0.48:30800/federation/ask/v2" \
  -d "q=查询 cluster-24 的 Pod 状态"
```

### 查看历史报告

```bash
# 列出报告
curl "http://10.2.0.48:30800/reports"

# 按集群过滤
curl "http://10.2.0.48:30800/reports?cluster=cluster-24"

# 查看具体报告
curl "http://10.2.0.48:30800/reports/cluster-24_20260309_143000.md"
```

---

## 模块文件速查

| 文件 | 职责 | 修改场景 |
|------|------|----------|
| `federation/__init__.py` | 全局单例工厂 | 修改初始化参数 |
| `federation/registry.py` | 子集群配置注册 | 修改配置加载逻辑 |
| `federation/client.py` | httpx 连接池 + HTTP 调用 | 修改超时/重试策略 |
| `federation/toolset.py` | 工具定义 + 报告保存 | 新增工具或修改保存逻辑 |
| `federation/agent.py` | Tool Calling 循环 + 并发 | 修改 Agent 行为 |
| `federation/aggregator.py` | v1 并发聚合 + LLM 合成 | 修改 v1 合成逻辑 |
| `prompts.py` | FEDERATION_AGENT_PROMPT | 修改 A2A 输出格式 |
