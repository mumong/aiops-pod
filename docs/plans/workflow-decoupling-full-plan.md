# 工作流节点解耦与可扩展性重构 — 完整实施计划

## 一、目标与原则

- **目标**：低耦合、高内聚、高扩展性；功能与对外行为不变，确保现有能力可用。
- **原则**：
  - **止血**：用「节点注册表」作为唯一配置源，消除 graph/executor/conclusion 对节点 ID 的散落写死。
  - **疏通**：用 `node_analyses` 作为「所有分析节点输出」的统一视图，结论节点与日志/格式化器只依赖此视图 + 注册表。
  - **整形**：执行器/格式化器通过「注册表 + 可选策略」获取节点名、快照、摘要，避免大段 if/elif 按节点 ID 分支。
  - **扩展**：未来增删节点时，仅改注册表（及可选配置文件），不改结论节点、不改 executor 的深层逻辑。

---

## 二、当前耦合点一览

| 位置 | 问题 | 解耦后 |
|------|------|--------|
| [graph.py](app/core/workflow/graph.py) | 手写 4 个 add_node/add_edge，直接 import 4 个节点类 | 从注册表循环构建图 |
| [state.py](app/core/workflow/state.py) | 仅有按节点拆开的字段，无「按节点 ID 聚合」的通用结构 | 新增 `node_analyses: Dict[str, str]`，保留原字段 |
| [conclusion_formatter.py](app/core/workflow/nodes/conclusion_formatter.py) | 写死读取 layer_analysis/evidence_analysis/rca_analysis 和「阶段1/2/3」 | 从注册表取 conclusion 前所有节点，从 node_analyses 取内容 |
| [executor.py](app/core/workflow/executor.py) | initial_state 手写所有 key；_get_node_display_name 写死 name_map；_extract_state_snapshot / _format_node_summary 按 node_name 分支 | initial_state 加 node_analyses；显示名/快照/摘要从注册表或策略获取 |
| [output_formatter.py](app/core/workflow/output_formatter.py) | _handle_node_complete 里 if node_id==layer/evidence/rca 写死 | 用 node_analyses 或注册表统一取「该节点分析」 |
| [prompts.py](app/core/prompts.py) + 各节点 | 各节点直接 import LAYER_CLASSIFIER_PROMPT 等常量，与 node_id 脱节 | 节点通过 get_workflow_prompt(node_id) 取 prompt，prompts 与注册表 node_id 一致 |

---

## 三、领域边界（DDD-lite）

- **工作流上下文**：`app/core/workflow/` — 图、状态、节点、执行器、输出格式化。对外只暴露「执行流 + 事件流」，不直接依赖 API 或 Holmes 内部实现。
- **服务/API 上下文**：`app/core/service.py`、`app/api/routes.py` — 通过 `WorkflowExecutor.execute_stream()` 与工作流交互，不关心节点 ID 枚举。
- **交互方式**：保持现状（Service 创建 Executor，消费事件流），不引入事件总线；后续若需要「工作流完成 → 发通知」等，再考虑事件/消息。

---

## 四、核心设计

### 4.1 节点注册表（单一事实来源）

- **新建** [app/core/workflow/node_registry.py](app/core/workflow/node_registry.py)（或放在 [nodes/__init__.py](app/core/workflow/nodes/__init__.py) 中，视规模而定）。
- **NodeSpec**（TypedDict 或 dataclass）：
  - `id: str` — 节点 ID（如 "layer", "evidence", "rca", "conclusion"）
  - `name: str` — 显示名（如 "问题定位", "证据链采集"）
  - `cls: Type[WorkflowNode]` — 节点类
  - `analysis_key: Optional[str]` — 对应 state 中的分析字段名（如 "layer_analysis"），用于向后兼容与快照
- **注册表**：有序列表 `WORKFLOW_NODE_SPECS`，默认顺序为 layer → evidence → rca → conclusion。
- **辅助函数**（示例）：
  - `get_specs_before(node_id: str) -> List[NodeSpec]`
  - `get_display_name(node_id: str) -> str`
  - `get_all_analysis_keys() -> List[str]`（用于 initial_state 中初始化 node_analyses 占位）

### 4.2 状态扩展（保持兼容）

- 在 [app/core/workflow/state.py](app/core/workflow/state.py) 中新增：
  - `node_analyses: Optional[Dict[str, str]]` — key 为节点 ID，value 为该节点分析文本（JSON 或纯文本）。
- 现有字段（layer_analysis, evidence_analysis, rca_analysis, conclusion 等）全部保留；各节点在写入这些字段的同时，写入 `node_analyses[node_id]`。

### 4.3 图构建（graph.py）

