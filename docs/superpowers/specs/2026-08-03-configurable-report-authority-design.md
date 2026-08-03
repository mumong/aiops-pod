# 可配置报告 Authority 模式设计

**日期**：2026-08-03

**状态**：用户已批准双模式方向，待书面规格复核

**范围**：Robusta canonical Fact Ledger 人类报告的维度真实性、核心结论和因果框

## 1. 背景

当前 dirty development line 为了让小模型稳定生成完整报告，在
`app/core/workflow/report_presentation.py` 中增加了确定性因果合成：当模型没有给出
可用 `causal_chain` 时，按 `configuration -> state/event/log -> measurement/span/flow`
把同一实体的事实组织为根本原因、传导机制和最终表现。

T002 只读审计确认了两个问题：

1. 没有 Fact、也没有 coverage 的核心维度仍被渲染为“已执行的数据源 / 查询完成”；
2. fallback 从全部 `non_coverage` facts 生成权威因果段，即使这些事实不在
   `valid_supporting_fact_ids` 中。

进一步追踪表明，`validate_rca_claims()` 校验 supporting/contradicting Fact IDs，但不校验
自由文本 `causal_chain` 的每个值。因此只收紧 fallback 仍会让显式模型 chain 绕过相同的
authority 边界。

另一方面，本项目主要使用的小模型无法稳定地在大量上下文中完成严格引用和复杂因果推理。
默认强制 strict 模式会频繁丢弃本来可读的报告。用户要求默认使用结构化模板根据核心数据稳定组织
语言，并把强 Fact-ID authority 校验作为按需开启的开关。

## 2. 目标

1. 无执行证据的维度永远不显示为查询完成。
2. 默认模板模式不依赖小模型生成因果链，使用通用结构化事实稳定组织可读报告。
3. 严格模式开启后，核心结论和因果框只消费 validated supporting facts。
4. 未携带角色级 Fact IDs 的显式 LLM `causal_chain` 不进入任一模式的确定性核心结论或因果框。
5. 两种模式共享相同的 Fact Ledger、维度摘要、机器附录和 remediation 安全合同。
6. 不增加任何故障类型专用分支。

## 3. 配置合同

唯一部署配置入口为：

```yaml
workflow:
  conclusion:
    strict_report_authority: false
```

- 缺失或 `false`：模板模式，作为默认值。
- `true`：严格 authority 模式。
- 字符串布尔值使用 `WorkflowNode._parse_bool_config()` 的既有规则解析。
- 非法值安全回退到默认 `false`。
- 第一版不增加环境变量别名，避免隐藏环境覆盖 ConfigMap 后导致实际报告策略不可见。
- workflow executor 已对每个请求复制配置快照；节点从自己的
  `workflow_config_override` 读取开关，不使用模块级可变状态。

该开关控制的是报告推理 authority，不控制 Fact Ledger 校验、来源选择、机器附录或 remediation
安全策略。后四者始终启用。

## 4. 模式语义

### 4.1 模板模式（默认）

模板模式服务于小模型和本地模型的稳定输出：

- 从当前单一主体的非 coverage、非 topology FactRecords 中提取核心数据；
- 按通用 `fact_type` 角色映射组织结构化链：
  - configuration：关键条件；
  - state/event/log：状态变化；
  - measurement/span/flow：观测结果；
- 使用 `_fact_signal()` 从 FactRecord 的实体、属性和值生成自然中文，不要求模型重新推理大量上下文；
- 允许未被 RCA 选为 supporting 的真实核心数据进入模板摘要；
- 不把模板链声明为“validated root cause”。报告中使用“结构化数据关联”语义，机器标记记录
  `report_authority_mode=template`；
- 多实体输入继续禁用合并链，避免跨实体拼接。

模板模式不是关闭真实性保护。精确值仍逐字来自 FactRecord；coverage、topology、低质量 raw 文本和
模型自由文本不能被模板合成为精确事实。

### 4.2 严格模式

严格模式面向审计、验收或用户明确要求强逻辑验证的场景：

- 从 `claim_validation.valid_supporting_fact_ids` 建立有序、存在于当前 Ledger 的 FactRecord 子集；
- 核心结论只能来自该子集；
- 因果框只从该子集按通用角色映射确定性生成；
- supporting facts 不足两个有效因果角色时不强行生成因果框；
- 没有 validated supporting fact 时输出证据不足的中性结论；
- contradicting facts 可作为反证或限制展示，但不被合成为原因；
- 机器标记记录 `report_authority_mode=strict`。

严格模式不要求小模型稳定生成 chain。模型仍可生成现象或证据解释，但只有通过现有 hidden Fact marker
校验的叙述才保留；未经角色级 Fact ID 约束的显式 `causal_chain` 不进入权威段。

## 5. 显式 LLM causal chain

当前 `causal_chain` 是自由文本字典，没有为 trigger、mechanism、manifestation 分别携带 Fact IDs。
在本任务中不能可靠证明每段文字属于 validated facts，因此两种模式都不直接使用它生成确定性核心结论
或因果框。

若未来需要恢复模型 chain 优先级，应另建 schema 迁移任务，为每个因果角色增加 `fact_ids`，并在
`validate_rca_claims()` 中逐角色校验。本任务不通过字符串匹配猜测模型 chain 的来源。

## 6. 维度真实性

维度状态独立于 authority 开关，始终执行以下规则：

| Fact/observation | coverage | 展示状态 | 展示语义 |
|---|---|---|---|
| 有真实信号 | 任意 | `present` 或 `partial` | 展示真实来源和信号 |
| 无真实信号 | 有明确完成/空 coverage | `empty` | 查询完成，当前窗口无匹配数据 |
| 无真实信号 | 无 coverage | `not_executed` | 本轮未执行，当前状态未验证 |

