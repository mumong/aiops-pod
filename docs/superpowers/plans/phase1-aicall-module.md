# Phase 1: 创建 aicall 模块（不改现有代码）

## Task 1: 类型定义

**Files:**
- Create: `app/core/aicall/__init__.py`
- Create: `app/core/aicall/types.py`
- Test: `tests/unit/aicall/test_types.py`

- [ ] **Step 1: 创建 types.py**

```python
# app/core/aicall/types.py
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

@dataclass
class AICallResult:
    """AI 调用结果（兼容现有 StreamResponse 接口）"""
    result: str = ""
    tool_calls: List[Dict] = field(default_factory=list)
    iterations: int = 0
    tool_call_count: int = 0
    duration_ms: float = 0.0
    intermediate_events: List[Dict] = field(default_factory=list)

@dataclass
class ThinkingEvent:
    """思考事件（实时推送到 stream_queue）"""
    type: str          # ai_message, tool_start, tool_result, iteration_end
    node: str = ""     # 所属节点 ID
    data: Dict = field(default_factory=dict)
    timestamp: float = 0.0
```

- [ ] **Step 2: 创建 __init__.py**

```python
# app/core/aicall/__init__.py
from .types import AICallResult, ThinkingEvent
from .client import AICall

__all__ = ["AICall", "AICallResult", "ThinkingEvent"]
```

- [ ] **Step 3: 写测试验证类型**

```python
# tests/unit/aicall/test_types.py
from app.core.aicall.types import AICallResult, ThinkingEvent

def test_aicall_result_defaults():
    r = AICallResult()
    assert r.result == ""
    assert r.tool_calls == []
    assert r.iterations == 0

def test_aicall_result_with_data():
    r = AICallResult(result="hello", tool_call_count=3, duration_ms=1500.0)
    assert r.result == "hello"
    assert r.tool_call_count == 3

def test_thinking_event():
    e = ThinkingEvent(type="tool_start", node="layer", data={"tool_name": "kubectl"})
    assert e.type == "tool_start"
    assert e.node == "layer"
```

- [ ] **Step 4: 运行测试**
Run: `cd /root/huhu/agent/combine-aiops-mcp/robusta && .venv/bin/python -m pytest tests/unit/aicall/test_types.py -v`

- [ ] **Step 5: Commit**
```bash
git add app/core/aicall/ tests/unit/aicall/
git commit -m "feat(aicall): add types module with AICallResult and ThinkingEvent"
```

---

## Task 2: MCP 工具适配器

**Files:**
- Create: `app/core/aicall/tools.py`
- Test: `tests/unit/aicall/test_tools.py`

- [ ] **Step 1: 创建 tools.py**

```python
# app/core/aicall/tools.py
"""MCP SSE 工具 → LangChain BaseTool 适配器"""
import json
import logging
import httpx
from typing import Any, Dict, List, Optional, Type
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# PLACEHOLDER_TOOLS_CONTENT
```

注意：tools.py 完整实现约 120 行，包含：
- `MCPToolAdapter(BaseTool)` 类：通过 MCP SSE 协议调用工具
- `_build_input_schema()` 方法：从 MCP JSON Schema 构建 Pydantic model
- `load_mcp_tools(mcp_config)` 函数：从配置加载所有 MCP 工具
- 复用现有 `app/core/mcp/mcp_patch.py` 中的 SSE 连接逻辑

- [ ] **Step 2: 写测试**
- [ ] **Step 3: 运行测试**
- [ ] **Step 4: Commit**

---

## Task 3: AICall 核心类

**Files:**
- Create: `app/core/aicall/client.py`
- Create: `app/core/aicall/streaming.py`
- Test: `tests/unit/aicall/test_client.py`

- [ ] **Step 1: 创建 streaming.py（事件处理）**

