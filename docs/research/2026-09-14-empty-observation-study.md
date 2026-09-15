# 查询成功但观测为空：具体机制、近邻与候选边界

日期：2026-09-14。用途：对用户早期“没报错为什么没结果”的反馈做独立技术切口核验；仅研究，不修改 MCP 或运行中的 Agent。

## 1. 小问题与真实实现

空结果是一次查询的输出形态，不是故障是否存在的结论。即使 SQL/PromQL 语法和调用权限均正确，结果也可能在选择、计算、比较或匹配阶段变空。

当前 `../mcpstander/servers/aiops_observability/query/metrics.py`：

- `validate_promql_scope` 要求每个向量选择器都有精确 namespace/pod 条件。这控制查询范围，不保证源指标有对应序列。
- `execute` 在查询前后核对 Pod 身份，检查 Prometheus 成功状态和响应形状。
- 约 397 行按 raw_series_count 设置 coverage=present/empty；正常返回中 status=query_succeeded。
- `compact_prometheus_result` 和 `execute` 正常结果组装没有把 Prometheus 顶层 warnings/infos 传入最终结果。此结论限该函数路径，不涉及其他服务日志是否另外保存 HTTP 返回。

本轮用 AST 提取真实 `compact_prometheus_result`，输入两份合成成功空向量响应，其中一份另带说明性 warnings 字段，得到相同的 compact 输出。没有执行 Prometheus 查询，也没有复现某条线上 warning。该反例说明：仅回读 MCP 返回归档，不一定能恢复已经在 MCP 内未转交的源端提示。

这与有限上下文主线有关：先明确 D 究竟是数据源响应还是 MCP 处理后的响应；后者未包含的内容，不能靠 Agent 归档回读补回来。

## 2. 必须区分的几种空结果

以 `rate(C{namespace="n",pod="p"}[5m]) > 0` 为说明性查询，C 是一个浮点计数器，不是实际集群中已核验的指标名。

| 情况 | 允许得出的结论 | 不允许得出的结论 |
|---|---|---|
| rate 有有限数值，但均未满足 >0 | 本次计算出的速率未满足该谓词 | 业务整体正常、所有错误都不存在 |
| 范围内只有一个可用浮点样本 | 该窗口不足以按通常 rate 语义计算此序列 | 没有增长、没有故障 |
| 指定选择器范围内没有序列/样本 | 本次选择器和时间口径没有取得数据 | 指标从未存在、采集器肯定故障 |
| 二元运算两侧都有数据但标签不匹配 | 该匹配规则下没有配对 | 两边对象没有业务关系 |
| 输入样本类型或引擎规则导致元素被移除 | 必须结合引擎注解及具体运算解释 | 无异常 |

