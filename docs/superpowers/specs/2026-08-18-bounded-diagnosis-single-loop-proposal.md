# Bounded Diagnosis Single Loop Proposal

## 1. Decision

在每个 parallel lane 内，用一个代码控制的 `BoundedDiagnosisLoop` 取代当前
“LLM 规划采证 + ReAct 自主补证 + RCA 泛化重试”组合。该 loop 专门面向本地
Qwen 小模型，模型只做两件事：提出语义假设，以及说明一次补采集的预期信息
增益。实体身份、Fact、查询执行、校验、预算和停止均由代码负责。

唯一交付物为 `aiops.bounded-diagnosis-loop.v1`。它写入现有
`LaneDiagnosisArtifact v2` 的 `rca_attempts` component；现有 `snapshot`、
`selection_manifest`、`rca_input`、`selected_rca`、`claim_validation`、
`final_projection` 和 `terminal_error` 继续各司其职，不再存在另一个隐式 agent
loop 或第三次分析。

硬约束：

- 每 lane 最多 **2 个实际 LLM HTTP 请求**；调用超时或无效响应也计数；
- 最多 **1 轮**定向补采集；
- 该轮最多 **2 个**定向只读工具调用；发出请求即计数，超时不重试；
- 第二个 LLM 槽位只能二选一：`final_after_follow_up` 或 `repair_initial`；
- 禁止按 Case、命名空间/工作负载名、错误文本、Reason、退出码或指标名分支；
- parallel conclusion 只渲染验证后的 lane artifact，不再增加 per-lane LLM 调用。

初始证据是 loop 的前置输入。parallel lane 的基线采集必须改成代码拥有的最小
只读 source plan，不使用 lane LLM；计划只按权威实体、source capability、
Fact 合同和配置启用状态生成。本文所称“最多 2 个定向工具调用”只指第一次 RCA
明确请求的唯一补采集轮，不把已经完成的基线 source plan 混入该计数。

## 2. Responsibility boundary

代码负责：

- 固定 lane 的 namespace/name/UID 和 canonical entity ID；
- 执行无 LLM 的基线 source plan，并将工具 observation 归一化为完整 Fact；
- 保留 lossless snapshot，生成 bounded selection manifest；
- 维护物理 LLM、补采集轮、工具调用、deadline 和第二槽位预算；
- 把模型的 capability intent 绑定到只读工具和权威实体参数；
- 校验查询范围、参数 schema、重复/包含查询、Fact ID 和 proposition；
- 计算增量 Fact、执行终止规则、持久化终态和确定性渲染。

Qwen 负责：

- 用当前 Facts 提出至多三个可区分的语义假设；
- 判断当前证据是否足够发布根因；
- 若不足，解释为什么仅再采一次值得、将区分什么，以及不同结果如何改变判断；
- 为补采集提出至多两个 capability-level information request；
- 将 Fact 绑定成 open-world propositions，并给出简短解释。

模型不选择实际 tool name，不修改实体参数，不认定 Fact 是否有效，也不决定预算
是否充足。自由文本没有事实权威。

## 3. State machine

```text
BASELINE_FACTS
  | snapshot/identity invalid ------------------------------> ERROR
  v
PASS_1_RESERVED -> QWEN_PASS_1
  | timeout/empty ------------------------------------------> INCONCLUSIVE
  | schema or repairable binding invalid
  |   -> reserve shared slot as repair_initial
  |   -> QWEN_PASS_2_REPAIR
  |        | valid diagnosed -------------------------------> DIAGNOSED
  |        | otherwise/timeout -----------------------------> INCONCLUSIVE
  |
  | valid diagnosed + proposition gate passes -------------> DIAGNOSED
  | valid inconclusive + no/denied follow-up --------------> INCONCLUSIVE
  v
FOLLOW_UP_ADMISSION
  | reject -------------------------------------------------> INCONCLUSIVE
  v
ONE_FOLLOW_UP_ROUND (1..2 directed calls, no retry)
  | no new diagnostic Fact --------------------------------> INCONCLUSIVE
  | trustworthy snapshot cannot be produced --------------> ERROR
  v
PASS_2_RESERVED as final_after_follow_up -> QWEN_PASS_2_FINAL
  | valid proposition gate passes -------------------------> DIAGNOSED
  | otherwise/timeout -------------------------------------> INCONCLUSIVE
```

`PASS_1_RESERVED` 和 `PASS_2_RESERVED` 在网络请求前原子递增预算。任何 transport
fallback 都不得在同一 reserve 下再发请求。本地网关启动时只选择一种已探测模式：
原生 JSON schema 或单次 plain-JSON generation；禁止当前 `native -> text fallback`
在一次逻辑调用中消耗两个实际请求。

