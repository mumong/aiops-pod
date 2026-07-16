# 小模型可观测性证据闭环实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**目标：** 在不引入 OOM、ConfigError、Terminating 等故障类型硬编码的前提下，让 Qwen 小模型稳定完成异常 Pod 发现、粗粒度 Case 采集、按需细粒度补证、结构化 RCA 和可读报告生成，并让工具与耗时统计真实可审计。

**架构：** 保留现有 Layer、Evidence、RCA、Conclusion 四节点。Layer 只做轻量异常实体发现并对相同工具参数通用去重；Evidence 对每个异常 Pod 先调用 `collect_aiops_case`，再根据摘要中的缺失、冲突和未回答问题按需展开 evidence ref；RCA 负责形成结构化根因；Conclusion 只基于结构化结果和确定性事实渲染报告，不重新改变根因语义。

**技术栈：** Python、LangGraph/LangChain、Pydantic、MCP SSE、pytest、Kubernetes、Prometheus、Elasticsearch/Filebeat、DeepFlow/ClickHouse、Tempo。

---

### Task 1：真实工具调用和耗时统计

**文件：**
- 修改：`app/core/aicall/client.py`
- 修改：`app/core/workflow/metrics.py`
- 修改：`app/core/workflow/reporter.py`
- 修改：`app/core/workflow/executor.py`
- 测试：`tests/unit/aicall/test_observation_processing.py`
- 测试：`tests/unit/workflow/test_executor_timing.py`

- [ ] **步骤 1：补充失败测试**

覆盖并行工具调用具有不同稳定序号、相同 `tool_call_id` 不重复计数、开始但无结果计入未完成、工具累计耗时与并行墙钟耗时分离、模型请求耗时与节点墙钟耗时分离。

- [ ] **步骤 2：运行统计模块测试并确认失败**

```bash
.venv/bin/python -m pytest -q \
  tests/unit/aicall/test_observation_processing.py \
  tests/unit/workflow/test_executor_timing.py
```

预期：新增断言在当前实现下失败，并明确暴露并发编号、重复计数或耗时命名问题。

- [ ] **步骤 3：实现通用调用身份和统计重建**

使用 `node + tool_call_id` 作为首选身份；缺少 call id 时使用节点、工具、标准化参数和发生顺序构造身份。最终统计只从完整 thinking event 流重建，不累加各节点的重复中间统计。输出字段区分：

```text
workflow_wall_duration
model_request_duration
tool_cumulative_duration
tool_critical_path_duration
tool_started/succeeded/failed/unfinished/deduplicated
```

- [ ] **步骤 4：运行统计模块测试**

预期：上述两个测试文件全部通过。

---

### Task 2：Layer 通用工具去重与停止

**文件：**
- 修改：`app/core/aicall/client.py`
- 修改：`app/core/workflow/nodes/layer_classifier.py`
- 修改：`app/core/prompts.py`
- 测试：`tests/unit/workflow/test_fast_paths.py`

- [ ] **步骤 1：补充失败测试**

验证同一节点内相同工具和标准化参数成功后不会再次实际执行；模糊全集群诊断完成一次 Pod 扫描并获得异常实体后，不会反复对同一 Pod 执行 `kubectl_get_by_name` 直到 recursion limit。

- [ ] **步骤 2：运行 Layer 测试并确认失败**

```bash
.venv/bin/python -m pytest -q tests/unit/workflow/test_fast_paths.py
```

- [ ] **步骤 3：实现低耦合去重**

去重只依据工具名和标准化参数，不依据 Pod 状态或故障类型。重复请求复用已有成功 observation，并写入 `tool_deduplicated` 审计事件。Layer 在异常实体集合已经确定且无新实体或新状态信息时结束工具循环，把深度采证交给 Evidence。

- [ ] **步骤 4：运行 Layer 模块测试**

预期：Layer、query direct、显式 Pod 路径相关测试全部通过。

---

### Task 3：覆盖率、充分度与按需细粒度补采

**文件：**
- 修改：`app/core/workflow/schemas.py`
- 修改：`app/core/workflow/nodes/evidence_collector.py`
- 修改：`app/core/prompts.py`
- 测试：`tests/unit/workflow/test_evidence_dynamic_stop.py`
- 测试：`tests/unit/workflow/test_context_handoff.py`

- [ ] **步骤 1：补充失败测试**

覆盖以下行为：

```text
source_coverage=100% 不等于 diagnostic_sufficiency=100%
Case 摘要存在缺失、冲突、稀疏样本或 unresolved question 时允许调用 get_aiops_case_evidence
Case 已包含决定性原始字段时不为增加次数而展开全部 ref
细粒度补采最多一轮并受 80% 上下文停止线约束
每个异常 Pod 只调用一次 collect_aiops_case
```

- [ ] **步骤 2：运行 Evidence 模块测试并确认失败**

```bash
.venv/bin/python -m pytest -q \
  tests/unit/workflow/test_evidence_dynamic_stop.py \
  tests/unit/workflow/test_context_handoff.py
```

- [ ] **步骤 3：实现通用 post-case evidence refinement**

Case 完成后执行一次窄任务模型调用，只允许 `get_aiops_case_evidence` 和启用的细粒度 AIOps 工具。输入只包含 Case 首屏事实、真实 `recommended_refs_by_dimension`、已获取 ref 和当前未回答问题。模型可以选择零个或少量 ref，不包含故障类型分支。

