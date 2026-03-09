# 架构与模块地图

## 设计原则

- **高内聚**：同一类能力（配置加载、流式输出、MCP 管理、Runbook、联邦查询）放在同一模块域
- **低耦合**：主服务不依赖"本地 tools"，默认仅通过配置连接第三方 MCP Server
- **多集群优先**：联邦查询（Agent-to-Agent）是核心差异化能力

---

## 目录结构总览

```
robusta/
├── run.py                              # 启动入口
├── app/
│   ├── main.py                         # FastAPI 应用 + 生命周期
│   ├── api/
│   │   └── routes.py                   # 所有 HTTP API 端点
│   └── core/
│       ├── service.py                  # HolmesService（全局单例编排器）
│       ├── prompts.py                  # 所有提示词（单集群 + 联邦）
│       ├── runbook.py                  # RunbookManager
│       ├── environment.py              # 环境检测与配置路径
│       ├── paths.py                    # 项目根目录工具
│       ├── federation/                 # 联邦查询模块（多集群）
│       │   ├── __init__.py             # FederationCoordinator + Agent 全局单例
│       │   ├── registry.py             # AgentRegistry（子集群配置注册）
│       │   ├── client.py               # SubAgentClient（httpx 连接池）
│       │   ├── aggregator.py           # FederationAggregator（v1 并发聚合）
│       │   ├── toolset.py              # ListClustersTool + QueryClusterTool
│       │   └── agent.py                # FederationAgent（v2 智能路由）
│       ├── holmes/                     # HolmesGPT 封装层
│       │   ├── config_loader.py        # YAML 配置加载
│       │   ├── query_stream.py         # 流式输出（text/sse）
│       │   ├── streaming.py            # SSE 消息封装
│       │   ├── call_wrapper.py         # 流式事件收集
│       │   ├── introspection.py        # 启动自检
│       │   └── tool_logging_patch.py   # 工具调用日志
│       ├── mcp/
│       │   └── mcp_patch.py            # MCP 工具补丁
│       └── workflow/                   # LangGraph 工作流（可选）
│           └── ...
├── knowledge_base/runbooks/            # Runbook 知识库
├── config/config.yaml                  # 本地开发配置
├── deploy/                             # K8s 部署配置
│   ├── configmap/config.yaml           # 生产配置
│   └── deployment.yaml
├── reports/                            # 子集群诊断报告保存目录（运行时生成）
└── Makefile                            # 构建 & 部署命令
```

---

## API 端点总览

| 端点 | 方法 | 说明 | 适用场景 |
|------|------|------|----------|
| `/ask` | GET/POST | 单集群查询（HolmesGPT） | 查询当前集群 |
| `/federation/ask` | GET/POST | 多集群并发查询（v1） | 全局对比，查询所有集群 |
| `/federation/ask/v2` | GET/POST | Agent-to-Agent 智能路由（v2） | 选择性查询、复杂问题 |
| `/reports` | GET | 列出已保存的子集群报告 | 审核历史报告 |
| `/reports/{filename}` | GET | 查看具体报告内容 | 查看诊断详情 |
| `/health` | GET | 健康检查 | 监控 |
| `/tools` | GET | 工具列表 | 排障 |
| `/tools/detail` | GET | 工具详情（按 toolset 分组） | 二次开发 |
| `/runbooks` | GET | Runbook 列表 | 排障 |

---

## 请求链路

### 单集群查询（`/ask`）

```
用户 → /ask?q=Pod重启
       ↓
  routes.py: ask_get/ask_post
       ↓
  HolmesService.execute_query_stream()
       ↓
  HolmesGPT agentic loop（Tool Calling）
    ├─ 读取 toolsets / mcp_servers 配置
    ├─ 构建 messages（System Prompt + Runbook + tools）
    └─ LLM 迭代触发 tool calls → 生成诊断结论
       ↓
  流式文本 / SSE 返回给用户
```

### Agent-to-Agent 联邦查询（`/federation/ask/v2`）

详见 [A2A 技术设计文档](./A2A_TECHNICAL_DESIGN.md)

---

## 核心模块说明

### 1. 入口与 API（`app/api/routes.py`）

注册所有 HTTP 路由，包括单集群、联邦查询、报告查看等端点。

### 2. 编排器（`app/core/service.py`）

`HolmesService` 是全局单例，负责：
- 加载配置 → 创建 AI 实例 → 加载 Runbooks
- 条件性初始化 FederationCoordinator 和 FederationAgent
- 提供 `execute_query()` 和 `execute_query_stream()` 方法

### 3. Holmes 子模块（`app/core/holmes/`）

| 模块 | 职责 |
|------|------|
| `config_loader.py` | 读取 YAML、环境变量替换、排除非 Holmes 字段 |
| `query_stream.py` | `execute_query_stream_text()` / `_sse()` |
| `call_wrapper.py` | 流式事件收集为响应对象 |
| `streaming.py` | SSE 消息封装、耗时格式化 |
| `introspection.py` | 启动时输出资源加载摘要 |

### 4. 联邦查询（`app/core/federation/`）

详见 [A2A 技术设计文档](./A2A_TECHNICAL_DESIGN.md)

### 5. 提示词（`app/core/prompts.py`）

| 常量 | 用途 |
|------|------|
| `SYSTEM_PROMPT` | 单集群 HolmesGPT 五层诊断模型 |
| `CONCLUSION_FORMATTER_PROMPT` | 诊断结论格式化模板 |
| `FEDERATION_AGENT_PROMPT` | A2A 智能路由 + 结构化输出模板 |
| `FEDERATION_SYNTHESIS_PROMPT` | v1 多集群合成提示词（aggregator 使用） |

### 6. Runbooks（`knowledge_base/runbooks/`）

- `catalog.json`：runbook 索引（AI 用 description 做语义匹配）
- `*.md`：具体 runbook 内容

---

## "我该改哪个文件？"速查表

| 你要做的事 | 去改哪里 |
|---|---|
| 改 Agent 诊断输出模板 | `app/core/prompts.py` |
| 改 A2A 联邦查询行为 | `app/core/federation/agent.py` |
| 改 A2A 输出格式 | `app/core/prompts.py` → `FEDERATION_AGENT_PROMPT` |
| 新增/编辑 Runbook | `knowledge_base/runbooks/*.md` + `catalog.json` |
| 新增 MCP 工具 | 写独立 MCP Server + 配置 `mcp_servers` |
| 改流式输出格式 | `app/core/holmes/query_stream.py` |
| 增加新 API | `app/api/routes.py` |
| 改服务启动流程 | `app/main.py` |
| 修改子集群配置 | `config/config.yaml` 或 `deploy/configmap/config.yaml` |