## 4. Strict prompt 1: assess, diagnose, or request one follow-up

Prompt 输入由代码拼接，动态数据只放 user message。`available_capabilities` 是中央
只读 capability registry 的投影，含 capability ID 和参数 JSON schema；不提供
Case 示例、已知错误文本或指标示例。

### System prompt

```text
你是本地 AIOps 根因分析器。只基于输入中的权威实体和完整 Fact 记录工作。

你的任务只有三个：
1. 提出最多 3 个可由当前 Fact 区分的语义假设；
2. 判断证据是否足以发布一个 Fact-bound 根因；
3. 若不足，判断唯一一次定向补采集是否有明确、较高的信息增益。

硬规则：
- 不调用工具，不输出工具名，不改变 authoritative_entity_id。
- 不引用输入中不存在的 fact_id。
- diagnosed 必须给出 primary causal proposition；每个 proposition 必须精确绑定
  fact_id、attribute、value_pointer、operator、expected_value 和 relation。
- 证据不足时必须 inconclusive，禁止用经验补齐事实。
- follow_up.decision=request 仅在 evidence_sufficiency=insufficient 且
  diagnostic_status=inconclusive 时允许。
- 请求最多 2 个，只能选择 available_capabilities 中的 capability_id，并遵守其
  parameters schema。请求表达要回答的语义问题；系统代码决定实际工具和实体参数。
- 每个请求必须说明：当前哪些 Fact 暴露了缺口、区分哪些 hypothesis、期望获得
  什么新 observation，以及 present/absent 两类结果分别怎样改变最终判断。
- 若补采只会增加背景、重复已有查询、扩大实体范围或不能改变任何判断，必须拒绝补采。
- 不输出 Markdown、代码围栏或额外解释，只输出一个 JSON object。

输出必须严格满足 DiagnosisPass1Output；未知字段禁止出现。
```

### User message

```text
{
  "contract_version": "aiops.diagnosis-pass1-input.v1",
  "authoritative_entity_id": <code-owned string>,
  "question": <string>,
  "selection_manifest": <code-owned object>,
  "facts": <complete selected FactRecord array>,
  "coverage_and_limitations": <code-owned object>,
  "prior_query_digests": <string array>,
  "available_capabilities": <capability id + parameter schema array>,
  "remaining_budget": {
    "llm_calls": 1,
    "follow_up_rounds": 1,
    "directed_tool_calls": 2
  }
}
```

### `DiagnosisPass1Output`

```json
{
  "contract_version": "aiops.diagnosis-pass1-output.v1",
  "evidence_sufficiency": {
    "verdict": "sufficient|insufficient",
    "reason": "short evidence-specific reason",
    "decisive_fact_ids": ["fact-..."],
    "blocking_unknowns": ["one concrete unanswered question"]
  },
  "hypotheses": [
    {
      "hypothesis_id": "h1",
      "statement": "semantic causal hypothesis",
      "supporting_fact_ids": ["fact-..."],
      "contradicting_fact_ids": ["fact-..."],
      "confidence": 0.0
    }
  ],
  "diagnosis": {
    "diagnostic_status": "diagnosed|inconclusive",
    "primary_hypothesis_id": "h1|null",
    "summary": "short explanation",
    "propositions": [
      {
        "subject_entity_id": "exact authoritative entity id",
        "fact_id": "fact-...",
        "attribute": "exact FactRecord.attribute",
        "value_pointer": "RFC 6901 pointer or empty string",
        "operator": "observed|equals|contains|gt|gte|lt|lte",
        "expected_value": null,
        "relation": "causal|corroborating|contradicting|context"
      }
    ],
    "primary_proposition_index": 0,
    "supporting_fact_ids": ["fact-..."],
    "contradicting_fact_ids": ["fact-..."]
  },
  "follow_up": {
    "decision": "none|request",
    "why_one_more_round_is_worthwhile": "specific reason or empty string",
    "expected_information_gain": {
      "level": "none|low|medium|high",
      "ambiguity_resolved": "which competing explanations will be separated",
      "decision_changes": [
        {
          "outcome": "bounded observable outcome",
          "effect": "promote h1|promote h2|exclude hypothesis|remain inconclusive"
        }
      ]
    },
    "requests": [
      {
        "request_id": "q1",
        "question": "single discriminating evidence question",
        "motivating_fact_ids": ["fact-..."],
        "target_hypothesis_ids": ["h1"],
        "capability_id": "one supplied capability id",
        "parameters": {},
        "expected_new_observation": "what new source observation is sought",
        "effect_if_present": "specific decision effect",
        "effect_if_absent": "specific decision effect"
      }
    ]
  }
}
```

