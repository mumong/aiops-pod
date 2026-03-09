# Agent-to-Agent 技术设计文档

## 技术实现原理

### 1. 核心架构

Agent-to-Agent (A2A) 使用 **LiteLLM Tool Calling** 实现，而不是直接使用 HolmesGPT 的 Agent 循环。

```
用户问题 → FederationAgent
         ↓
    [自定义 Tool Calling 循环]
         ↓
    litellm.completion(tools=[...])
         ↓
    LLM 返回 tool_calls
         ↓
    执行工具 → 添加结果到 messages
         ↓
    继续循环 or 返回最终答案
```

### 2. 为什么不使用 HolmesGPT 的 Agent 循环？

**HolmesGPT Agent 的特点**：
- 设计用于单集群 K8s 诊断
- 内置了大量 K8s 工具（kubectl、helm、prometheus 等）
- 有复杂的状态管理和工作流逻辑
- 与 Runbooks、工具集紧密耦合

**A2A 的需求**：
- 只需要 2 个简单工具：`list_clusters()` 和 `query_cluster()`
- 不需要 K8s 工具（子集群已经有了）
- 需要更简单、更可控的循环逻辑
- 避免与 HolmesGPT 内部逻辑冲突

**结论**：自己实现一个轻量级的 Tool Calling 循环更合适。

### 3. 实现细节

#### 3.1 Tool Calling 循环

```python
def ask_stream(self, question: str) -> Generator[str, None, None]:
    messages = [
        {"role": "system", "content": FEDERATION_AGENT_PROMPT},
        {"role": "user", "content": question}
    ]

    for step in range(self.max_steps):
        # 调用 LLM
        response = litellm.completion(
            model=self.model,
            api_key=self.api_key,
            messages=messages,
            tools=self._get_tools_schema(),  # OpenAI 格式的工具定义
            tool_choice="auto",
            stream=False
        )

        message = response.choices[0].message

        if message.tool_calls:
            # 有工具调用 → 执行工具 → 继续循环
            for tool_call in message.tool_calls:
                result = self._execute_tool(tool_call.function.name, params)
                messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": str(result)})
        else:
            # 没有工具调用 → 返回最终答案
            yield message.content
            return
```

#### 3.2 工具定义

使用 **OpenAI Function Calling 格式**：

```python
{
    "type": "function",
    "function": {
        "name": "list_clusters",
        "description": "列出所有可用的子集群信息",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
}
```

#### 3.3 工具执行

```python
def _execute_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    tool = self.toolset.get_tool_by_name(tool_name)
    context = self.toolset.get_context()  # 提供 registry 等上下文
    return tool._invoke(params, context)
```

### 4. 与 HolmesGPT 的关系

**使用的 HolmesGPT 组件**：
- `holmes.core.tools.Tool` 基类（定义工具接口）
- `holmes.core.tools.Toolset` 基类（定义工具集接口）

**不使用的 HolmesGPT 组件**：
- `holmes.core.agent` - Agent 循环逻辑
- `holmes.core.tool_executor` - 工具执行器
- `holmes.plugins.*` - 各种插件

**使用的第三方库**：
- `litellm` - LLM 调用（HolmesGPT 也使用这个库）
- `httpx` - HTTP 客户端（调用子集群）

**结论**：
- 没有改动 HolmesGPT 源码
- 只是复用了 Tool/Toolset 接口定义
- 自己实现了 Tool Calling 循环

### 5. 工具分离考虑

#### 当前实现：工具在代码中

```
robusta/app/core/federation/
├── toolset.py          # ListClustersTool, QueryClusterTool
├── agent.py            # FederationAgent (Tool Calling 循环)
└── registry.py         # AgentRegistry (读取配置)
```

#### 是否需要放到 mcpstander？

**mcpstander 的优势**：
- 工具独立部署，可以被多个服务复用
- 实现 Agent 逻辑与工具的分离
- 统一的工具管理

**A2A 工具的特点**：
- `list_clusters()` 需要读取主集群的 `agents_registry.yaml` 配置
- `query_cluster()` 需要调用子集群的 HTTP 端点
- 这两个工具是**主集群特有的元工具**，不太可能被其他服务复用
- 与主集群的配置和状态紧密耦合

**结论**：
- **不建议**放到 mcpstander
- A2A 工具是主集群的"协调工具"，不是通用的 K8s 诊断工具
- 保持在代码中更简单、更高效

**如果坚持分离**：
- 可以在 mcpstander 中创建 `federation-mcp` 服务器
- 但需要解决配置共享问题（如何让 MCP 服务器访问 agents_registry.yaml）
- 增加了复杂度，收益不大

### 6. 技术栈总结

| 组件 | 技术 | 说明 |
|------|------|------|
| LLM 调用 | litellm | 支持多种 LLM 提供商 |
| Tool Calling | OpenAI Function Calling 格式 | 行业标准 |
| HTTP 客户端 | httpx (异步) | 调用子集群 |
| 工具接口 | holmes.core.tools.Tool | 复用 HolmesGPT 接口 |
| 配置加载 | YAML + dataclass | 简单可靠 |
| 并发控制 | asyncio + ThreadPoolExecutor | 避免事件循环冲突 |

### 7. 优势与限制

**优势**：
- ✅ 简单：只有 ~500 行代码
- ✅ 可控：完全掌握 Tool Calling 循环逻辑
- ✅ 独立：不依赖 HolmesGPT 的复杂逻辑
- ✅ 灵活：容易扩展新工具

**限制**：
- ⚠️ 串行调用：Agent 可能串行调用 query_cluster（可优化）
- ⚠️ 无状态管理：没有 HolmesGPT 的状态跟踪能力
- ⚠️ 依赖 LLM：路由决策完全依赖 LLM 的理解能力

### 8. 与原有 FederationCoordinator 的对比

| 特性 | FederationCoordinator | FederationAgent |
|------|----------------------|-----------------|
| 实现方式 | 规则路由 | LLM Tool Calling |
| 查询策略 | 并发查询所有子集群 | 智能选择子集群 |
| 问题分解 | 不支持 | 支持 |
| 延迟 | 低（直接并发） | 中（多轮 LLM 调用） |
| 灵活性 | 低 | 高 |
| 适用场景 | 全局对比 | 选择性查询 |

### 9. 未来优化方向

1. **并发优化**：
   - 添加 `query_clusters_batch()` 工具
   - Agent 先收集所有需要查询的集群，然后批量并发执行

2. **缓存机制**：
   - `list_clusters()` 结果缓存（避免重复调用）
   - 子集群响应缓存（相同问题短时间内不重复查询）

3. **状态跟踪**：
   - 记录 Agent 的决策过程
   - 输出中间步骤（如"正在查询 cluster-24..."）

4. **错误恢复**：
   - 工具调用失败时的重试机制
   - 部分子集群失败时的降级策略

## 总结

Agent-to-Agent 实现是一个**轻量级、自定义的 Tool Calling 循环**，而不是基于 HolmesGPT 的 Agent 框架。这样做的原因是：

1. **需求简单**：只需要 2 个工具，不需要 HolmesGPT 的复杂功能
2. **避免冲突**：HolmesGPT 的 Agent 是为单集群设计的，强行复用会有冲突
3. **更可控**：自己实现循环逻辑，完全掌握执行流程
4. **易扩展**：未来可以轻松添加新工具或优化逻辑

**没有改动 HolmesGPT 源码**，只是复用了 Tool/Toolset 接口定义，使用 litellm 库实现了自己的 Tool Calling 循环。
