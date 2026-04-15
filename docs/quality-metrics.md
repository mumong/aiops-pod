# 质量指标采集原理与测试方法

> 本文档说明 AIOps Copilot 工作流的 4 个核心质量指标：采集原理、代码位置、测试提取方式。

---

## 指标总览

| 指标 | 含义 | 阈值 | 产出节点 |
|------|------|------|----------|
| 证据完整率 | 计划采集的证据中实际采集到的比例 | >= 80% | evidence |
| MTTR | 从接收问题到输出报告的总耗时 | < 900s | 全流程 |
| Runbook 覆盖 | 是否匹配到与问题相关的故障手册 | >= 80% | layer + rca |
| 层级准确率 | 问题层级判定是否正确 | >= 80% | layer |

---

## 1. 证据完整率 (Evidence Completeness)

### 采集原理

**公式**: `collected / total`

- `total` = evidence_plan 项数 + 额外采集的工具调用数
- `collected` = 其中 `collected=True` 的项数

**代码**: `evidence_collector.py` → `_calculate_completeness()`

**数据流**:

```
LLM 输出 JSON evidence_plan（如 6 项）
    ↓
LLM 通过 AICall agent loop 调用 MCP 工具（记录在 thinking_events）
    ↓
_build_evidence_items_from_thinking() 匹配 plan ↔ 实际工具调用
    ↓
匹配上的 plan 项 → collected=True, source="thinking_match"
未匹配的 plan 项 → collected=False, source="planned"
plan 外的额外工具调用 → collected=True, source="thinking_extra"
    ↓
completeness = collected / total
```

**三种运行模式**:

| 模式 | 条件 | 行为 |
|------|------|------|
| 有 plan + 有工具调用 | LLM 输出了 JSON plan 且调了工具 | 正常匹配，最准确 |
| 无 plan + 有工具调用 | LLM 没输出 JSON 但调了工具 | 从工具调用反向构建，N/N=100% |
| 无 plan + 无工具调用 | LLM 什么都没做 | 回退到 layer 节点的工具调用（source="layer_fallback"） |

**过滤**: TodoWrite 等非证据工具不计入统计（`_NON_EVIDENCE_TOOLS = {"todowrite", "todo_write", "todo"}`）

**输出**:
- `state["evidence_completeness"]`: float (0.0-1.0)
- `state["evidence_analysis"]["collection_summary"]`: 如 `"计划 8 项，实际采集 8 项，未采集 0 项，完整度 100%"`

### 测试提取

`test_accuracy.py` 按优先级提取:

```
优先级1: 性能统计块
  正则: r'证据[：:]\s*(\d+)/(\d+)\s*项.*?完整度[：:]\s*(\d+)%'
  匹配: "证据: 8/8 项, 完整度: 100%"

优先级2: 节点交接数据
  正则: r'evidence_items=(\d+)/(\d+)'
  匹配: "📤 → 下游数据: evidence_items=8/8"

优先级3: collection_summary
  正则: r'计划\s*(\d+)\s*项.*?实际采集\s*(\d+)\s*项'
  匹配: "计划 8 项，实际采集 8 项"
```

### 常见异常

| 现象 | 原因 | 排查 |
|------|------|------|
| 0/0 (0%) | LLM 没输出 plan 也没调工具 | 检查 evidence prompt 和 thinking_events |
| 总是 100% | LLM 没输出 JSON plan，所有工具调用都算 extra | 检查 `_extract_plan_from_thinking()` |
| TodoWrite 膨胀 | 非证据工具被计入 | 已通过 `_NON_EVIDENCE_TOOLS` 过滤 |

---

## 2. MTTR (Mean Time To Resolve)

### 采集原理

**公式**: `end_time - start_time`（秒）

**代码**: `executor.py` + `metrics.py`

```python
# executor.py
total_start = time.time()          # 工作流开始
...各节点依次执行...
elapsed = time.time() - total_start  # 工作流结束

# 各节点独立计时
node_start = time.time()
result = node.execute(state)
node_elapsed = time.time() - node_start
```

**输出格式** (`metrics.py` → `format_stats_block()`):

