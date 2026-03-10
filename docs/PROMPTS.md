# 提示词参考

所有 LLM 提示词统一管理在 `app/core/prompts.py`。

---

## 提示词总览

| 常量名 | 使用场景 | 使用者 | 说明 |
|--------|----------|--------|------|
| `SYSTEM_PROMPT` | 默认模式（HolmesGPT） | `service.py` → HolmesGPT | 单集群诊断的核心提示词，定义 AI 角色和行为 |
| `LAYER_CLASSIFIER_PROMPT` | 工作流节点 1 | `layer_classifier.py` | 问题定位：判断 QUERY/L0-L4 层级 |
| `EVIDENCE_COLLECTOR_PROMPT` | 工作流节点 2 | `evidence_collector.py` | 证据采集：调用工具获取数据 |
| `ROOT_CAUSE_ANALYZER_PROMPT` | 工作流节点 3 | `root_cause_analyzer.py` | 根因分析：构建因果链 |
| `CONCLUSION_FORMATTER_PROMPT` | 工作流节点 4 | `conclusion_formatter.py` | 报告生成：格式化最终输出 |
| `FEDERATION_AGENT_PROMPT` | A2A 联邦查询 | `federation/agent.py` | 多集群智能路由提示词 |
| `FEDERATION_SYNTHESIS_PROMPT` | 联邦查询 v1 | `federation/aggregator.py` | 多集群报告合成提示词 |

---

## 提示词详细说明

### 1. `SYSTEM_PROMPT` — 核心系统提示词

**文件位置**：`app/core/prompts.py` 第 23 行

**使用场景**：`USE_WORKFLOW=false` 时，作为 HolmesGPT agentic loop 的 System Prompt。

**核心内容**：
- 定义 AI 角色为 K8s-SRE Agent
- 意图识别：区分"直接回答"（数据查询）和"故障诊断"两条路径
- 环境限制（如禁用 `kubectl top`）
- L0-L4 五层诊断框架
- 输出格式模板（查询类 / 诊断类）

**修改场景**：调整默认模式下 AI 的行为准则、输出格式、安全限制。

---

### 2. `LAYER_CLASSIFIER_PROMPT` — 问题定位

**文件位置**：`app/core/prompts.py` 第 150 行

**使用场景**：工作流模式节点 1，判断用户问题属于哪个层级。

**核心逻辑**：
- 输入：用户的自然语言问题
- 输出：JSON 格式 `{layer, confidence, reasoning, key_entities, possible_scenarios}`
- 层级分类：
  - `QUERY`：数据查询（CPU 使用率、Pod 列表、状态概览等）
  - `L0`：基础设施（磁盘、内存、内核）
  - `L1`：集群与节点（kubelet、NotReady、证书）
  - `L2`：工作负载（OOM、CrashLoop、镜像拉取）
  - `L3`：服务与网络（DNS、Ingress、NetworkPolicy）
  - `L4`：应用（503、依赖服务、配置错误）

**修改场景**：调整层级分类标准、增加新层级、优化分类准确率。

---

### 3. `EVIDENCE_COLLECTOR_PROMPT` — 证据采集

**文件位置**：`app/core/prompts.py` 第 237 行

**使用场景**：工作流模式节点 2，根据定层结果调用工具采集证据。

**双路径行为**：
- **QUERY 模式**：直接采集数据（如 PromQL 查询），不使用 Runbook，不做故障模板采集
- **L0-L4 模式**：按故障模板多维采集（现象确认、资源状态、日志/事件、配置、依赖）

**输出**：JSON 格式 `{evidence_summary, evidence_details[], tools_used[], gaps[]}`

**修改场景**：调整各层级的默认采集策略、增加 PromQL 示例、修改采集模板。

---

### 4. `ROOT_CAUSE_ANALYZER_PROMPT` — 根因分析

**文件位置**：`app/core/prompts.py` 第 380 行

**使用场景**：工作流模式节点 3，基于采集的证据进行根因分析。

**双路径行为**：
- **QUERY 模式**：仅汇总数据，不做因果链分析，不调用工具（`tool_executor=None`）
- **L0-L4 模式**：构建因果链、评估根因置信度、给出修复建议

**输出**：JSON 格式 `{root_cause, confidence, category, causal_chain[], evidence_support[]}`

**修改场景**：调整根因分析深度、因果链推理逻辑、置信度评估标准。

---

### 5. `CONCLUSION_FORMATTER_PROMPT` — 报告生成

**文件位置**：`app/core/prompts.py` 第 519 行

**使用场景**：工作流模式节点 4，生成最终用户可读报告。

**双路径行为**：
- **QUERY 模式**：使用数据表格模板（`📊 查询结果`），简洁直接
- **L0-L4 模式**：使用完整诊断报告模板（现象/证据/根因/修复/验证）

**修改场景**：调整报告格式、输出模板、详略程度。

---

### 6. `FEDERATION_AGENT_PROMPT` — A2A 智能路由

**文件位置**：`app/core/prompts.py` 第 734 行

**使用场景**：`/federation/ask/v2` 端点，控制主 Agent 如何路由查询到子集群。

**核心内容**：
- 可用工具：`list_clusters()`、`query_cluster(cluster_name, question, ...)`
- 路由策略：理解用户意图，决定查询哪些集群、发送什么问题
- 输出格式：结构化的多集群汇总报告

**修改场景**：调整路由策略、输出格式、跨集群对比逻辑。

---

### 7. `FEDERATION_SYNTHESIS_PROMPT` — 多集群合成

**使用场景**：`/federation/ask` 端点（v1），汇总所有子集群的诊断报告。

**修改场景**：调整多集群报告的合成逻辑。

---

## 提示词映射关系

```
用户请求
  │
  ├── USE_WORKFLOW=false ──→ SYSTEM_PROMPT (HolmesGPT)
  │
  ├── USE_WORKFLOW=true  ──→ 工作流四节点
  │       ├── LAYER_CLASSIFIER_PROMPT    → 定层（QUERY/L0-L4）
  │       ├── EVIDENCE_COLLECTOR_PROMPT  → 采证
  │       ├── ROOT_CAUSE_ANALYZER_PROMPT → 根因
  │       └── CONCLUSION_FORMATTER_PROMPT → 报告
  │
  ├── /federation/ask    ──→ FEDERATION_SYNTHESIS_PROMPT
  │
  └── /federation/ask/v2 ──→ FEDERATION_AGENT_PROMPT
```

---

## 修改提示词后的生效方式

1. 修改 `app/core/prompts.py` 中的对应常量
2. 重新构建并部署：
```bash
make build push deploy-master    # 或 deploy-slave
```

提示词编译进镜像中，修改后需要重新构建。不支持运行时热更新。