Schema 另加约束：`hypotheses.maxItems=3`、`requests.maxItems=2`；confidence 是
0..1 数字。`diagnosed` 要求 sufficient、非空 propositions 和有效 primary index；
`request` 要求 insufficient、inconclusive、information gain 为 medium/high、至少
两个不同的 decision effects。代码以 proposition validator 的结果为准。

## 5. Follow-up admission and execution

代码仅在以下条件全部成立时触发补采集：

1. pass 1 通过 JSON schema、实体、Fact membership 和 hypothesis reference 校验；
2. 输出明确为 `insufficient + inconclusive + request`；
3. “为什么值得”非空，信息增益为 medium/high，至少一个可能 outcome 会改变
   hypothesis 排序、排除候选或满足/破坏发布门；
4. 1..2 个 request 均引用已有 motivating Facts 和合法 hypothesis；
5. capability 可用、只读，parameters 通过 registry schema，代码能强制绑定本 lane
   的 namespace/name/UID，且不会扩大实体或时间范围上限；
6. 规范化 query digest 未出现过，也不被一次既有查询完全包含；
7. 第二 LLM 槽位、1 轮 follow-up、工具数和 lane deadline 均足够。

任一条件不成立即拒绝补采集并终止为 `inconclusive`，记录稳定 reason code；不会
为了让模型“再想一次”而调用第二次 LLM。合法的两个 request 可在同一轮并行，
每个 request 只能映射到一次工具调用。工具内部 agent、链式调用和自动重试关闭。

结果经通用 adapter 做身份、source status、Fact schema、evidence ref 和内容 digest
校验后合并 snapshot。`new_fact_ids` 只含此前 snapshot 中不存在且 canonical content
不等价的新 Fact；coverage/error/context-only 记录仍保留，但另算
`new_diagnostic_fact_ids`。

## 6. Strict prompt 2: final after follow-up or one repair

第二提示词只有一个模板，通过 `second_call_mode` 明确二选一用途。输出无
`follow_up` 字段，模型不能再请求数据。

### System prompt

```text
你是本地 AIOps 最终根因分析器。这是本 lane 最后一次模型调用。

second_call_mode 只有两种：
- final_after_follow_up：一次定向补采集已经结束；比较 before Facts 与新增 Facts，
  给出最终 diagnosed 或 inconclusive。
- repair_initial：第一次输出仅因给定的 schema/binding errors 被拒绝；只修复结构和
  Fact 绑定，不能请求或假设新证据。

硬规则：
- 不调用工具，不请求补采集，不改变 authoritative_entity_id。
- 只使用输入中的 Fact；validation_errors 是约束，不是环境事实。
- diagnosed 必须有一个 exact primary causal proposition；inconclusive 可以无 proposition。
- supporting_fact_ids 必须等于 causal/corroborating propositions 的 Fact ID 有序并集。
- 不引用未知 Fact，不把 coverage/context-only Fact 当 primary cause。
- final_after_follow_up 必须说明新增 Fact 是否真正改变了 hypothesis；未解决关键缺口
  就保持 inconclusive。
- repair_initial 只允许修复机器指出的字段；不得换成一个没有 Fact 支持的新故事。
- 不输出 Markdown、代码围栏或额外解释，只输出一个 JSON object。

输出必须严格满足 FinalDiagnosisOutput；未知字段禁止出现。
```

### User message

```text
{
  "contract_version": "aiops.diagnosis-pass2-input.v1",
  "second_call_mode": "final_after_follow_up|repair_initial",
  "authoritative_entity_id": <code-owned string>,
  "pass1_output": <model output or parsed partial>,
  "validation_errors": <code-owned error array; repair mode only>,
  "before_fact_ids": <string array>,
  "facts": <final selected complete FactRecord array>,
  "follow_up_execution": {
    "requested_ids": <string array>,
    "executed_query_digests": <string array>,
    "tool_outcomes": <success|empty|timeout|error array>,
    "new_fact_ids": <string array>,
    "new_diagnostic_fact_ids": <string array>
  },
  "selection_manifest": <code-owned object>
}
```

### `FinalDiagnosisOutput`