```
├─ 总耗时: 5.8m
├─ 问题定位: 74.9s (22%) ✅
├─ 证据链采集: 179.4s (52%) ✅
├─ 根因分析: 89.4s (26%) ✅
├─ 汇总总结: 0.0s (0%) ✅
```

百分比以总耗时为分母，各节点加起来 ≈ 100%。

### 测试提取

```
优先级1: 性能统计块
  正则: r'[├└─]+\s*总耗时[：:\s]*([\d.]+)(s|m|h)'
  单位转换: m → ×60, h → ×3600

优先级2: HTTP 请求实际耗时 (wall_clock)
```

---

## 3. Runbook 覆盖率 (Runbook Coverage)

### 采集原理

**三层提取链** (`reporter.py`):

```
来源1: thinking_events 中的 fetch_runbook 工具调用
  → 从 result_preview 提取 .md 文件名
  → 从 result_preview 提取 # 标题
  → 如: "l2-oomkilled.md", "L2 Pod OOMKilled (Exit Code 137)"

来源2: state 文本搜索
  → 在 conclusion + rca_analysis + evidence_analysis 中
  → 正则匹配所有 .md 文件名（排除 README.md 等）

来源3: RCA 节点的 primary_runbooks 字段
  → rca_analysis JSON 中的 "primary_runbooks" 数组
  → 或 state["primary_runbook_id"]
```

**过滤**: 排除 README.md, CLAUDE.md, ARCHITECTURE.md, CHANGELOG.md

**输出**:
- `核心 Runbook`: 最相关的 runbook（来自 primary_runbooks）
- `参考 Runbook`: 所有引用过的 runbook

### 测试提取

```
优先级1: RCA JSON
  正则: r'"primary_runbooks"\s*:\s*\[([^\]]+)\]'
  匹配: "primary_runbooks": ["L2 Pod OOMKilled (Exit Code 137)"]

优先级2: <runbook> 标签
  正则: r'<runbook>\s*#\s+(.+?)(?:\n|$)'
  匹配: <runbook> # L2 Pod OOMKilled ...

优先级3: fetch_runbook 日志
  正则: r'fetch_runbook.*?找到.*?([\w][\w.-]*\.md)'
```

**匹配判定**: 场景定义了 `expected_runbook`（如 `"l2-oomkilled"`），提取到的 runbook 文件名或标题中包含该关键词即为匹配成功。

---

## 4. 层级准确率 (Layer Accuracy)

### 采集原理

**layer 节点两阶段架构** (`layer_classifier.py`):

```
阶段1: AICall.call() — 带工具的 agentic loop
  → kubectl get pods -A（全局扫描）
  → kubectl describe pod（异常 Pod 详情）
  → fetch_runbook（可选）
  → 输出自然语言分析文本

阶段2: AICall.call_simple() — 无工具的结构化提取
  → 输入: 阶段1的分析文本 + 工具输出
  → 使用 LAYER_EXTRACT_PROMPT
  → 输出 JSON: { "layer": "L2", "confidence": 0.95, ... }
```

**回退链**:
1. LLM 两阶段提取 → JSON 中的 `layer` 字段
2. 规则引擎关键词匹配
3. 默认 L2

**五层模型**:

| 层级 | 名称 | 典型特征 |
|------|------|----------|
| L0 | 基础设施层 | Evicted, disk pressure, ENOSPC |
| L1 | 集群节点层 | Node NotReady, kubelet 异常 |
| L2 | 工作负载层 | OOMKilled, CrashLoopBackOff |
| L3 | 服务网络层 | ImagePullBackOff, DNS 失败 |
| L4 | 应用层 | 应用日志报错, 健康检查失败 |

### 测试提取

```
优先级1: 节点交接数据
  正则: r'📤.*?layer=(?:Layer\.)?(L[0-4])'
  匹配: "📤 → 下游数据: layer=Layer.L2"

优先级2: 节点输出
  正则: r'层级[：:\s]*Layer\.(L[0-4])'

优先级3: layer_analysis JSON
  正则: r'layer_analysis=\{.*?"layer":\s*"(L[0-4])"'

优先级4: 频率统计（文本中出现最多的 L0-L4）
```