- `build_diagnosis_workflow(holmes_service, metrics, runbook_catalog)`：
  - 从注册表顺序遍历 `WORKFLOW_NODE_SPECS`，对每项实例化 `spec.cls(holmes_service, metrics, runbook_catalog)`，`add_node(spec.id, node.execute)`。
  - 对相邻节点 `add_edge(prev.id, curr.id)`，首节点 `set_entry_point(first.id)`，末节点 `add_edge(last.id, END)`。
- `build_simple_workflow`：从同一注册表中按 ID 筛选子集（如 ["layer", "conclusion"]），只添加这些节点并按子集顺序连边。

### 4.4 各分析节点

- **Layer / Evidence / RCA**：在写入 `layer_analysis` / `evidence_analysis` / `rca_analysis` 的同时，执行 `new_state.setdefault("node_analyses", {})[self.node_id] = <同一分析文本>`。
- **Prompt 解耦**：将各节点内对 `LAYER_CLASSIFIER_PROMPT` 等常量的直接 import 改为调用 `get_workflow_prompt(self.node_id)`（[prompts.py](app/core/prompts.py) 已有 `get_workflow_prompt(node_id)` 和 `WORKFLOW_PROMPTS`）。若某节点需要 format 参数，可在节点内对 `get_workflow_prompt(self.node_id)` 的结果再做 `.format(...)`。

### 4.5 结论节点（conclusion_formatter.py）

- **输入**：不再接收三个固定参数 `layer_analysis, evidence_analysis, rca_analysis`，而是：
  - 使用 `_collect_preceding_analyses(state)`：根据注册表找到 "conclusion" 之前的节点列表，对每个节点从 `state.get("node_analyses", {}).get(node_id)` 取分析；若为空则回退到 `state.get(spec.analysis_key, "{}")`。
  - 返回 `List[Tuple[node_id, display_name, analysis_text]]`。
- **LLM 与 Fallback**：
  - `_generate_with_llm(question, preceding_analyses: List[Tuple[str,str,str]])`：循环生成「# 阶段N：{display_name}\n{text}」。
  - `_format_fallback` 同样接收该列表，对已知 node_id 保留现有段落格式，其余统一归为「其他分析」。
- 对外 `execute(state)` 的入参仍为 `WorkflowState`，仅内部改为从上述通用结构读取。

### 4.6 执行器（executor.py）

- **initial_state**：在现有字段基础上增加 `"node_analyses": {}`（并可在后续从注册表 `get_all_analysis_keys()` 做占位，非必须）。
- **_get_node_display_name(node_id)**：改为从注册表 `get_display_name(node_id)` 获取，若无则返回 node_id。
- **_extract_state_snapshot(node_name, state)**：
  - 优先从注册表获取该节点的 `analysis_key`，若存在则从 state 取该 key 及该节点已知关键字段组成 snapshot；
  - 对未在注册表中定义「专用快照逻辑」的节点，通用分支：`snapshot = { "node_id": node_name, "analysis": state.get("node_analyses", {}).get(node_name, "") }`。
  - 为保持兼容，现有 layer/evidence/rca/conclusion 的 snapshot 结构可保留为首选，仅当注册表中有对应 spec 时使用，避免破坏现有 consumer。
- **_format_node_summary(node_name, state, snapshot)**：同样可先从注册表取「摘要策略」（若后续引入）；短期可用通用逻辑：若有 `snapshot.get("analysis")` 则取前若干字符，否则保持现有按 node_name 分支（与现有日志兼容）。

### 4.7 输出格式化器（output_formatter.py）

- **_handle_node_complete**：不再写死 `if node_id == "layer"` 等；改为根据 `event.get("node")` 从 `state_snapshot` 中取该节点的分析内容。例如统一用 `snapshot.get("layer_analysis") or snapshot.get("evidence_analysis") or snapshot.get("rca_analysis")` 或更通用地 `snapshot.get("analysis")`（若执行器在 snapshot 中统一放入 node_analyses 对应项）。这样新增节点时，只要执行器在 snapshot 里带上该节点的分析，格式化器即可展示，无需改分支。

### 4.8 Prompts 与节点（prompts.py + 各节点）

- 保持 `WORKFLOW_PROMPTS = { "layer": ..., "evidence": ..., "rca": ..., "conclusion": ... }` 及 `get_workflow_prompt(node_id)`。
- 各节点改为通过 `get_workflow_prompt(self.node_id)` 获取 prompt，不再直接 import 具名常量。新增节点时只需在 `WORKFLOW_PROMPTS` 中增加一项，与注册表中的 node_id 一致即可。

---

## 五、实施顺序（供 Agent 按序执行）

