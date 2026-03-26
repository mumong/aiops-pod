# 质量指标体系说明

> 本文档说明 AIOps Copilot 的诊断质量指标如何计算、如何判断达标、如何配置调优。

---

## 指标总览

每次诊断完成后，系统自动输出以下质量指标：

| 指标 | 含义 | 默认阈值 | 判定方式 |
|------|------|----------|----------|
| MTTR | 从接收问题到输出报告的总耗时 | < 10 分钟 | 直接计时 |
| 根因置信度 | 诊断结论的可信程度 | >= 80% | 5 维度加权评分 + 惩罚项 |
| 证据完整率 | 计划采集的证据中实际采集到的比例 | > 90% | 按证据级别加权计算 |
| Runbook 覆盖 | 是否匹配到相关故障手册 | 匹配即达标 | 文本匹配检测 |

---

## 根因置信度：5 维度加权评分

### 计算公式

```
最终置信度 = max(0, 加权总分 - 惩罚总分)
加权总分 = Σ(维度得分 × 维度权重) / Σ(维度权重)
```

### 评分维度

| 维度 | 默认权重 | 数据来源 | 评分规则 |
|------|---------|----------|----------|
| evidence_strength | 35% | `evidence_items` 列表 | 按证据级别加权的完整率（见下方） |
| causal_chain | 25% | `causal_chain` + 证据引用 | 完整因果链=1.0，部分=0.5，无=0.0 |
| tool_coverage | 15% | `tool_results` | 工具调用成功数 / 总调用数 |
| runbook_match | 15% | `runbook_matched` | 匹配到 Runbook=1.0，未匹配=0.0 |
| llm_self_score | 10% | LLM 输出中的置信度声明 | 从 rca_analysis / conclusion 文本提取 |

权重总和为 1.0。evidence_strength 权重最高，因为有工具证据支撑的诊断最可靠。llm_self_score 权重最低，因为 LLM 自评受 prompt 引导，容易偏高。

### 惩罚项

惩罚项用于替代硬编码保底，让分数更诚实：

| 惩罚 | 默认扣分 | 触发条件 | 封顶 |
|------|---------|----------|------|
| critical_missing | 每项 -15% | `DeterministicDecision.critical_missing` 非空 | -45% |
| fallback_applied | -5% | 置信度来源走了回退路径（非结构化数据提取） | — |

### 输出示例

```
📊 置信度评分明细

  ├─ 加权证据完整率: 90% (权重 35%) → 贡献 31.5%
  ├─ 因果链完整性: 100% (权重 25%) → 贡献 25.0%
  ├─ 关键探针覆盖率: 80% (权重 15%) → 贡献 12.0%
  ├─ Runbook 匹配质量: 100% (权重 15%) → 贡献 15.0%
  ├─ LLM 自评分数: 85% (权重 10%) → 贡献 8.5%
  └─ 惩罚 critical_missing: -15% (1 项关键证据缺失: memory_usage)
```

### LLM 自评分数提取优先级

1. `deterministic_decision.confidence_score`（结构化输出，最可靠）
2. `rca_analysis` JSON 中的 `confidence` 字段
3. 文本正则匹配（`置信度: 85%` 等格式）
4. `layer_confidence`（问题定位阶段的置信度）
5. 兜底值 0.5（标记 `fallback_applied=true`）

---

## 证据完整率：加权计算

### 计算公式

```
加权完整率 = Σ(已采集证据的级别权重) / Σ(所有计划证据的级别权重)
```

### 证据级别权重

| EvidenceLevel | 默认权重 | 说明 |
|---------------|---------|------|
| CRITICAL | 1.0 | 关键证据，缺失严重影响诊断 |
| IMPORTANT | 0.6 | 重要证据，缺失影响准确性 |
| SUPPLEMENTARY | 0.3 | 补充证据，缺失影响不大 |

### 设计意图

缺失一个 CRITICAL 证据比缺失一个 SUPPLEMENTARY 证据影响大得多。例如：

- 缺 1 个 SUPPLEMENTARY（3 CRITICAL 全采集）→ 完整率 ≈ 90%
- 缺 1 个 CRITICAL（其他全采集）→ 完整率 ≈ 47%

### 输出示例

```
📊 证据完整率明细

  ├─ CRITICAL: 2/2 (权重 1.0) → 100%
  ├─ IMPORTANT: 3/4 (权重 0.6) → 75%
  └─ SUPPLEMENTARY: 1/2 (权重 0.3) → 50%
```

