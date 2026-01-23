# K8s-SRE Agent 项目指南

> 本文档是项目开发的"北极星"，所有开发、迭代、增强必须严格遵照此文档执行。
> 
> **版本**: 1.2.0 | **更新日期**: 2026-01-23 | **状态**: Phase 1-3 已完成

---

## 📑 目录

1. [项目概述](#1-项目概述)
2. [当前架构](#2-当前架构)
3. [核心模块功能](#3-核心模块功能)
4. [现有问题与挑战](#4-现有问题与挑战)
5. [未来需求：L0-L4 五个典型案例](#5-未来需求l0-l4-五个典型案例)
6. [技术方案：确定性 AIOps 增强](#6-技术方案确定性-aiops-增强)
7. [实施路线图](#7-实施路线图)
8. [参考资料与业界最佳实践](#8-参考资料与业界最佳实践)

---

## 1. 项目概述

### 1.1 项目定位

**K8s-SRE Agent** 是基于 [HolmesGPT](https://github.com/robusta-dev/holmesgpt) 的智能 Kubernetes 运维诊断 Agent。核心定位：

```
用户自然语言提问 → AI 自动调用工具采集证据 → 分层定位 → 输出结构化诊断报告
```

### 1.2 核心价值主张

| 能力 | 说明 |
|------|------|
| 🏗️ **分层诊断** | 基于 L0-L4 五层架构模型，从底层向上逐层排查 |
| 🔍 **证据驱动** | 每个结论必须有明确的证据来源（工具输出、指标、日志） |
| 📚 **Runbook 知识库** | 19+ 内置故障诊断手册，AI 自动参考 |
| 🛠️ **智能修复** | 识别根因后可自动执行安全的修复操作 |
| 🔌 **MCP 扩展** | 支持 Helm、Prometheus、Elasticsearch 等外部工具集成 |

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

## 2. 当前架构

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
│  ┌─────────────┬─────────────┬─────────────┬─────────────┐              │
│  │ /ask        │ /health     │ /tools      │ /runbooks   │              │
│  │ (主查询)    │ (健康检查)  │ (工具列表)  │ (知识库)    │              │
│  └─────────────┴─────────────┴─────────────┴─────────────┘              │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       核心服务层 (HolmesService)                         │
│  ┌────────────────────────────────────────────────────────────────┐     │
│  │  SYSTEM_PROMPT (分层诊断模型 L0-L4) + Runbooks (知识库 RAG)    │     │
│  └────────────────────────────────────────────────────────────────┘     │
│                                  │                                       │
│                                  ▼                                       │
│  ┌────────────────────────────────────────────────────────────────┐     │
│  │               HolmesGPT (LLM + Tool Calling)                   │     │
│  │  - 理解用户意图                                                 │     │
│  │  - 迭代调用工具采集证据                                         │     │
│  │  - 基于证据推理并生成报告                                       │     │
│  └────────────────────────────────────────────────────────────────┘     │
│                                  │                                       │
│                                  ▼                                       │
│  ┌────────────────────────────────────────────────────────────────┐     │
│  │            确定性规则引擎 (Soft Intercept) [新增]               │     │
│  │  - 对 tool_result 做规则匹配                                    │     │
│  │  - 输出 deterministic_decision 事件                            │     │
│  │  - 附加"机器判定"到最终报告（不阻断 LLM 输出）                  │     │
│  └────────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
            ┌─────────────────────┼─────────────────────┬─────────────────┐
            ▼                     ▼                     ▼                 ▼
      ┌──────────┐         ┌──────────┐         ┌──────────┐       ┌──────────┐
      │ kubectl  │         │Prometheus│         │  Helm    │       │   Bash   │
      │  核心    │         │  指标    │         │ (MCP)    │       │  命令    │
      └──────────┘         └──────────┘         └──────────┘       └──────────┘
```

### 2.2 数据流（SSE 模式）

```
1. 用户发送请求: POST /ask?q=xxx&format=sse
2. API 层接收，调用 HolmesService.execute_query_stream()
3. 构建 system_prompt + runbooks + user_prompt
4. HolmesGPT.call_stream() 开始迭代
   │
   ├── [事件: run_start] → 通知客户端诊断开始
   │
   ├── [事件: tool_start] → AI 决定调用某工具
   ├── [事件: tool_result] → 工具返回结果（可能被截断 → artifact_id）
   │
   ├── [事件: ai_message / ai_reasoning] → AI 思考过程
   │
   ├── [事件: iteration_end] → 一轮迭代结束（token/耗时统计）
   │   └── (重复直到 AI 给出最终答案或达到 max_steps)
   │
   ├── [事件: deterministic_decision] → 规则引擎判定结果 [新增]
   │
   ├── [事件: final] → 最终答案（保证输出）
   │
   └── [事件: run_end] → 诊断结束
```

### 2.3 项目结构

```
robusta/
├── app/
│   ├── api/
│   │   └── routes.py              # FastAPI 路由定义
│   ├── core/
│   │   ├── service.py             # HolmesService（核心编排）
│   │   ├── prompts.py             # SYSTEM_PROMPT（分层诊断模型）
│   │   ├── runbook.py             # Runbook 加载与合并
│   │   ├── paths.py               # 路径工具
│   │   ├── environment.py         # 环境检测
│   │   ├── holmes/                # Holmes 相关模块
│   │   │   ├── event_mapper.py    # 事件映射（含软拦截集成点）
│   │   │   ├── event_schema.py    # 事件 schema 工具
│   │   │   ├── query_stream.py    # 流式查询逻辑
│   │   │   ├── artifacts.py       # 大输出存储
│   │   │   └── ...
│   │   ├── skills/                # 确定性技能层 [新增]
│   │   │   ├── __init__.py
│   │   │   └── rules_engine.py    # 规则引擎（软拦截）
│   │   └── mcp/                   # MCP 管理
│   └── main.py                    # 应用入口
├── deploy/
│   ├── k8s-simple.yaml            # Deployment + Service
│   ├── rbac.yaml                  # ServiceAccount + ClusterRole
│   ├── configmap/
│   │   ├── config.yaml            # 应用配置
│   │   └── runbooks.yaml          # Runbook 知识库 ConfigMap
│   └── secrets/
│       └── core.yaml              # API Key 等敏感信息
├── test/
│   ├── e2e/                       # 端到端测试（kind 故障注入）
│   │   ├── manifests/             # 故障场景 YAML
│   │   ├── scripts/               # 注入脚本
│   │   ├── run_all.sh             # 一键执行
│   │   └── validate.sh            # 验收脚本
│   └── ...
├── guide/
│   └── guide.md                   # 本文档
├── Dockerfile
├── Makefile
├── VERSION
└── requirements.txt
```

---

## 3. 核心模块功能

### 3.1 HolmesService (`app/core/service.py`)

**职责**：全局服务单例，负责 HolmesGPT 的初始化、配置加载、查询执行。

| 方法 | 功能 |
|------|------|
| `initialize()` | 加载配置、创建 AI 实例、合并 Runbooks |
| `execute_query()` | 同步执行查询 |
| `execute_query_stream()` | 流式执行查询（SSE/Text） |
| `get_tools_info()` | 获取可用工具列表 |
| `get_tools_detail()` | 获取工具详情（含 schema） |
| `health_check()` | 健康检查 |

### 3.2 SYSTEM_PROMPT (`app/core/prompts.py`)

**职责**：定义 AI 的角色、行为准则、诊断流程、输出规范。

**核心内容**：
- 角色定义：K8s-SRE Agent
- 方法论：L0-L4 分层诊断模型
- 诊断流程：提取实体 → 初步定层 → 收集证据 → 定位根因
- 输出模板：查询类、诊断类（强制证据链表格）
- 安全限制：禁止危险命令
- 行为准则：无证据不结论

### 3.3 Skills 模块 (`app/core/skills/`)

**职责**：在 LLM 输出之外，提供确定性规则判定（软拦截）。

**设计原则**：
1. **高内聚低耦合**：每个文件职责单一，模块间通过数据模型交互
2. **不阻断**：永不抛异常、不阻塞 `final` 事件
3. **不覆盖**：只附加判定结果到最终报告，不替换 LLM 输出
4. **可扩展**：新增场景只需添加配置，无需修改核心逻辑

**模块结构**：

```
app/core/skills/
├── __init__.py     # 统一对外接口
├── models.py       # 数据模型（Layer, Confidence, DeterministicDecision 等）
├── evidence.py     # 证据规格定义与提取器（EvidenceSpec, EvidenceExtractor）
├── rules.py        # 声明式规则定义（Rule, RULES）
├── engine.py       # 规则引擎（RulesEngine）
├── gate.py         # 证据门禁（EvidenceGate）
└── formatter.py    # 输出格式化器（DecisionFormatter）
```

**数据流**：

```
tool_text → detect_scenario → evaluate_evidence → match_rule → calculate_confidence → apply_gate → format
```

**核心数据模型**：

```python
@dataclass
class DeterministicDecision:
    layer: Layer                    # L0/L1/L2/L3/L4（枚举）
    scenario: str                   # 原子异常场景名
    category: str                   # 分类标签
    confidence: Confidence          # 高/中/低（枚举）
    confidence_score: float         # 量化分数 [0, 1]
    matched_rules: List[str]        # 命中的规则
    collected_evidence: List[str]   # 已采集证据
    missing_evidence: List[str]     # 缺失证据
    critical_missing: List[str]     # 关键缺失（触发降级）
    next_steps: List[str]           # 建议补证/下一步
    evidence_refs: List[str]        # 引用的 tool_result 事件
    facts: List[Dict]               # 结构化事实
```

**置信度计算**：

```python
# 算法：基础置信度 - 缺失证据权重 - Critical 额外惩罚
score = rule.base_confidence
for item in evidence_items:
    if not item.collected:
        score -= item.weight
        if item.level == EvidenceLevel.CRITICAL:
            score -= 0.1  # Critical 额外惩罚

# 转换为等级：>= 0.8 高，>= 0.5 中，< 0.5 低
```

**当前覆盖场景**：
- L0-DiskFull: 日志文件占满磁盘 (ENOSPC / disk > 95%)
- L1-KubeletCert: Kubelet 证书异常导致 Node NotReady
- L2-OOMKilled: OOMKilled (Exit Code 137)
- L3-DNSLatency: DNS 查询延迟 (dns_lookup_seconds p95 >= 0.45s)
- L4-Dependency503: 依赖服务固定返回 503

### 3.4 Event Mapper (`app/core/holmes/event_mapper.py`)

**职责**：将 Holmes StreamEvents 映射为统一内部事件 schema，并集成软拦截。

**软拦截集成点**（在 `final` 事件发出前）：

```python
decision = evaluate_deterministic_decision(question, internal_events)
if decision:
    yield emit("deterministic_decision", decision.to_dict())
    final_content += format_decision_markdown(decision)
```

### 3.5 Runbook 知识库 (`deploy/configmap/runbooks.yaml`)

**职责**：为 AI 提供结构化故障诊断知识。

**Runbook 类型**：
- **知识型 (knowledge)**：提供诊断知识和参考，可灵活运用
- **流程型 (procedure)**：包含明确操作步骤，严格按流程执行

**当前 Runbook 数量**：19+ 手册，覆盖 L0-L4 各层典型场景

---

## 4. 现有问题与挑战

### 4.1 核心痛点

| 问题 | 表现 | 影响 |
|------|------|------|
| **LLM 输出"似是而非"** | 结论模糊、缺乏明确因果链 | 运维人员无法直接信任和执行 |
| **证据采集不完整** | LLM 可能遗漏关键工具调用 | 导致置信度降低、误诊 |
| **缺乏确定性保障** | 纯依赖 LLM 推理，无规则兜底 | 同一问题可能得到不同诊断 |
| **输出格式不稳定** | 有时不遵守模板、用"总结"替代 | 自动化消费困难 |
| **根因分析深度不足** | 停留在现象层，未追溯到根本原因 | 难以做到"治本" |

### 4.2 业界参考：确定性 AIOps 的核心挑战

根据 2025-2026 业界研究：

1. **Causal vs Correlation**：传统 APM 依赖相关性，易误诊；因果推理（Causal AI）正成为主流
2. **Evidence Gating**：缺乏"证据门禁"机制，无法阻止证据不足时输出低置信结论
3. **Deterministic Guardrails**：需要在 LLM 外部建立"确定性护栏"，对概率性推理做兜底
4. **Multi-hop Tracing**：复杂系统需要多跳因果链追溯（A → B → C → Root Cause）

---

## 5. 未来需求：L0-L4 五个典型案例

### 5.1 目标场景定义

| 层级 | 原子异常场景 | 故障注入方法 | 核心识别特征 | 预期修复动作 |
|------|-------------|-------------|-------------|-------------|
| **L0** | 日志文件占满磁盘 | `fallocate` 创建大文件 或 `emptyDir.sizeLimit` | `node_disk_utilization > 95%` 或 `ENOSPC` | 清理指定路径大文件 |
| **L1** | Kubelet 证书失效模拟 | `mv` 移动证书文件 | Node `NotReady` + 证书错误日志 (x509) | 还原证书并重启 Kubelet |
| **L2** | OOMKilled (内存超限) | 运行内存泄漏脚本 | `Exit Code 137` + `OOMKilled` 事件 | 临时调高 Pod 内存 Limit |
| **L3** | CoreDNS 网络延迟注入 | `tc` 注入 500ms 延迟 | `dns_lookup_duration` 激增 (p95 >= 0.45s) | 移除 `tc` 延迟规则 |
| **L4** | 依赖服务固定返回 503 | 修改 Mock 服务返回码 | 应用 5xx 激增 + 依赖因果关联 | 滚动更新/重启依赖服务 |

### 5.2 目标效果

对于每个典型案例，系统应能：

1. **准确识别**：判定正确的层级和场景分类
2. **完整采证**：自动调用所有必需的工具/命令
3. **强根因分析**：输出清晰的因果链（A → B → C → Root Cause）
4. **高置信度**：在证据充分时输出"高"置信度；证据不足时明确标注并建议补采
5. **可执行建议**：给出具体、可操作的修复命令
6. **格式稳定**：严格遵守输出模板

### 5.3 验收标准

每个场景必须通过以下验收：

```
✅ 层级判定正确（L0/L1/L2/L3/L4）
✅ 场景分类正确（DiskFull/KubeletCertInvalid/OOMKilled/DNSLatency/Dependency503）
✅ 证据链完整（所有必需证据项已采集）
✅ 置信度合理（证据充分=高，缺失=中/低）
✅ 根因表述清晰（非"似是而非"）
✅ 修复建议可执行
```

---

## 6. 技术方案：确定性 AIOps 增强

### 6.1 方案总览

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         增强后的诊断流程                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. 用户提问                                                              │
│       │                                                                   │
│       ▼                                                                   │
│  2. LLM 理解意图 + 参考 Runbook                                          │
│       │                                                                   │
│       ▼                                                                   │
│  3. [证据规划] 确定必须采集的证据清单 (Evidence Plan)                     │
│       │                                                                   │
│       ▼                                                                   │
│  4. LLM 调用工具 → 采集原始数据                                          │
│       │                                                                   │
│       ▼                                                                   │
│  5. [Facts 提取] 将原始输出结构化为 JSON Facts                           │
│       │                                                                   │
│       ▼                                                                   │
│  6. [规则判定] Rules Engine 对 Facts 做 if/else 分型                     │
│       │                                                                   │
│       ├── 命中规则 → 输出 DeterministicDecision                          │
│       │                                                                   │
│       └── 证据不足 → 标记 missing_evidence + 建议补采                    │
│               │                                                           │
│               ▼                                                           │
│  7. [Evidence Gate] 若缺失关键证据，强制降级置信度                        │
│       │                                                                   │
│       ▼                                                                   │
│  8. LLM 生成最终报告（结合 deterministic 判定）                          │
│       │                                                                   │
│       ▼                                                                   │
│  9. 输出：final 报告 + deterministic appendix                            │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 6.2 核心增强模块

#### 6.2.1 证据规划器 (Evidence Planner)

**目标**：为每个场景定义"必备证据清单"，确保不遗漏关键信息。

**设计**：

```python
# 示例：L2 OOMKilled 场景的证据规划
EVIDENCE_PLANS = {
    "L2-OOMKilled": {
        "required": [
            {
                "id": "pod_status",
                "description": "Pod 状态（containerStatuses.lastState.terminated）",
                "tool": "kubectl_get_by_name",
                "params": {"resource": "pod", "output": "json"},
                "extract": "$.status.containerStatuses[*].lastState.terminated"
            },
            {
                "id": "exit_code",
                "description": "Exit Code（应为 137）",
                "extract_from": "pod_status",
                "rule": "exitCode == 137"
            },
            {
                "id": "previous_logs",
                "description": "崩溃前日志",
                "tool": "run_bash_command",
                "params": {"command": "kubectl logs --previous --tail=200 {pod_name}"}
            },
            {
                "id": "resource_limits",
                "description": "容器资源限制配置",
                "tool": "kubectl_get_by_name",
                "params": {"resource": "pod", "output": "yaml"},
                "extract": "$.spec.containers[*].resources.limits.memory"
            }
        ],
        "optional": [
            {
                "id": "node_memory",
                "description": "节点内存状态",
                "tool": "prometheus_query",
                "params": {"query": "node_memory_MemAvailable_bytes{node='{node}'} / node_memory_MemTotal_bytes{node='{node}'}"}
            }
        ]
    }
}
```

#### 6.2.2 Facts 提取器 (Facts Extractor)

**目标**：将工具原始输出转化为结构化 JSON，便于规则引擎处理。

**设计**：

```python
# 示例：从 kubectl get pod -o json 提取 Facts
def extract_pod_facts(raw_json: dict) -> dict:
    """提取 Pod 状态相关的 Facts"""
    facts = {
        "pod_name": raw_json.get("metadata", {}).get("name"),
        "namespace": raw_json.get("metadata", {}).get("namespace"),
        "phase": raw_json.get("status", {}).get("phase"),
        "containers": []
    }
    
    for cs in raw_json.get("status", {}).get("containerStatuses", []):
        container_fact = {
            "name": cs.get("name"),
            "ready": cs.get("ready"),
            "restart_count": cs.get("restartCount", 0),
            "state": {},
            "last_state": {}
        }
        
        # 提取 terminated 状态
        if "terminated" in cs.get("lastState", {}):
            term = cs["lastState"]["terminated"]
            container_fact["last_state"] = {
                "type": "terminated",
                "exit_code": term.get("exitCode"),
                "reason": term.get("reason"),
                "message": term.get("message", "")[:200]
            }
        
        facts["containers"].append(container_fact)
    
    return facts
```

#### 6.2.3 规则引擎增强 (Rules Engine v2)

**目标**：更严格的规则匹配 + 置信度量化 + 缺证据强制降级。

**增强设计**：

```python
# 规则定义（声明式）
RULES = {
    "R-L2-OOM-1": {
        "layer": "L2",
        "scenario": "OOMKilled",
        "conditions": [
            {"fact": "containers[*].last_state.reason", "op": "contains", "value": "OOMKilled"},
            # OR
            {"fact": "containers[*].last_state.exit_code", "op": "eq", "value": 137}
        ],
        "condition_logic": "OR",
        "confidence_base": 0.9,
        "evidence_requirements": [
            {"id": "exit_code", "weight": 0.3, "description": "Exit Code 137"},
            {"id": "previous_logs", "weight": 0.2, "description": "崩溃前日志"},
            {"id": "resource_limits", "weight": 0.3, "description": "Memory Limit 配置"},
            {"id": "oom_message", "weight": 0.2, "description": "OOMKilled 事件/消息"}
        ]
    }
}

# 置信度计算
def calculate_confidence(rule, collected_evidence: List[str]) -> Tuple[str, float]:
    """
    计算置信度：
    - 所有 required 证据都有 → 基础置信度
    - 缺失 N 个证据 → 每个扣除对应 weight
    - 置信度 < 0.5 → "低"
    - 置信度 0.5-0.8 → "中"
    - 置信度 > 0.8 → "高"
    """
    base = rule["confidence_base"]
    for req in rule["evidence_requirements"]:
        if req["id"] not in collected_evidence:
            base -= req["weight"]
    
    if base < 0.5:
        return "低", base
    elif base < 0.8:
        return "中", base
    else:
        return "高", base
```

#### 6.2.4 证据门禁 (Evidence Gate)

**目标**：当关键证据缺失时，强制降级置信度并提示补采。

**设计**：

```python
def apply_evidence_gate(decision: DeterministicDecision, facts: dict) -> DeterministicDecision:
    """
    证据门禁：
    - 若 missing_evidence 包含任何 critical 级别证据 → 置信度强制降为"低"
    - 生成明确的补采命令
    """
    critical_missing = [e for e in decision.missing_evidence if e.startswith("[Critical]")]
    
    if critical_missing:
        decision.confidence = "低"
        decision.next_steps.insert(0, "⚠️ 关键证据缺失，请先执行以下命令补采后重新诊断：")
        # 生成具体补采命令...
    
    return decision
```

### 6.3 Runbook 增强：决策型模板

每个典型场景的 Runbook 需重构为以下结构：

```markdown
# L2-OOMKilled (内存超限)

## Required Evidence Checklist
| # | 证据项 | 级别 | 采集命令 | 预期输出 |
|---|--------|------|----------|----------|
| E1 | Pod 退出原因 | Critical | `kubectl describe pod {name}` | "OOMKilled" in lastState |
| E2 | Exit Code | Critical | `kubectl get pod -o json` | exitCode = 137 |
| E3 | 崩溃前日志 | Important | `kubectl logs --previous --tail=200` | 应用内存使用痕迹 |
| E4 | Memory Limit | Critical | `kubectl get pod -o yaml` | resources.limits.memory |
| E5 | 节点内存状态 | Optional | Prometheus query | node_memory_available |

## Collection Plan
1. 首先执行 E1、E2 确认是否为 OOMKilled
2. 若确认，执行 E3 获取崩溃前日志（判断是泄漏还是峰值）
3. 执行 E4 获取当前配置的 memory limit
4. 可选：E5 确认节点是否也有内存压力

## Decision Rules
```
IF E1.lastState.reason == "OOMKilled" OR E2.exitCode == 137:
    THEN scenario = "OOMKilled"
    
    IF E4.memory_limit < 512Mi:
        THEN root_cause = "Memory limit 配置过小"
    ELIF E3.logs contains "out of memory" OR "allocation failed":
        THEN root_cause = "应用内存泄漏或请求量激增"
    ELSE:
        THEN root_cause = "待进一步分析日志确认内存消耗来源"
```

## Root Cause Analysis
因果链：
```
应用内存使用超过 limit → 触发 cgroup OOM Killer → 容器被 Kill (exitCode=137)
  └── 可能原因：
      ├── limit 设置过小（与实际需求不匹配）
      ├── 应用存在内存泄漏（GC 不及时、缓存无限增长）
      └── 流量激增导致内存峰值超限
```

## Remediation
### 临时措施（需审批）
- 调高 memory limit：`kubectl patch deploy {name} -p '{"spec":{"template":{"spec":{"containers":[{"name":"{container}","resources":{"limits":{"memory":"1Gi"}}}]}}}}'`

### 根本措施
- 分析 E3 日志确定内存消耗来源
- 若为泄漏：修复代码后重新发布
- 若为峰值：考虑 HPA 或增加副本数
```

### 6.4 输出模板增强

最终报告应包含以下部分：

```markdown
## 📍 问题定位
- **层级**: L2 - 工作负载层
- **分类**: OOMKilled
- **置信度**: 高 (0.92)

## 🔍 现象描述
Pod `nginx-xxx` 在 namespace `default` 中反复重启，状态 CrashLoopBackOff

## 🕵️ 证据链
| # | 证据来源 | 原始数据 | 支持的结论 |
|---|----------|----------|------------|
| E1 | kubectl describe pod | lastState.reason=OOMKilled | 确认是 OOM 导致退出 |
| E2 | kubectl get pod -o json | exitCode=137 | 137 = SIGKILL（OOM） |
| E3 | kubectl logs --previous | "Cannot allocate memory" | 应用侧确认内存分配失败 |
| E4 | kubectl get pod -o yaml | limits.memory=512Mi | 当前配置的内存上限 |

## 🎯 根因结论
**结论**: 基于证据 E1、E2、E3、E4，Pod 因内存使用超过 limit (512Mi) 被 OOM Killer 终止。
**因果链**: 应用内存使用 > 512Mi → cgroup OOM → exitCode 137

## 🛠️ 修复建议
1. **临时措施**（需审批）: 调高 memory limit 到 1Gi
   ```bash
   kubectl patch deploy nginx -p '{"spec":{"template":{"spec":{"containers":[{"name":"nginx","resources":{"limits":{"memory":"1Gi"}}}]}}}}'
   ```
2. **根本措施**: 分析日志确定内存消耗来源，修复泄漏或配置合理 limit

---

## 🧩 机器判定（Deterministic，软拦截）
- **层级**: L2
- **原子异常场景**: OOMKilled (内存超限)
- **分类**: OOMKilled
- **置信度**: 高
- **命中规则**:
  - R-L2-OOM-1: terminated.reason=OOMKilled OR exitCode=137
- **证据完整性**: ✅ 所有 Critical 证据已采集
- **引用事件**: tool_result#3, tool_result#5, tool_result#7
```

---

## 7. 实施路线图

### Phase 1：规则引擎增强 ✅ 已完成

**目标**：完善 5 个典型场景的规则覆盖

| 任务 | 状态 | 说明 |
|------|------|------|
| L0-DiskFull 规则 | ✅ 已完成 | 关键词匹配 + df 解析 + 值提取 |
| L1-KubeletCert 规则 | ✅ 已完成 | Node NotReady + x509/certificate 关键词 |
| L2-OOMKilled 规则 | ✅ 已完成 | exitCode=137 + OOMKilled + 正则提取 |
| L3-DNSLatency 规则 | ✅ 已完成 | dns_lookup_seconds 提取 + p95 阈值判定 |
| L4-Dependency503 规则 | ✅ 已完成 | upstream 503 + 5xx 关键词 |
| 置信度量化 | ✅ 已完成 | 基础分 - 缺失权重 - Critical 惩罚 |
| 证据门禁 | ✅ 已完成 | 缺失 Critical 证据强制降为"低" |

### Phase 2：证据规划与 Facts 提取 ✅ 已完成

**目标**：为每个场景定义标准化证据采集流程

| 任务 | 状态 | 说明 |
|------|------|------|
| EvidenceSpec 数据结构 | ✅ 已完成 | `evidence.py` - 声明式证据规格 |
| EvidenceExtractor 框架 | ✅ 已完成 | 关键词 + 正则 + 值提取 |
| 5 场景 Evidence Plan | ✅ 已完成 | `EVIDENCE_SPECS` 配置 |
| 与 event_mapper 集成 | ✅ 已完成 | 自动从 tool_result 提取证据 |

### Phase 3：Runbook 重构 ✅ 已完成

**目标**：将所有 Runbook 重构为决策型模板

| 任务 | 状态 | 说明 |
|------|------|------|
| 增强版模板定义 | ✅ 已完成 | 6 大模块：识别特征/证据清单/取证流程/判定规则/根因模板/修复方案 |
| L0-DiskFull Runbook | ✅ 已完成 | 触发关键词 + 5 项证据 + 5 条规则 |
| L1-KubeletCert Runbook | ✅ 已完成 | 触发关键词 + 4 项证据 + 4 条规则 |
| L2-OOMKilled Runbook | ✅ 已完成 | 触发关键词 + 5 项证据 + 3 条规则 + 原因分型 |
| L3-DNSLatency Runbook | ✅ 已完成 | 触发关键词 + 4 项证据 + 4 条规则 |
| L4-Dependency503 Runbook | ✅ 已完成 | 触发关键词 + 4 项证据 + 3 条规则 |

### Phase 4：E2E 测试与验收 🔄 进行中

**目标**：建立自动化验收流程

| 任务 | 状态 | 说明 |
|------|------|------|
| Kind 测试框架 | ✅ 已完成 | test/e2e/ 目录 |
| 5 场景故障注入 | ✅ 已完成 | L0/L1/L2/L3/L4 manifests |
| Skills 单元测试 | ✅ 已完成 | test/unit/test_skills.py - 7 项测试全通过 |
| 自动化验收脚本 | ✅ 已完成 | test/e2e/test_scenarios.sh |
| CI/CD 集成 | 📋 待开始 | GitHub Actions |

### Phase 5：高级功能（远期）

| 任务 | 说明 |
|------|------|
| Causal Graph 构建 | 基于 PyRCA/DoWhy 构建因果图 |
| 多跳因果追溯 | A → B → C 自动追溯 |
| 异常检测集成 | 与 Prometheus Alertmanager 联动 |
| 自学习规则 | 基于历史诊断反馈优化规则 |

---

## 8. 参考资料与业界最佳实践

### 8.1 核心参考

1. **HolmesGPT** - CNCF Sandbox 项目，本项目底层引擎
   - [GitHub](https://github.com/robusta-dev/holmesgpt)
   - [CNCF Blog: Agentic troubleshooting built for the cloud native era](https://www.cncf.io/blog/2026/01/07/holmesgpt-agentic-troubleshooting-built-for-the-cloud-native-era/)

2. **Causal AI for RCA** - IBM Instana 的因果推理方案
   - [arXiv: Causal AI-based Root Cause Identification](https://arxiv.org/abs/2502.18240)
   - 核心观点：因果 > 相关性；需要接近实时的问题定位

3. **ProRCA** - 因果 Python 库
   - [arXiv: ProRCA: A Causal Python Package](https://arxiv.org/abs/2503.01475)
   - 特点：多跳因果链追溯、基于 DoWhy

4. **Deterministic AI Guardrails** - 2026 监管趋势
   - [Medium: Deterministic AI Infrastructure and 2026 Global Regulatory Landscape](https://medium.com/@devdollzai/analysis-of-deterministic-ai-infrastructure-and-the-2026-global-regulatory-landscape)
   - 核心观点：概率性 AI 需要确定性护栏；合规要求确定性可解释

5. **OpenRCA** - LLM RCA 基准
   - [OpenReview: Can Large Language Models Locate the Root Cause](https://openreview.net/forum?id=M4qNIzQYpd)
   - 发现：当前 LLM 在复杂 RCA 任务上表现有限（Claude 3.5 仅 11.34%）

### 8.2 业界最佳实践总结

| 原则 | 说明 | 本项目应用 |
|------|------|------------|
| **Causation over Correlation** | 因果推理优于相关性分析 | 规则引擎显式定义因果链 |
| **Evidence Gating** | 证据不足时不给出高置信结论 | Evidence Gate 强制降级 |
| **Deterministic Guardrails** | 在概率性 AI 外部建立确定性兜底 | Rules Engine 软拦截 |
| **Structured Facts** | 原始数据结构化后再推理 | Facts Extractor 模块 |
| **Explainability** | 每个结论可追溯到具体证据 | 证据链表格、引用事件 |
| **Layered Diagnosis** | 分层逐级排查 | L0-L4 五层模型 |

### 8.3 设计哲学

```
╔════════════════════════════════════════════════════════════════════════╗
║                                                                        ║
║   LLM 是"指挥官"，不是"士兵"                                          ║
║                                                                        ║
║   - LLM 负责：理解意图、规划任务、生成报告                             ║
║   - 确定性模块负责：证据采集、规则判定、证据门禁                       ║
║                                                                        ║
║   软拦截 = 不阻断 + 不覆盖 + 提供参考                                  ║
║                                                                        ║
║   - 永远让 LLM 输出完整报告                                            ║
║   - 在报告后附加机器判定结果                                           ║
║   - 当证据不足时提示，但不阻止输出                                     ║
║                                                                        ║
╚════════════════════════════════════════════════════════════════════════╝
```

---

## 附录

### A. 修改记录

| 日期 | 版本 | 变更内容 | 作者 |
|------|------|----------|------|
| 2026-01-22 | 1.0.0 | 初始版本 | AI |

### B. 术语表

| 术语 | 说明 |
|------|------|
| RCA | Root Cause Analysis，根因分析 |
| MCP | Model Context Protocol，模型上下文协议（工具扩展） |
| SSE | Server-Sent Events，服务端推送事件 |
| Runbook | 故障诊断手册/操作手册 |
| Facts | 结构化的证据数据 |
| Evidence Gate | 证据门禁，缺失关键证据时触发 |
| Soft Intercept | 软拦截，不阻断主流程的辅助判定 |

### C. 待审查问题

> 请用户审查以下问题并提供反馈：

1. **5 个典型场景的优先级**：是否有某些场景需要优先完善？
2. **置信度阈值**：高/中/低的分界线（0.8/0.5）是否合适？
3. **证据门禁策略**：缺失 Critical 证据时是否应强制降级为"低"置信度？
4. **输出格式**：当前模板是否满足运维人员阅读需求？
5. **远期功能**：Causal Graph / 多跳追溯 / 自学习规则的优先级如何排序？

# 人工干预准则

## rules
你的所有代码必须满足优秀的设计风格，高内聚低耦合，方便未来扩展，可读性高。
并且代码一定是正确没有重大bug的。

保持文件与架构的高效有用的前提下，尽量简洁与不复杂。