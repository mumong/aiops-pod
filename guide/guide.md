---
# K8s-SRE Agent 项目指南

> 本文档是项目开发的"北极星"，所有开发、迭代、增强必须严格遵照此文档执行。

> **版本**: 2.0.0 | **更新日期**: 2026-01-28 | **状态**: Phase 1-6 已完成

---

## 目录

1. [项目概述](#1-项目概述)
2. [架构总览](#2-架构总览)
3. [核心模块](#3-核心模块)
   - [API 层](#31-api-层)
   - [核心服务层](#32-核心服务层-holmesservice)
   - [工作流系统](#33-工作流系统)
   - [确定性技能层](#34-确定性技能层-skills)
   - [输出处理层](#35-输出处理层)
4. [节点开发指南](#4-节点开发指南)
5. [配置与部署](#5-配置与部署)

---

## 1. 项目概述

### 1.1 项目定位

**K8s-SRE Agent** 是基于 HolmesGPT 的智能 Kubernetes 运维诊断 Agent。核心定位：

```
用户自然语言提问 → AI 自动调用工具采集证据 → 分层定位 → 输出结构化诊断报告
```

### 1.2 核心价值主张

| 能力 | 说明 |
|------|------|
| 🏗️ **分层诊断** | 基于 L0-L4 五层架构模型，从底层向上逐层排查 |
| 🔍 **证据驱动** | 每个结论必须有明确的证据来源（工具输出、指标、日志） |
| 📚 **Runbook 知识库** | 26+ 内置故障诊断手册，AI 自动参考 |
| 🛠️ **智能修复** | 识别根因后可自动执行安全的修复操作 |
| 🔌 **MCP 扩展** | 支持 Helm、Prometheus、Elasticsearch 等外部工具集成 |
| 📊 **确定性保障** | 基于规则的引擎提供可解释的判定结果 |

### 1.3 五层诊断模型

```
┌─────────────────────────────────────────────────────────────────┐
│ L4: 应用层 (Application)                                        │
│     业务逻辑错误、代码异常、配置错误、依赖服务不可用              │
├─────────────────────────────────────────────────────────────────┤
│ L3: 服务与网络层 (Service & Network)                             │
│     Service/Ingress 配置、DNS 解析、NetworkPolicy、跨 Pod 通信   │
├─────────────────────────────────────────────────────────────────┤
│ L2: 工作负载层 (Workload)                                        │
│     Pod 生命周期、容器状态、镜像拉取、探针、资源限制              │
├─────────────────────────────────────────────────────────────────┤
│ L1: 集群与节点层 (Cluster & Node)                                │
│     Node 状态、调度器、kubelet、容器运行时、系统资源              │
├─────────────────────────────────────────────────────────────────┤
│ L0: 基础设施层 (Infrastructure)                                  │
│     磁盘、内存、CPU、网络连通性、内核、文件系统                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. 架构总览

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              用户层                                      │
│         curl /ask?q="Pod 一直重启" (REST API / SSE)                      │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          API 层 (FastAPI)                                │
│  ┌─────────────┬─────────────┬─────────────┬─────────────┬─────────────┐              │
│  │ /ask        │ /health     │ /tools      │ /runbooks   │              │
│  │ (主查询)    │ (健康检查)  │ (工具列表)  │ (知识库)    │              │
│  └─────────────┴─────────────┴─────────────┴─────────────┘              │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       核心服务层 (HolmesService)                         │
│  ┌───────────────────────────────────────────────────────────────────────┐              │
│  │  SYSTEM_PROMPT (分层诊断模型 L0-L4) + Runbooks (知识库 RAG)    │              │
│  └───────────────────────────────────────────────────────────────────────┘              │
│                                  │                                       │
│  ┌───────────────────────────────────────────────────────────────────────┐              │
│  │            HolmesGPT (LLM + Tool Calling)                   │              │
│  │  - 理解用户意图                                              │              │
│  │  - 迭代调用工具采集证据                                         │              │
│  │  - 基于证据推理并生成报告                                       │              │
│  └───────────────────────────────────────────────────────────────────────┘              │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    两种执行模式（可切换）                          │
│  ┌───────────────────────────────────────────────────────────────────────┐              │
│  │  原有模式 │ 工作流模式 │                                   │              │
│  │  - Agentic Tool Calling  │  - LangGraph 分阶段工作流   │              │
│  │  - HolmesGPT 直接驱动     │  - 节点式编排         │              │
│  │  - 不确定，依赖 LLM 推理      │  - 确定性流程控制   │              │
│  └───────────────────────────────────────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 运行模式切换

| 模式 | 启用方式 | 适用场景 | 输出格式 |
|------|----------|----------|----------|
| 原有模式 | `USE_WORKFLOW=false` (默认) | 探索性诊断、灵活分析 | SSE / Text |
| 工作流模式 | `USE_WORKFLOW=true` | 生产环境、确定性流程 | SSE / Text |

### 2.3 数据流（SSE 模式）

```
1. 用户发送请求: POST /ask?q=xxx&format=sse
2. API 层接收，调用 HolmesService.execute_query_stream()
3. 构建 system_prompt + runbooks + user_prompt
4. HolmesGPT.call_stream() 开始迭代
   │
   ├── [事件: run_start] → 通知客户端诊断开始
   ├── [事件: tool_start] → AI 决定调用某工具
   ├── [事件: tool_result] → 工具返回结果（可能被截断 → artifact_id）
   ├── [事件: ai_message] → AI 思考过程
   ├── [事件: iteration_end] → 一轮迭代结束（token/耗时统计）
   ├── [事件: deterministic_decision] → 规则引擎判定结果 [新增]
   ├── [事件: final] → 最终答案（保证输出）
   └── (重复直到 AI 给出最终答案或达到 max_steps)
   │
   └── [事件: run_end] → 诊断结束
```

---

## 3. 核心模块

### 3.1 API 层 (`app/api/`)

| 文件 | 职责 |
|------|------|
| `routes.py` | FastAPI 路由定义，各端点的处理逻辑 |

**主要端点**：

| 端点 | 方法 | 功能 |
|------|------|------|
| `/ask` | GET/POST | 主查询入口，支持 text 和 sse 两种输出格式 |
| `/health` | GET | 健康检查 |
| `/tools` | GET | 可用工具列表 |
| `/tools/detail` | GET | 工具详情（含 schema） |
| `/runbooks` | GET | 可用 Runbooks |
| `/api/v1/mcp/*` | MCP 管理（新增） |

---

### 3.2 核心服务层 (`app/core/`)

| 模块 | 文件 | 职责 |
|------|------|------|
| **服务编排** | `service.py` | HolmesService，全局服务单例，负责初始化、配置加载、查询执行 |
| **提示词管理** | `prompts.py` | SYSTEM_PROMPT（原模式）+ WORKFLOW_PROMPTS（工作流节点）|
| **Runbook 管理** | `runbook.py` | Runbook 加载、合并本地配置 |
| **路径工具** | `paths.py` | 项目根路径、配置文件路径 |
| **环境检测** | `environment.py` | 环境变量检测、日志环境信息 |

### 3.3 Holmes 相关模块 (`app/core/holmes/`)

| 模块 | 文件 | 职责 |
|------|------|------|
| **流式输出** | `streaming.py` | SSE/Text 格式化工具、duration 格式化 |
| **事件映射** | `event_mapper.py` | 将 Holmes StreamEvents 映射为统一内部事件 |
| **事件 Schema** | `event_schema.py` | 事件类型定义工具 |
| **查询流** | `query_stream.py` | execute_query_stream_sse/text，封装 HolmesGPT 调用 |
| **调用封装** | `call_wrapper.py` | call_with_stream，流式调用封装 |
| **自省** | `introspection.py` | 资源加载日志记录 |
| **大输出存储** | `artifacts.py` | 被截断的工具输出存储 |

---

### 3.4 工作流系统 (`app/core/workflow/`)

| 模块 | 文件 | 职责 |
|------|------|------|
| **状态模型** | `state.py` | WorkflowState，节点间共享状态的数据模型 |
| **图构建** | `graph.py` | build_diagnosis_workflow，LangGraph 工作流图 |
| **执行器** | `executor.py` | WorkflowExecutor，执行工作流并发出事件 |
| **指标** | `metrics.py` | WorkflowMetrics，性能与质量指标记录 |
| **节点基类** | `nodes/base.py` | WorkflowNode，节点抽象基类 |

**工作流节点结构**：

```
app/core/workflow/nodes/
├── base.py              # 节点基类
├── layer_classifier.py    # 节点1：问题定位
├── evidence_collector.py # 节点2：证据采集
├── root_cause_analyzer.py # 节点3：根因分析
└── conclusion_formatter.py  # 节点4：汇总总结
```

### 3.5 确定性技能层 (`app/core/skills/`)

| 模块 | 文件 | 职责 |
|------|------|------|
| `__init__.py` | 技能层统一对外接口 |
| `models.py` | 数据模型：Layer, Confidence, EvidenceItem, EvidenceLevel 等 |
| `evidence.py` | 证据规格定义与提取器（EvidenceSpec, EvidenceExtractor） |
| `rules.py` | 明确式规则定义（Rule, RULES） |
| `engine.py` | 规则引擎（RulesEngine） |
| `gate.py` | 证据门禁（EvidenceGate） |
| `formatter.py` | 决策结果格式化（DecisionFormatter） |

### 3.6 输出处理层 (`app/core/log_utils.py`)

| 模块 | 文件 | 职责 |
|------|------|------|
| `log_utils.py` | 日志控制工具：suppress_holmes_logging() |

**设计原则**：
- 低耦合：不依赖具体业务逻辑，只操作日志框架
- 高内聚：功能单一，只处理日志控制
- 易扩展：新的节点都可以使用此上下文管理器

**使用方式**：
```python
from app.core.log_utils import suppress_holmes_logging

# 在调用 LLM 时临时禁用 HolmesGPT 的日志输出
with suppress_holmes_logging():
    response = self.holmes_service.ai.call(messages)
```

---

## 4. 节点开发指南

### 4.1 节点基类 (`nodes/base.py`)

```python
class WorkflowNode:
    """
    工作流节点基类

    所有节点必须继承此类，实现统一的接口规范
    """

    def __init__(self, holmes_service: Any = None, metrics: Any = None, runbook_catalog: Any = None):
        """
        初始化节点

        Args:
            holmes_service: HolmesService 实例（用于 LLM 调用）
            metrics: WorkflowMetrics 实例（用于记录统计）
            runbook_catalog: RunbookCatalog 实例（用于 runbook 匹配）
        """
        self.holmes_service = holmes_service
        self.metrics = metrics
        self.runbook_catalog = runbook_catalog

    @property
    def node_id(self) -> str:
        """节点唯一标识（用于工作流图中的路由）"""
        raise NotImplementedError

    @property
    def node_name(self) -> str:
        """节点显示名称（用于日志和用户输出）"""
        raise NotImplementedError

    def get_required_fields(self) -> List[str]:
        """
        执行此节点所需的 WorkflowState 字段

        子类应重写此方法，声明依赖的字段

        返回值示例：["question", "layer"] 或 ["layer", "evidence_analysis"]
        """
        return []

    def execute(self, state: WorkflowState) -> WorkflowState:
        """
        节点执行逻辑

        Args:
            state: 当前工作流状态

        Returns:
            更新后的工作流状态

        设计原则：
            1. 不要修改原始 state，返回新的字典
            2. 所有修改通过 new_state.update() 添加
            3. 异常处理：捕获异常并添加到 errors 列表
            4. 保持幂等性：多次执行相同输入应产生相同输出
        """
        new_state: WorkflowState = {"current_node": self.node_id}

        try:
            # 节点具体逻辑
            result = self._execute_impl(state)
            new_state.update(result)

        except Exception as e:
            logger.error(f"节点 {self.node_id} 执行失败: {e}", exc_info=True)
            new_state.setdefault("errors", []).append(
                f"节点 {self.node_id} 执行失败: {str(e)}"
            )

        return new_state

    def _execute_impl(self, state: WorkflowState) -> WorkflowState:
        """
        节点具体实现逻辑（子类必须实现）

        子类应在此方法中实现节点的核心业务逻辑
        """
        raise NotImplementedError
```

### 4.2 新增节点标准流程

#### 步骤 1：创建节点文件

在 `app/core/workflow/nodes/` 下创建新节点文件，命名规范：`{功能}_{node}.py`

示例：
- `quick_diagnosis.py` - 快速诊断节点
- `resource_check.py` - 资源检查节点
- `security_scan.py` - 安全扫描节点

#### 步骤 2：实现节点类

```python
"""
节点模板：{功能}_{node}.py
"""

from typing import Any, Dict, List
import logging
from app.core.workflow.nodes.base import WorkflowNode
from app.core.workflow.state import WorkflowState
from app.core.log_utils import suppress_holmes_logging

logger = logging.getLogger(__name__)


class YourNodeNameNode(WorkflowNode):
    """
    节点简短描述

    职责：...
    """

    def __init__(self, holmes_service: Any = None, metrics: Any = None, runbook_catalog: Any = None):
        super().__init__(holmes_service, metrics, runbook_catalog)
        # 添加节点特定的初始化逻辑

    @property
    def node_id(self) -> str:
        """必须与 graph.py 中的节点 ID 一致"""
        return "your_node_id"  # 小写，下划线分隔

    @property
    def node_name(self) -> str:
        """节点显示名称，用于日志输出"""
        return "你的节点名称"

    def get_required_fields(self) -> List[str]:
        """
        声明执行此节点所需的状态字段
        """
        # 示例：["question", "layer", "evidence_analysis"]
        return []

    def execute(self, state: WorkflowState) -> WorkflowState:
        """
        节点核心执行逻辑
        """
        new_state: WorkflowState = {"current_node": self.node_id}

        try:
            result = self._execute_impl(state)
            new_state.update(result)

        except Exception as e:
            logger.error(f"节点 {self.node_id} 执行失败: {e}", exc_info=True)
            new_state.setdefault("errors", []).append(
                f"节点 {self.node_id} 执行失败: {str(e)}"
            )

        return new_state

    def _execute_impl(self, state: WorkflowState) -> WorkflowState:
        """
        节点具体实现逻辑

        在这里实现节点的核心业务逻辑：
        1. 调用 LLM 分析（使用 suppress_holmes_logging()）
        2. 处理工具结果
        3. 构建输出数据
        """
        # 节点具体实现
        return {}
```

#### 步骤 3：定义 Prompt

在 `app/core/prompts.py` 中添加节点的 Prompt：

```python
# 节点 Prompt（添加到 WORKFLOW_PROMPTS 字典末尾）

YOUR_NODE_PROMPT = """
# 角色
你是...

# 输入信息
你将收到...

# 输出要求
请以 JSON 格式输出，包含以下字段：
{
    "field1": "value1",
    "field2": "value2"
}
"""
```

#### 步骤 4：更新图构建 (`graph.py`)

在 `app/core/workflow/graph.py` 的 `build_diagnosis_workflow` 函数中添加新节点：

```python
def build_diagnosis_workflow(holmes_service, metrics, runbook_catalog):
    from app.core.workflow.nodes.layer_classifier import LayerClassifierNode
    from app.core.workflow.nodes.evidence_collector import EvidenceCollectorNode
    from app.core.workflow.nodes.root_cause_analyzer import RootCauseAnalyzerNode
    from app.core.workflow.nodes.conclusion_formatter import ConclusionFormatterNode
    from app.core.workflow.nodes.your_node import YourNodeNameNode  # 新增节点导入

    # 创建各节点实例
    layer_node = LayerClassifierNode(holmes_service, metrics, runbook_catalog)
    evidence_node = EvidenceCollectorNode(holmes_service, metrics, runbook_catalog)
    rca_node = RootCauseAnalyzerNode(holmes_service, metrics, runbook_catalog)
    conclusion_node = ConclusionFormatterNode(holmes_service, metrics, runbook_catalog)
    your_node = YourNodeNameNode(holmes_service, metrics, runbook_catalog)  # 新节点实例

    # 构建工作流图
    workflow = StateGraph(WorkflowState)

    # 添加节点和边
    workflow.add_node("layer", layer_node)
    workflow.add_node("evidence", evidence_node)
    workflow.add_node("rca", rca_node)
    workflow.add_node("conclusion", conclusion_node)
    workflow.add_node("your_node", your_node)  # 添加新节点

    # 定义节点之间的边
    workflow.add_edge("layer", "evidence")
    workflow.add_edge("evidence", "rca")
    workflow.add_edge("rca", "conclusion")

    # 添加新节点的边（根据实际流程）
    # workflow.add_edge("rca", "your_node")

    # 设置起点和终点
    workflow.set_entry_point("layer")
    workflow.set_finish_point("conclusion")

    return workflow
```

#### 步骤 5：更新 Prompt 管理

在 `app/core/prompts.py` 中添加获取函数：

```python
# 在文件末尾添加便捷获取函数

def get_workflow_prompt(node_id: str) -> str:
    """
    获取工作流节点的 Prompt

    Args:
        node_id: 节点标识（如 "layer", "evidence", "your_node"）

    Returns:
        节点对应的 Prompt 字符串
    """
    return WORKFLOW_PROMPTS.get(node_id, "")
```

#### 步骤 6：更新状态模型

如果新节点需要新增状态字段，在 `app/core/workflow/state.py` 的 `WorkflowState` 类型中添加：

```python
# WorkflowState 类型扩展
from typing import TypedDict, List, Optional

class WorkflowState(TypedDict):
    # 现有字段...
    question: str
    layer: Optional[Layer]
    evidence_items: List[EvidenceItem]
    tool_results: List[dict]
    root_cause: Optional[str]
    causal_chain: Optional[dict]
    conclusion: Optional[str]
    errors: List[str]
    warnings: List[str]
    current_node: str

    # 新增字段（根据节点需求添加）
    # your_new_field: Optional[str]  # 示例
```

### 4.3 节点开发最佳实践

| 最佳实践 | 说明 |
|------|------|
| **日志抑制** | 所有 LLM 调用必须使用 `suppress_holmes_logging()` 上下文管理器 |
| **错误处理** | 捕获异常并添加到 state.errors，不要抛出未处理异常 |
| **幂等性** | 相同输入应产生相同输出，便于调试和重试 |
| **Prompt 设计** | 明确指定输出格式（JSON），便于后续节点解析 |
| **状态更新** | 只通过 state.update() 更新，不直接修改传入的 state |
| **指标记录** | 关键操作（LLM 调用、工具调用）需使用 self.metrics.record_xxx() |
| **工具调用** | 如需调用工具，通过 self.holmes_service.ai.tool_executor 获取工具执行器 |

### 4.4 节点间数据传递

工作流节点通过 `WorkflowState` 共享数据：

```python
# 常用状态字段

字段名                类型       | 说明
----------------------|----------|----------
question             | str       | 用户原始问题
layer               | Layer      | 问题定位结果
layer_confidence    | float      | 层级置信度
layer_analysis      | str       | LLM 分析结果（JSON）
evidence_items      | List      | 证据项列表
evidence_completeness | float      | 证据完整度
evidence_analysis   | str       | 证据分析结果（JSON）
root_cause          | str       | 根因结论
causal_chain        | dict       | 因果链
rca_analysis         | str       | 根因分析结果（JSON）
conclusion           | str       | 最终报告
conclusion_formatted | str       | 格式化后的报告
current_node        | str       | 当前执行节点
errors               | List      | 错误列表
warnings             | List      | 警告列表
```

**使用示例**：

```python
# 节点 A 读取前置节点输出的字段
layer = state.get("layer")
layer_analysis = state.get("layer_analysis")

# 节点 A 生成新的字段
new_field_value = self._analyze_something(layer_analysis)

# 节点 A 更新状态
new_state = {
    "current_node": self.node_id,
    "new_field": new_field_value,
    "layer": layer  # 保留原有数据供下游使用
}
return new_state
```

---

## 5. 配置与部署

### 5.1 配置文件位置

| 文件 | 用途 | 说明 |
|------|------|------|
| `deploy/secrets/core.yaml` | 敏感配置 | API Key、工作流开关 |
| `deploy/configmap/config.yaml` | 应用配置 | Prometheus URL、工具集配置 |
| `deploy/configmap/runbooks.yaml` | Runbook 知识库 | 26+ 故障诊断手册 |

### 5.2 关键配置项

**敏感配置 (`deploy/secrets/core.yaml`)**：
```yaml
stringData:
  DEEPSEEK_API_KEY: "sk-xxx"          # DeepSeek API Key
  USE_WORKFLOW: "true"                # 启用工作流模式
```

**应用配置 (`deploy/configmap/config.yaml`)**：
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: aiops-config
data:
  MODEL_NAME: "deepseek-chat"       # 使用的 LLM 模型
  MAX_STEPS: "50"                   # 最大迭代次数
  LOG_LEVEL: "INFO"                 # 日志级别
```

### 5.3 部署方式

```bash
# 1. 构建镜像
docker build -t your-registry/aiops-copilot:latest .

# 2. 推送镜像
docker push your-registry/aiops-copilot:latest

# 3. 应用配置
kubectl apply -f deploy/secrets/core.yaml
kubectl apply -f deploy/configmap/config.yaml
kubectl apply -f deploy/configmap/runbooks.yaml
kubectl apply -f deploy/k8s-simple.yaml

# 4. 验证部署
kubectl get pods -n aiops-e2e
kubectl logs -f deployment/aiops-copilot -n aiops-e2e
```

### 5.4 本地开发

```bash
# 安装依赖
pip install -r requirements.txt

# 启用工作流模式进行测试
export USE_WORKFLOW=true
python app/main.py

# 查看日志
tail -f logs/app.log
```

---

## 附录：设计哲学

```
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                        ║
║   LLM 是"指挥官"，不是"士兵"                                          ║
║                                                                        ║
║   - LLM 负责：理解意图、规划任务、生成报告                             ║
║   - 确定性模块负责：证据采集、规则判定、证据门禁                       ║
║                                                                        ║
║   潯拦截 = 不阻断 + 不覆盖 + 提供参考                                  ║
║                                                                        ║
║   - 不阻断：永不抛异常、不阻塞 `final` 事件                           ║
║   - 不覆盖：只附加判定结果到最终报告，不替换 LLM 输出                   ║
║                                                                        ║
║   - 远远让 LLM 输出完整报告                                            ║
║   - 在报告后附加机器判定结果                                           ║
║   - 当证据不足时提示，但不阻止输出                                     ║
║                                                                        ╚════════════════════════════════════════════════════╝
```

### 修改记录

| 日期 | 版本 | 作者 | 变更内容 |
|------|------|------|----------|
| 2026-01-28 | 2.0.0 | AI | 初始版本：LangGraph 工作流系统上线 |