```json
{
  "contract_version": "aiops.final-diagnosis-output.v1",
  "diagnostic_status": "diagnosed|inconclusive",
  "primary_hypothesis_id": "h1|null",
  "evidence_change": {
    "changed_the_decision": true,
    "new_fact_ids_used": ["fact-..."],
    "remaining_unknowns": ["concrete unresolved question"]
  },
  "summary": "short evidence-bound conclusion",
  "propositions": [
    {
      "subject_entity_id": "exact authoritative entity id",
      "fact_id": "fact-...",
      "attribute": "exact FactRecord.attribute",
      "value_pointer": "RFC 6901 pointer or empty string",
      "operator": "observed|equals|contains|gt|gte|lt|lte",
      "expected_value": null,
      "relation": "causal|corroborating|contradicting|context"
    }
  ],
  "primary_proposition_index": 0,
  "supporting_fact_ids": ["fact-..."],
  "contradicting_fact_ids": ["fact-..."],
  "causal_explanation": ["short ordered semantic steps"],
  "confidence": 0.0,
  "limitations": ["evidence boundary"]
}
```

第二次输出失败、超时或 proposition gate 不通过时直接 `inconclusive`，不允许第三次
修复。`repair_initial` 输入不含可执行 capability，且即使模型输出类似请求字段也会
因 `extra=forbid` 被拒绝。

## 7. Budget and stop rules

Budget ledger 是代码拥有的 append-only 状态：

```json
{
  "llm_limit": 2,
  "llm_used": 0,
  "second_slot": "available|final_after_follow_up|repair_initial|spent",
  "follow_up_round_limit": 1,
  "follow_up_rounds_used": 0,
  "directed_tool_limit": 2,
  "directed_tools_used": 0,
  "seen_query_digests": [],
  "deadline_at": "code-owned monotonic deadline"
}
```

停止规则：

- **证据充分**：pass 1 diagnosed 且 proposition gate 通过，立即 diagnosed；不补采、
  不调用 pass 2。
- **拒绝补采**：低/无信息增益、无 decision change、范围漂移、capability 不可用、
  schema 不合法、预算/deadline 不足或请求超过 2 个，立即 inconclusive。
- **无新 Fact**：一轮执行后 `new_diagnostic_fact_ids=[]`，不浪费第二 LLM 槽位，
  立即 inconclusive，reason=`follow_up_no_new_diagnostic_fact`。empty/coverage 仍归档。
- **重复查询**：代码按 capability、权威实体和规范化 parameters 计算 digest；相同或
  被既有查询包含的请求不执行、不计工具调用。若无可执行 request，立即 inconclusive。
- **工具超时**：dispatch 已计一次工具调用；不重试。若同轮另一调用产生新诊断 Fact，
  timeout 作为 limitation 进入 pass 2；否则按无新 Fact 终止 inconclusive。
- **LLM 超时**：reserve 已计一次 LLM；不做 transport retry。pass 1 超时直接
  inconclusive；pass 2 超时也直接 inconclusive。
- **结构修复**：只对 JSON schema、未知/错位 Fact binding、primary index、support-set
  equality 等机器可指明错误使用第二槽位。缺少 causal Fact、低质量 Fact、忽略更强
  candidate 属于证据问题，不允许用 repair 重写故事。
- **补采后终止**：pass 2 是最终调用；valid gate 通过才 diagnosed，否则 inconclusive。
- **error**：仅在权威身份无法建立、基线 snapshot/Fact integrity 无法信任、final
  snapshot 无法构造，或 artifact write/hash verification 失败时使用。工具/LLM 不可用、
  empty、timeout、解析失败但 snapshot 仍可信时均为 inconclusive，不升级为 error。
- **lane deadline**：停止发起新工作并取消尚未 dispatch 的 request。已有可信 snapshot
  可落盘则 inconclusive；无法完成可信 artifact 则由 total join 记录 error lane。

## 8. Single loop artifact

```json
{
  "contract_version": "aiops.bounded-diagnosis-loop.v1",
  "group_id": "g1",
  "authoritative_entity_id": "k8s.pod:namespace/name:uid",
  "terminal_status": "diagnosed|inconclusive|error",
  "terminal_reason_code": "stable-code",
  "budget": {
    "llm_limit": 2,
    "llm_used": 1,
    "second_slot": "available|final_after_follow_up|repair_initial|spent",
    "follow_up_round_limit": 1,
    "follow_up_rounds_used": 0,
    "directed_tool_limit": 2,
    "directed_tools_used": 0
  },
  "initial_snapshot_ref": {},
  "pass1": {"input_ref": {}, "model_ref": {}, "validation_ref": {}},
  "follow_up": {
    "admission": {},
    "request_query_digests": [],
    "observation_refs": [],
    "new_fact_ids": [],
    "new_diagnostic_fact_ids": []
  },
  "pass2": {
    "mode": "none|final_after_follow_up|repair_initial",
    "input_ref": {},
    "model_ref": {},
    "validation_ref": {}
  },
  "final_snapshot_ref": {},
  "selected_rca_ref": {},
  "claim_validation_ref": {},
  "transition_log": [
    {"from": "BASELINE_FACTS", "to": "PASS_1_RESERVED", "reason_code": "ready"}
  ]
}
```

