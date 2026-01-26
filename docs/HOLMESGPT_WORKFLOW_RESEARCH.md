# HolmesGPT 工作流能力调研报告

## 调研目标

调研 HolmesGPT (robusta-dev/holmesgpt) 框架是否支持工作流搭建，包括：
1. 内置的 workflow/pipeline 机制
2. 事件流（StreamEvents）架构的分阶段处理能力
3. Multi-agent 或 chain 能力
4. 可用的扩展点

---

## 1. 内置 Workflow/Pipeline 机制

### 1.1 Agentic Loop 架构

HolmesGPT 采用 **Agentic Loop（智能体循环）** 架构，而非传统的线性 pipeline：

**核心特点**：
- **任务列表驱动**：将问题分解为多个子任务，逐个执行
- **迭代式精炼**：通过多轮迭代逐步完善假设和结论
- **主动决策**：AI 主动决定需要获取哪些数据
- **上下文关联**：跨数据源检测关联关系（如部署与 Pod 崩溃的关联）

**工作流程**：
```
1. 理解意图 (Understand Intent)
   ↓
2. 创建任务列表 (Create Task List)
   ↓
3. 查询数据源 (Query Data Sources)
   ↓
4. 关联上下文 (Correlate Context)
   ↓
5. 解释并建议修复 (Explain & Suggest Fixes)
```

### 1.2 事件驱动的执行流程

从代码实现来看，HolmesGPT 的执行流程基于事件流：

```python
# app/core/holmes/event_mapper.py
事件序列：
run_start → tool_start → tool_result → ai_message/ai_reasoning 
→ iteration_end → deterministic_decision → final → run_end
```

**关键事件类型**：
- `run_start`: 诊断开始
- `tool_start`: AI 决定调用工具
- `tool_result`: 工具返回结果（可能被截断，存储为 artifact）
- `ai_message` / `ai_reasoning`: AI 思考过程
- `iteration_end`: 一轮迭代结束（包含 token/耗时统计）
- `deterministic_decision`: 规则引擎判定结果（软拦截）
- `final`: 最终答案（保证输出）
- `run_end`: 诊断结束

### 1.3 Runbook 流程支持

HolmesGPT 支持两种类型的 Runbook：

**流程型 Runbook (`type: procedure`)**：
- 包含明确的操作步骤（安装、卸载、升级）
- AI 会根据用户意图选择正确的流程段落执行
- 严格按步骤执行，使用指定工具和参数

**知识型 Runbook (`type: knowledge`)**：
- 提供诊断知识、原理分析、常见场景
- 作为参考资料辅助诊断
- 可灵活运用，结合实际情况选择适用的方法

---

## 2. StreamEvents 架构的分阶段处理能力

### 2.1 事件流架构设计

**核心模块**：`app/core/holmes/event_mapper.py`

```python
def iter_internal_events(
    service: Any,
    question: str,
    system_prompt: str,
    user_prompt: Optional[str],
    msgs: Optional[list],
    run_id: str,
    max_preview_chars: int = 1200,
) -> Generator[Dict, None, None]:
    """
    产生统一内部事件 dict：
      {type, id, run_id, seq, ts_ms, ...payload }
    """
```

**设计特点**：
- **高内聚**：只负责"把 Holmes 事件转成我们的事件"
- **低耦合**：上层可选择 SSE 渲染、文本渲染、WebSocket 等
- **可扩展**：支持 tool 输出裁剪、异常分类、artifact 存储等

### 2.2 分阶段处理能力

**阶段划分**：

1. **初始化阶段** (`initialization`)
   - 加载配置、创建 AI 实例
   - 加载和合并 runbook catalogs
   - 配置工具集和 MCP 服务器

2. **消息构建阶段** (`message_building`)
   - 构建 System Prompt + Runbook catalog + tools 信息
   - 准备初始消息

3. **LLM 迭代阶段** (`llm_iteration`)
   - 多轮迭代执行（最多 `max_steps` 次）
   - 每轮迭代：工具调用 → 结果处理 → AI 推理 → 迭代结束

4. **规则判定阶段** (`deterministic_decision`)
   - 基于工具结果进行确定性规则判定
   - 计算置信度和证据链

5. **最终输出阶段** (`final`)
   - 生成最终答案
   - 附加确定性判定结果

### 2.3 事件拦截与扩展点

