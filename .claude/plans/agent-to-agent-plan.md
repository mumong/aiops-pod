# Agent-to-Agent 真正实现计划

## 问题分析

### 当前实现的问题

**不是真正的 Agent-to-Agent**：
- 只是简单的并发 HTTP 调用
- 基于规则：把用户问题发给所有已配置的子集群
- 无智能路由：无法理解"查询集群 1、3、5"
- 无问题分解：无法针对不同集群发送不同问题

**示例问题**：
1. 用户："查询集群 1、3、5 的 CPU"
   - 当前：发给所有 100 个集群
   - 期望：只发给集群 1、3、5

2. 用户："查询集群 1 的 memory 和集群 3 的 cpu"
   - 当前：无法处理（发送相同问题给所有集群）
   - 期望：发送不同问题给不同集群

---

## 真正的 Agent-to-Agent 架构

### 核心设计

```
用户问题 → 主 Agent (HolmesGPT + Tool Calling)
              ↓
         [推理循环]
              ↓
    ┌─────────┴─────────┐
    ↓                    ↓
list_clusters()    query_cluster(name, question)
    ↓                    ↓
返回集群列表        HTTP 调用子集群 /ask
    ↓                    ↓
主 Agent 理解      收集子集群响应
    ↓                    ↓
决定查询哪些集群    主 Agent 汇总
    ↓
发送针对性问题
    ↓
LLM 合成最终报告
```

### 关键组件

**1. FederationToolset（新增）**
- 类似 `prometheus/metrics` 或 `kubernetes/logs`
- 包含 2 个工具：
  - `list_clusters()` - 列出所有可用集群
  - `query_cluster(cluster_name, question)` - 查询特定集群

**2. FederationAgent（新增）**
- 使用 HolmesGPT 的 Tool Calling 循环
- 系统提示词：多集群协调专家
- 能理解用户问题并分解任务

**3. 保持向后兼容**
- 原有的 `/federation/ask` 端点保留
- 新增 `/federation/ask/v2` 使用 Agent 模式
- 或通过配置切换模式

---

## 实现步骤

### Phase 1: 创建 FederationToolset

**文件位置**：`app/core/toolsets/federation.py`

**工具定义**：

```python
from holmes.core.tools import Tool, Toolset

class ListClustersTool(Tool):
    def _invoke(self, params, context):
        # 从 AgentRegistry 获取集群列表
        registry = context.get("federation_registry")
        clusters = registry.get_enabled_agents()
        return {
            "clusters": [
                {
                    "name": c.name,
                    "url": c.url,
                    "description": c.description
                }
                for c in clusters
            ]
        }

class QueryClusterTool(Tool):
    def _invoke(self, params, context):
        cluster_name = params["cluster_name"]
        question = params["question"]

        # 调用 SubAgentClient
        client = context.get("federation_client")
        result = sync_run(client.query(...))

        return {
            "cluster": cluster_name,
            "success": result.success,
            "response": result.text,
            "error": result.error
        }
```

### Phase 2: 创建 FederationAgent

**文件位置**：`app/core/federation/agent.py`

**核心逻辑**：

```python
class FederationAgent:
    def __init__(self, registry, model, api_key):
        self.registry = registry
        self.toolset = FederationToolset(registry)
        self.llm = create_llm(model, api_key)

    def ask(self, question):
        # 构建系统提示词
        system_prompt = FEDERATION_AGENT_PROMPT

        # 构建初始消息
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ]

        # Tool Calling 循环（类似单集群）
        for step in range(max_steps):
            response = self.llm.chat(messages, tools=self.toolset.tools)

            if response.tool_calls:
                # 执行工具调用
                for tool_call in response.tool_calls:
                    result = self.toolset.invoke(tool_call)
                    messages.append(tool_result_message)
            else:
                # 没有工具调用，返回最终答案
                return response.content
```

### Phase 3: 系统提示词设计

**FEDERATION_AGENT_PROMPT**：

```
你是多集群 Kubernetes 运维协调专家。

你的任务是理解用户的多集群查询需求，智能地决定：
1. 需要查询哪些子集群
2. 给每个子集群发送什么具体问题

可用工具：
- list_clusters(): 列出所有可用的子集群
- query_cluster(cluster_name, question): 查询特定子集群

工作流程：
1. 先调用 list_clusters() 了解有哪些集群
2. 分析用户问题，确定需要查询哪些集群
3. 针对每个集群调用 query_cluster()，可能发送不同的问题
4. 汇总所有子集群的响应，生成统一报告

示例：
- 用户："查询集群 1、3、5 的 CPU"
  → 只查询 cluster-1, cluster-3, cluster-5
  → 每个都发送 "CPU 利用率是多少"

- 用户："查询集群 1 的 memory 和集群 3 的 cpu"
  → query_cluster("cluster-1", "内存使用情况")
  → query_cluster("cluster-3", "CPU 利用率")
```

