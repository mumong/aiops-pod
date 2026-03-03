<div align="center">

# K8s AIOps Copilot

**用自然语言诊断 Kubernetes 故障**

基于 HolmesGPT + FastAPI + MCP 的智能运维 Agent，从提问到结构化诊断报告，全程自动化。

</div>

---

## 它能做什么

向 Agent 提问，它会自动调用工具采集证据，定位根因，输出诊断报告：

```
Q: "为什么 payment-service 的 Pod 一直在重启？"

→ 调用工具查询 Pod 状态、Events、日志、资源使用
→ 识别根因：容器内存超限（OOMKilled），内存 Limit 设为 256Mi 但实际峰值 420Mi
→ 输出完整报告：现象 / 证据链 / 根因 / 修复步骤 / 验证方式
```

---

---

## 架构优化（v2.0+）

本次更新引入了渐进式架构重构，核心目标是**高内聚、低耦合、易扩展**，同时保持功能不变。

### 优化内容

| 优化项 | 说明 | 优势 |
|---------|------|------|
| **常量提取** | 将硬编码值（50, 60, 100, 500 等）提取到 `app/core/constants.py` | 集中管理配置，避免魔法数字散落 |
| **辅助函数提取** | 将重复的文本处理、配置重置、初始化等待逻辑提取到独立模块 | 减少代码重复，提高可维护性 |
| **统一输出格式化** | 使用 `emit_text()`、`format_node_box()` 等统一接口 | 输出格式一致，易于调试和修改 |
| **动态节点配置** | 节点处理不再硬编码4个节点，使用配置注册系统 | 支持未来灵活增减节点 |

### 模块组织

```
app/core/
├── constants.py         # 常量定义（MAX_QUESTION_DISPLAY_LENGTH, DEFAULT_MAX_STEPS 等）
├── config_helpers.py    # 配置管理函数（should_reset_config, wait_for_initialization）
├── text_helpers.py      # 文本处理辅助函数（truncate_question, format_node_box, NODE_TITLES）
│                      # 节点配置注册系统（NodeConfig, DEFAULT_NODE_CONFIGS）
└── workflow/
    ├── executor.py         # 工作流执行器（LangGraph 编排）
    └── nodes/            # 各节点实现
        ├── layer_classifier.py
        ├── evidence_collector.py
        ├── root_cause_analyzer.py
        └── conclusion_formatter.py
```

---

## 如何添加新工作流节点

工作流节点采用**配置注册模式**，支持动态扩展：

### 步骤 1：定义节点实现

在 `app/core/workflow/nodes/` 下创建新的节点类：

```python
from app.core.workflow.nodes.base import WorkflowNode

class MyCustomNode(WorkflowNode):
    @property
    def node_id(self) -> str:
        return "my_custom"

    @property
    def node_name(self) -> str:
        return "自定义节点"

    def get_required_fields(self) -> List[str]:
        return ["question", "layer"]

    def execute(self, state: WorkflowState) -> WorkflowState:
        # 节点处理逻辑
        # ...
        return new_state
```

### 步骤 2：注册节点配置

在 `app/core/workflow/graph.py` 的 `build_diagnosis_workflow` 函数中添加新节点：

```python
from app.core.workflow.nodes.my_custom_node import MyCustomNode

def build_diagnosis_workflow(holmes_service, metrics, runbook_catalog):
    # 创建节点实例
    my_custom_node = MyCustomNode(holmes_service, metrics, runbook_catalog)

    # 添加到工作流图中
    workflow.add_node("my_custom", my_custom_node)
    workflow.add_edge("layer", "my_custom")
    workflow.add_edge("my_custom", "evidence")
    workflow.add_edge("my_custom", "rca")
    workflow.add_edge("my_custom", "conclusion")

    # 设置入口和出口
    workflow.set_entry_point("layer")
    workflow.set_finish_point("conclusion")
```

### 步骤 3：注册输出配置

在 `app/core/text_helpers.py` 中添加节点标题和格式化函数：

```python
# 添加到 NODE_TITLES
NODE_TITLES = {
    "layer": "📊 问题定位结果",
    "evidence": "🔍 证据采集结果",
    "rca": "🎯 根因分析结果",
    "conclusion": "📋 汇总总结结果",
    "my_custom": "🔧 自定义节点",  # 新增
}

# 添加格式化函数（如需要自定义输出）
def _default_my_custom_formatter(snapshot: Dict[str, Any]) -> List[str]:
    # 从 snapshot 提取关键信息
    return [
        f"   自定义字段: {snapshot.get('custom_field', '?')}",
    ]
```

### 步骤 4：更新工作流图

在 `app/core/workflow/graph.py` 中确保新节点被正确集成到工作流图中。