1. **新增节点注册表**
   - 新建 `node_registry.py`（或合入 `nodes/__init__.py`），定义 `NodeSpec`、`WORKFLOW_NODE_SPECS`、`get_specs_before`、`get_display_name`。
   - 将现有 4 个节点按当前顺序注册进去。

2. **重构 graph.py**
   - `build_diagnosis_workflow` 与 `build_simple_workflow` 改为从注册表循环构建节点与边，行为与当前一致（顺序仍为 layer→evidence→rca→conclusion；simple 仍为 layer→conclusion）。

3. **扩展 state 与节点写入 node_analyses**
   - 在 `WorkflowState` 中增加 `node_analyses: Optional[Dict[str, str]]`。
   - 在 LayerClassifierNode、EvidenceCollectorNode、RootCauseAnalyzerNode 的 `execute` 中，在写入各自 analysis 字段的同时写入 `node_analyses[self.node_id]`。

4. **结论节点改为动态输入**
   - 实现 `_collect_preceding_analyses(state)`，基于注册表与 `node_analyses`（及 analysis_key 回退）。
   - 修改 `_generate_with_llm` 与 `_format_fallback` 接受「前置分析列表」，生成与当前语义一致的报告。

5. **执行器与格式化器解耦**
   - executor：initial_state 增加 `node_analyses`；`_get_node_display_name` 用注册表；`_extract_state_snapshot` 在保留现有 4 节点分支的前提下，对通用节点使用 `node_analyses`；`_format_node_summary` 可先保留分支或改为从 snapshot 统一取 analysis 的简短摘要。
   - output_formatter：_handle_node_complete 改为从 snapshot 中按通用方式取当前节点分析（例如 snapshot.get("analysis") 或按 node_id 从 node_analyses 取），避免写死 layer/evidence/rca。

6. **Prompts 与节点解耦**
   - 将 layer_classifier、evidence_collector、root_cause_analyzer、conclusion_formatter 中对具体 prompt 常量的 import 改为使用 `get_workflow_prompt(self.node_id)`，并在需要时对返回值做 `.format(...)`。

7. **回归与兼容性**
   - 跑现有单测（若有）及手工回归：相同问题下，SSE 事件类型与顺序、最终 answer 结构、日志中的节点名与摘要与当前一致；仅实现方式改为可扩展。

---

## 六、可选后续（本次不实现）

- 将 `WORKFLOW_NODE_SPECS` 的「顺序与启用集合」放到配置文件（如 config.yaml 的 `workflow.nodes`），实现不同场景下不同 pipeline。
- 为 NodeSpec 增加可选 `snapshot_extractor(state) -> dict` 或 `summary_formatter(snapshot) -> str`，进一步把 executor/output_formatter 中的「按节点定制」收口到注册表一侧。
- 若未来 Service 需要可替换执行实现，可引入抽象接口（如 `IWorkflowRunner`）与依赖注入，由调用方注入 `WorkflowExecutor` 或工厂。

---

## 七、文件变更清单（汇总）

| 文件 | 操作 |
|------|------|
| [app/core/workflow/node_registry.py](app/core/workflow/node_registry.py) | 新建：NodeSpec、WORKFLOW_NODE_SPECS、辅助函数 |
| [app/core/workflow/graph.py](app/core/workflow/graph.py) | 修改：从注册表构建图 |
| [app/core/workflow/state.py](app/core/workflow/state.py) | 修改：新增 node_analyses 字段 |
| [app/core/workflow/nodes/layer_classifier.py](app/core/workflow/nodes/layer_classifier.py) | 修改：写 node_analyses；用 get_workflow_prompt |
| [app/core/workflow/nodes/evidence_collector.py](app/core/workflow/nodes/evidence_collector.py) | 修改：写 node_analyses；用 get_workflow_prompt |
| [app/core/workflow/nodes/root_cause_analyzer.py](app/core/workflow/nodes/root_cause_analyzer.py) | 修改：写 node_analyses；用 get_workflow_prompt |
| [app/core/workflow/nodes/conclusion_formatter.py](app/core/workflow/nodes/conclusion_formatter.py) | 修改：动态收集前置分析，LLM/fallback 用通用列表 |
| [app/core/workflow/executor.py](app/core/workflow/executor.py) | 修改：initial_state、_get_node_display_name、_extract_state_snapshot（及可选 _format_node_summary） |
| [app/core/workflow/output_formatter.py](app/core/workflow/output_formatter.py) | 修改：_handle_node_complete 通用化 |
| [app/core/prompts.py](app/core/prompts.py) | 无需改结构，仅保证 WORKFLOW_PROMPTS 与注册表 node_id 一致 |

以上计划在保持功能与对外行为不变的前提下，实现低耦合、高内聚与高扩展性，便于后续增加或减少节点。
