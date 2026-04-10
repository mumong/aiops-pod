# Phase 2: 节点迁移（逐个替换 HolmesGPT 调用）

## Task 5: base.py _call_llm() 替换

**Files:**
- Modify: `app/core/workflow/nodes/base.py`
- Test: `tests/unit/workflow/test_base_aicall.py`

- [ ] **Step 1: 修改 base.py 的 _call_llm()**

将现有的 HolmesGPT 调用：
```python
# 旧代码（依赖 holmes）
from holmes.core.prompt import build_initial_ask_messages
response = call_with_stream_and_queue(ai, messages, event_queue, node_id)
```

替换为：
```python
# 新代码（使用 aicall）
from app.core.aicall import AICall, AICallResult
result, events = self.ai_call.call(
    system_prompt=system_prompt,
    question=question,
    tools=self.tools,
    max_steps=max_steps,
    stream_queue=self._event_queue,
)
```

关键：AICallResult 的字段与现有 StreamResponse 兼容：
- `result.result` → 最终文本
- `result.tool_calls` → 工具调用记录
- `result.intermediate_events` → thinking 事件

- [ ] **Step 2: 更新 WorkflowNode 构造函数**

新增 `ai_call` 和 `tools` 参数：
```python
class WorkflowNode(ABC):
    def __init__(self):
        self.ai_call: Optional[AICall] = None
        self.tools: List[BaseTool] = []
        self._event_queue = None
```

- [ ] **Step 3: 写测试（mock AICall）**
- [ ] **Step 4: 运行测试**
- [ ] **Step 5: Commit**

---

## Task 6: layer_classifier 节点迁移

**Files:**
- Modify: `app/core/workflow/nodes/layer_classifier.py`

- [ ] **Step 1: 替换 _analyze_with_llm() 中的 HolmesGPT 调用**

阶段1（工具调用）：`self._call_llm()` → 已在 Task 5 中替换
阶段2（JSON 提取）：`litellm.completion()` → `self.ai_call.call_simple()`

- [ ] **Step 2: 验证两阶段架构数据流完整**
- [ ] **Step 3: Commit**

---

## Task 7: evidence_collector 节点迁移

**Files:**
- Modify: `app/core/workflow/nodes/evidence_collector.py`

- [ ] **Step 1: 替换 _plan_evidence_with_llm() 中的调用**
- [ ] **Step 2: 验证证据采集清单合并逻辑不受影响**
- [ ] **Step 3: Commit**

---

## Task 8: root_cause_analyzer 节点迁移

**Files:**
- Modify: `app/core/workflow/nodes/root_cause_analyzer.py`

- [ ] **Step 1: lite 模式：litellm.completion() → ai_call.call_simple()**
- [ ] **Step 2: full 模式：_call_llm() 已在 Task 5 替换**
- [ ] **Step 3: Commit**

---

## Task 9: conclusion_formatter 节点迁移

**Files:**
- Modify: `app/core/workflow/nodes/conclusion_formatter.py`

- [ ] **Step 1: _generate_with_llm() 中 litellm.completion() → ai_call.call_simple()**
- [ ] **Step 2: 验证输出格式不变**
- [ ] **Step 3: Commit**

---

## Task 10: executor + graph 适配

**Files:**
- Modify: `app/core/workflow/executor.py`
- Modify: `app/core/workflow/graph.py`

- [ ] **Step 1: executor 初始化时创建 AICall 实例并传给各节点**

```python
# executor.py
from app.core.aicall import AICall
from app.core.aicall.tools import load_mcp_tools

ai_call = AICall(model=..., api_key=..., api_base=...)
mcp_tools = load_mcp_tools(config.mcp_servers)

# 传给每个节点
for node in node_instances.values():
    node.ai_call = ai_call
    node.tools = mcp_tools
```

- [ ] **Step 2: graph.py 中 build_diagnosis_workflow() 接收 ai_call 参数**
- [ ] **Step 3: 端到端测试（部署验证）**
- [ ] **Step 4: Commit**