Prometheus 官方 operators 文档明确比较默认过滤元素、向量匹配失败可移除元素；bool 改变的是已有匹配元素的比较输出，不会自动补出原本不存在的序列。本轮查看了[官方 operators 文档](https://prometheus.io/docs/prometheus/latest/querying/operators/)，网页是滚动版本；未把其新特性当作当前部署版本能力。

`rate` 样本数量条件在本节作为实施前提，尚未用本地 Prometheus 引擎重跑。本轮尝试读取 v3.5.0 functions.go 以固定版本核验时超时，因此不能把此例称为引擎级验证。

## 3. 一个可实施的工程草案：原查询与伴随检查

这是扩展设计，不是已实现功能，也不是已成立的创新结论。

1. 固定原查询 Q、目标对象标识、评估时间 T 和允许的时间范围。先归档原响应及源端注解，不把空结果直接变成阴性故障证据。
2. 用实际 PromQL 解析器得到语法树。对明确支持的结构生成伴随检查；例如 Q 为浮点 rate 后接标量比较时，生成未比较的 rate 表达式 E，以及相同选择器和窗口的 count_over_time。不是用字符串替换实现通用重写。
3. 每个伴随检查保留相同 namespace/pod、offset、@、范围窗口及子查询时间语义，并再次通过安全与预算检查。第一版可直接拒绝复杂子查询和不支持的类型，不能悄悄换语义或去掉对象限制。
4. 以原评估时间执行受限检查，保存各自查询、响应及来源引用；原始查询结果不被伴随查询覆盖。固定时间不等于获得了跨请求数据库事务快照，迟到样本或远端数据变动仍可能造成不一致。
5. 程序依据已取得的有限值、样本数量、标签匹配和源端注解返回“谓词未满足”“计算条件不足”“源选择为空”或“未判定”。不能仅凭样本数>=2 就排除类型混合、NaN、源端注解等情况；多序列必须逐系列对应，不能用一个序列可计算代表全部。
6. 现有 Agent 解释结果，或建议下一步；若使用小模型，其职责是选择受支持的检查候选，而不是填写结果或认证源覆盖。自动修正原查询是另一操作，不能把诊断查询的结果冒充原查询证据。
7. 超时、查询预算耗尽、未支持语法、身份变化、响应截断或结果矛盾时停止相应分类，保留未判定。缺少诊断支路不等于该支路结果为空。

可以将多个瞬时向量支路加保留标签后合并为一次只读 PromQL 请求，以减少往返；但要处理标签碰撞、结果上限和服务器成本，而且它不提供跨远端数据源的事务一致性。该选项没有实际实现或测试，不作为区别贡献。

拟输出示例，仅为结构说明：

```json
{
  "original_query_result": "empty",
  "empty_stage": "comparison",
  "basis": [{"check_id": "rate-before-filter", "value": 0}],
  "permitted_statement": "evaluated_rate_did_not_satisfy_predicate",
  "health_conclusion": "not_established",
  "unresolved": []
}
```

程序能确定的是指定运算的结果关系，不能确定该查询足以回答整个诊断问题。这正是模型与确定性计算的分工边界。

## 4. 现有产品：PromLens 已有相关解释能力

仓库：[prometheus/promlens](https://github.com/prometheus/promlens)。为避免把当前网页误当历史公开，本轮通过 GitHub commits API 使用 until=2026-09-14 查询 README 最近提交，固定到：

- commit `70c092c3304f2796c23b7c6706d6998a5766108e`；committer 时间 2026-07-10T10:01:56Z。
- 该版本 README 说明 PromLens 是 PromQL query builder/analyzer/visualizer，并称部分功能已并入 Prometheus Explain。这里只确认仓库陈述，未验证用户部署的 Prometheus 是否有这些功能。
- `app/src/PromLens/NodeVisualizer/ExplainViews/BinaryExpr/VectorScalar.tsx`：约 23—25 行处理输入向量为空；约 54—81 行计算比较 keep/bool 并显示 dropped。
- 同目录 `VectorVector.tsx`：解释 on/ignoring/group 匹配，显示 no matching series、dropped，并给出匹配错误与调整提示。核读了相关源码摘录，没有运行产品。

固定版本源码：[VectorScalar](https://github.com/prometheus/promlens/blob/70c092c3304f2796c23b7c6706d6998a5766108e/app/src/PromLens/NodeVisualizer/ExplainViews/BinaryExpr/VectorScalar.tsx)、[VectorVector](https://github.com/prometheus/promlens/blob/70c092c3304f2796c23b7c6706d6998a5766108e/app/src/PromLens/NodeVisualizer/ExplainViews/BinaryExpr/VectorVector.tsx)。

因此，“展开子表达式，解释过滤和不匹配”不是空白。将其改成 MCP JSON 或交给小模型阅读，不足以自动形成创造性。

## 5. 新核读的专利

### 5.1 US11741161B2

**System and Method for Generating a Refined Query**，Siemens；申请日 2021-05-05，授权公告日 2023-08-29；首页记载 US20220358166A1 于 2022-11-10 公开。

原件：[USPTO](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/11741161)。本轮核读 PDF 第 1、9、10 页，含全部权利要求 1—11，未完整精读说明书。

权利要求 1、6：当前含 triple patterns 的查询结果与用户选定/补充的参考结果比较，按照遗漏/不需要答案等计算分数，在查询修改树中选择节点和操作，结合机器学习生成细化查询。权利要求 3、8 有再执行及终止条件；4、9 包括增加/去掉 triple patterns 和过滤条件、加强/减弱约束。

与草案的区别：其参考答案来自用户，目标是产生细化查询；本草案不要求用户预知缺失答案，也不以“得到非空”为成功，而解释原查询是否支持特定负向陈述。不过查询修改、结果比较和模型辅助已有明确公开，区别是否非显而易见仍未证明。

### 5.2 US20100100563A1

**Method of Computing a Cooperative Answer to a Zero-result Query through a High Latency API**；申请日 2009-10-19，公开日 2010-04-22。首页列示临时申请，本轮不核定有效优先权或法律状态。

原件：[USPTO](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/20100100563)。本轮查看第 1、19、20 页，核读独立权利要求 11、16 及相关从属条款；没有读取第 18 页的前部权利要求，不能说全部权项已经核读。

权利要求 11：针对返回空集的布尔查询，并行提交子查询，返回非空/空的基数信息；非空就展示对应子查询，仍为空则继续其子查询。12—14 涉及否定范式的合取图、所有父节点失败时的展开、维护零结果查询列表及包含关系去除；15 允许返回估计的数量。

这与“空结果触发结构化子查询检查、减少 API 等待”非常接近。不能只因为它不写 PromQL/Agent，就把伴随检查当作新方法。它没有在所核条款中给出 PromQL range-vector 样本充分性或诊断结论资格，但添加这些领域规则是否只是常规适配，需要专门论证。

## 6. 当前判断和下一验证条件

问题真实、范围小、工程可实施。但目前不推荐直接以“空结果 + 子查询检查 + 小模型解释”独立立项；既有产品和专利已提供很强的处理链启示。保留其为候选对照，不宣布被单篇完整覆盖，也不宣布已具备新颖性。

若继续，必须把非平凡区别落在可测的处理关系上，例如在时间变化、源端丢弃与目标约束均存在时如何形成可信且有资源上限的负向证据，而不是仅输出更多原因标签。尚未找到这一点的充分区别证据，不用该例替代总目标完成。

研究原件 SHA-256：

- 11741161：`8e78625caa12dc400cd0411fe439d17c4d6c7ac3608e669f6b7fda2c6a21acec`。
- 20100100563：`abb8f88a95a251767263d069cf4e7918823b1759fa68cfe15b09b6188e50e0bd`。

本轮没有运行原查询、伴随查询、PromLens 或 Prometheus 引擎，没有修改 Agent、MCP、权限、集群或测试任务。网页和代码核验、合成 payload 试验与完整执行验证严格分开。
