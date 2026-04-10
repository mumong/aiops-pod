# 设计文档：脱离 HolmesGPT — aicall 模块 + 项目重构

> 日期：2026-04-09
> 状态：已确认
> 目标：用 LangChain/LangGraph 替换 HolmesGPT AI 调用层，实现完全的 prompt 控制权

---

## 1. 背景与动机

### 1.1 当前问题

- HolmesGPT 的 `generic_ask.jinja2` 模板在 system prompt 最前面注入固定指令，用户 prompt 被稀释
- 无法控制 JSON 输出格式（HolmesGPT 优先执行工具调用而非输出 JSON）
- PromQL 查询等专业指导被通用指令淹没
- `service.py` 963 行、`executor.py` 846 行，职责混杂
- `holmes/` 目录是 HolmesGPT 的适配层，增加了不必要的间接性

### 1.2 目标

1. 完全控制 system prompt 的内容和位置
2. 统一的 AI 调用接口（`aicall` 模块）
3. 模块化、低耦合、高内聚的代码结构
4. 为未来扩展（session 管理、memory、skill 调用）预留接口
5. 分阶段迁移，不中断现有功能

---

## 2. 架构设计

### 2.1 目标目录结构

```
app/core/
├── aicall/                        # 新模块：AI 调用抽象层
│   ├── __init__.py                # 导出 AICall, AICallResult
│   ├── client.py                  # AICall 核心类
│   ├── streaming.py               # 流式事件处理
│   ├── tools.py                   # MCP → LangChain Tool 适配器
│   └── types.py                   # 类型定义
│
├── config/                        # 配置管理（从 service.py 拆出）
│   ├── __init__.py
│   ├── loader.py                  # YAML + 环境变量加载
│   └── settings.py                # 配置数据类
│
├── runbook/                       # Runbook 管理（独立模块）
│   ├── __init__.py
│   ├── catalog.py                 # RunbookCatalog（替代 holmes 依赖）
│   └── manager.py                 # 现有 runbook.py 迁入
│
├── workflow/                      # 工作流（精简）
│   ├── executor.py                # 精简：只保留执行逻辑
│   ├── reporter.py                # 新：报告保存 + 指标提取
│   ├── graph.py                   # 保持不变
│   ├── state.py                   # 保持不变
│   ├── metrics.py                 # 保持不变
│   └── nodes/
│       ├── base.py                # _call_llm() → aicall
│       └── ...                    # 各节点精简
│
├── service.py                     # 精简：~200 行，只做协调
│
└── [删除] holmes/                 # 整个目录废弃
```

### 2.2 aicall 模块接口

```python
# app/core/aicall/client.py

class AICall:
    """AI 调用抽象层"""

    def __init__(self, model: str, api_key: str, api_base: str = ""):
        """
        初始化 LangChain ChatModel

        Args:
            model: 模型名（如 "deepseek/deepseek-chat"）
            api_key: API Key
            api_base: API 代理地址（可选）
        """

    def call(
        self,
        system_prompt: str,
        question: str,
        tools: List[BaseTool] = None,
        max_steps: int = 10,
        stream_queue: Queue = None,
    ) -> Tuple[AICallResult, List[ThinkingEvent]]:
        """
        执行 AI 调用（支持多轮工具调用）

        内部实现：ReAct agent loop
        1. 构建 messages: [system_prompt, user_question]
        2. 调用 LLM（带 tool binding）
        3. 如果 LLM 返回 tool_call → 执行工具 → 结果反馈 → 回到 2
        4. 如果 LLM 返回文本 → 结束
        5. 最多 max_steps 轮
        6. 每个事件推送到 stream_queue

        Returns:
            (AICallResult, List[ThinkingEvent])
        """

    def call_simple(
        self,
        system_prompt: str,
        question: str,
    ) -> str:
        """简单调用（无工具，直接返回文本）"""
```

### 2.3 类型定义

```python
# app/core/aicall/types.py

@dataclass
class AICallResult:
    result: str                    # 最终文本输出
    tool_calls: List[Dict]         # 工具调用记录
    iterations: int                # 迭代轮数
    tool_call_count: int           # 工具调用总次数
    duration_ms: float             # 总耗时

@dataclass
class ThinkingEvent:
    type: str                      # ai_message, tool_start, tool_result, iteration_end
    node: str                      # 所属节点 ID
    data: Dict                     # 事件数据
    timestamp: float               # 时间戳
```

### 2.4 MCP 工具适配器

```python
# app/core/aicall/tools.py

class MCPToolAdapter(BaseTool):
    """将 MCP SSE 工具转为 LangChain Tool"""

    name: str
    description: str
    mcp_url: str                   # MCP SSE 端点
    parameters: Dict               # JSON Schema 参数定义

    def _run(self, **kwargs) -> str:
        """通过 MCP SSE 协议调用工具"""

def load_mcp_tools(mcp_config: Dict) -> List[BaseTool]:
    """从配置加载所有 MCP 工具"""
```

### 2.5 ReAct Agent Loop 实现参考

参考 HolmesGPT 的 agentic loop（`ai.call_stream()`）和 LangGraph 的 ReAct 模式：