- [ ] **步骤 4：修正统计语义**

对外区分：

```json
{
  "source_coverage": {},
  "case_target_coverage": {},
  "detail_retrieval": {},
  "diagnostic_sufficiency": {},
  "unresolved_questions": []
}
```

删除“Case 成功即诊断完整度 100%”的文案。

- [ ] **步骤 5：运行 Evidence 模块测试**

预期：Evidence 和上下文交接相关测试全部通过。

---

### Task 4：结构化 RCA 和可读报告

**文件：**
- 修改：`app/core/workflow/schemas.py`
- 修改：`app/core/workflow/nodes/root_cause_analyzer.py`
- 修改：`app/core/workflow/nodes/conclusion_formatter.py`
- 修改：`app/core/prompts.py`
- 测试：`tests/unit/workflow/test_structured_schemas.py`
- 测试：`tests/unit/workflow/test_fast_paths.py`
- 测试：`tests/unit/workflow/test_ask_conclusion_remediation_json.py`

- [ ] **步骤 1：补充报告失败测试**

最终报告必须保留以下结构：

```text
诊断摘要
现象描述
可观测性数据
拓扑关系与拓扑解读
已采集的核心证据
根因分析
修复建议
验证步骤
结构化修复计划
机器可核验附录
性能统计与诊断追踪
```

同时不得出现单独“采集统计”章节，不得在不同章节生成互相矛盾的根因或无证据修复倍数。

- [ ] **步骤 2：运行报告模块测试并确认失败**

```bash
.venv/bin/python -m pytest -q \
  tests/unit/workflow/test_structured_schemas.py \
  tests/unit/workflow/test_fast_paths.py \
  tests/unit/workflow/test_ask_conclusion_remediation_json.py
```

- [ ] **步骤 3：收敛 Conclusion 职责**

RCA 为每个异常实体输出结构化 issue。Conclusion 以结构化 issue、真实可观测性事实和确定性附录为输入，主要负责渲染和压缩，不重新生成新的根因、影响范围或修复参数。报告中的拓扑边后必须生成自然语言解读，说明调用入口、Service 选择、工作负载归属和责任边界。

- [ ] **步骤 4：运行报告模块测试**

预期：结构化 schema、报告模板和修复安全测试全部通过。

---

### Task 5：模块集成、真实部署和验收

**文件：**
- 修改：`VERSION`
- 修改：`deploy/k8s-simple.yaml`
- 按需修改：`deploy/configmap/config.yaml`
- 不提交：`deploy/secrets/core.yaml`

- [ ] **步骤 1：运行完整相关测试组**

```bash
.venv/bin/python -m pytest -q \
  tests/unit/aicall/test_observation_processing.py \
  tests/unit/workflow/test_executor_timing.py \
  tests/unit/workflow/test_evidence_dynamic_stop.py \
  tests/unit/workflow/test_context_handoff.py \
  tests/unit/workflow/test_fast_paths.py \
  tests/unit/workflow/test_structured_schemas.py \
  tests/unit/workflow/test_ask_conclusion_remediation_json.py \
  tests/unit/workflow/test_remediation_plan_handling.py \
  tests/unit/remediation/test_plans.py
```

- [ ] **步骤 2：构建并部署新版本**

沿用仓库现有镜像构建和 Kubernetes 部署方式，等待 Deployment Ready，并核对运行镜像 tag/digest。

- [ ] **步骤 3：执行真实模糊问题验收**

```bash
curl --no-buffer -G "http://10.2.0.48:30800/ask" \
  --data-urlencode "q=我的集群现在有什么问题？"
```

验收：

```text
每个异常 Pod 恰好一次 collect_aiops_case
需要时存在少量 get_aiops_case_evidence，证据充分时允许为 0
没有相同工具参数重复调用
Metrics、Logging、DeepFlow、Tempo、Topology 来源真实
工具统计与日志事件逐项一致
报告结构完整且没有采集统计章节
拓扑有自然语言解读
根因引用真实原文和 evidence ref
无内部矛盾、无无证据倍数或节点健康结论
```

- [ ] **步骤 4：使用另一类异常做通用性回归**

选择当前真实环境中非 OOM 的异常 Pod，确认不依赖测试 Pod 名称、namespace、标签或故障类型分支。

---

### Task 6：独立审计、提交与双远端推送

**文件：**
- 审计：本次提交全部 diff
- 审计：真实运行输出和 Pod 日志

- [ ] **步骤 1：独立审查**

使用无历史上下文的独立审查 Agent，检查工具真实性、统计一致性、细粒度补采合理性、证据边界、报告可读性和通用性。

- [ ] **步骤 2：敏感信息与提交范围检查**

```bash
git diff --check
git status --short
git diff --cached --stat
git diff --cached | rg -n "sk-[A-Za-z0-9]|API_KEY|TOKEN|PASSWORD|SECRET"
```

明确排除 `deploy/secrets/core.yaml`、临时输出、真实凭据和运行时归档。

- [ ] **步骤 3：提交**

提交消息：

```text
feat: stabilize evidence-driven observability diagnosis
```

- [ ] **步骤 4：推送两个远端**

```bash
git push origin perf/behavior-preserving-latency
git push aiops-pod perf/behavior-preserving-latency
```

推送后核对两个远端分支 commit SHA 与本地 `HEAD` 一致。