```python
# app/core/aicall/streaming.py
"""流式事件处理：将 LLM 调用过程中的事件推送到 queue"""
import queue
import time
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

def push_event(
    event_queue: Optional[queue.Queue],
    event_type: str,
    node_id: str = "",
    **data
):
    """推送 thinking 事件到 queue（非阻塞）"""
    if not event_queue:
        return
    event = {
        "type": event_type,
        "node": node_id,
        "timestamp": time.time(),
        **data
    }
    try:
        event_queue.put_nowait(("thinking", event))
    except queue.Full:
        logger.debug(f"Event queue full, dropping: {event_type}")
```

- [ ] **Step 2: 创建 client.py（AICall 核心）**

AICall 核心实现约 200 行，关键方法：
- `__init__(model, api_key, api_base)` — 创建 ChatOpenAI 实例
- `call(system_prompt, question, tools, max_steps, stream_queue)` — ReAct loop
- `call_simple(system_prompt, question)` — 无工具直接调用
- `_run_agent_loop(messages, tools, max_steps, queue, node_id)` — 内部循环
- `_execute_tool(tool_call, tools_map)` — 执行单个工具调用

参考 HolmesGPT 的 `ai.call_stream()` 实现：
1. 构建 messages: [SystemMessage, HumanMessage]
2. model.bind_tools(tools) 绑定工具
3. 循环：model.invoke(messages) → 检查 tool_calls → 执行 → 反馈
4. 每步推送 thinking 事件到 queue
5. 返回 AICallResult + thinking_events

- [ ] **Step 3: 写集成测试（mock LLM）**
- [ ] **Step 4: 运行测试**
- [ ] **Step 5: Commit**

---

## Task 4: investigation_tools MCP Server

**Files:**
- Create: `mcpstander/servers/holmes_tools/investigation.py`
- Modify: `mcpstander/deploy/configmap.yaml`

- [ ] **Step 1: 创建 investigation.py**

```python
# mcpstander/servers/holmes_tools/investigation.py
"""调查工具 MCP Server: TodoWrite + fetch_runbook"""
import os
import json
from mcp.server.fastmcp import FastMCP

RUNBOOK_DIR = os.environ.get("RUNBOOK_DIR", "/app/runbooks")
mcp = FastMCP("investigation_tools")
_tasks = {}  # 全局任务存储（per-session）

@mcp.tool()
def TodoWrite(todos: list) -> str:
    """创建或更新调查任务列表"""
    for todo in todos:
        _tasks[todo["id"]] = todo
    # 格式化输出（兼容 HolmesGPT 格式）
    completed = sum(1 for t in _tasks.values() if t.get("status") == "completed")
    in_progress = sum(1 for t in _tasks.values() if t.get("status") == "in_progress")
    pending = sum(1 for t in _tasks.values() if t.get("status") == "pending")
    lines = [f"# CURRENT INVESTIGATION TASKS",
             f"**Task Status**: {completed} completed, {in_progress} in progress, {pending} pending", ""]
    icons = {"completed": "✓", "in_progress": "~", "pending": " ", "failed": "✗"}
    for t in _tasks.values():
        icon = icons.get(t.get("status", "pending"), " ")
        lines.append(f"[{icon}] [{t['id']}] {t['content']}")
    lines.append("\n**Instructions**: Use TodoWrite tool to update task status.")
    return "\n".join(lines)

@mcp.tool()
def fetch_runbook(runbook_id: str) -> str:
    """获取 Runbook 诊断手册内容"""
    safe_id = os.path.basename(runbook_id)
    path = os.path.join(RUNBOOK_DIR, safe_id)
    if not os.path.isfile(path):
        return f"ERROR: Runbook '{runbook_id}' not found in {RUNBOOK_DIR}"
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    return (f"<runbook>\n{content}\n</runbook>\n"
            "Note: the above are DIRECTIONS not ACTUAL RESULTS. "
            "Follow the steps using TOOLS and report findings.")
```

- [ ] **Step 2: 更新 mcpstander configmap**
- [ ] **Step 3: 更新 robusta configmap 添加 investigation_tools**
- [ ] **Step 4: 部署测试**
- [ ] **Step 5: Commit**
