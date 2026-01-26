# LangGraph 工作流开发指南

> 本文档详细说明如何使用 LangGraph 构建和扩展诊断工作流

## 目录

1. [架构概述](#1-架构概述)
2. [核心概念](#2-核心概念)
3. [节点与 LLM 调用](#3-节点与-llm-调用)
4. [目录结构](#4-目录结构)
5. [如何添加新节点](#5-如何添加新节点)
6. [如何修改工作流图](#6-如何修改工作流图)
7. [状态管理](#7-状态管理)
8. [与现有模块集成](#8-与现有模块集成)
9. [配置与启用](#9-配置与启用)
10. [测试指南](#10-测试指南)
11. [最佳实践](#11-最佳实践)

---

## 1. 架构概述

### 1.1 为什么使用 LangGraph？

传统的 HolmesGPT 使用 **Agentic Loop** 模式：
- LLM 自主决定调用哪些工具
- 执行顺序不可控
- 难以单独维护某个诊断步骤

LangGraph 工作流模式：
- **确定性流程**：明确的节点执行顺序
- **模块化**：每个节点独立维护
- **可扩展**：轻松添加/替换节点
- **状态管理**：清晰的数据流转

### 1.2 整体架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                          工作流层 (LangGraph)                        │
│                                                                      │
│   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐        │
│   │ 问题定位 │ → │ 证据采集 │ → │ 根因分析 │ → │ 汇总总结 │        │
│   │ (节点1)  │   │ (节点2)  │   │ (节点3)  │   │ (节点4)  │        │
│   └──────────┘   └──────────┘   └──────────┘   └──────────┘        │
│        │              │              │              │               │
│        └──────────────┴──────────────┴──────────────┘               │
│                            ↓                                         │
│                    WorkflowState（共享状态）                         │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                       现有能力层                                     │
│                                                                      │
│   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐           │
│   │ Skills 模块   │   │ HolmesGPT   │   │   Runbooks   │           │
│   │ (规则引擎)    │   │ (工具调用)   │   │  (知识库)    │           │
│   └──────────────┘   └──────────────┘   └──────────────┘           │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.3 数据流

```
用户问题
    ↓
┌─────────────────┐
│   节点1: 定层   │ → 输出: layer, layer_confidence
└─────────────────┘
    ↓
┌─────────────────┐
│   节点2: 证据   │ → 输出: evidence_items, evidence_completeness
└─────────────────┘
    ↓
┌─────────────────┐
│   节点3: 分析   │ → 输出: deterministic_decision, root_cause
└─────────────────┘
    ↓
┌─────────────────┐
│   节点4: 总结   │ → 输出: conclusion
└─────────────────┘
    ↓
最终诊断报告
```

---

## 2. 核心概念

### 2.1 StateGraph（状态图）

LangGraph 的核心是 `StateGraph`，它定义了：
- **节点（Nodes）**：执行具体逻辑的函数
- **边（Edges）**：节点之间的连接
- **状态（State）**：在节点间传递的数据

```python
from langgraph.graph import StateGraph, END

# 创建状态图
workflow = StateGraph(WorkflowState)

# 添加节点
workflow.add_node("layer", layer_node.execute)
workflow.add_node("evidence", evidence_node.execute)

# 添加边
workflow.set_entry_point("layer")
workflow.add_edge("layer", "evidence")
workflow.add_edge("evidence", END)

# 编译
compiled = workflow.compile()
```

### 2.2 WorkflowState（工作流状态）

状态是一个 `TypedDict`，定义了所有节点可以读写的字段：

```python
class WorkflowState(TypedDict, total=False):
    # 输入
    question: str
    run_id: str
    
    # 节点1输出
    layer: Optional[Layer]
    layer_confidence: Optional[float]
    
    # 节点2输出
    evidence_items: List[EvidenceItem]
    
    # ... 更多字段
```

### 2.3 WorkflowNode（节点基类）

所有节点继承自 `WorkflowNode` 基类：

```python
class WorkflowNode(ABC):
    @property
    @abstractmethod
    def node_id(self) -> str:
        """节点唯一标识"""
        pass
    
    @property
    @abstractmethod
    def node_name(self) -> str:
        """节点显示名称"""
        pass
    
    @abstractmethod
    def execute(self, state: WorkflowState) -> WorkflowState:
        """执行节点逻辑，返回更新后的状态"""
        pass
```

---

## 3. 节点与 LLM 调用

### 3.1 每个节点都有独立的 LLM 分析

**核心设计**：每个节点都有自己的专用 System Prompt，调用 LLM 进行独立分析：

```
┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│  节点1      │   │  节点2      │   │  节点3      │   │  节点4      │
│             │   │             │   │             │   │             │
│ LAYER_      │   │ EVIDENCE_   │   │ ROOT_CAUSE_ │   │ CONCLUSION_ │
│ CLASSIFIER_ │   │ COLLECTOR_  │   │ ANALYZER_   │   │ FORMATTER_  │
│ PROMPT      │   │ PROMPT      │   │ PROMPT      │   │ PROMPT      │
│     +       │   │     +       │   │     +       │   │     +       │
│ question    │   │ question    │   │ question    │   │ 前3个节点   │
│             │   │ + layer     │   │ + evidence  │   │ 的分析结果  │
│     ↓       │   │     ↓       │   │     ↓       │   │     ↓       │
│   LLM       │   │   LLM       │   │   LLM       │   │   LLM       │
│     ↓       │   │     ↓       │   │     ↓       │   │     ↓       │
│ layer_      │   │ evidence_   │   │ rca_        │   │ conclusion  │
│ analysis    │   │ analysis    │   │ analysis    │   │             │
└─────────────┘   └─────────────┘   └─────────────┘   └─────────────┘
```

### 3.2 Prompt 文件位置

所有节点的专用 Prompt 定义在 `app/core/workflow/prompts.py`：

| Prompt 名称 | 用途 | 输出格式 |
|-------------|------|----------|
| `LAYER_CLASSIFIER_PROMPT` | 节点1：判断问题层级 | JSON |
| `EVIDENCE_COLLECTOR_PROMPT` | 节点2：规划证据采集 | JSON |
| `ROOT_CAUSE_ANALYZER_PROMPT` | 节点3：根因推理 | JSON |
| `CONCLUSION_FORMATTER_PROMPT` | 节点4：生成报告 | Markdown |

### 3.3 节点 LLM 调用示例

```python
class LayerClassifierNode(WorkflowNode):
    def __init__(self, holmes_service: Any = None):
        self.holmes_service = holmes_service
    
    def execute(self, state: WorkflowState) -> WorkflowState:
        question = state.get("question", "")
        
        # 调用 LLM（使用专用 Prompt）
        if self.holmes_service and self.holmes_service.ai:
            response = self.holmes_service.ai.call(
                system_prompt=LAYER_CLASSIFIER_PROMPT,  # 专用 Prompt
                user_prompt=question,
                msgs=[]
            )
            result = parse_json(response.result)
        else:
            # 回退到规则匹配
            result = self._analyze_with_rules(question)
        
        # 保存 LLM 分析结果供下游使用
        return {
            "layer": result["layer"],
            "layer_analysis": json.dumps(result),  # 完整 LLM 输出
        }
```

### 3.4 节点间数据传递

每个节点的 LLM 分析结果会保存到状态中，供下游节点使用：

```python
# 状态中的 LLM 分析字段
class WorkflowState(TypedDict):
    # 节点1 的 LLM 分析
    layer_analysis: str      # JSON 字符串
    
    # 节点2 的 LLM 分析
    evidence_analysis: str   # JSON 字符串
    
    # 节点3 的 LLM 分析
    rca_analysis: str        # JSON 字符串
    
    # 节点4 基于前3个节点的分析生成最终报告
    conclusion: str          # Markdown
```

节点4（汇总总结）会读取前3个节点的分析结果：

```python
class ConclusionFormatterNode(WorkflowNode):
    def execute(self, state: WorkflowState) -> WorkflowState:
        # 读取前3个节点的 LLM 分析
        layer_analysis = state.get("layer_analysis", "{}")
        evidence_analysis = state.get("evidence_analysis", "{}")
        rca_analysis = state.get("rca_analysis", "{}")
        
        # 构建上下文，调用 LLM 生成最终报告
        context = f"""
# 阶段1：问题定位
{layer_analysis}

# 阶段2：证据采集
{evidence_analysis}

# 阶段3：根因分析
{rca_analysis}
"""
        response = self.holmes_service.ai.call(
            system_prompt=CONCLUSION_FORMATTER_PROMPT,
            user_prompt=context,
            msgs=[]
        )
        
        return {"conclusion": response.result}
```

---

## 4. 目录结构

```
app/core/workflow/
├── __init__.py              # 模块入口，导出公共接口
├── state.py                 # WorkflowState 定义
├── graph.py                 # 工作流图构建函数
├── executor.py              # 工作流执行器（SSE 兼容）
└── nodes/                   # 节点模块目录
    ├── __init__.py          # 节点导出
    ├── base.py              # WorkflowNode 基类
    ├── layer_classifier.py   # 节点1：问题定位
    ├── evidence_collector.py # 节点2：证据采集
    ├── root_cause_analyzer.py # 节点3：根因分析
    └── conclusion_formatter.py # 节点4：汇总总结
```

---

## 4. 如何添加新节点

### 4.1 创建节点文件

在 `app/core/workflow/nodes/` 目录下创建新文件：

```python
# app/core/workflow/nodes/my_new_node.py

"""
节点X：我的新节点

职责：
- 描述这个节点做什么
- 输入依赖哪些字段
- 输出哪些字段
"""

from typing import List
from app.core.workflow.nodes.base import WorkflowNode
from app.core.workflow.state import WorkflowState


class MyNewNode(WorkflowNode):
    """我的新节点"""
    
    def __init__(self, config: dict = None):
        """
        初始化节点
        
        Args:
            config: 可选的配置参数
        """
        self.config = config or {}
    
    @property
    def node_id(self) -> str:
        return "my_node"  # 唯一标识，用于工作流图
    
    @property
    def node_name(self) -> str:
        return "我的新节点"  # 显示名称，用于日志和报告
    
    def get_required_fields(self) -> List[str]:
        """声明节点执行所需的前置字段"""
        return ["question", "layer"]  # 依赖的字段
    
    def execute(self, state: WorkflowState) -> WorkflowState:
        """
        执行节点逻辑
        
        Args:
            state: 当前工作流状态（只读）
        
        Returns:
            更新后的状态（只更新自己负责的字段）
        """
        # 创建新状态（不修改输入 state）
        new_state: WorkflowState = {
            "current_node": self.node_id,
        }
        
        try:
            # 读取输入
            question = state.get("question", "")
            layer = state.get("layer")
            
            # 执行业务逻辑
            result = self._do_something(question, layer)
            
            # 更新输出字段
            new_state.update({
                "my_output_field": result,
            })
        
        except Exception as e:
            # 错误处理：写入 errors 列表
            new_state.setdefault("errors", []).append(
                f"节点 {self.node_id} 执行失败: {str(e)}"
            )
        
        return new_state
    
    def _do_something(self, question: str, layer) -> str:
        """内部业务逻辑"""
        # ... 实现具体逻辑
        return "result"
```

### 4.2 更新状态定义（如需要新字段）

如果新节点需要输出新字段，更新 `state.py`：

```python
# app/core/workflow/state.py

class WorkflowState(TypedDict, total=False):
    # ... 现有字段 ...
    
    # 新增：节点X 输出
    my_output_field: Optional[str]
```

### 4.3 注册节点

更新 `nodes/__init__.py`：

```python
# app/core/workflow/nodes/__init__.py

from .my_new_node import MyNewNode

__all__ = [
    # ... 现有导出 ...
    "MyNewNode",
]
```

### 4.4 添加到工作流图

更新 `graph.py`：

```python
# app/core/workflow/graph.py

from app.core.workflow.nodes.my_new_node import MyNewNode

def build_diagnosis_workflow(holmes_service=None):
    workflow = StateGraph(WorkflowState)
    
    # 现有节点
    layer_node = LayerClassifierNode()
    evidence_node = EvidenceCollectorNode(holmes_service)
    rca_node = RootCauseAnalyzerNode(holmes_service)
    conclusion_node = ConclusionFormatterNode()
    
    # 新节点
    my_node = MyNewNode()
    
    # 添加节点
    workflow.add_node("layer", layer_node.execute)
    workflow.add_node("evidence", evidence_node.execute)
    workflow.add_node("rca", rca_node.execute)
    workflow.add_node("my_node", my_node.execute)  # 新增
    workflow.add_node("conclusion", conclusion_node.execute)
    
    # 定义边（修改流程）
    workflow.set_entry_point("layer")
    workflow.add_edge("layer", "evidence")
    workflow.add_edge("evidence", "rca")
    workflow.add_edge("rca", "my_node")        # 新增
    workflow.add_edge("my_node", "conclusion") # 修改
    workflow.add_edge("conclusion", END)
    
    return workflow.compile()
```

---

## 5. 如何修改工作流图

### 5.1 添加条件分支

```python
from langgraph.graph import StateGraph, END

def should_skip_rca(state: WorkflowState) -> str:
    """根据证据完整度决定是否跳过根因分析"""
    completeness = state.get("evidence_completeness", 0)
    if completeness < 0.3:
        return "skip"  # 证据不足，跳过
    return "continue"

def build_workflow_with_conditions():
    workflow = StateGraph(WorkflowState)
    
    # 添加节点...
    
    # 条件分支
    workflow.add_conditional_edges(
        "evidence",                    # 从哪个节点
        should_skip_rca,              # 条件函数
        {
            "continue": "rca",        # 继续 → 根因分析
            "skip": "conclusion"      # 跳过 → 直接总结
        }
    )
    
    return workflow.compile()
```

### 5.2 并行执行（未来扩展）

```python
# LangGraph 支持并行节点执行
# 例如：同时采集多种证据

workflow.add_node("evidence_k8s", k8s_evidence_node.execute)
workflow.add_node("evidence_prom", prometheus_evidence_node.execute)

# 从 layer 分支到多个节点
workflow.add_edge("layer", "evidence_k8s")
workflow.add_edge("layer", "evidence_prom")

# 合并到下一个节点
workflow.add_edge("evidence_k8s", "merge")
workflow.add_edge("evidence_prom", "merge")
```

---

## 6. 状态管理

### 6.1 状态设计原则

1. **只更新自己的字段**：每个节点只更新自己负责的输出字段
2. **不修改输入状态**：返回新状态字典，不直接修改 state 参数
3. **使用 Optional**：所有字段都是可选的（`total=False`）
4. **类型安全**：使用 TypedDict 提供类型提示

### 6.2 状态字段规范

```python
class WorkflowState(TypedDict, total=False):
    # === 输入 ===
    question: str           # 用户问题（必需）
    run_id: str            # 运行 ID
    
    # === 节点1输出 ===
    layer: Optional[Layer]
    layer_confidence: Optional[float]
    layer_reasoning: Optional[str]
    
    # === 节点2输出 ===
    evidence_items: List[EvidenceItem]
    tool_results: List[Dict]
    evidence_completeness: Optional[float]
    
    # === 节点3输出 ===
    deterministic_decision: Optional[DeterministicDecision]
    root_cause: Optional[str]
    causal_chain: Optional[Dict[str, str]]
    
    # === 节点4输出 ===
    conclusion: Optional[str]
    conclusion_formatted: Optional[str]
    
    # === 元数据 ===
    current_node: Optional[str]
    errors: List[str]
    warnings: List[str]
```

### 6.3 读取和更新状态

```python
def execute(self, state: WorkflowState) -> WorkflowState:
    # 读取状态（使用 .get() 提供默认值）
    question = state.get("question", "")
    layer = state.get("layer")
    
    # 创建新状态
    new_state: WorkflowState = {
        "current_node": self.node_id,
        "my_field": "value",
    }
    
    # 添加到列表类型字段
    errors = state.get("errors", [])
    if some_error:
        new_state["errors"] = errors + ["新错误"]
    
    return new_state
```

---

## 7. 与现有模块集成

### 7.1 集成 Skills 模块（规则引擎）

```python
from app.core.skills import get_engine, evaluate_deterministic_decision
from app.core.skills.evidence import EvidenceExtractor

class RootCauseAnalyzerNode(WorkflowNode):
    def __init__(self):
        self.engine = get_engine()  # 获取规则引擎实例
    
    def execute(self, state: WorkflowState) -> WorkflowState:
        # 使用规则引擎
        decision = self.engine.evaluate(question, evidence_text)
```

### 7.2 集成 HolmesGPT 工具

```python
class EvidenceCollectorNode(WorkflowNode):
    def __init__(self, holmes_service):
        self.holmes_service = holmes_service
    
    def execute(self, state: WorkflowState) -> WorkflowState:
        if self.holmes_service:
            # 使用 HolmesGPT 工具执行器
            tool_executor = self.holmes_service.ai.tool_executor
            
            # 调用工具
            result = tool_executor.execute(
                tool_name="kubectl_get_by_name",
                params={"resource": "pod", "name": "my-pod"}
            )
```

### 7.3 集成 Runbooks

```python
class LayerClassifierNode(WorkflowNode):
    def execute(self, state: WorkflowState) -> WorkflowState:
        # 可以查询 Runbook 获取场景知识
        from app.core.runbook import RunbookManager
        
        manager = RunbookManager()
        # ... 使用 runbook 信息辅助定层
```

---

## 8. 配置与启用

### 8.1 环境变量

```bash
# 启用工作流模式
export USE_WORKFLOW=true

# 启动服务
python run.py
```

### 8.2 配置文件（可选扩展）

可以在 `config/config.yaml` 中添加工作流配置：

```yaml
workflow:
  enabled: true
  mode: full  # full / simple
  nodes:
    layer_classifier:
      use_llm_fallback: false
    evidence_collector:
      timeout_seconds: 30
```

### 8.3 API 使用

```bash
# SSE 格式
curl -N "http://localhost:8000/ask?q=Pod一直重启&format=sse"

# 文本格式
curl -N "http://localhost:8000/ask?q=Pod一直重启&format=text"
```

---

## 9. 测试指南

### 9.1 单节点测试

```python
# test/unit/test_my_node.py

from app.core.workflow.nodes.my_new_node import MyNewNode
from app.core.workflow.state import WorkflowState

def test_my_node_basic():
    node = MyNewNode()
    
    state: WorkflowState = {
        "question": "测试问题",
        "layer": Layer.L2,
        "errors": [],
    }
    
    result = node.execute(state)
    
    assert result.get("my_output_field") is not None
    assert len(result.get("errors", [])) == 0
```

### 9.2 工作流集成测试

```python
from app.core.workflow import build_diagnosis_workflow

def test_full_workflow():
    workflow = build_diagnosis_workflow()
    
    initial_state = {
        "question": "Pod OOMKilled",
        "run_id": "test-001",
        # ... 初始化其他字段
    }
    
    final_state = initial_state
    for event in workflow.stream(initial_state):
        for node_name, updated_state in event.items():
            final_state.update(updated_state)
    
    assert final_state.get("layer") is not None
    assert final_state.get("conclusion") is not None
```

### 9.3 运行测试

```bash
# 运行工作流测试
python test/workflow_poc_test.py

# 或使用 pytest
pytest test/unit/test_workflow.py -v
```

---

## 10. 最佳实践

### 10.1 节点设计原则

1. **单一职责**：每个节点只做一件事
2. **高内聚**：相关逻辑放在同一节点
3. **低耦合**：节点间只通过状态通信
4. **可测试**：每个节点可独立测试

### 10.2 错误处理

```python
def execute(self, state: WorkflowState) -> WorkflowState:
    new_state = {"current_node": self.node_id}
    
    try:
        # 业务逻辑
        result = self._do_work(state)
        new_state["output"] = result
    
    except Exception as e:
        # 1. 记录日志
        logger.error(f"节点执行失败: {e}", exc_info=True)
        
        # 2. 写入 errors
        new_state["errors"] = state.get("errors", []) + [
            f"节点 {self.node_id} 失败: {str(e)}"
        ]
        
        # 3. 提供降级值（可选）
        new_state["output"] = "降级默认值"
    
    return new_state
```

### 10.3 日志规范

```python
import logging

logger = logging.getLogger(__name__)

class MyNode(WorkflowNode):
    def execute(self, state: WorkflowState) -> WorkflowState:
        logger.info(f"📍 节点 {self.node_id} 开始执行")
        
        # ... 执行逻辑 ...
        
        logger.info(f"✅ 节点 {self.node_id} 完成: result={result}")
        
        return new_state
```

### 10.4 性能考虑

1. **避免阻塞**：长时间操作考虑超时
2. **缓存结果**：重复计算的结果可缓存
3. **并行执行**：独立的证据采集可并行

---

## 附录

### A. 常见问题

**Q: 如何调试工作流？**

A: 
1. 设置日志级别为 DEBUG
2. 使用测试脚本单独运行节点
3. 检查 SSE 事件中的 `node_complete` 事件

**Q: 节点间如何传递大量数据？**

A: 使用 `state.tool_results` 或创建专门的状态字段。避免在状态中存储过大的数据。

**Q: 如何实现人工干预？**

A: LangGraph 支持 `interrupt_before` 和 `interrupt_after`，可以在指定节点暂停等待用户输入。

### B. 参考资源

- [LangGraph 官方文档](https://langchain-ai.github.io/langgraph/)
- [项目架构文档](docs/ARCHITECTURE.md)
- [Skills 模块文档](app/core/skills/__init__.py)