**软拦截机制**（在 `event_mapper.py` 中实现）：

```python
# 软拦截：基于 tool_result 等事件做确定性规则判定
try:
    decision = evaluate_deterministic_decision(question, internal_events)
    if decision:
        ev_det = emit("deterministic_decision", decision.to_dict())
        yield ev_det
        final_content = (final_content or "") + format_decision_markdown(decision)
except Exception:
    # 软拦截必须"永远不影响主流程"
    pass
```

**特点**：
- **不阻断**：永不抛异常、不阻塞 `final` 事件
- **不覆盖**：只附加判定结果到最终报告，不替换 LLM 输出
- **可扩展**：新增场景只需添加配置，无需修改核心逻辑

---

## 3. Multi-Agent 或 Chain 能力

### 3.1 架构特点

HolmesGPT **不采用传统的 multi-agent 架构**，而是通过以下方式实现协作：

**1. 工具集（Toolsets）机制**：
- 内置多个工具集：Kubernetes、Prometheus、Logs、Traces、Cloud Provider 等
- 每个工具集提供一组相关工具
- 通过 MCP（Model Context Protocol）集成外部工具

**2. 迭代式任务分解**：
- AI 将复杂问题分解为多个子任务
- 每个子任务独立执行
- 通过上下文累积逐步完善分析

**3. 确定性规则引擎**：
- `app/core/skills/engine.py` 中的 `RulesEngine`
- 在 LLM 输出之外提供确定性规则判定
- 形成"LLM + 规则引擎"的双重验证机制

### 3.2 Chain-like 能力

虽然没有显式的 chain 定义，但通过以下机制实现类似效果：

**1. 事件链**：
```
tool_start → tool_result → ai_message → iteration_end → (循环)
```

**2. 证据链**：
- 规则引擎构建因果链（causal chain）
- 包含：root_cause、trigger、mechanism、manifestation

**3. 分层诊断链**：
- L0: 基础设施层
- L1: 集群与节点层
- L2: 工作负载层
- L3: 服务与网络层
- L4: 应用层

---

## 4. 扩展点分析

### 4.1 自定义工具集（Custom Toolsets）

**位置**：通过 Helm 配置或 YAML 文件定义

**能力**：
- 添加组织特定的工具
- 集成外部监控系统
- 扩展调查能力

**示例**：
```yaml
toolsets:
  - name: custom-grafana
    description: Grafana dashboard analysis
    tools:
      - name: query_dashboard
        command: curl -H "Authorization: Bearer ${GRAFANA_TOKEN}" ...
```

### 4.2 MCP 服务器集成

**位置**：`app/core/mcp/manager.py`

**能力**：
- 通过 MCP 协议集成外部工具
- 支持本地 auto-start（可选）
- 动态发现和注册工具

### 4.3 Runbook 集成

**位置**：`app/core/runbook.py`

**能力**：
- 加载自定义 runbook catalog
- 合并内置和自定义 runbook
- 支持流程型和知识型 runbook

### 4.4 事件映射层扩展

**位置**：`app/core/holmes/event_mapper.py`

**扩展点**：
- Tool 输出裁剪和预处理
- 异常分类和标记
- Artifact 存储策略
- 自定义事件类型

**示例**：
```python
# 在 iter_internal_events 中可以添加：
if et == StreamEvents.TOOL_RESULT:
    # 自定义处理逻辑
    result_str = preprocess_tool_result(result_str)
    # 分类异常
    anomaly_type = classify_anomaly(result_str)
    # 存储 artifact
    artifact_id = store_artifact(result_str)
```

### 4.5 规则引擎扩展

**位置**：`app/core/skills/`

**扩展点**：
- 新增场景检测规则（`rules.py`）
- 自定义证据提取器（`evidence.py`）
- 扩展置信度计算逻辑（`engine.py`）
- 自定义输出格式化（`formatter.py`）

**示例**：
```python
# 在 rules.py 中添加新规则
RULES = [
    Rule(
        scenario="L2-OOMKilled",
        conditions=[...],
        base_confidence=Confidence.HIGH,
        ...
    ),
    # 新增规则
    Rule(
        scenario="L3-CustomIssue",
        conditions=[...],
        ...
    ),
]
```

### 4.6 Prompt 扩展

**位置**：`app/core/prompts.py`

**能力**：
- 自定义 System Prompt
- 修改分层诊断模型
- 调整输出模板和安全规则

