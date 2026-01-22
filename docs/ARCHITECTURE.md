# 架构与模块地图（你要改哪里，一看就懂）

## 目标与设计原则

本项目的目标是做一个“可长期演进”的运维 Agent：

- **高内聚**：同一类能力（配置加载、流式输出、MCP 管理、Runbook）放在同一模块域里。
- **低耦合**：主服务不依赖“本地 tools”，默认仅通过配置连接 **第三方 MCP Server**；本地 auto-start 只是可选能力。
- **功能不变**：当前重构都遵循“只拆分/搬运，不改默认行为与输出协议”。

---

## 一条请求的完整链路（从 `/ask` 到工具调用）

1. 用户请求进入 API：
   - `app/api/routes.py`：处理 `/ask`（GET/POST）、`/tools`、`/runbooks`、`/api/v1/mcp/status`
2. 进入核心编排器：
   - `app/core/service.py`：`HolmesService.execute_query()` 或 `HolmesService.execute_query_stream()`
3. HolmesGPT 运行（tool calling）：
   - 读取配置（toolsets / mcp_servers）
   - 构建 messages（System Prompt + Runbook catalog + tools 信息）
   - LLM 在迭代中触发 tool calls（Holmes 框架内部执行）
4. 输出返回：
   - text 模式：返回“可读的文本流”
   - sse 模式：返回“JSON SSE events”

---

## 目录结构（按模块域拆分）

### 1) 入口与 API

- **`run.py`**
  - 启动入口：调用 `app/main.py`
- **`app/main.py`**
  - FastAPI 应用与生命周期（lifespan）
  - 可选：本地 MCP auto-start（默认关闭，通过 `MCP_AUTO_START_LOCAL=true` 开启）
- **`app/api/routes.py`**
  - HTTP API：
    - `GET/POST /ask`：主入口
    - `GET /tools`：列出 Holmes 已注册工具（含 MCP tools）
    - `GET /runbooks`：列出 runbook catalog
    - `GET /api/v1/mcp/status`：仅显示“本地 auto-start 管理器”的状态（与远程 MCP 的连通性不是一回事）

你要改什么：
- **加/改 API**：改 `app/api/routes.py`
- **服务启动流程**：改 `app/main.py`

---

### 2) 核心编排器（尽量保持薄）

- **`app/core/service.py`**
  - `HolmesService.initialize()`：加载配置、创建 AI、加载/合并 runbooks
  - `execute_query()`：同步执行
  - `execute_query_stream()`：流式执行（根据 output_format 路由）

它依赖下方的“holmes 子模块”实现细节，但自身只保留编排逻辑。

你要改什么：
- **改变执行流程（但不建议把细节塞回 service.py）**：优先新增/修改 `app/core/holmes/` 下的实现，再由 `service.py` 组合。

---

### 3) Holmes 子模块（被抽离出来的可复用能力）

这些文件是你提到的“逻辑抽离后看不懂”的核心。可以把它们理解为：`HolmesService` 的“组件库”。

- **`app/core/holmes/config_loader.py`**
  - 负责：读取 YAML、环境变量替换 `${VAR}`、去掉 `stream_output` 字段写入临时文件、再调用 `Config.load_from_file`
  - 你要改的场景：
    - 想增加新的配置源（比如从远程读取配置）
    - 想调整环境变量替换策略

- **`app/core/holmes/query_stream.py`**
  - 负责：两种流式输出实现（行为与输出保持原样）
    - `execute_query_stream_text()`：人类可读纯文本流
    - `execute_query_stream_sse()`：JSON SSE events
  - 你要改的场景：
    - 想修改“流式输出格式/字段/事件类型”

- **`app/core/holmes/call_wrapper.py`**
  - 负责：把 `ai.call_stream(...)` 的事件收集成一个“类似 ai.call() 的响应对象”
  - 你要改的场景：
    - 想改变“stream 模式下 tool_calls 的收集方式”

- **`app/core/holmes/streaming.py`**
  - 负责：SSE 消息封装、耗时格式化

- **`app/core/holmes/introspection.py`**
  - 负责：启动时输出工具集/MCP/runbooks 的加载摘要（方便排障）

---

### 4) Prompt（方法论与输出规范）

- **`app/core/prompts.py`**
  - `SYSTEM_PROMPT`：分层诊断模型（L0-L4）、强制输出模板、安全禁令等

你要改什么：
- **改 Agent 的“思考方式/输出模板/安全规则”**：改 `app/core/prompts.py`

---

### 5) Runbooks（知识库/RAG）

- **`knowledge_base/runbooks/`**
  - `catalog.json`：runbook 索引（AI 用 description 做匹配）
  - `*.md`：具体 runbook 内容
- **`app/core/runbook.py`**
  - `RunbookManager`：加载并校验 catalog、合并内置与自定义 runbooks、配置搜索路径

你要改什么：
- **新增/编辑 runbook 内容**：改 `knowledge_base/runbooks/*.md`
- **新增/编辑索引条目**：改 `knowledge_base/runbooks/catalog.json`
- **改变 runbook 的加载/合并策略**：改 `app/core/runbook.py`

---

### 6) Tools（你未来最关心：只用第三方 MCP）

你现在的推荐模式是：**禁用本地 tools，只通过配置连接第三方 MCP Server**。

- **第三方 MCP（推荐）**
  - 配置位置：
    - 本地：`config/config.yaml`
    - K8s：`deploy/configmap/config.yaml`（由 Deployment 通过 `CONFIG_FILE` 指向挂载路径）
  - 配置字段：`mcp_servers.<name>.config.url`（SSE URL）+ `enabled: true`
  - 你要改什么：
    - **新增一个你自己的 MCP tool**：写一个独立 MCP Server（HTTP/SSE），部署后把 URL 写进 `mcp_servers`

- **内置 toolsets（可选）**
  - 配置字段：`toolsets.<toolset_name>.enabled`
  - 你要改什么：
    - 想完全不用内置工具：把 `toolsets` 全部设为 `enabled: false`（只剩第三方 MCP）

- **本地 MCP auto-start（可选，不推荐在生产依赖）**
  - 代码位置：`app/core/mcp/manager.py`
  - 开关：
    - 环境变量：`MCP_AUTO_START_LOCAL=true`
    - 单个 server：`mcp_servers.<name>.autostart: true` 且 url 必须是 `localhost/127.0.0.1`
  - 用途：本地开发时方便启动 test MCP server（生产推荐只连第三方 MCP）

---

## “我该改哪个文件？”速查表

| 你要做的事 | 去改哪里 |
|---|---|
| 改 Agent 的诊断框架/输出模板/安全禁令 | `app/core/prompts.py` |
| 新增/修改 Runbook 内容 | `knowledge_base/runbooks/*.md` |
| 新增/修改 Runbook 目录索引 | `knowledge_base/runbooks/catalog.json` |
| 改 Runbook 加载/合并逻辑 | `app/core/runbook.py` |
| 只使用第三方 MCP（不跑本地工具） | 配置 `mcp_servers`（`config/config.yaml` 或 `deploy/configmap/config.yaml`） |
| 新增一个你自己的 tool（推荐方式） | 写独立 MCP Server（HTTP/SSE）+ 配置到 `mcp_servers` |
| 修改流式输出格式（text/sse） | `app/core/holmes/query_stream.py` |
| 修改 SSE 消息封装/耗时显示 | `app/core/holmes/streaming.py` |
| 修改启动时输出哪些工具/资源信息 | `app/core/holmes/introspection.py` |
| 修改服务启动/生命周期 | `app/main.py` |
| 增加新的 HTTP API | `app/api/routes.py` |


