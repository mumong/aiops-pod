# Bounded Diagnosis：单一交付 Loop

## 目标

把原 T004–T011 收敛为一个纵向交付单元：从真实工具 Observation 到
最终报告一次贯通，不再按 fan-in、日志、Proposition、报告、回放、部署
分别开启实现/审查循环。

本计划保留已经完成的 T001/T002 和当前 T003 产物，不引入 Case、错误
文本、指标名或 workload 特判。

## 唯一 Loop

```text
实现 Bounded Diagnosis Contract v2
  → 一次集中单元/回放验证
  → 一次独立审查
  → 一次 VERSION 升级与镜像部署
  → 一次 baseline/N=1/N=3/N=5/N=10 冻结实测
  → 一次最终审计
```

中间发现失败时只回到同一个实现单元修复，不再创建新的架构任务或
并行 reviewer 链。

## 每条 Lane 的固定状态机

```text
BASELINE_COLLECT
  → SNAPSHOT_V2
  → ANALYZE_1
  → VALIDATE_1
      ├─ valid/finalize       → TERMINAL
      ├─ collect_once         → TARGETED_COLLECT（最多 2 calls）
      │                           → DELTA_CHECK
      │                               ├─ 有新信息 → ANALYZE_2 → VALIDATE_2
      │                               └─ 无新信息 → INCONCLUSIVE
      ├─ repairable_format    → ANALYZE_2 → VALIDATE_2
      └─ unsafe/unrepairable  → INCONCLUSIVE
  → PERSIST_TERMINAL
  → TOTAL_FAN_IN
  → DETERMINISTIC_REPORT
```

`ANALYZE_2` 是共享预算：用过补采集后的最终分析，就不能再做结构修复；
用过结构修复，就不能再补采集。

## 硬预算

```yaml
max_llm_calls_per_lane: 2
max_targeted_collection_rounds: 1
max_targeted_tool_calls: 2
max_rca_input_facts: 32
max_concurrency: 3
max_global_narrative_calls: 1
```

时间限制使用配置项并在真实基准后定值；无论时间配置是多少，都不能
突破上述次数预算。N 个 lane 的模型调用上限为 `2N + 1`。

## 代码与模型边界

代码负责：实体/UID、基础采集计划、Observation/Fact 归一化、快照、选择
清单、查询去重、预算、Proposition 绑定、终态、total join 和最终事实区。

Qwen 负责：提出语义假设、判断当前证据能否区分候选、在确有信息增益时
请求一次补采集、基于最终证据生成简短解释。

Qwen 不负责：批准自己的结论、决定是否突破预算、重新归属实体、删除
Fact、宣称 join 完整或决定哪些已验证事实最终可见。

## 一次补采集的准入条件

第一次 RCA 只有同时满足以下条件才能返回 `collect_once`：

1. 指出一个会影响主要候选排序的具体未决问题；
2. 现有 selected/omitted Facts 不能回答该问题；
3. 请求绑定当前 authoritative entity；
4. 使用允许的只读工具能力；
5. 给出预期新信息、支持结果、排除结果；
6. 查询指纹未执行过；
7. 不以“更完整/再看看/全面检查”作为理由。

代码拒绝不满足条件的请求；拒绝后直接进入 `inconclusive`，不把拒绝
再交给模型循环讨论。

## Delta 与停止

Observation 指纹至少包含：

```text
tool + entity UID + normalized args + time window
```

补采集后出现以下任一情况立即停止，不调用第三次模型：

- 没有新的、可归属的 Observation；
- 只有重复查询或 deduplicated result；
- 工具失败且没有形成可验证的负向边界；
- Validation 2 不通过；
- lane 超时或取消；
- artifact 完整性失败。

成功的 scoped empty 是真实边界，可以作为 delta 交给第二次最终分析；
它不能覆盖同维度已有的 present Observation。

## 最终状态

```text
confirmed             系统明确原因/直接错误事实通过精确绑定
supported_hypothesis  真实证据一致，但因果仍主要来自模型解释
inconclusive          证据或模型能力不足
error                 执行、归档、完整性或 total-join 失败
```

在兼容旧接口期间，`confirmed/supported_hypothesis` 可投影为旧
`diagnosed`，但新 artifact 必须保留更精确的 publication status。

## 单一实现范围

一次实现同时贯通：

- 用有界状态机替换 evidence collector 的开放式 `while True` ReAct；
- 为首次/最终 RCA 增加结构化 decision 和 follow-up request；
- 把 source-backed observation 统一归一化进 Fact snapshot；
- 实现开放式 Evidence Proposition 与精确绑定；
- 持久化 ordered total fan-in；
- 让 report 只展示 validated support set；
- 保留可选 narrative，但不允许它增加、删除或改写事实。

## 集中验收

只设置一道实现验收门：

1. 单元测试证明 2 次 LLM、1 轮补采集、2 工具调用上限不可突破；
2. 单元测试证明重复查询、无 delta、无效 scope 会停止；
3. replay 证明旧 c05 lane 不消失、日志 present 不变 absent、支持 Fact ID
   贯穿 snapshot/claim/report；
4. 禁止特判扫描通过；
5. 一名独立 reviewer 审查完整纵向 diff；
6. 然后只构建和部署一次镜像；
7. 固定请求运行 baseline、N=1、N=3、N=5、N=10，并记录 wall time、
   Run ID、LLM/tool 调用数、lane inventory、四维覆盖和 artifact hash。

若真实运行仍因 Qwen 能力不足而 `inconclusive`，只要证据完整、预算受控、
没有虚假诊断和静默丢 lane，即属于工程合同正确；模型召回率作为独立指标
记录，不再通过无限循环弥补。
