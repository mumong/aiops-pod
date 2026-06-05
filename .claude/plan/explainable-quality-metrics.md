# 📋 实施计划：质量指标可解释化 + 可量化 + 可配置

## 任务类型
- [x] 后端 (→ Claude + Codex 协作)

## 背景分析

### 现状问题

1. **根因置信度**（executor.py:524-611）：4层回退提取 + 硬编码保底 0.8/0.85，本质是"猜数字"
2. **证据完整率**（metrics.py:182-186）：简单 `collected/planned` 计数比，`EvidenceItem.weight` 字段存在但从未参与计算
3. **配置**：阈值仅支持环境变量，评分规则全部硬编码
4. **可解释性**：只输出一个百分比，用户无法理解"85% 是怎么来的"

### Codex 发现的额外问题（交叉验证确认）

5. **双轨不一致**：`evidence_collector.py:634` 已有按 weight 的加权完整度算法，但 `metrics.py` 没复用
6. **体系分叉**：`metrics_extractor.py:212` legacy 模式有独立的置信度逻辑，与 workflow 模式不统一
7. **runbook threshold bug**：`metrics.py:234` 的 `runbook_coverage.threshold` 误用了 evidence threshold
8. **prompt 引导偏高**：prompts.py 中"至少 0.8"的指令会系统性抬高 LLM 自评分，与去保底矛盾
9. **阈值展示不一致**：output_formatter 文案写 `>80%`，主阈值默认是 `>90%`

### 已有但未利用的数据

- `EvidenceItem.weight`（默认 0.2）和 `EvidenceLevel`（CRITICAL/IMPORTANT/SUPPLEMENTARY）
- `DeterministicDecision.collected_evidence` / `missing_evidence` / `critical_missing`
- `DeterministicDecision.causal_chain`
- `evidence_collector.py` 中已有的加权完整度算法
- `state["thinking_events"]` 中的工具调用记录

---

## 技术方案（Claude + Codex 共识）

### 核心设计：多维度加权评分 + 惩罚项

```
最终置信度 = max(0, Σ(维度得分 × 维度权重) - Σ(惩罚项))
```

#### 1. 根因置信度 — 5 维度加权评分（Codex 校准后权重）

| 维度 | 权重(默认) | 评分规则 | 数据来源 |
|------|-----------|----------|----------|
| evidence_strength | 0.35 | 加权证据完整率（复用 EvidenceLevel 权重） | evidence_items |
| causal_chain | 0.25 | 因果链完整性：完整链=1.0, 部分=0.5, 无=0.0；需绑定证据引用 | causal_chain + evidence refs |
| tool_coverage | 0.15 | 关键探针覆盖率（非简单成功率，按关键工具是否调用） | tool_results |
| runbook_match | 0.15 | Runbook 匹配质量（匹配=1.0, 未匹配=0.0） | runbook_matched |
| llm_self_score | 0.10 | LLM 自评分数（从 rca_analysis 提取，保留现有正则） | rca_analysis |

#### 2. 惩罚项（替代硬编码保底）

| 惩罚 | 扣分 | 触发条件 |
|------|------|----------|
| critical_missing | -0.15/项（封顶 -0.45） | DeterministicDecision.critical_missing 非空 |
| fallback_applied | -0.05 | 置信度来源走了回退路径（非 deterministic_decision） |

**关键决策**：删除 executor.py 中的 0.8/0.85 硬保底，用惩罚项 + 维度加权替代。仅保留技术兜底（所有维度都无数据时 fallback=0.5），并在 breakdown 中标注 `fallback_applied=true`。

#### 3. 证据完整率 — 加权计算（复用已有算法）

复用 `evidence_collector.py` 中已有的加权逻辑，统一到 metrics 层：

```
加权完整率 = Σ(已采集证据的权重) / Σ(所有计划证据的权重)
```

默认权重（可配置）：
| EvidenceLevel | 默认权重 |
|---------------|---------|
| CRITICAL | 1.0 |
| IMPORTANT | 0.6 |
| SUPPLEMENTARY | 0.3 |

额外输出 `critical_coverage`：CRITICAL 级别证据的独立覆盖率。

#### 4. 配置化

在 `config.yaml` 新增 `metrics` 配置块：

```yaml
metrics:
  thresholds:
    mttr_seconds: 600
    rca_confidence: 0.8
    evidence_completeness: 0.9

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

  penalties:
    critical_missing: 0.15    # 每项关键证据缺失扣分
    critical_missing_cap: 0.45 # 封顶
    fallback_applied: 0.05    # 回退路径扣分

  evidence_level_weights:
    CRITICAL: 1.0
    IMPORTANT: 0.6
    SUPPLEMENTARY: 0.3
```

优先级：环境变量 > config.yaml > 代码默认值

#### 5. 评分明细输出