核心维度仍始终成行，但 `not_executed` 行不得包含“已执行的数据源”“查询完成”或“未采样到”。若有
empty coverage，数据来源使用 coverage Fact 的真实 `source_system`，不使用无来源的占位文字。

## 7. 组件与数据流

### `ConclusionFormatterNode`

- 新增 `_is_strict_report_authority_enabled()`，从
  `workflow.conclusion.strict_report_authority` 读取配置，默认 `false`；
- 调用 `_apply_fact_ledger_report_contract()` 时显式传递解析后的布尔值；
- `_apply_fact_ledger_report_contract()` 的直接测试调用保持默认模板模式。

### `report_presentation.py`

- `DimensionPresentation` 支持 `not_executed`；
- `build_dimension_presentations()` 保留 coverage 来源，并区分无 coverage 与已执行空结果；
- `render_human_report()` 接收 `strict_report_authority: bool = False`；
- 统一的事实选择器根据模式返回模板 core records 或 strict supporting records；
- `_synthesize_causal_chain()` 只负责通用事实类型到结构角色的确定性映射；
- 模式决定标签、核心结论 fallback 和是否允许权威因果框；
- 最终报告写入隐藏的模式标记，便于测试、回放和问题定位。

```text
canonical ledgers + validated claim + workflow config snapshot
                         |
                         +--> dimension facts/coverage
                         |        |
                         |        +--> present / partial / empty / not_executed
                         |
                         +--> strict_report_authority?
                                  |
                    false --------+-------- true
                      |                       |
              core FactRecords        validated supporting FactRecords
                      |                       |
              template association      strict causal synthesis
                      |                       |
                      +----------+------------+
                                 |
                   human report + mode marker + machine appendix
```

## 8. 失败和边界处理

- 配置缺失、类型错误或未知字符串：使用模板模式。
- Ledger 中的 supporting ID 不存在：忽略该 ID；若没有有效 supporting facts，严格模式不生成因果框。
- 只有一个因果角色：展示该事实的中性核心摘要，不伪造缺失环节。
- 多实体：不生成跨实体因果框，两种模式都按实体展示观测摘要。
- 空 Ledger：核心维度显示 `not_executed`，核心结论说明当前没有可用核心数据。
- 模型 chain 非空：不进入确定性核心段；保留现有经 Fact marker 校验的补充叙述路径。
- 模板模式不降低 remediation 写操作门禁，也不改变 canonical/trusted-legacy 来源选择。

## 9. 测试设计

实现必须按两个独立 red-green 循环完成。

### 循环一：维度真实性

1. 通过 `ConclusionFormatterNode._apply_fact_ledger_report_contract()` 输入仅含 Kubernetes state Fact、
   且没有 Metrics/Logging/Tracing coverage；断言三个缺失维度为未执行/未验证，并禁止完成措辞。
2. 输入明确 empty coverage；断言仅该维度显示查询完成，并展示 coverage 的真实来源。
3. 保留现有“真实信号优先于空 provider coverage”行为。

### 循环二：报告模式

1. 默认配置和显式 `false` 均选择模板模式；同一组 configuration/state/measurement facts 稳定生成
   结构化数据关联，不依赖传入的 LLM chain。
2. 显式 `true` 选择严格模式；当 supporting 只有 state Fact 时，非 supporting configuration 和
   measurement 可以留在观测摘要，但不得进入核心结论或严格因果框。
3. 严格模式下 configuration/state/measurement 都是 validated supporting 时，生成完整三段因果框。
4. 两种模式都忽略一个包含未支持精确值的显式 LLM chain。
5. 配置缺失、非法字符串回退到模板模式；布尔字符串按既有 parser 行为解析。
6. 现有多实体隔离、grounded narrative、span 摘要、remediation 和机器附录测试继续通过。

## 10. 修改范围

预计只修改：

- `app/core/workflow/report_presentation.py`
- `app/core/workflow/nodes/conclusion_formatter.py`
- `tests/unit/workflow/test_report_presentation.py`
- `tests/unit/workflow/test_ask_conclusion_remediation_json.py` 或现有最邻近的 conclusion config 测试文件
- `deploy/configmap/config.yaml`
- 本设计与后续实施计划/agent-loop 证据文件

## 11. 非目标

- 不修改 Fact Ledger schema、MCPStander 或 data 采集协议；
- 不新增角色级 causal Fact ID schema；
- 不修复 `VERSION=11.0.86` 与部署 tag `11.0.82` 的不一致；
- 不验证 live image、provider、MCP、模型延迟或 Evidence ReAct 集成；
- 不改工作流拓扑、Prompt 或 remediation policy；
- 不增加任何 OOM、CrashLoop、ImagePull 等故障专用规则。

## 12. 完成标准

只有以下结果均有 fresh evidence 时才算完成：

1. 无 Fact/coverage 的核心维度不再冒充查询完成；
2. 默认模板模式能从核心 FactRecords 稳定生成自然的结构化摘要；
3. strict 开关默认关闭，并可通过 ConfigMap 明确开启；
4. strict 模式核心结论和因果框只包含 validated supporting facts；
5. 未带角色级 Fact IDs 的显式 LLM chain 不进入两种模式的确定性核心段；
6. focused 与 adjacent 回归通过；
7. 用户现有 dirty 文件和任务允许路径之外的内容没有变化；
8. 独立 reviewer 给出 `ACCEPT`。