---

## 未来可扩展和优化方向

### 1. 节点编排优化
- **并发节点执行**：对于独立节点（如证据采集），可并行执行提升性能
- **条件分支**：根据诊断结果动态选择后续节点路径
- **循环重试**：支持节点级别的重试机制

### 2. 工具集成增强
- **工具结果缓存**：避免重复调用相同工具
- **批量工具调用**：对于多个相似查询，合并为一次批量调用
- **工具超时配置**：不同工具类型支持不同超时时间

### 3. 输出格式化统一
- **多语言支持**：支持国际化输出模板
- **输出格式选择**：支持 JSON/Markdown/HTML 等多种格式
- **可配置的详细程度**：支持 `--verbose`、`--concise` 等输出级别

### 4. 监控和可观测性
- **结构化日志**：统一日志格式，支持 JSON 输出便于解析
- **性能指标**：记录每个节点的执行耗时、工具调用耗时
- **Trace 集成**：集成 OpenTelemetry/Jaeger 实现分布式追踪

### 5. 配置管理增强
- **配置验证**：启动时验证配置完整性
- **配置热更新**：支持不重启服务更新部分配置
- **多环境配置**：支持 dev/staging/prod 多套配置

---


## 核心特性

**分层诊断 (L0–L4)**
内置五层故障分类模型——从磁盘 / 内存 / 内核（L0），到集群节点（L1）、工作负载（L2）、服务网络（L3），直到应用逻辑（L4）。Agent 首先定层，再聚焦采集该层证据，避免大海捞针。

**证据驱动，有据可查**
每个结论都有对应的工具输出作为来源。没有证据，不下结论。若关键证据缺失，Agent 会主动说明并给出补采建议。

**流式输出，实时反馈**
支持 SSE 流式响应。诊断过程中每次工具调用、每条 AI 推理都实时推送到客户端，无需等待全部完成。

**MCP 工具扩展**
通过 MCP 协议连接任意外部工具。内置集成：Kubernetes、Prometheus、Elasticsearch、Helm。新增工具只需写一个 MCP Server 并配置 URL。

**Runbook 知识库**
内置 26+ 故障诊断手册，AI 自动根据场景检索匹配。支持自定义 Runbook，放入 `knowledge_base/runbooks/` 并更新 `catalog.json` 即可生效。

**确定性规则双保险**
除 LLM 推理外，内置基于规则的判定引擎。对于 OOMKilled、磁盘满、镜像拉取失败等典型场景，可给出置信度评分和可解释的判定依据。

**两种执行模式**
- **默认模式**：HolmesGPT agentic loop，LLM 自主规划和执行工具调用，适合探索性诊断
- **工作流模式**（`USE_WORKFLOW=true`）：LangGraph 编排的四阶段流水线（定层 → 采证 → 根因 → 报告），流程确定，适合生产环境

---

## 架构概览

```
用户
  │  自然语言提问 (REST / SSE)
  ▼
FastAPI  ──────────────────────────────────────────────
  │  /ask  /tools  /runbooks  /health
  ▼
HolmesService（核心编排）
  │  System Prompt（L0-L4 诊断框架）
  │  Runbook 知识库（RAG 匹配）
  ▼
HolmesGPT（LLM + Tool Calling）
  │
  ├── 内置工具集：Prometheus、Docker、Kubernetes
  │
  └── MCP 工具集（SSE 连接）
        ├── K8s MCP Server
        ├── Elasticsearch MCP Server
        ├── Helm MCP Server
        └── 自定义 MCP Server ...
```

**工作流模式下的四阶段流水线：**

```
问题定层  →  证据采集  →  根因分析  →  报告生成
 (L0-L4)    (kubectl)    (因果链)    (Markdown)
```

---

## 快速开始

**环境要求**：Python 3.12+，可访问 Kubernetes 集群

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置 API Key
export DEEPSEEK_API_KEY=sk-xxx

# 3. 启动服务
python run.py
```

服务默认监听 `http://0.0.0.0:8000`。

---

## 使用方式

### 发起诊断查询

```bash
# 流式输出（推荐）
curl "http://localhost:8000/ask?q=payment-service 的 Pod 为什么一直重启&format=sse"

# 纯文本输出
curl "http://localhost:8000/ask?q=集群节点磁盘快满了怎么排查&format=text"

# POST 方式
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"q": "为什么 ingress 返回 503", "stream": true, "format": "sse"}'
```

### SSE 事件格式

流式模式下，每个事件以 `event: <type>\ndata: <json>` 格式推送：