```
根因置信度: 82%
  ├─ 证据强度: 90% (权重 35%) → 贡献 31.5%
  ├─ 因果链: 100% (权重 25%) → 贡献 25.0%
  ├─ 工具覆盖: 80% (权重 15%) → 贡献 12.0%
  ├─ Runbook匹配: 100% (权重 15%) → 贡献 15.0%
  ├─ LLM自评: 85% (权重 10%) → 贡献 8.5%
  ├─ 惩罚: critical_missing×1 = -15%
  └─ 最终: 82% (加权92% - 惩罚10%)

证据完整率: 87% (加权)
  ├─ CRITICAL: 2/2 (权重 1.0) → 100%
  ├─ IMPORTANT: 3/4 (权重 0.6) → 75%
  └─ SUPPLEMENTARY: 1/2 (权重 0.3) → 50%
```

---

## 实施步骤

### Step 1: 新增 `app/core/workflow/quality_scorer.py` — 评分引擎

创建独立的评分模块：

```python
# 核心接口
class ConfidenceDimension:
    name: str; weight: float; score: float; detail: str

class Penalty:
    name: str; value: float; reason: str

class QualityScorer:
    def __init__(self, config: dict): ...
    def score_confidence(self, state, metrics) -> tuple[float, list[ConfidenceDimension], list[Penalty]]: ...
    def score_evidence_completeness(self, evidence_items) -> tuple[float, dict]: ...
```

- 预期产物：`quality_scorer.py`（~150 行）

### Step 2: 修改 `metrics.py` — 扩展数据结构 + 配置加载

- 新增 `confidence_breakdown: List[Dict]` 和 `penalties: List[Dict]` 字段
- 新增 `evidence_breakdown: Dict` 字段
- 从 config.yaml 加载 `metrics` 配置块
- 修改 `format_metrics_block()` 输出评分明细
- 修复 `runbook_coverage.threshold` bug（L234）
- 预期产物：修改 ~60 行

### Step 3: 修改 `executor.py` — 替换硬编码评分逻辑

- 删除 executor.py:524-611 的 4 层回退 + 保底逻辑
- 替换为调用 `QualityScorer.score_confidence()` 和 `score_evidence_completeness()`
- 将评分明细存入 metrics
- 预期产物：修改 ~50 行（净减少代码）

### Step 4: 修改 `config.yaml` + `deploy/configmap/config.yaml`

- 两份配置同步新增 `metrics` 块
- 在 `config_loader.py` 的 `_excluded_keys` 中添加 `"metrics"`
- 预期产物：各增加 ~25 行配置

### Step 5: 统一 legacy 模式（metrics_extractor.py）

- 让 legacy 模式也调用 `QualityScorer`，消除体系分叉
- 预期产物：修改 ~20 行

### Step 6: 修复一致性问题

- 修复 output_formatter 阈值展示不一致
- 修复 runbook_coverage.threshold 误用
- 预期产物：修改 ~10 行

---

## 关键文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `app/core/workflow/quality_scorer.py` | 新增 | 评分引擎（核心） |
| `app/core/workflow/metrics.py` | 修改 | 扩展数据结构 + 配置 + 输出 + 修复 bug |
| `app/core/workflow/executor.py:500-615` | 修改 | 替换硬编码评分 |
| `app/core/holmes/config_loader.py` | 修改 | `_excluded_keys` 添加 `"metrics"` |
| `app/core/holmes/metrics_extractor.py` | 修改 | 统一调用 QualityScorer |
| `app/core/workflow/output_formatter.py` | 修改 | 修复阈值展示 |
| `config/config.yaml` | 修改 | 新增 `metrics` 配置块 |
| `deploy/configmap/config.yaml` | 修改 | 同步新增 `metrics` 配置块 |

## 风险与缓解

| 风险 | 缓解措施 |
|------|----------|
| 去保底后分数可能偏低，用户不适应 | 惩罚项有封顶；技术兜底 0.5 兜住极端情况 |
| LLM 自评受 prompt 引导偏高 | 权重降至 10%（Codex 建议）；后续可考虑去除 prompt 中的保底引导 |
| evidence_strength 与 tool_coverage 重叠 | evidence_strength 衡量"证据质量"，tool_coverage 衡量"关键探针是否调用"，定义边界清晰 |
| legacy 模式改动影响非工作流路径 | 统一调用 QualityScorer，输入输出接口不变 |
| config.yaml 缺少 metrics 块 | 所有配置有代码默认值，缺失时回退 |

## 不改动的文件（明确排除）

- `prompts.py` — 用户自维护，不动（Codex 建议的 prompt 引导问题留作后续优化）
- 工作流节点逻辑 — 不改流程，只改指标计算

## SESSION_ID（供 /ccg:execute 使用）
- CODEX_SESSION: 019d2871-5b54-7f93-8dd8-909e920294ec
- GEMINI_SESSION: N/A（纯后端任务）
