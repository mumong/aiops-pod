# 性能分析与优化记录

## 基准测试数据（问题："查询本机cpu使用率"）

| 实验 | 耗时 | LLM迭代 | 工具调用 | 分析 |
|------|------|---------|----------|------|
| 纯 DeepSeek API | **2.9s** | 1 | 0 | 基准线 |
| DeepSeek + 20 tools | **3.2s** | 1 | 1 | 工具数不影响 |
| 模拟 2 轮 tool calling | **7.0s** | 2 | 2 | ~3.5s/轮 |
| **HolmesGPT 框架** | **87.0s** | **13** | **20** | 核心瓶颈 |
| **工作流 4 节点** | **3.5min** | ~25+ | ~30+ | 4x agentic loop |

## 瓶颈分析

### 关键洞察

1. **工具 schema 数量对延迟影响很小**（3.2s vs 2.9s）
2. **每轮 LLM 调用 ~5-7s 是固定成本，减少轮数是最有效的优化**
3. QUERY 模式（简单查询）走了完整 4 节点工作流，浪费 evidence + rca 两个 agentic loop
4. TodoWrite 占了 5 轮迭代，纯浪费
5. 很多 bash 命令被安全验证拒绝，又浪费迭代

### K8s 日志验证

一次"查询CPU使用率"的完整流程：
1. LLM 创建了 4 个 TodoWrite 任务
2. 每个任务都是：TodoWrite更新状态 → 调工具取数据 → TodoWrite更新状态
3. **TodoWrite 占了 5 轮迭代，纯浪费**
4. 一个简单查询做了 **13 轮 LLM 调用**，每轮 ~5-7s

## 优化方案

### Step 1: QUERY 模式走简化工作流（预计 -70%）

**修改文件**: `app/core/workflow/graph.py`

在 `build_diagnosis_workflow` 中添加条件路由：
- layer 节点判断意图后，如果 `layer == QUERY`，跳过 evidence + rca，直接到 conclusion
- 如果 `layer == L0-L4`，走完整 4 节点诊断流程

```python
def _route_after_layer(state):
    if state.get("layer") == Layer.QUERY:
        return "conclusion"  # 跳过 evidence + rca
    return "evidence"  # 走完整诊断流程

workflow.add_conditional_edges("layer", _route_after_layer, {
    "conclusion": "conclusion",
    "evidence": "evidence",
})
```

**效果**: QUERY 模式从 4 次 agentic loop → 2 次，耗时减少 ~60-70%

### Step 2: 节点级 max_steps 控制（预计 -30%）

**修改文件**: `app/core/service.py` + 各节点文件

新增 `_call_with_stream_limited(messages, max_steps)` 方法，各节点使用合理的 max_steps：

| 节点 | 场景 | max_steps | 原因 |
|------|------|-----------|------|
| layer | 所有 | 3 | 定层只需 1 轮 LLM |
| evidence | 诊断 | 10 | 需要调工具采集 |
| rca | 诊断 | 8 | 需要调工具补充分析 |
| conclusion | 所有 | N/A | 使用 litellm 直接调用，无 agentic loop |

**效果**: 限制每节点最大迭代，避免 LLM 发散（13 轮 → 最多 10 轮）

### Step 3: 修复耗时统计

**修改文件**: 各节点文件

使用 `response.iterations` 和 `response.duration_ms` 更新 metrics，替代硬编码 `llm_calls=1`。

## 修改清单

| 文件 | 说明 |
|------|------|
| `app/core/workflow/graph.py` | QUERY 条件路由（跳过 evidence+rca） |
| `app/core/service.py` | 新增 `_call_with_stream_limited()` |
| `app/core/workflow/nodes/layer_classifier.py` | max_steps=3, 修复统计 |
| `app/core/workflow/nodes/evidence_collector.py` | max_steps=10, 修复统计，移除硬编码 llm_calls |
| `app/core/workflow/nodes/root_cause_analyzer.py` | max_steps=8, 修复统计 |

## 预期效果

| 场景 | 优化前 | 优化后 |
|------|--------|--------|
| 简单查询（CPU使用率） QUERY模式 | 3.5min (4节点x13轮) | **30-60s** (2节点x3轮) |
| 复杂诊断（集群有什么问题） | 6.3min (4节点) | **2-3min** (4节点x受限轮数) |
| 默认模式 | 87s (13轮) | **30-40s** (max_steps=10) |

## 验证方法

```bash
# 简单查询（预期 30-60s）
curl -G "http://10.2.0.48:30800/ask" --data-urlencode "q=查询本机cpu使用率"

# 复杂诊断（预期 2-3min）
curl -G "http://10.2.0.48:30800/ask" --data-urlencode "q=我的集群有什么问题"
```