**匹配判定**: 提取到的层级 == 场景定义的 `expected_layer`

---

## 测试方法

### 运行 E2E 测试

```bash
# 单场景单次
.venv/bin/python test/e2e/test_accuracy.py --scenario l2-oomkilled -n 1

# 单场景多次（统计稳定性）
.venv/bin/python test/e2e/test_accuracy.py --scenario l2-oomkilled -n 5

# 并发测试
.venv/bin/python test/e2e/test_accuracy.py --scenario l2-oomkilled -n 5 -c 5

# 全场景
.venv/bin/python test/e2e/test_accuracy.py --all -n 3
```

### 测试输出

每次测试生成:
- `testreports/<timestamp>/<scenario>/response_N.md` — 完整响应文本
- `testreports/<timestamp>/<scenario>/stats.json` — 聚合统计 JSON

### stats.json 结构

```json
{
  "summary": {
    "total": 5,
    "success": 5,
    "fail": 0
  },
  "quality_metrics": {
    "mttr": {
      "threshold": "< 900s",
      "values": [234.5, 198.3],
      "result_seconds": 216.4,
      "pass": true
    },
    "layer_accuracy": {
      "threshold": ">= 80%",
      "per_scenario": {"l2-oomkilled": {"correct": 5, "total": 5}},
      "result_percent": 100.0,
      "pass": true
    },
    "runbook_coverage": {
      "threshold": ">= 80%",
      "per_scenario": {"l2-oomkilled": {"matched": 5, "total": 5}},
      "result_percent": 100.0,
      "pass": true
    },
    "evidence_completeness": {
      "threshold": ">= 80%",
      "values": [100.0, 91.0],
      "result_percent": 95.5,
      "pass": true
    }
  }
}
```

### 场景配置

测试场景定义在 `test_accuracy.py` 的 `SCENARIOS` 字典中:

```python
SCENARIOS = {
    "l2-oomkilled": {
        "question": "我的集群有什么问题",
        "expected_layer": "L2",
        "expected_runbook": "l2-oomkilled",
        "setup": "deploy/e2e/l2-oomkilled.yaml",  # 测试环境部署
    },
    "l3-imagepull": {
        "question": "我的集群有什么问题",
        "expected_layer": "L3",
        "expected_runbook": "l3-imagepull",
        ...
    }
}
```

---

## 数据流总览

```
用户问题
  ↓
┌─────────────────────────────────────────────────┐
│ layer 节点                                       │
│ 产出: layer(L0-L4), confidence, key_entities     │
│ 指标: 层级准确率                                  │
└─────────────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────────────┐
│ evidence 节点                                    │
│ 产出: evidence_items, evidence_analysis          │
│ 指标: 证据完整率                                  │
└─────────────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────────────┐
│ rca 节点                                         │
│ 产出: root_cause, causal_chain, primary_runbooks │
│ 指标: Runbook 覆盖率                              │
└─────────────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────────────┐
│ conclusion 节点                                   │
│ 产出: 完整诊断报告 (Markdown)                     │
│ 指标: MTTR（整体耗时）                            │
└─────────────────────────────────────────────────┘
```

---

## 关键代码位置

| 要查什么 | 文件 |
|----------|------|
| 证据完整率计算 | `app/core/workflow/nodes/evidence_collector.py` → `_calculate_completeness()` |
| 证据项构建 | `evidence_collector.py` → `_build_evidence_items_from_thinking()` |
| MTTR 计时 | `app/core/workflow/executor.py` → `execute_stream()` |
| 性能统计格式化 | `app/core/workflow/metrics.py` → `format_stats_block()` |
| Runbook 提取 | `app/core/workflow/reporter.py` → 三层提取链 |
| 层级判定 | `app/core/workflow/nodes/layer_classifier.py` → 两阶段架构 |
| 测试指标提取 | `test/e2e/test_accuracy.py` → `extract_*` 系列函数 |
| 测试聚合统计 | `test/e2e/test_accuracy.py` → stats.json 生成 |