---

## 配置方式

### 优先级

```
环境变量 > config.yaml metrics 块 > 代码默认值
```

### config.yaml 配置

在 `config/config.yaml`（本地）或 `deploy/configmap/config.yaml`（K8s）中：

```yaml
metrics:
  # 达标阈值
  thresholds:
    mttr_seconds: 600          # MTTR 阈值（秒），默认 10 分钟
    rca_confidence: 0.8        # 根因置信度阈值，默认 80%
    evidence_completeness: 0.9 # 证据完整率阈值，默认 90%

  # 置信度评分维度权重（总和应为 1.0）
  confidence_dimensions:
    evidence_strength:
      weight: 0.35
      description: "加权证据完整率"
    causal_chain:
      weight: 0.25
      description: "因果链完整性"
    tool_coverage:
      weight: 0.15
      description: "关键探针覆盖率"
    runbook_match:
      weight: 0.15
      description: "Runbook 匹配质量"
    llm_self_score:
      weight: 0.10
      description: "LLM 自评分数"

  # 惩罚项
  penalties:
    critical_missing: 0.15     # 每项关键证据缺失扣分
    critical_missing_cap: 0.45 # 封顶
    fallback_applied: 0.05     # 回退路径扣分

  # 证据级别权重
  evidence_level_weights:
    CRITICAL: 1.0
    IMPORTANT: 0.6
    SUPPLEMENTARY: 0.3
```

### 环境变量覆盖（仅阈值）

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `METRICS_MTTR_THRESHOLD` | `600` | MTTR 阈值（秒） |
| `METRICS_RCA_CONFIDENCE_THRESHOLD` | `0.8` | 根因置信度阈值 |
| `METRICS_EVIDENCE_THRESHOLD` | `0.9` | 证据完整率阈值 |

---

## 调优指南

### 想要提高置信度分数？

| 方向 | 改什么 | 怎么改 |
|------|--------|--------|
| 增加证据采集深度 | `config.yaml` | `workflow.max_steps.evidence` 调大（默认 10） |
| 增加根因分析深度 | `config.yaml` | `workflow.max_steps.rca` 调大（默认 8） |
| 完善 Runbook 覆盖 | `knowledge_base/runbooks/` | 新增故障场景的 Runbook 文件 + 更新 `catalog.json` |
| 降低达标门槛 | `config.yaml` | `metrics.thresholds.rca_confidence` 调低 |

### 想要调整评分权重？

直接修改 `config.yaml` 的 `metrics.confidence_dimensions`，无需改代码。例如，如果你认为 Runbook 匹配不重要：

```yaml
confidence_dimensions:
  evidence_strength:
    weight: 0.40    # 提高
  runbook_match:
    weight: 0.05    # 降低
```

### 想要修改评分逻辑？

| 需求 | 改哪里 |
|------|--------|
| 新增评分维度 | `app/core/workflow/quality_scorer.py` → `score_confidence()` |
| 修改惩罚规则 | `app/core/workflow/quality_scorer.py` → 惩罚项部分 |
| 修改证据级别权重计算 | `app/core/workflow/quality_scorer.py` → `score_evidence_completeness()` |
| 修改输出格式 | `app/core/workflow/metrics.py` → `format_metrics_block()` |
| 修改 LLM 自评提取正则 | `app/core/workflow/quality_scorer.py` → `_extract_llm_self_score()` |

不需要改 `prompts.py`。评分完全基于客观数据，不依赖 prompt 引导。

---

## 代码架构

```
quality_scorer.py          ← 评分引擎（核心）
  ├─ QualityScorer         ← 评分器，从 config 加载权重
  ├─ ConfidenceDimension   ← 单个维度的得分
  ├─ Penalty               ← 惩罚项
  └─ ConfidenceResult      ← 评分结果（含明细）

metrics.py                 ← 指标数据结构 + 格式化输出
  ├─ WorkflowMetrics       ← 含 confidence_breakdown / evidence_breakdown
  ├─ load_metrics_config() ← 从 config.yaml 加载阈值
  └─ format_metrics_block()← 输出质量指标表 + 评分明细

executor.py                ← 调用 QualityScorer，存入 metrics
metrics_extractor.py       ← Legacy 模式（非工作流）的指标提取
```