```
event: run_start
data: {"run_id": "abc123", "question": "..."}

event: tool_start
data: {"tool": "kubectl_get_pods", "input": "..."}

event: tool_result
data: {"tool": "kubectl_get_pods", "preview": "NAME  STATUS  ...", "truncated": false}

event: ai_message
data: {"content": "根据 Pod 状态可以看到..."}

event: final
data: {"answer": "## 诊断报告\n...", "status": "success", "elapsed_seconds": 12.3}
```

### 其他端点

```bash
# 查看已加载的工具列表
GET /tools

# 查看工具详情（含参数 schema）
GET /tools/detail

# 查看可用 Runbook
GET /runbooks

# 健康检查
GET /health
```

---

## 配置

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DEEPSEEK_API_KEY` | — | DeepSeek API Key（必填） |
| `DEEPSEEK_MODEL` | `deepseek-chat` | 使用的模型 |
| `USE_WORKFLOW` | `false` | 启用 LangGraph 工作流模式 |
| `API_HOST` | `0.0.0.0` | 服务监听地址 |
| `API_PORT` | `8000` | 服务监听端口 |
| `CONFIG_FILE` | 自动检测 | 指定配置文件路径 |
| `HOLMES_INIT_TIMEOUT_SECONDS` | `0`（无超时） | 初始化超时秒数 |

### 工具集配置（`config/config.yaml`）

```yaml
# 内置工具集
toolsets:
  prometheus/metrics:
    enabled: true
    config:
      prometheus_url: "http://prometheus:9090"
  docker/core:
    enabled: true
  kubernetes/logs:
    enabled: false  # 建议通过 MCP 集成

# 外部 MCP 工具集
mcp_servers:
  elasticsearch:
    description: "Elasticsearch - 查询日志索引"
    config:
      url: "http://mcp-server:8082/sse"
      mode: "sse"
    enabled: true

  k8s-mcp-service:
    description: "K8s MCP - 查询集群资源"
    config:
      url: "http://mcp-server:8093/sse"
      mode: "sse"
    enabled: true
```

---

## 扩展：添加新工具

推荐通过 MCP 协议接入新工具，无需修改 Agent 源码：

1. 实现一个 MCP Server（HTTP/SSE 协议）
2. 在 `config/config.yaml` 的 `mcp_servers` 中添加配置：

```yaml
mcp_servers:
  my-custom-tool:
    description: "我的自定义工具 - 描述 AI 何时应使用此工具"
    config:
      url: "http://my-mcp-server:8099/sse"
      mode: "sse"
    enabled: true
```

3. 重启服务，工具自动可用。

---

## 扩展：添加 Runbook

Runbook 是 Agent 的领域知识库。添加新的故障处理手册：

1. 在 `knowledge_base/runbooks/` 下创建 `.md` 文件，按标准 Markdown 编写故障诊断步骤
2. 在 `knowledge_base/runbooks/catalog.json` 中注册：

```json
{
  "items": [
    {
      "title": "Pod OOMKilled 处理指南",
      "description": "当容器因内存不足被杀死时的诊断和处理方法",
      "path": "oomkilled.md"
    }
  ]
}
```

Agent 会根据用户问题自动匹配并引用相关 Runbook。

---

## 部署到 Kubernetes

```bash
# 构建并推送镜像
make build && make push

# 部署（含 namespace 创建、configmap、secret、deployment）
make deploy

# 查看日志
make logs

# 重启
make restart
```

**配置文件位置（K8s 环境）：**
- 应用配置：`deploy/configmap/config.yaml`
- Runbook 知识库：`deploy/configmap/runbooks.yaml`
- 敏感配置（API Key）：`deploy/secrets/core.yaml`

---

## 五层诊断模型

Agent 的诊断框架将 Kubernetes 故障分为五个层级，由下至上逐层排查：

```
L4  应用层      业务逻辑错误、配置错误、依赖服务不可用
L3  服务网络层  Service/Ingress 配置、DNS 解析、NetworkPolicy
L2  工作负载层  Pod 生命周期、镜像拉取、资源限制、探针
L1  集群节点层  Node 状态、kubelet、容器运行时、调度
L0  基础设施层  磁盘、内存、CPU、内核、文件系统
```

每次诊断，Agent 首先判断问题所在层级，再针对该层采集相关证据，避免无效的全量排查。

---

## 技术栈

- **API 框架**：[FastAPI](https://fastapi.tiangolo.com/)
- **AI 引擎**：[HolmesGPT](https://github.com/robusta-dev/holmesgpt)（Tool Calling 框架）
- **工作流编排**：[LangGraph](https://github.com/langchain-ai/langgraph)（工作流模式）
- **工具协议**：[MCP](https://modelcontextprotocol.io/)（Model Context Protocol）
- **LLM**：DeepSeek（可替换为任意 OpenAI 兼容模型）