### Phase 4: 集成到现有架构

**修改 `routes.py`**：

```python
@app.get("/federation/ask/v2")
async def federation_ask_v2(q: str, max_steps: int = 30):
    """真正的 Agent-to-Agent 模式"""
    service = get_service()
    agent = service.federation_agent  # 新增

    def generate():
        yield from agent.ask_stream(question=q, max_steps=max_steps)

    return StreamingResponse(generate(), media_type="text/plain")
```

**修改 `service.py`**：

```python
class HolmesService:
    def initialize(self):
        # ... 现有逻辑 ...

        # 初始化 FederationAgent（如果启用）
        if federation_config and federation_config.get("enabled"):
            self.federation_agent = FederationAgent(
                registry=registry,
                model=self.config.model,
                api_key=self.config.api_key
            )
```

---

## 技术细节

### 1. 集群名称映射

**问题**：用户说"集群 1"，如何映射到 "cluster-24"？

**方案 A**：配置中添加别名
```yaml
sub_agents:
  - name: "cluster-24"
    aliases: ["1", "集群1", "cluster1"]
```

**方案 B**：LLM 理解
- list_clusters 返回所有集群信息
- LLM 根据上下文理解"集群 1"指的是哪个

### 2. 并发控制

**问题**：Agent 可能串行调用 query_cluster，效率低

**方案**：
- Agent 先收集所有需要查询的集群和问题
- 批量并发执行（类似现在的实现）
- 或者：提供 `query_clusters_batch()` 工具

### 3. 向后兼容

**方案 A**：双端点
- `/federation/ask` - 原有的简单模式（基于规则）
- `/federation/ask/v2` - 新的 Agent 模式

**方案 B**：配置切换
```yaml
federation:
  mode: "agent"  # 或 "simple"
```

---

## 优缺点分析

### Agent 模式的优势

✅ **智能路由**：理解用户意图，只查询需要的集群
✅ **问题分解**：针对不同集群发送不同问题
✅ **灵活性**：可以处理复杂的多集群查询场景
✅ **可扩展**：未来可以添加更多工具（如 compare_clusters）

### Agent 模式的挑战

⚠️ **复杂度**：需要 Tool Calling 循环，增加代码复杂度
⚠️ **延迟**：多轮 LLM 调用可能增加延迟
⚠️ **成本**：更多的 LLM 调用意味着更高的 API 成本
⚠️ **可靠性**：依赖 LLM 的推理能力，可能出错

### 简单模式的优势

✅ **简单**：代码简单，易于维护
✅ **快速**：直接并发调用，延迟低
✅ **可靠**：基于规则，不依赖 LLM 推理

---

## 推荐方案

### 混合模式

**默认：简单模式**（当前实现）
- 适用场景：查询所有集群、对比分析
- 优势：快速、可靠

**可选：Agent 模式**（新增）
- 适用场景：选择性查询、复杂问题分解
- 触发条件：用户明确指定集群名称

**实现**：
```python
def should_use_agent_mode(question):
    # 检测用户问题中是否包含集群名称
    keywords = ["集群 1", "cluster-1", "cluster 1", "集群1"]
    return any(k in question.lower() for k in keywords)

@app.get("/federation/ask")
async def federation_ask(q: str):
    if should_use_agent_mode(q):
        return federation_ask_agent(q)  # Agent 模式
    else:
        return federation_ask_simple(q)  # 简单模式
```

---

## 实现优先级

### P0（必须）
1. 创建 FederationToolset（list_clusters, query_cluster）
2. 创建 FederationAgent（使用 HolmesGPT）
3. 设计系统提示词
4. 集成到 service.py

### P1（重要）
1. 集群名称映射逻辑
2. 并发优化（批量查询）
3. 向后兼容处理

### P2（可选）
1. 混合模式自动切换
2. 更多工具（compare_clusters, filter_clusters）
3. 性能优化

---

## 下一步

**建议**：
1. 先实现最小可行版本（MVP）
2. 只实现 Agent 模式，不考虑向后兼容
3. 验证可行性后再优化

**MVP 范围**：
- FederationToolset（2 个工具）
- FederationAgent（基础 Tool Calling 循环）
- 新端点 `/federation/ask/v2`
- 简单的系统提示词

**预计工作量**：
- 核心代码：~300 行
- 测试验证：2-3 小时
- 文档更新：1 小时

是否开始实现 MVP？