```python
# 伪代码：aicall/client.py 内部实现

def _run_agent_loop(self, messages, tools, max_steps, queue):
    model = self.chat_model.bind_tools(tools)
    events = []

    for step in range(max_steps):
        response = model.invoke(messages)

        # LLM 返回文本（结束）
        if not response.tool_calls:
            return response.content, events

        # LLM 返回工具调用
        for tool_call in response.tool_calls:
            # 推送 tool_start 事件
            if queue:
                queue.put_nowait(("thinking", {
                    "type": "tool_start",
                    "tool_name": tool_call["name"],
                }))

            # 执行工具
            result = self._execute_tool(tool_call, tools)

            # 推送 tool_result 事件
            if queue:
                queue.put_nowait(("thinking", {
                    "type": "tool_result",
                    "tool_name": tool_call["name"],
                    "result_preview": result[:500],
                    "status": "success",
                }))

            # 将工具结果加入 messages
            messages.append(ToolMessage(content=result, ...))

    return "达到最大迭代次数", events
```

---

## 3. MCP 工具扩展

### 3.1 新增 investigation_tools MCP Server

在 mcpstander 中新增：

```
mcpstander/servers/holmes_tools/investigation.py
端口：8098
```

工具列表：
- `TodoWrite(todos: list[dict]) → str` — 任务管理
- `fetch_runbook(runbook_id: str) → str` — 获取 Runbook 内容
- `list_runbooks() → str` — 列出所有 Runbook

### 3.2 Runbook 文件挂载

mcpstander 容器需要挂载 Runbook 文件：
- ConfigMap `aiops-runbooks` 挂载到 mcpstander 的 `/app/runbooks/`
- 或通过共享 Volume 从 aiops-copilot 容器同步

### 3.3 配置更新

```yaml
# robusta deploy/configmap/config.yaml
mcp_servers:
  investigation_tools:
    description: "调查工具 - TodoWrite + Runbook"
    config:
      url: "http://mcp-server-manager.mcp.svc.cluster.local:8098/sse"
      mode: "sse"
    enabled: true
```

---

## 4. service.py 拆分

### 4.1 拆分后的 service.py（~200 行）

```python
class HolmesService:
    """API 入口协调器"""

    def __init__(self):
        self.config = None
        self.ai_call = None          # AICall 实例
        self.runbook_manager = None   # RunbookManager
        self.mcp_tools = []           # LangChain Tool 列表

    async def initialize(self, config_path: str):
        """初始化所有模块"""
        self.config = ConfigLoader.load(config_path)
        self.ai_call = AICall(
            model=self.config.llm_model,
            api_key=self.config.llm_api_key,
            api_base=self.config.llm_api_base,
        )
        self.mcp_tools = await load_mcp_tools(self.config.mcp_servers)
        self.runbook_manager = RunbookManager(self.config.runbook_path)

    def execute_query_stream(self, question, ...):
        """路由到 workflow 或 legacy 模式"""
```

### 4.2 config/loader.py（~150 行）

```python
class ConfigLoader:
    """配置加载器"""

    @staticmethod
    def load(config_path: str) -> AppConfig:
        """加载 YAML + 环境变量覆盖"""

class AppConfig:
    """应用配置"""
    llm_model: str
    llm_api_key: str
    llm_api_base: str
    mcp_servers: Dict
    workflow: Dict
    metrics: Dict
    federation: Dict
```

---

## 5. executor.py 拆分

### 5.1 executor.py（~400 行）

保留：
- `execute_stream()` — 工作流执行 + 事件流
- `_run_workflow_in_thread()` — 后台线程执行
- `_format_handoff_summary()` — 节点间数据传递

### 5.2 reporter.py（~200 行）

从 executor.py 拆出：
- `_update_metrics_from_state()` — 指标提取
- `_extract_runbook_info()` — Runbook 识别
- `_save_report()` — 报告保存
- `_extract_layer_from_report()` — 层级提取

---

## 6. 迁移阶段

### Phase 1：创建 aicall 模块（不改现有代码）
- 实现 `AICall` 类 + MCP 工具适配器
- 实现 `MCPToolAdapter`
- 单元测试验证 aicall 独立可用
- 在 mcpstander 中实现 investigation_tools

### Phase 2：节点迁移
- `base.py` 的 `_call_llm()` 改为调用 `AICall.call()`
- 逐个节点验证（layer → evidence → rca → conclusion）
- 确保 thinking_events 格式兼容

### Phase 3：service.py 拆分 + holmes/ 清理
- 创建 `config/` 模块
- 创建 `runbook/` 模块
- 精简 `service.py`
- 删除 `holmes/` 目录
- 从 `requirements.txt` 移除 `holmesgpt`

### Phase 4：代码精简
- `executor.py` 拆分为 executor + reporter
- 节点公共逻辑提取
- 清理冗余代码

---

## 7. 风险与缓解

| 风险 | 缓解措施 |
|------|----------|
| LangChain Tool Calling 与 HolmesGPT 行为差异 | Phase 1 充分测试，对比输出 |
| MCP 工具适配器性能 | 复用现有 MCP SSE 连接池 |
| 流式事件格式变化 | ThinkingEvent 保持与现有格式兼容 |
| Runbook 注入方式变化 | catalog 仍在 system_prompt 中注入 |
| 回退能力 | Phase 2 保留 `USE_WORKFLOW` 开关 |

---

## 8. 验收标准

- [ ] `aicall` 模块独立可用，单元测试通过
- [ ] 所有 4 个工作流节点使用 `aicall` 调用 LLM
- [ ] `holmesgpt` 从 `requirements.txt` 移除
- [ ] `holmes/` 目录完全删除
- [ ] `service.py` < 250 行
- [ ] `executor.py` < 450 行
- [ ] 诊断报告质量不低于当前水平（MTTR、准确率、证据完整率）
- [ ] TodoWrite + fetch_runbook 通过 MCP 工具可用
- [ ] 流式输出格式保持兼容
