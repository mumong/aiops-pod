# 工作流使用指南

## 概述

这是基于 LangGraph 的分阶段诊断工作流实现，将运维诊断步骤抽象为4个独立的工作流节点。

**已实现的4个节点**：
- ✅ 节点1：问题定位（LayerClassifierNode）- 基于关键词规则匹配，判定问题层级 L0-L4
- ✅ 节点2：证据链采集（EvidenceCollectorNode）- 根据场景采集证据
- ✅ 节点3：根因分析（RootCauseAnalyzerNode）- 规则引擎匹配 + 通用推理
- ✅ 节点4：汇总总结（ConclusionFormatterNode）- 格式化输出完整报告

## 启用工作流模式

### 方式1：环境变量（推荐）

```bash
export USE_WORKFLOW=true
python run.py
```

### 方式2：在代码中设置

```python
import os
os.environ["USE_WORKFLOW"] = "true"
```

## 使用示例

### 1. 启动服务

```bash
# 启用工作流模式
export USE_WORKFLOW=true

# 启动服务
python run.py
```

### 2. 发送查询请求

```bash
# SSE 格式（推荐）
curl -N "http://localhost:8000/ask?q=Pod一直重启&format=sse"

# 文本格式
curl -N "http://localhost:8000/ask?q=Pod一直重启&format=text"
```

### 3. 查看工作流事件

工作流模式会发出以下事件类型：

- `run_start` - 工作流开始
- `node_start` - 节点开始执行
- `node_complete` - 节点执行完成
- `final` - 最终答案
- `run_end` - 工作流结束

## 工作流架构

```
┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│  问题定位   │ → │  证据采集   │ → │  根因分析   │ → │  汇总总结   │
│  (节点1)    │   │  (节点2)    │   │  (节点3)    │   │  (节点4)    │
└─────────────┘   └─────────────┘   └─────────────┘   └─────────────┘
```

### 节点1：问题定位 (LayerClassifierNode)

**功能**：从用户问题中提取关键实体，基于关键词规则快速判断层级（L0-L4）

**规则示例**：
- "Pod"、"重启"、"OOM" → L2（工作负载层）
- "磁盘"、"ENOSPC" → L0（基础设施层）
- "DNS"、"CoreDNS" → L3（服务与网络层）

**输出**：
- `layer`: L0/L1/L2/L3/L4
- `layer_confidence`: 置信度 [0, 1]
- `layer_reasoning`: 判定理由

### 节点2：证据链采集 (EvidenceCollectorNode)

**功能**：根据层级和问题确定场景，采集该场景所需的证据

**场景映射**：
- L0 → DiskFull（磁盘满）
- L1 → KubeletCert（证书异常）
- L2 → OOMKilled（内存超限）
- L3 → DNSLatency（DNS延迟）
- L4 → Dependency503（依赖异常）

**输出**：
- `evidence_items`: 证据列表
- `tool_results`: 工具调用结果
- `evidence_completeness`: 证据完整度

### 节点3：根因分析 (RootCauseAnalyzerNode)

**功能**：基于证据链进行规则匹配和根因分析

**分析逻辑**：
1. 尝试规则引擎匹配（确定性判定）
2. 如规则未命中，使用通用推理
3. 构建因果链

**输出**：
- `deterministic_decision`: 确定性判定结果
- `root_cause`: 根因结论
- `causal_chain`: 因果链分析

### 节点4：汇总总结 (ConclusionFormatterNode)

**功能**：整合所有节点输出，生成完整的诊断报告

**输出**：
- `conclusion`: 完整报告
- `conclusion_formatted`: 格式化后的 Markdown

## 代码结构

```
app/core/workflow/
├── __init__.py              # 统一对外接口
├── state.py                 # 工作流状态模型
├── graph.py                 # 工作流图构建
├── executor.py              # 工作流执行器
└── nodes/                   # 工作流节点
    ├── __init__.py
    ├── base.py              # 节点基类
    ├── layer_classifier.py   # 节点1：问题定位
    └── conclusion_formatter.py # 节点4：汇总总结
```

## 扩展指南

### 添加新节点

1. 在 `app/core/workflow/nodes/` 中创建新节点文件
2. 继承 `WorkflowNode` 基类
3. 实现 `node_id`、`node_name`、`execute` 方法
4. 在 `graph.py` 中注册节点

示例：

```python
# app/core/workflow/nodes/my_node.py
from app.core.workflow.nodes.base import WorkflowNode
from app.core.workflow.state import WorkflowState

class MyNode(WorkflowNode):
    @property
    def node_id(self) -> str:
        return "my_node"
    
    @property
    def node_name(self) -> str:
        return "我的节点"
    
    def execute(self, state: WorkflowState) -> WorkflowState:
        # 实现节点逻辑
        return {"current_node": self.node_id}
```

### 修改工作流图

在 `app/core/workflow/graph.py` 中修改：

```python
def build_diagnosis_workflow(holmes_service: Any = None) -> StateGraph:
    workflow = StateGraph(WorkflowState)
    
    # 添加新节点
    my_node = MyNode()
    workflow.add_node("my_node", my_node.execute)
    
    # 修改边
    workflow.add_edge("layer", "my_node")
    workflow.add_edge("my_node", "conclusion")
    
    return workflow.compile()
```

## 故障排查

### 1. 工作流未启用

**现象**：仍然使用原有的 agentic loop 模式

**解决**：检查环境变量 `USE_WORKFLOW` 是否设置为 `true`

### 2. 导入错误

**现象**：`ImportError: cannot import name 'WorkflowExecutor'`

**解决**：
```bash
pip install langgraph
```

### 3. 节点执行失败

**现象**：事件中包含 `error` 类型

**解决**：查看日志，检查节点实现是否有异常

## 下一步计划

1. **增强节点2**：集成 HolmesGPT 工具调用，采集真实证据
2. **增强节点3**：增加 LLM 辅助推理（当规则不确定时）
3. **完善节点1**：增加 LLM 辅助定层（当规则不确定时）
4. **添加条件分支**：根据证据完整度决定是否跳过某些节点
5. **性能优化**：并行执行、缓存等
6. **人工干预**：支持在关键节点暂停等待用户确认

## 参考

- [LangGraph 文档](https://langchain-ai.github.io/langgraph/)
- [项目架构文档](docs/ARCHITECTURE.md)
- [工作流设计计划](.cursor/plans/分阶段工作流调研_ae756b9c.plan.md)