### 4.7 服务层扩展

**位置**：`app/core/service.py`

**扩展点**：
- 自定义查询执行流程
- 添加预处理和后处理逻辑
- 集成外部服务

---

## 5. 关键发现总结

### 5.1 工作流支持能力

✅ **支持的工作流特性**：
- ✅ Agentic loop 架构（迭代式任务分解）
- ✅ 事件驱动的分阶段处理
- ✅ Runbook 流程支持
- ✅ 软拦截机制（不阻断主流程）
- ✅ 确定性规则引擎

❌ **不支持的特性**：
- ❌ 显式的 workflow 定义语言（如 YAML workflow）
- ❌ 传统意义上的 multi-agent 架构
- ❌ 显式的 chain 定义（如 LangChain）
- ❌ 工作流可视化编辑器

### 5.2 分阶段处理能力

✅ **强项**：
- 清晰的事件流架构
- 每个阶段都有明确的事件标记
- 支持中间结果存储（artifact）
- 支持迭代统计（token、耗时）

✅ **扩展性**：
- 事件映射层可扩展
- 支持自定义事件类型
- 软拦截机制不阻断主流程

### 5.3 Multi-Agent/Chain 能力

**替代方案**：
- 通过工具集（toolsets）实现功能模块化
- 通过 MCP 协议集成外部 agent
- 通过规则引擎实现确定性验证
- 通过迭代式任务分解实现类似 chain 的效果

### 5.4 扩展点总结

**主要扩展点**：
1. **Custom Toolsets** - 最常用的扩展方式
2. **MCP 服务器集成** - 集成外部工具和 agent
3. **Runbook 集成** - 添加流程型知识
4. **事件映射层** - 自定义事件处理逻辑
5. **规则引擎** - 添加确定性判定规则
6. **Prompt 定制** - 调整 AI 行为

---

## 6. 工作流搭建建议

### 6.1 基于现有架构的工作流实现

**方案 1：基于 Runbook 的流程定义**
- 使用流程型 Runbook 定义标准操作流程
- AI 根据用户意图选择对应的 Runbook
- 按步骤执行

**方案 2：基于事件流的流程编排**
- 在 `event_mapper.py` 中添加流程控制逻辑
- 根据事件类型和内容决定下一步操作
- 实现条件分支和循环

**方案 3：基于规则引擎的流程控制**
- 扩展规则引擎支持流程规则
- 根据证据状态决定下一步调查方向
- 实现自动化的诊断流程

### 6.2 扩展建议

**短期扩展**：
1. 在事件映射层添加流程控制逻辑
2. 扩展 Runbook 支持更复杂的流程定义
3. 添加流程状态管理

**长期扩展**：
1. 引入显式的 workflow 定义语言
2. 支持 workflow 可视化编辑器
3. 实现 workflow 版本管理和回滚

---

## 7. 参考资料

- [HolmesGPT 官方文档](https://docs.robusta.dev/master/configuration/holmesgpt/getting-started.html)
- [Custom Toolsets 文档](https://docs.robusta.dev/master/configuration/holmesgpt/custom_toolsets.html)
- [HolmesGPT GitHub 仓库](https://github.com/robusta-dev/holmesgpt)
- [CNCF 博客：HolmesGPT 架构介绍](https://www.cncf.io/blog/2026/01/07/holmesgpt-agentic-troubleshooting-built-for-the-cloud-native-era/)

---

## 8. 结论

HolmesGPT **支持工作流搭建**，但采用的方式与传统 workflow 引擎不同：

**核心优势**：
- ✅ 灵活的 agentic loop 架构
- ✅ 清晰的事件流和分阶段处理
- ✅ 丰富的扩展点
- ✅ 不阻断的软拦截机制

**适用场景**：
- ✅ 诊断和故障排查流程
- ✅ 基于规则的自动化判定
- ✅ 迭代式问题分解和解决
- ✅ 需要 AI 主动决策的场景

**不适用场景**：
- ❌ 需要严格顺序执行的线性流程
- ❌ 需要显式 workflow 定义和可视化的场景
- ❌ 需要传统 multi-agent 协作的场景

**建议**：
- 对于诊断类工作流，HolmesGPT 的架构非常适合
- 可以通过扩展事件映射层和规则引擎实现更复杂的工作流
- 考虑引入显式 workflow 定义语言以支持更复杂的流程编排