该对象是审计“为什么调用第二次模型/为什么补采/为什么停止”的唯一事实来源。
预算值、query digest、Fact delta 和 transition 由代码填写，模型不能回写。

## 9. Current implementation gaps and replacement points

当前工作树已具备 B3 的重要底座，但还不是 bounded loop：

- `nodes/parallel_evidence.py` 已有单 Pod lane、total result、error lane 和
  `LaneDiagnosisArtifact v2` 持久化；保留 fan-out/total-join，将 lane worker 中
  `EvidenceCollectorNode.execute() -> RootCauseAnalyzerNode.execute()` 替换为一个
  `BoundedDiagnosisLoop.run()`。
- `nodes/evidence_collector.py` 当前先调用 structured plan LLM，再进入 max_steps=20
  的工具 agent；协议失败还能重试，并存在 post-case refinement/reconciliation。
  它没有每 lane 2 LLM、1 follow-up round、2 directed tools 的共同 budget。parallel
  lane 应改走无 LLM baseline collector；旧 collector 只保留不在本设计范围的兼容路径。
- `nodes/root_cause_analyzer.py` 当前第一次 RCA 后，只要有 eligible Fact 且结果
  inconclusive/claim invalid，就调用第二次泛化 repair；第一次输出没有证据充分性、
  补采理由或预期信息增益合同。以本文 pass 1/pass 2 controller 取代
  `_should_repair_rca()` 的开放条件。
- 当前 RCA structured 调用启用了 `allow_text_fallback=True`；底层
  `call_structured()` 可能先发 native 请求再发 text fallback。新 one-shot Qwen adapter
  必须让预算对应实际 HTTP 请求。
- `schemas.py::RCAOutput` 和 `fact_contract.py::validate_rca_claims()` 当前主要验证
  Fact membership、scope 和 quality，尚不能证明自由文本 claim 被 exact
  attribute/pointer/value entail。新增本文两份 output schema，并接入 B3 设计中的
  open-world proposition validator；validator 是唯一 publication gate。
- `entity_evidence_snapshot.py` 的 lossless snapshot + SelectionManifest v2 可复用；
  follow-up 后只追加通过合同的 Facts，并重新生成 selection manifest，禁止让模型改 Fact。
- `lane_diagnosis_artifact.py` 的 diagnosed/inconclusive/error、hash 验证和八个 component
  可复用；把 `rca_attempts` 内容升级为本文 single loop artifact。
- `nodes/conclusion_formatter.py` 的 multi-group 确定性 fan-in 方向可复用；必须只读取
  `validated_supporting_fact_ids` 和 resolved primary proposition，禁止重新选 support，
  也禁止为 lane 结论增加额外 LLM。
- `prompts.py` 当前 evidence/RCA prompt 含大量已知错误文本、指标/命令示例和自主
  ReAct 停止指令。parallel bounded path 只使用本文两份提示词；生产 admission 和
  termination 不检查这些文本或名称。

建议新增一个聚焦 owner（例如 `app/core/workflow/bounded_diagnosis_loop.py`）保存状态机、
budget ledger、admission 和 artifact projection；提示词与 schema 放独立模块。不要把
这些分支继续堆入已很大的 evidence collector、RCA node 或 Fact contract。

## 10. Acceptance checks

最小验收集：

1. 每条 lane execution trace 的实际 LLM request 数 `<=2`，包含 native/fallback/timeout；
2. 第二槽位不可能同时出现 repair 和 final-after-follow-up；
3. follow-up round `<=1`，directed dispatch `<=2`，所有 query digest 唯一；
4. pass 1 必须明确 sufficiency、值得补采的原因和 expected information gain；
5. 无新诊断 Fact、重复查询、工具/LLM timeout 均按本文规则停止且不重试；
6. 任意未知 attribute/value proposition 可验证，错误 pointer/value/entity 必须拒绝；
7. diagnosed 的 support set 在 claim、selected RCA、final projection、artifact 和 report
   完全一致；
8. 搜索生产 diff 不出现 Case/fixture、已知错误文本、退出码或指标名驱动的新分支；
9. 每个输入 lane 都有一个可 hash-verify 的 terminal artifact 和 single loop artifact。
