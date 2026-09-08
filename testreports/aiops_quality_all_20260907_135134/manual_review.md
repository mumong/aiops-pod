# 550 次 AIOps 报告人工审查

[返回原始指标总览](readme.md)

## 结论

本次 11 个 Case × 50 次全部完成，550/550 请求成功；完成于 2026-09-08 08:32:15（runner 记录的本地时间）。所有最终报告均已逐份阅读根因结论。原始评分版本为 `2026-09-07.4`。本审查没有修改 Agent、根因匹配规则、Case 合同或既有评分文件。

人工按下述“主要故障机制”口径：490 份通过、37 份不通过、23 份待复核。与脚本相比有 39 份明确偏低、4 份明确偏高；另有 23 份不强行判定。不能把所有未通过都解释成脚本误判，也不能把原始 85.1% 当作逐句正确率。

人工主要机制通过占全部报告 89.1%。这是本次宽于精确字符串规则的审查结果，不替换原始 85.1%；待复核项不并入通过数。它不是源端事实逐条认证，也不是通用生产准确率。

## 审查口径与边界

- 阅读对象是每份 `report.md` 的根因结论段，包含提取出的所有异常组，而非只看被脚本判失败的报告。`manual_review.json` 为 550 份记录各自保存 Run ID、判断、理由、原始评分和报告 SHA-256。
- 通过：主要失效机制正确，允许不改变机制的同义表达、精确字串遗漏、未定位更深的代码行/控制器身份。只列候选并明确无法确认主要机制，不算通过。
- 不通过：主要机制错误或诊断未完成。待复核：错误的具体修复目标、前后冲突、严重证据矛盾或额外集群异常尚未独立验证。
- “通过”不表示整段解释正确。尤其 137≠OOM、44Mi<64Mi、Running≠故障修复、容器退出≠自动删除 Pod；这些错误不能被主机制命中掩盖。
- 提问是“我的集群有什么问题？”。额外 Prometheus 异常可能是真实环境干扰，不能仅因不在当前 Case 预期中就认定 Agent 幻觉；它的时效和因果须另行复核。
- 本轮未逐条回读 550 份报告背后的全部原始事实、整改建议和执行效果；没有重新运行集群故障。人工意见不是新一轮机器重评分。
- 固定实验程序主动输出 `runtime_exit`、`config_missing_exit`、`oom_growth`、`readiness_fail` 等故障模式。这种可观测线索是合法报告证据，但会使测试比未知生产故障容易；同一 fixture 重复 50 次衡量重复稳定性，不是 50 种独立故障。

## 各 Case 的人工结果

| Case | 原脚本根因准确率 | 人工通过 | 人工不通过 | 待复核 | 明确偏低 | 明确偏高 |
|---|---:|---:|---:|---:|---:|---:|
| [c01](c01/readme.md) | 92.0% | 48/50 | 1/50 | 1/50 | 2 | 0 |
| [c02](c02/readme.md) | 98.0% | 49/50 | 1/50 | 0/50 | 0 | 0 |
| [c03](c03/readme.md) | 98.0% | 49/50 | 0/50 | 1/50 | 0 | 0 |
| [c04](c04/readme.md) | 98.0% | 49/50 | 1/50 | 0/50 | 0 | 0 |
| [c05](c05/readme.md) | 94.0% | 50/50 | 0/50 | 0/50 | 3 | 0 |
| [c06](c06/readme.md) | 72.0% | 46/50 | 2/50 | 2/50 | 12 | 2 |
| [c07](c07/readme.md) | 94.0% | 44/50 | 0/50 | 6/50 | 2 | 0 |
| [c08](c08/readme.md) | 94.0% | 49/50 | 0/50 | 1/50 | 3 | 0 |
| [c09](c09/readme.md) | 84.0% | 48/50 | 1/50 | 1/50 | 8 | 1 |
| [c10](c10/readme.md) | 32.0% | 17/50 | 25/50 | 8/50 | 5 | 1 |
| [c11](c11/readme.md) | 80.0% | 41/50 | 6/50 | 3/50 | 4 | 0 |

明确偏低：原脚本失败、人工主要机制通过。明确偏高：原脚本通过、人工主要机制不通过。待复核不算作两者。

## 重点问题

### 1. c10 的低分主要有真实诊断问题

c10 的预期机制是 `/health` 返回 HTTP 500 → Liveness Probe 连续失败 → kubelet 终止并重启容器。本轮人工仅 17 份主要机制通过，25 份不通过，8 份待复核，不能靠放宽关键词把 32% 合理提高到接近 100%。

例如 [c10 #25 · 8fc23f6dff4c4e98](c10/run-25-8fc23f6dff4c4e98/report.md) 把“Exit Code 137＋96Mi”称为充分且不可辩驳的 OOM 证据；这是错误推理。[c10 #30 · fa163027a415434c](c10/run-30-fa163027a415434c/report.md) 主要根因仍是内存不足，但因包含 Liveness 500 链条而被脚本判通过，属于明确偏高。

另一方面 [c10 #13 · b5770abec6044924](c10/run-13-b5770abec6044924/report.md)、[c10 #21 · a003be2518b04e1d](c10/run-21-a003be2518b04e1d/report.md)、[c10 #47 · 3c4b09dc10ca4b52](c10/run-47-3c4b09dc10ca4b52/report.md)、[c10 #48 · 5bb155d65451412d](c10/run-48-5bb155d65451412d/report.md)、[c10 #49 · b8d54dfdf07044d7](c10/run-49-b8d54dfdf07044d7/report.md) 已定位探针终止机制，脚本仍未通过，属于明确偏低。

### 2. c06 的精确字串和不确定性规则偏严，但也有误放行

12 份主要运行时退出机制已正确，却因退出码措辞、缺少具体堆栈或 OOM 排除句等未通过。反例：[c06 #10 · 8c2e19f102ac4433](c06/run-10-8c2e19f102ac4433/report.md) 把 allocated_mib=0 当内存分配异常；[c06 #16 · 9c88f92591db4eb0](c06/run-16-9c88f92591db4eb0/report.md) 把处理请求后的退出确认为应用入口点错误。这两份脚本反而通过。

### 3. c09、c11 的“未知”要区分层次

已确认 503 就绪失败，仅未知哪个真实下游；已确认 finalizer 阻断，仅未知哪个控制器负责——不等于主要机制未识别。但明确缺少 finalizer 存在证据、无法判断到底哪个机制阻断删除，则不能强行判对。

[c09 #12 · 90cad484f4c64c60](c09/run-12-90cad484f4c64c60/report.md) 将目标 Pod 自身 IP 当成外部故障依赖，脚本漏掉了实体错误。c11 多份报告虽然识别 finalizer，却额外编造 OOM→自动删除的前置因果；主要机制通过不能为此背书。

### 4. Runbook 覆盖率没有发现漏记期望手册

逐次将 `events.json` 中 fetch_runbook 的返回手册标题与期望手册比对（只认取得的手册，不用正文交叉提及），550 次期望命中集合均与评分一致。此核验不证明手册在每个 lane 使用得正确，也不惩罚无关手册。

- c08：50 次中仅 16 次取得 pod-oomkilled；42 次取得 pod-crashloop-runtime。32% 是当前“期望手册覆盖”口径的真实低覆盖，而不是根因机制都没判断出来。
- c10：44 次取得 pod-crashloop-runtime，仅 2 次取得 pod-notready-probe-failed；每次期望两本，因此平均覆盖为 (44+2)/(50×2)=46%。
- c07：两本期望手册全部必要，是测试口径而非业务定律。只用一本便正确诊断时，根因可通过但 Runbook 为 50%，两项并不矛盾。
- 覆盖率不测选择精确性：多取无关 Runbook 不扣分。不能把 100% 覆盖解释成 100% 选用正确。

### 5. 证据均值计算正确，但计划匹配本身有偏差

550 份 score 的计数均与 554 个 Evidence lane 归档的 plan_total/plan_collected 加总一致。按当前实现排除 optional/reference 等非计分 inventory 项后，554 个 lane 的清单计数也全部可复算一致。

当前公式：

```text
单次证据率 = 同次所有 lane 的 Σplan_collected / Σplan_total
Case 证据率 = 该 Case 各有效成功运行的单次证据率算术平均
总体证据率 = 各有效 Case 证据率算术平均
```

本轮总体为 81.5304538895% → 81.5%，不是把所有运行的完成/计划数量合并计算。没有算术错误，但评分器直接读取 Agent 产生的完成计数，不是在测试侧独立核对“每个目标问题确实由工具证据回答”。

实际矛盾：[c08 #1 · 06808c8c78c8404a](c08/run-01-06808c8c78c8404a/report.md) 的备用计划要求确认 Pod 当前状态/事件，工具 kubectl_describe 已成功返回目标 Pod 的 OOMKilled、137、BackOff，inventory 的 structured-plan-fallback-1 却仍为未完成，得分4/5。同类“备用计划未完成且同 lane 有成功 describe”的候选共89个，尚未对89个逐一证明所有参数/语义等价，不将其全部机械加分。

代码中的 pod_lifecycle 匹配在缺少结构化 kind 时偏向 deletionTimestamp/finalizers/Terminating 标记，可能拒绝能够回答一般状态问题的 describe。这个偏差来自 Agent 归档匹配逻辑；本轮不修改主程序，也不在测试端悄悄重定义通过。

未完成的拓扑门槛项有307个 lane，其中306个对应 lane 的 tool_data 未归档 query_pod_topology；不等于307次工具报错或后端无数据。还有 YAML、previous logs 等未完成项。每项详情可查看 evidence.archive.json 的 evidence_plan、evidence_inventory、tool_data。

另外，计数规则并不简单等于 evidence_plan 的 counts_for_completeness 标志：当前实现按 inventory 的来源/level/描述过滤。不能直接按 YAML 清单长度或原标志重算并宣称评分错误。成功负观测可能回答排除问题；也不能一律把 empty 算作成功正向证据。

### 6. MTTR 和请求成功率不能代替全链路稳定性

单次请求耗时的 Case 等权平均为 120.512 秒；最大单次 693.819 秒，超过300秒的运行共31次。550次均有 run_start、final、run_end，没有客户端重新发起导致的额外 run_start。整个串行实验含注入/等待/清理耗时约18.68小时。

`MTTR` 在本脚本实际表示请求到最终结果的诊断耗时，不是从故障开始到资源修复恢复的真实 MTTR。本轮虽550/550请求成功，仍记录292条 status=error 的工具结果事件（包含模型尝试不存在工具名等）；不能据此声称所有 Logging/Tracing/Metrics 调用都成功。

## 后续优先级（本轮不改评分）

1. 保留 c10 的负例，不为提高分数放宽到只要出现探针词就通过；明确 137 只能证明 SIGKILL 这一常见解释，不能单独证明 OOM。
2. 将本次偏低、偏高、否定句、未知细节和同义词报告加入冻结回归集；将来改评分必须同时跑正反例，并保留独立留出报告，避免为本批答案过拟合。
3. 把主机制命中、实体/数值正确性、证据绑定充分性分开审计；用户展示仍可保留一个根因准确率，后台保留明确失败理由。
4. 将全局发现任务与单 Case 预期的范围差异显式记录；额外异常先验证，不机械惩罚，也不机械放行。
5. 计划完成率继续保留原口径，同时单列匹配矛盾供审查，不把自报计划完成率包装成独立关键证据充分率。

## 每份报告的审查记录

以下均为独立人工意见，不回写 score.json。通过/不通过/待复核对应 pass/fail/review。

### c01

两份证据不足只涉及标签细节；一份真实 CPU 误诊；一份伴随集群外部异常，需区分目标命中与全报告范围准确性。

| # | 原脚本 | 人工意见 | 原始报告 | 理由 |
|---:|---|---|---|---|
| 1 | 通过 | 通过 | [897af6293e8c4228](c01/run-01-897af6293e8c4228/report.md) | 明确识别节点选择器/亲和性与节点标签不匹配导致 Pending。 |
| 2 | 通过 | 通过 | [f8a08058d70a4fe9](c01/run-02-f8a08058d70a4fe9/report.md) | 明确识别节点选择器/亲和性与节点标签不匹配导致 Pending。 |
| 3 | 通过 | 通过 | [df416d9cba0a43b1](c01/run-03-df416d9cba0a43b1/report.md) | 明确识别节点选择器/亲和性与节点标签不匹配导致 Pending。 |
| 4 | 通过 | 通过 | [a49ca1ce11c642eb](c01/run-04-a49ca1ce11c642eb/report.md) | 明确识别节点选择器/亲和性与节点标签不匹配导致 Pending。 |
| 5 | 通过 | 通过 | [8e54168ce3ee4d0e](c01/run-05-8e54168ce3ee4d0e/report.md) | 明确识别节点选择器/亲和性与节点标签不匹配导致 Pending。 |
| 6 | 未通过 | 通过 | [ae12fc3882dd4587](c01/run-06-ae12fc3882dd4587/report.md) | 主要机制已正确确认；仅具体标签键值未展示而声明证据不足，按主要根因口径属于脚本低估。 |
| 7 | 通过 | 通过 | [c1693277a6294a1d](c01/run-07-c1693277a6294a1d/report.md) | 明确识别节点选择器/亲和性与节点标签不匹配导致 Pending。 |
| 8 | 通过 | 通过 | [79124b1dbbe6429b](c01/run-08-79124b1dbbe6429b/report.md) | 明确识别节点选择器/亲和性与节点标签不匹配导致 Pending。 |
| 9 | 通过 | 通过 | [3f86d4d7d5a24fd6](c01/run-09-3f86d4d7d5a24fd6/report.md) | 明确识别节点选择器/亲和性与节点标签不匹配导致 Pending。 |
| 10 | 通过 | 通过 | [85a9382fa2524d5f](c01/run-10-85a9382fa2524d5f/report.md) | 明确识别节点选择器/亲和性与节点标签不匹配导致 Pending。 |
| 11 | 未通过 | 通过 | [b2916c91e921474b](c01/run-11-b2916c91e921474b/report.md) | 主要机制已正确确认；仅具体标签键值未展示而声明证据不足，按主要根因口径属于脚本低估。 |
| 12 | 通过 | 通过 | [8dc47e8023234ccb](c01/run-12-8dc47e8023234ccb/report.md) | 明确识别节点选择器/亲和性与节点标签不匹配导致 Pending。 |
| 13 | 通过 | 通过 | [41951bc6dd604424](c01/run-13-41951bc6dd604424/report.md) | 明确识别节点选择器/亲和性与节点标签不匹配导致 Pending。 |
| 14 | 通过 | 通过 | [f8b6bf227de84e15](c01/run-14-f8b6bf227de84e15/report.md) | 明确识别节点选择器/亲和性与节点标签不匹配导致 Pending。 |
| 15 | 通过 | 通过 | [3fb44f5767c7479e](c01/run-15-3fb44f5767c7479e/report.md) | 明确识别节点选择器/亲和性与节点标签不匹配导致 Pending。 |
| 16 | 未通过 | 待复核 | [efd6d89d335e4a10](c01/run-16-efd6d89d335e4a10/report.md) | 目标 c01 根因正确，但额外发布 Prometheus OOM 根因；问题是全局集群查询，不能仅凭额外实体判错，需核对该异常当时是否真实/当前。 |
| 17 | 通过 | 通过 | [ee4a7105e7764a91](c01/run-17-ee4a7105e7764a91/report.md) | 明确识别节点选择器/亲和性与节点标签不匹配导致 Pending。 |
| 18 | 通过 | 通过 | [e7550de3ed05412b](c01/run-18-e7550de3ed05412b/report.md) | 明确识别节点选择器/亲和性与节点标签不匹配导致 Pending。 |
| 19 | 通过 | 通过 | [04ee82f4527b4cf8](c01/run-19-04ee82f4527b4cf8/report.md) | 明确识别节点选择器/亲和性与节点标签不匹配导致 Pending。 |
| 20 | 通过 | 通过 | [1e837b11acef4317](c01/run-20-1e837b11acef4317/report.md) | 明确识别节点选择器/亲和性与节点标签不匹配导致 Pending。 |
| 21 | 通过 | 通过 | [f5c7d4597893461f](c01/run-21-f5c7d4597893461f/report.md) | 明确识别节点选择器/亲和性与节点标签不匹配导致 Pending。 |
| 22 | 通过 | 通过 | [65bcf64427084eb2](c01/run-22-65bcf64427084eb2/report.md) | 明确识别节点选择器/亲和性与节点标签不匹配导致 Pending。 |
| 23 | 通过 | 通过 | [db25288cb8ab45e7](c01/run-23-db25288cb8ab45e7/report.md) | 明确识别节点选择器/亲和性与节点标签不匹配导致 Pending。 |
| 24 | 通过 | 通过 | [f1d8e52bffe049d1](c01/run-24-f1d8e52bffe049d1/report.md) | 明确识别节点选择器/亲和性与节点标签不匹配导致 Pending。 |
| 25 | 通过 | 通过 | [f814988060754b9b](c01/run-25-f814988060754b9b/report.md) | 明确识别节点选择器/亲和性与节点标签不匹配导致 Pending。 |
| 26 | 通过 | 通过 | [8f4e5e3208f94beb](c01/run-26-8f4e5e3208f94beb/report.md) | 明确识别节点选择器/亲和性与节点标签不匹配导致 Pending。 |
| 27 | 通过 | 通过 | [387096591bb14e06](c01/run-27-387096591bb14e06/report.md) | 明确识别节点选择器/亲和性与节点标签不匹配导致 Pending。 |
| 28 | 通过 | 通过 | [9ffb899873444e54](c01/run-28-9ffb899873444e54/report.md) | 明确识别节点选择器/亲和性与节点标签不匹配导致 Pending。 |
| 29 | 通过 | 通过 | [a34da5e5e7d5401c](c01/run-29-a34da5e5e7d5401c/report.md) | 明确识别节点选择器/亲和性与节点标签不匹配导致 Pending。 |
| 30 | 通过 | 通过 | [841c10c7f825498d](c01/run-30-841c10c7f825498d/report.md) | 明确识别节点选择器/亲和性与节点标签不匹配导致 Pending。 |
| 31 | 通过 | 通过 | [f430596432fa491a](c01/run-31-f430596432fa491a/report.md) | 明确识别节点选择器/亲和性与节点标签不匹配导致 Pending。 |
| 32 | 通过 | 通过 | [2253c9700b534eed](c01/run-32-2253c9700b534eed/report.md) | 明确识别节点选择器/亲和性与节点标签不匹配导致 Pending。 |
| 33 | 通过 | 通过 | [9ccbdb9507274de3](c01/run-33-9ccbdb9507274de3/report.md) | 明确识别节点选择器/亲和性与节点标签不匹配导致 Pending。 |
| 34 | 未通过 | 不通过 | [952f997412ce4163](c01/run-34-952f997412ce4163/report.md) | 明确误诊集群 CPU 不足，没有识别注入的节点标签不匹配。 |
| 35 | 通过 | 通过 | [9821e24f886c459e](c01/run-35-9821e24f886c459e/report.md) | 明确识别节点选择器/亲和性与节点标签不匹配导致 Pending。 |
| 36 | 通过 | 通过 | [8be509fd2fa44de7](c01/run-36-8be509fd2fa44de7/report.md) | 明确识别节点选择器/亲和性与节点标签不匹配导致 Pending。 |
| 37 | 通过 | 通过 | [babd950420e543d5](c01/run-37-babd950420e543d5/report.md) | 明确识别节点选择器/亲和性与节点标签不匹配导致 Pending。 |
| 38 | 通过 | 通过 | [ca47a29ae19441eb](c01/run-38-ca47a29ae19441eb/report.md) | 明确识别节点选择器/亲和性与节点标签不匹配导致 Pending。 |
| 39 | 通过 | 通过 | [4984605cef1149eb](c01/run-39-4984605cef1149eb/report.md) | 明确识别节点选择器/亲和性与节点标签不匹配导致 Pending。 |
| 40 | 通过 | 通过 | [c468ac30d0a14434](c01/run-40-c468ac30d0a14434/report.md) | 明确识别节点选择器/亲和性与节点标签不匹配导致 Pending。 |
| 41 | 通过 | 通过 | [4147dc782df34ddf](c01/run-41-4147dc782df34ddf/report.md) | 明确识别节点选择器/亲和性与节点标签不匹配导致 Pending。 |
| 42 | 通过 | 通过 | [e8222354be7d42c9](c01/run-42-e8222354be7d42c9/report.md) | 明确识别节点选择器/亲和性与节点标签不匹配导致 Pending。 |
| 43 | 通过 | 通过 | [324c18f91558441b](c01/run-43-324c18f91558441b/report.md) | 明确识别节点选择器/亲和性与节点标签不匹配导致 Pending。 |
| 44 | 通过 | 通过 | [0ae51e80d4684682](c01/run-44-0ae51e80d4684682/report.md) | 明确识别节点选择器/亲和性与节点标签不匹配导致 Pending。 |
| 45 | 通过 | 通过 | [1560bbff97bf45df](c01/run-45-1560bbff97bf45df/report.md) | 明确识别节点选择器/亲和性与节点标签不匹配导致 Pending。 |
| 46 | 通过 | 通过 | [af0c90ed7dc44228](c01/run-46-af0c90ed7dc44228/report.md) | 明确识别节点选择器/亲和性与节点标签不匹配导致 Pending。 |
| 47 | 通过 | 通过 | [c5b7180142754d39](c01/run-47-c5b7180142754d39/report.md) | 明确识别节点选择器/亲和性与节点标签不匹配导致 Pending。 |
| 48 | 通过 | 通过 | [2eba48ab35c54ecd](c01/run-48-2eba48ab35c54ecd/report.md) | 明确识别节点选择器/亲和性与节点标签不匹配导致 Pending。 |
| 49 | 通过 | 通过 | [bd04bd38f54c494a](c01/run-49-bd04bd38f54c494a/report.md) | 明确识别节点选择器/亲和性与节点标签不匹配导致 Pending。 |
| 50 | 通过 | 通过 | [9c93b03ccf6740ff](c01/run-50-9c93b03ccf6740ff/report.md) | 明确识别节点选择器/亲和性与节点标签不匹配导致 Pending。 |

### c02

主根因49份正确，1份真正未确认；部分报告混淆节点DNS/CoreDNS或附加凭证解释，不证明这些次要解释正确。

| # | 原脚本 | 人工意见 | 原始报告 | 理由 |
|---:|---|---|---|---|
| 1 | 通过 | 通过 | [81598c3cefeb4b25](c02/run-01-81598c3cefeb4b25/report.md) | 明确识别无效镜像仓库 registry.invalid 的域名解析失败导致拉取失败。 |
| 2 | 通过 | 通过 | [86f8c12fbfb7497f](c02/run-02-86f8c12fbfb7497f/report.md) | 明确识别无效镜像仓库 registry.invalid 的域名解析失败导致拉取失败。 |
| 3 | 通过 | 通过 | [55fef972ab29469b](c02/run-03-55fef972ab29469b/report.md) | 明确识别无效镜像仓库 registry.invalid 的域名解析失败导致拉取失败。 |
| 4 | 通过 | 通过 | [f69edcbff4304dc8](c02/run-04-f69edcbff4304dc8/report.md) | 明确识别无效镜像仓库 registry.invalid 的域名解析失败导致拉取失败。 |
| 5 | 通过 | 通过 | [d781751bcf83469e](c02/run-05-d781751bcf83469e/report.md) | 明确识别无效镜像仓库 registry.invalid 的域名解析失败导致拉取失败。 |
| 6 | 通过 | 通过 | [1c26366d23a5495b](c02/run-06-1c26366d23a5495b/report.md) | DNS 解析失败主机制正确；将无效地址写作有效地址是表述瑕疵。 |
| 7 | 通过 | 通过 | [d6cf1ba9e5e5481e](c02/run-07-d6cf1ba9e5e5481e/report.md) | 明确识别无效镜像仓库 registry.invalid 的域名解析失败导致拉取失败。 |
| 8 | 通过 | 通过 | [5e090d0febb94917](c02/run-08-5e090d0febb94917/report.md) | 明确识别无效镜像仓库 registry.invalid 的域名解析失败导致拉取失败。 |
| 9 | 通过 | 通过 | [a0bc338467264d8b](c02/run-09-a0bc338467264d8b/report.md) | 明确识别无效镜像仓库 registry.invalid 的域名解析失败导致拉取失败。 |
| 10 | 通过 | 通过 | [58ee3e0d4f1a40bf](c02/run-10-58ee3e0d4f1a40bf/report.md) | 明确识别无效镜像仓库 registry.invalid 的域名解析失败导致拉取失败。 |
| 11 | 通过 | 通过 | [64bbead0769a4436](c02/run-11-64bbead0769a4436/report.md) | 明确识别无效镜像仓库 registry.invalid 的域名解析失败导致拉取失败。 |
| 12 | 通过 | 通过 | [8723beb7622c42f0](c02/run-12-8723beb7622c42f0/report.md) | 明确识别无效镜像仓库 registry.invalid 的域名解析失败导致拉取失败。 |
| 13 | 通过 | 通过 | [1dcd39f2391c4d7a](c02/run-13-1dcd39f2391c4d7a/report.md) | 明确识别无效镜像仓库 registry.invalid 的域名解析失败导致拉取失败。 |
| 14 | 通过 | 通过 | [cf9ca6280e4744f9](c02/run-14-cf9ca6280e4744f9/report.md) | 明确识别无效镜像仓库 registry.invalid 的域名解析失败导致拉取失败。 |
| 15 | 通过 | 通过 | [e1a747195dcc411d](c02/run-15-e1a747195dcc411d/report.md) | 明确识别无效镜像仓库 registry.invalid 的域名解析失败导致拉取失败。 |
| 16 | 未通过 | 不通过 | [f0cd89dde7f54504](c02/run-16-f0cd89dde7f54504/report.md) | 仅确认 ImagePullBackOff，明确无法区分镜像不存在、鉴权与网络/DNS，未给出具体主根因。 |
| 17 | 通过 | 通过 | [08e2f073005b4830](c02/run-17-08e2f073005b4830/report.md) | 明确识别无效镜像仓库 registry.invalid 的域名解析失败导致拉取失败。 |
| 18 | 通过 | 通过 | [9f68d031f5474904](c02/run-18-9f68d031f5474904/report.md) | 主根因正确，但正文同时出现 diagnosis_publishable=false，发布状态与叙述不一致；不据此改变语义根因命中。 |
| 19 | 通过 | 通过 | [9df244ef939e4456](c02/run-19-9df244ef939e4456/report.md) | 明确识别无效镜像仓库 registry.invalid 的域名解析失败导致拉取失败。 |
| 20 | 通过 | 通过 | [a2c63644fc4046d6](c02/run-20-a2c63644fc4046d6/report.md) | 明确识别无效镜像仓库 registry.invalid 的域名解析失败导致拉取失败。 |
| 21 | 通过 | 通过 | [6bdb7332588d4cbe](c02/run-21-6bdb7332588d4cbe/report.md) | 明确识别无效镜像仓库 registry.invalid 的域名解析失败导致拉取失败。 |
| 22 | 通过 | 通过 | [8742163476de41d8](c02/run-22-8742163476de41d8/report.md) | 明确识别无效镜像仓库 registry.invalid 的域名解析失败导致拉取失败。 |
| 23 | 通过 | 通过 | [2ce8b35b9ca54dc4](c02/run-23-2ce8b35b9ca54dc4/report.md) | 明确识别无效镜像仓库 registry.invalid 的域名解析失败导致拉取失败。 |
| 24 | 通过 | 通过 | [f0b04d638e514391](c02/run-24-f0b04d638e514391/report.md) | 明确识别无效镜像仓库 registry.invalid 的域名解析失败导致拉取失败。 |
| 25 | 通过 | 通过 | [0aa86d1643504002](c02/run-25-0aa86d1643504002/report.md) | 明确识别无效镜像仓库 registry.invalid 的域名解析失败导致拉取失败。 |
| 26 | 通过 | 通过 | [4cbb57da2eaa4121](c02/run-26-4cbb57da2eaa4121/report.md) | 明确识别无效镜像仓库 registry.invalid 的域名解析失败导致拉取失败。 |
| 27 | 通过 | 通过 | [df028417f0b54ce8](c02/run-27-df028417f0b54ce8/report.md) | 明确识别无效镜像仓库 registry.invalid 的域名解析失败导致拉取失败。 |
| 28 | 通过 | 通过 | [0fcc9219e9ea46c1](c02/run-28-0fcc9219e9ea46c1/report.md) | 明确识别无效镜像仓库 registry.invalid 的域名解析失败导致拉取失败。 |
| 29 | 通过 | 通过 | [bd0e2b2a6748478c](c02/run-29-bd0e2b2a6748478c/report.md) | 明确识别无效镜像仓库 registry.invalid 的域名解析失败导致拉取失败。 |
| 30 | 通过 | 通过 | [4c932d21006c40a5](c02/run-30-4c932d21006c40a5/report.md) | 明确识别无效镜像仓库 registry.invalid 的域名解析失败导致拉取失败。 |
| 31 | 通过 | 通过 | [4bf80da1b5cf457a](c02/run-31-4bf80da1b5cf457a/report.md) | 明确识别无效镜像仓库 registry.invalid 的域名解析失败导致拉取失败。 |
| 32 | 通过 | 通过 | [7bcb4117ab234038](c02/run-32-7bcb4117ab234038/report.md) | 明确识别无效镜像仓库 registry.invalid 的域名解析失败导致拉取失败。 |
| 33 | 通过 | 通过 | [7937440848fe497b](c02/run-33-7937440848fe497b/report.md) | 明确识别无效镜像仓库 registry.invalid 的域名解析失败导致拉取失败。 |
| 34 | 通过 | 通过 | [41ab96ae12c348ed](c02/run-34-41ab96ae12c348ed/report.md) | 明确识别无效镜像仓库 registry.invalid 的域名解析失败导致拉取失败。 |
| 35 | 通过 | 通过 | [30aa5291969049f1](c02/run-35-30aa5291969049f1/report.md) | 明确识别无效镜像仓库 registry.invalid 的域名解析失败导致拉取失败。 |
| 36 | 通过 | 通过 | [a5dc43c7078742cf](c02/run-36-a5dc43c7078742cf/report.md) | 明确识别无效镜像仓库 registry.invalid 的域名解析失败导致拉取失败。 |
| 37 | 通过 | 通过 | [77949cde51fd49a3](c02/run-37-77949cde51fd49a3/report.md) | 已定位 registry.invalid 解析失败；同时猜测集群 DNS 配置问题，不能据此认定 DNS 服务自身故障。 |
| 38 | 通过 | 通过 | [d3b0efeaf3204837](c02/run-38-d3b0efeaf3204837/report.md) | 明确识别无效镜像仓库 registry.invalid 的域名解析失败导致拉取失败。 |
| 39 | 通过 | 通过 | [143a6f5b976e4d43](c02/run-39-143a6f5b976e4d43/report.md) | 明确识别无效镜像仓库 registry.invalid 的域名解析失败导致拉取失败。 |
| 40 | 通过 | 通过 | [bb0b13f8b89a42b2](c02/run-40-bb0b13f8b89a42b2/report.md) | 明确识别无效镜像仓库 registry.invalid 的域名解析失败导致拉取失败。 |
| 41 | 通过 | 通过 | [9bb53681c726499e](c02/run-41-9bb53681c726499e/report.md) | 明确识别无效镜像仓库 registry.invalid 的域名解析失败导致拉取失败。 |
| 42 | 通过 | 通过 | [da328e94ace64f2f](c02/run-42-da328e94ace64f2f/report.md) | 明确识别无效镜像仓库 registry.invalid 的域名解析失败导致拉取失败。 |
| 43 | 通过 | 通过 | [30dec1d4c1c14e34](c02/run-43-30dec1d4c1c14e34/report.md) | 无效域名主机制正确；附带未配置 imagePullSecrets 不是 DNS 失败的原因，属于非主因赘述。 |
| 44 | 通过 | 通过 | [6bf0633623c34d34](c02/run-44-6bf0633623c34d34/report.md) | 明确识别无效镜像仓库 registry.invalid 的域名解析失败导致拉取失败。 |
| 45 | 通过 | 通过 | [308a922cc323497f](c02/run-45-308a922cc323497f/report.md) | 明确识别无效镜像仓库 registry.invalid 的域名解析失败导致拉取失败。 |
| 46 | 通过 | 通过 | [7641523d1e8e42da](c02/run-46-7641523d1e8e42da/report.md) | 明确识别无效镜像仓库 registry.invalid 的域名解析失败导致拉取失败。 |
| 47 | 通过 | 通过 | [f367496c2b2b4cff](c02/run-47-f367496c2b2b4cff/report.md) | 明确识别无效镜像仓库 registry.invalid 的域名解析失败导致拉取失败。 |
| 48 | 通过 | 通过 | [18f9c50cc49143cb](c02/run-48-18f9c50cc49143cb/report.md) | 明确识别无效镜像仓库 registry.invalid 的域名解析失败导致拉取失败。 |
| 49 | 通过 | 通过 | [a4e8ec3633254335](c02/run-49-a4e8ec3633254335/report.md) | 明确识别无效镜像仓库 registry.invalid 的域名解析失败导致拉取失败。 |
| 50 | 通过 | 通过 | [b4dc575674c74664](c02/run-50-b4dc575674c74664/report.md) | 明确识别无效镜像仓库 registry.invalid 的域名解析失败导致拉取失败。 |

### c03

主根因49份正确，1份把卷名与ConfigMap名混淆，作为待复核而非直接修正评分。

| # | 原脚本 | 人工意见 | 原始报告 | 理由 |
|---:|---|---|---|---|
| 1 | 通过 | 通过 | [b392f89062704ca5](c03/run-01-b392f89062704ca5/report.md) | 明确识别 ConfigMap unavailable-config 缺失导致卷挂载失败。 |
| 2 | 通过 | 通过 | [9a090d8a33144969](c03/run-02-9a090d8a33144969/report.md) | 明确识别 ConfigMap unavailable-config 缺失导致卷挂载失败。 |
| 3 | 通过 | 通过 | [26af5e963651475f](c03/run-03-26af5e963651475f/report.md) | 明确识别 ConfigMap unavailable-config 缺失导致卷挂载失败。 |
| 4 | 通过 | 通过 | [233c1ec368564cbe](c03/run-04-233c1ec368564cbe/report.md) | 明确识别 ConfigMap unavailable-config 缺失导致卷挂载失败。 |
| 5 | 通过 | 通过 | [5e92406dd5ef4234](c03/run-05-5e92406dd5ef4234/report.md) | 明确识别 ConfigMap unavailable-config 缺失导致卷挂载失败。 |
| 6 | 通过 | 通过 | [cf3d95fa405b496a](c03/run-06-cf3d95fa405b496a/report.md) | 明确识别 ConfigMap unavailable-config 缺失导致卷挂载失败。 |
| 7 | 通过 | 通过 | [7e0848f951ea4d9d](c03/run-07-7e0848f951ea4d9d/report.md) | 明确识别 ConfigMap unavailable-config 缺失导致卷挂载失败。 |
| 8 | 通过 | 通过 | [8d0a826ce99544c1](c03/run-08-8d0a826ce99544c1/report.md) | 明确识别 ConfigMap unavailable-config 缺失导致卷挂载失败。 |
| 9 | 通过 | 通过 | [6dfaa5309342412a](c03/run-09-6dfaa5309342412a/report.md) | 明确识别 ConfigMap unavailable-config 缺失导致卷挂载失败。 |
| 10 | 通过 | 通过 | [c78b0a97e3f94c00](c03/run-10-c78b0a97e3f94c00/report.md) | 明确识别 ConfigMap unavailable-config 缺失导致卷挂载失败。 |
| 11 | 通过 | 通过 | [aa3ac694294e4b86](c03/run-11-aa3ac694294e4b86/report.md) | 明确识别 ConfigMap unavailable-config 缺失导致卷挂载失败。 |
| 12 | 通过 | 通过 | [623c555ac86c488b](c03/run-12-623c555ac86c488b/report.md) | 明确识别 ConfigMap unavailable-config 缺失导致卷挂载失败。 |
| 13 | 通过 | 通过 | [594296423f5a4ee7](c03/run-13-594296423f5a4ee7/report.md) | 明确识别 ConfigMap unavailable-config 缺失导致卷挂载失败。 |
| 14 | 通过 | 通过 | [278efba42b8b4d1f](c03/run-14-278efba42b8b4d1f/report.md) | 明确识别 ConfigMap unavailable-config 缺失导致卷挂载失败。 |
| 15 | 通过 | 通过 | [b53b0a09f2e84f49](c03/run-15-b53b0a09f2e84f49/report.md) | 明确识别 ConfigMap unavailable-config 缺失导致卷挂载失败。 |
| 16 | 通过 | 通过 | [0f2a6ceba66a4d24](c03/run-16-0f2a6ceba66a4d24/report.md) | 明确识别 ConfigMap unavailable-config 缺失导致卷挂载失败。 |
| 17 | 通过 | 通过 | [60251b16685c448e](c03/run-17-60251b16685c448e/report.md) | 明确识别 ConfigMap unavailable-config 缺失导致卷挂载失败。 |
| 18 | 通过 | 通过 | [ba91e0d627d94024](c03/run-18-ba91e0d627d94024/report.md) | 明确识别 ConfigMap unavailable-config 缺失导致卷挂载失败。 |
| 19 | 通过 | 通过 | [cfb9c071a9534ae8](c03/run-19-cfb9c071a9534ae8/report.md) | 明确识别 ConfigMap unavailable-config 缺失导致卷挂载失败。 |
| 20 | 通过 | 通过 | [e678f9d7496948fa](c03/run-20-e678f9d7496948fa/report.md) | 明确识别 ConfigMap unavailable-config 缺失导致卷挂载失败。 |
| 21 | 通过 | 通过 | [7e995a049b2c4d0e](c03/run-21-7e995a049b2c4d0e/report.md) | 明确识别 ConfigMap unavailable-config 缺失导致卷挂载失败。 |
| 22 | 通过 | 通过 | [0885f621ab4241fb](c03/run-22-0885f621ab4241fb/report.md) | 明确识别 ConfigMap unavailable-config 缺失导致卷挂载失败。 |
| 23 | 通过 | 通过 | [f5824ba175d4453f](c03/run-23-f5824ba175d4453f/report.md) | 明确识别 ConfigMap unavailable-config 缺失导致卷挂载失败。 |
| 24 | 通过 | 通过 | [937f6676db1d42f3](c03/run-24-937f6676db1d42f3/report.md) | 明确识别 ConfigMap unavailable-config 缺失导致卷挂载失败。 |
| 25 | 通过 | 通过 | [ec1ae9a4813e4af6](c03/run-25-ec1ae9a4813e4af6/report.md) | 明确识别 ConfigMap unavailable-config 缺失导致卷挂载失败。 |
| 26 | 通过 | 通过 | [5c78da23f4d044d3](c03/run-26-5c78da23f4d044d3/report.md) | 明确识别 ConfigMap unavailable-config 缺失导致卷挂载失败。 |
| 27 | 通过 | 通过 | [750697b95825416c](c03/run-27-750697b95825416c/report.md) | 明确识别 ConfigMap unavailable-config 缺失导致卷挂载失败。 |
| 28 | 通过 | 通过 | [54ddd0e9de2543b4](c03/run-28-54ddd0e9de2543b4/report.md) | 明确识别 ConfigMap unavailable-config 缺失导致卷挂载失败。 |
| 29 | 通过 | 通过 | [5bf818ec223b48f6](c03/run-29-5bf818ec223b48f6/report.md) | 明确识别 ConfigMap unavailable-config 缺失导致卷挂载失败。 |
| 30 | 通过 | 通过 | [451a6204950f4d16](c03/run-30-451a6204950f4d16/report.md) | 明确识别 ConfigMap unavailable-config 缺失导致卷挂载失败。 |
| 31 | 通过 | 通过 | [11770ec2a3084d0b](c03/run-31-11770ec2a3084d0b/report.md) | 明确识别 ConfigMap unavailable-config 缺失导致卷挂载失败。 |
| 32 | 通过 | 通过 | [49aad98c702547c2](c03/run-32-49aad98c702547c2/report.md) | 明确识别 ConfigMap unavailable-config 缺失导致卷挂载失败。 |
| 33 | 通过 | 通过 | [51e7e63a0c664779](c03/run-33-51e7e63a0c664779/report.md) | 明确识别 ConfigMap unavailable-config 缺失导致卷挂载失败。 |
| 34 | 未通过 | 待复核 | [363cec4a59ca44f2](c03/run-34-363cec4a59ca44f2/report.md) | ConfigMap 缺失/挂载失败机制正确，但将卷名 input 错当成 ConfigMap 名（实际 unavailable-config）；可能误导修复目标，不按纯省略直接放过。 |
| 35 | 通过 | 通过 | [90fe76d6954f4adc](c03/run-35-90fe76d6954f4adc/report.md) | 明确识别 ConfigMap unavailable-config 缺失导致卷挂载失败。 |
| 36 | 通过 | 通过 | [18aa4bf956524d4f](c03/run-36-18aa4bf956524d4f/report.md) | 明确识别 ConfigMap unavailable-config 缺失导致卷挂载失败。 |
| 37 | 通过 | 通过 | [1e4a4138bc02478c](c03/run-37-1e4a4138bc02478c/report.md) | 明确识别 ConfigMap unavailable-config 缺失导致卷挂载失败。 |
| 38 | 通过 | 通过 | [ad11e1ddb8b341c6](c03/run-38-ad11e1ddb8b341c6/report.md) | 明确识别 ConfigMap unavailable-config 缺失导致卷挂载失败。 |
| 39 | 通过 | 通过 | [3d58f89a5e9a40bb](c03/run-39-3d58f89a5e9a40bb/report.md) | 明确识别 ConfigMap unavailable-config 缺失导致卷挂载失败。 |
| 40 | 通过 | 通过 | [16d8c9a40df64e3c](c03/run-40-16d8c9a40df64e3c/report.md) | 明确识别 ConfigMap unavailable-config 缺失导致卷挂载失败。 |
| 41 | 通过 | 通过 | [2a2c118751d84de6](c03/run-41-2a2c118751d84de6/report.md) | 明确识别 ConfigMap unavailable-config 缺失导致卷挂载失败。 |
| 42 | 通过 | 通过 | [a1300b7aad954bb1](c03/run-42-a1300b7aad954bb1/report.md) | 明确识别 ConfigMap unavailable-config 缺失导致卷挂载失败。 |
| 43 | 通过 | 通过 | [a5e2d4f616e04996](c03/run-43-a5e2d4f616e04996/report.md) | 明确识别 ConfigMap unavailable-config 缺失导致卷挂载失败。 |
| 44 | 通过 | 通过 | [600b86d25d3d4387](c03/run-44-600b86d25d3d4387/report.md) | 明确识别 ConfigMap unavailable-config 缺失导致卷挂载失败。 |
| 45 | 通过 | 通过 | [acf9ab7ccafc4f2e](c03/run-45-acf9ab7ccafc4f2e/report.md) | 明确识别 ConfigMap unavailable-config 缺失导致卷挂载失败。 |
| 46 | 通过 | 通过 | [0e154ce2d22c4958](c03/run-46-0e154ce2d22c4958/report.md) | 明确识别 ConfigMap unavailable-config 缺失导致卷挂载失败。 |
| 47 | 通过 | 通过 | [1bd9737cf0984a79](c03/run-47-1bd9737cf0984a79/report.md) | 明确识别 ConfigMap unavailable-config 缺失导致卷挂载失败。 |
| 48 | 通过 | 通过 | [23b79cc721644c2b](c03/run-48-23b79cc721644c2b/report.md) | 明确识别 ConfigMap unavailable-config 缺失导致卷挂载失败。 |
| 49 | 通过 | 通过 | [d75794be65564052](c03/run-49-d75794be65564052/report.md) | 明确识别 ConfigMap unavailable-config 缺失导致卷挂载失败。 |
| 50 | 通过 | 通过 | [04a588e8fccb4ea9](c03/run-50-04a588e8fccb4ea9/report.md) | 明确识别 ConfigMap unavailable-config 缺失导致卷挂载失败。 |

### c04

49份主要根因正确，1份实际未确认。多份将env注入泛称卷挂载，属于机制阶段表述不精确；不把主要根因命中等同整篇技术细节无误。

| # | 原脚本 | 人工意见 | 原始报告 | 理由 |
|---:|---|---|---|---|
| 1 | 通过 | 通过 | [126f177344c74f9f](c04/run-01-126f177344c74f9f/report.md) | 明确识别 Secret 的 unavailable-key 缺失导致 CreateContainerConfigError，主要机制正确。 |
| 2 | 通过 | 通过 | [9feb4f5f5c104217](c04/run-02-9feb4f5f5c104217/report.md) | 明确识别 Secret 的 unavailable-key 缺失导致 CreateContainerConfigError，主要机制正确。 |
| 3 | 通过 | 通过 | [e37d138cd90a4ff4](c04/run-03-e37d138cd90a4ff4/report.md) | 明确识别 Secret 的 unavailable-key 缺失导致 CreateContainerConfigError，主要机制正确。 |
| 4 | 通过 | 通过 | [786ba6a9970c466f](c04/run-04-786ba6a9970c466f/report.md) | 明确识别 Secret 的 unavailable-key 缺失导致 CreateContainerConfigError，主要机制正确。 |
| 5 | 通过 | 通过 | [160300ee746942b7](c04/run-05-160300ee746942b7/report.md) | 明确识别 Secret 的 unavailable-key 缺失导致 CreateContainerConfigError，主要机制正确。 |
| 6 | 通过 | 通过 | [9bd26982f4bd442b](c04/run-06-9bd26982f4bd442b/report.md) | 明确识别 Secret 的 unavailable-key 缺失导致 CreateContainerConfigError，主要机制正确。 |
| 7 | 通过 | 通过 | [3c0d81a4c08f4970](c04/run-07-3c0d81a4c08f4970/report.md) | 明确识别 Secret 的 unavailable-key 缺失导致 CreateContainerConfigError，主要机制正确。 |
| 8 | 通过 | 通过 | [fe468a2b50194ac3](c04/run-08-fe468a2b50194ac3/report.md) | 明确识别 Secret 的 unavailable-key 缺失导致 CreateContainerConfigError，主要机制正确。 |
| 9 | 通过 | 通过 | [8bd0ef501f1a4fe9](c04/run-09-8bd0ef501f1a4fe9/report.md) | 明确识别 Secret 的 unavailable-key 缺失导致 CreateContainerConfigError，主要机制正确。 |
| 10 | 通过 | 通过 | [18ffb6ddf9464605](c04/run-10-18ffb6ddf9464605/report.md) | 明确识别 Secret 的 unavailable-key 缺失导致 CreateContainerConfigError，主要机制正确。 |
| 11 | 通过 | 通过 | [58c5f86227794efb](c04/run-11-58c5f86227794efb/report.md) | 明确识别 Secret 的 unavailable-key 缺失导致 CreateContainerConfigError，主要机制正确。 |
| 12 | 通过 | 通过 | [91329aede4914d41](c04/run-12-91329aede4914d41/report.md) | 明确识别 Secret 的 unavailable-key 缺失导致 CreateContainerConfigError，主要机制正确。 |
| 13 | 通过 | 通过 | [44af61a131f54d28](c04/run-13-44af61a131f54d28/report.md) | 明确识别 Secret 的 unavailable-key 缺失导致 CreateContainerConfigError，主要机制正确。 |
| 14 | 通过 | 通过 | [6398e2047e714de7](c04/run-14-6398e2047e714de7/report.md) | 明确识别 Secret 的 unavailable-key 缺失导致 CreateContainerConfigError，主要机制正确。 |
| 15 | 通过 | 通过 | [d38cc4d9b5fa4c69](c04/run-15-d38cc4d9b5fa4c69/report.md) | 明确识别 Secret 的 unavailable-key 缺失导致 CreateContainerConfigError，主要机制正确。 |
| 16 | 通过 | 通过 | [45b692d2d6fb4e47](c04/run-16-45b692d2d6fb4e47/report.md) | 明确识别 Secret 的 unavailable-key 缺失导致 CreateContainerConfigError，主要机制正确。 |
| 17 | 通过 | 通过 | [69260b03452e41da](c04/run-17-69260b03452e41da/report.md) | 明确识别 Secret 的 unavailable-key 缺失导致 CreateContainerConfigError，主要机制正确。 |
| 18 | 通过 | 通过 | [ce8beb9944354730](c04/run-18-ce8beb9944354730/report.md) | 明确识别 Secret 的 unavailable-key 缺失导致 CreateContainerConfigError，主要机制正确。 |
| 19 | 通过 | 通过 | [23b8db5d4e9646b0](c04/run-19-23b8db5d4e9646b0/report.md) | 明确识别 Secret 的 unavailable-key 缺失导致 CreateContainerConfigError，主要机制正确。 |
| 20 | 通过 | 通过 | [1bf0f6451ad34d50](c04/run-20-1bf0f6451ad34d50/report.md) | 明确识别 Secret 的 unavailable-key 缺失导致 CreateContainerConfigError，主要机制正确。 |
| 21 | 通过 | 通过 | [963a8b7fbc9f4960](c04/run-21-963a8b7fbc9f4960/report.md) | 明确识别 Secret 的 unavailable-key 缺失导致 CreateContainerConfigError，主要机制正确。 |
| 22 | 通过 | 通过 | [ce6880c6e7024211](c04/run-22-ce6880c6e7024211/report.md) | 明确识别 Secret 的 unavailable-key 缺失导致 CreateContainerConfigError，主要机制正确。 |
| 23 | 通过 | 通过 | [9352af69faf043bc](c04/run-23-9352af69faf043bc/report.md) | 明确识别 Secret 的 unavailable-key 缺失导致 CreateContainerConfigError，主要机制正确。 |
| 24 | 通过 | 通过 | [43aab1d4a3324ac9](c04/run-24-43aab1d4a3324ac9/report.md) | 明确识别 Secret 的 unavailable-key 缺失导致 CreateContainerConfigError，主要机制正确。 |
| 25 | 通过 | 通过 | [dafce6624c4e4f50](c04/run-25-dafce6624c4e4f50/report.md) | 明确识别 Secret 的 unavailable-key 缺失导致 CreateContainerConfigError，主要机制正确。 |
| 26 | 通过 | 通过 | [88c6088817344edb](c04/run-26-88c6088817344edb/report.md) | 明确识别 Secret 的 unavailable-key 缺失导致 CreateContainerConfigError，主要机制正确。 |
| 27 | 通过 | 通过 | [a2bdb054f73a4089](c04/run-27-a2bdb054f73a4089/report.md) | 明确识别 Secret 的 unavailable-key 缺失导致 CreateContainerConfigError，主要机制正确。 |
| 28 | 通过 | 通过 | [0df1225b450b430b](c04/run-28-0df1225b450b430b/report.md) | 明确识别 Secret 的 unavailable-key 缺失导致 CreateContainerConfigError，主要机制正确。 |
| 29 | 通过 | 通过 | [dbab163f85bb4ffa](c04/run-29-dbab163f85bb4ffa/report.md) | 明确识别 Secret 的 unavailable-key 缺失导致 CreateContainerConfigError，主要机制正确。 |
| 30 | 通过 | 通过 | [d7bce098d0fd48ec](c04/run-30-d7bce098d0fd48ec/report.md) | 明确识别 Secret 的 unavailable-key 缺失导致 CreateContainerConfigError，主要机制正确。 |
| 31 | 通过 | 通过 | [78e5b7c540d1496b](c04/run-31-78e5b7c540d1496b/report.md) | 明确识别 Secret 的 unavailable-key 缺失导致 CreateContainerConfigError，主要机制正确。 |
| 32 | 通过 | 通过 | [5e87e12fb5054e23](c04/run-32-5e87e12fb5054e23/report.md) | 明确识别 Secret 的 unavailable-key 缺失导致 CreateContainerConfigError，主要机制正确。 |
| 33 | 通过 | 通过 | [e9fef2da08594adb](c04/run-33-e9fef2da08594adb/report.md) | 明确识别 Secret 的 unavailable-key 缺失导致 CreateContainerConfigError，主要机制正确。 |
| 34 | 通过 | 通过 | [9ef8a01c21b049b1](c04/run-34-9ef8a01c21b049b1/report.md) | 明确识别 Secret 的 unavailable-key 缺失导致 CreateContainerConfigError，主要机制正确。 |
| 35 | 通过 | 通过 | [9397e55feec84ac7](c04/run-35-9397e55feec84ac7/report.md) | 明确识别 Secret 的 unavailable-key 缺失导致 CreateContainerConfigError，主要机制正确。 |
| 36 | 通过 | 通过 | [5f9aab994dc14312](c04/run-36-5f9aab994dc14312/report.md) | 明确识别 Secret 的 unavailable-key 缺失导致 CreateContainerConfigError，主要机制正确。 |
| 37 | 通过 | 通过 | [0395746ee6184b74](c04/run-37-0395746ee6184b74/report.md) | 明确识别 Secret 的 unavailable-key 缺失导致 CreateContainerConfigError，主要机制正确。 |
| 38 | 通过 | 通过 | [3043063124ff468d](c04/run-38-3043063124ff468d/report.md) | 明确识别 Secret 的 unavailable-key 缺失导致 CreateContainerConfigError，主要机制正确。 |
| 39 | 通过 | 通过 | [32451479e6a8479c](c04/run-39-32451479e6a8479c/report.md) | Secret key 缺失主机制正确；错误描述为持续重启，实际是创建前阻塞，记为次要状态解释瑕疵。 |
| 40 | 通过 | 通过 | [b1f95d75c696431a](c04/run-40-b1f95d75c696431a/report.md) | 明确识别 Secret 的 unavailable-key 缺失导致 CreateContainerConfigError，主要机制正确。 |
| 41 | 通过 | 通过 | [b49446947fed4cbb](c04/run-41-b49446947fed4cbb/report.md) | 明确识别 Secret 的 unavailable-key 缺失导致 CreateContainerConfigError，主要机制正确。 |
| 42 | 未通过 | 不通过 | [b4131b64df5a46ab](c04/run-42-b4131b64df5a46ab/report.md) | 仅定位 CreateContainerConfigError，明确无法区分 Secret/ConfigMap/权限/路径，没有确认本 Case 的 Secret key 缺失。 |
| 43 | 通过 | 通过 | [6d724cafa8b540e8](c04/run-43-6d724cafa8b540e8/report.md) | 明确识别 Secret 的 unavailable-key 缺失导致 CreateContainerConfigError，主要机制正确。 |
| 44 | 通过 | 通过 | [15c7e6bcd27e4924](c04/run-44-15c7e6bcd27e4924/report.md) | 明确识别 Secret 的 unavailable-key 缺失导致 CreateContainerConfigError，主要机制正确。 |
| 45 | 通过 | 通过 | [634758e85d2945bd](c04/run-45-634758e85d2945bd/report.md) | 明确识别 Secret 的 unavailable-key 缺失导致 CreateContainerConfigError，主要机制正确。 |
| 46 | 通过 | 通过 | [3e09c4f667f54524](c04/run-46-3e09c4f667f54524/report.md) | 明确识别 Secret 的 unavailable-key 缺失导致 CreateContainerConfigError，主要机制正确。 |
| 47 | 通过 | 通过 | [3698e970aaff410e](c04/run-47-3698e970aaff410e/report.md) | 明确识别 Secret 的 unavailable-key 缺失导致 CreateContainerConfigError，主要机制正确。 |
| 48 | 通过 | 通过 | [c352f20cc1f04ca3](c04/run-48-c352f20cc1f04ca3/report.md) | 明确识别 Secret 的 unavailable-key 缺失导致 CreateContainerConfigError，主要机制正确。 |
| 49 | 通过 | 通过 | [ec95f843fb3544e5](c04/run-49-ec95f843fb3544e5/report.md) | Secret key 缺失主机制正确；声称阻止镜像拉取缺乏依据，不能据此改变镜像拉取阶段判断。 |
| 50 | 通过 | 通过 | [3e82f5cd9e0d4310](c04/run-50-3e82f5cd9e0d4310/report.md) | 明确识别 Secret 的 unavailable-key 缺失导致 CreateContainerConfigError，主要机制正确。 |

### c05

50份主要根因均正确；3份仅省略Multus名称被脚本误判。CRD/CR措辞和注解拼写有细节瑕疵，不等同根因机制错误。

| # | 原脚本 | 人工意见 | 原始报告 | 理由 |
|---:|---|---|---|---|
| 1 | 通过 | 通过 | [8c45fde914d1496e](c05/run-01-8c45fde914d1496e/report.md) | 明确识别 NetworkAttachmentDefinition unavailable-network 缺失导致网络沙箱创建失败。 |
| 2 | 通过 | 通过 | [8b6cf8bbcfa84c94](c05/run-02-8b6cf8bbcfa84c94/report.md) | 明确识别 NetworkAttachmentDefinition unavailable-network 缺失导致网络沙箱创建失败。 |
| 3 | 通过 | 通过 | [4b0345d890fd4898](c05/run-03-4b0345d890fd4898/report.md) | 明确识别 NetworkAttachmentDefinition unavailable-network 缺失导致网络沙箱创建失败。 |
| 4 | 通过 | 通过 | [735f886cdfbb49b5](c05/run-04-735f886cdfbb49b5/report.md) | 明确识别 NetworkAttachmentDefinition unavailable-network 缺失导致网络沙箱创建失败。 |
| 5 | 通过 | 通过 | [52659c3f9e444b79](c05/run-05-52659c3f9e444b79/report.md) | 明确识别 NetworkAttachmentDefinition unavailable-network 缺失导致网络沙箱创建失败。 |
| 6 | 通过 | 通过 | [a5c21a02c83045a5](c05/run-06-a5c21a02c83045a5/report.md) | 明确识别 NetworkAttachmentDefinition unavailable-network 缺失导致网络沙箱创建失败。 |
| 7 | 通过 | 通过 | [83cced889f854648](c05/run-07-83cced889f854648/report.md) | 明确识别 NetworkAttachmentDefinition unavailable-network 缺失导致网络沙箱创建失败。 |
| 8 | 通过 | 通过 | [c734c21c784b4369](c05/run-08-c734c21c784b4369/report.md) | 明确识别 NetworkAttachmentDefinition unavailable-network 缺失导致网络沙箱创建失败。 |
| 9 | 未通过 | 通过 | [3220bd48adbf48fe](c05/run-09-3220bd48adbf48fe/report.md) | 主机制与资源名称明确正确，未写 Multus 产品名不影响结论；脚本要求 Multus 导致低估。 |
| 10 | 通过 | 通过 | [6ff836bb74984594](c05/run-10-6ff836bb74984594/report.md) | 明确识别 NetworkAttachmentDefinition unavailable-network 缺失导致网络沙箱创建失败。 |
| 11 | 通过 | 通过 | [97838b12179e4ba6](c05/run-11-97838b12179e4ba6/report.md) | 明确识别 NetworkAttachmentDefinition unavailable-network 缺失导致网络沙箱创建失败。 |
| 12 | 通过 | 通过 | [01bc54fccada4281](c05/run-12-01bc54fccada4281/report.md) | 明确识别 NetworkAttachmentDefinition unavailable-network 缺失导致网络沙箱创建失败。 |
| 13 | 通过 | 通过 | [cf0e0e885ea24eca](c05/run-13-cf0e0e885ea24eca/report.md) | 明确识别 NetworkAttachmentDefinition unavailable-network 缺失导致网络沙箱创建失败。 |
| 14 | 通过 | 通过 | [09711460104440bc](c05/run-14-09711460104440bc/report.md) | 明确识别 NetworkAttachmentDefinition unavailable-network 缺失导致网络沙箱创建失败。 |
| 15 | 通过 | 通过 | [ec0fa1d9abb44185](c05/run-15-ec0fa1d9abb44185/report.md) | 明确识别 NetworkAttachmentDefinition unavailable-network 缺失导致网络沙箱创建失败。 |
| 16 | 通过 | 通过 | [ea339e81f65948ae](c05/run-16-ea339e81f65948ae/report.md) | 明确识别 NetworkAttachmentDefinition unavailable-network 缺失导致网络沙箱创建失败。 |
| 17 | 通过 | 通过 | [23eb26160a2d453a](c05/run-17-23eb26160a2d453a/report.md) | 明确识别 NetworkAttachmentDefinition unavailable-network 缺失导致网络沙箱创建失败。 |
| 18 | 通过 | 通过 | [a94405013c094c64](c05/run-18-a94405013c094c64/report.md) | 明确识别 NetworkAttachmentDefinition unavailable-network 缺失导致网络沙箱创建失败。 |
| 19 | 通过 | 通过 | [19d79753bd884104](c05/run-19-19d79753bd884104/report.md) | 明确识别 NetworkAttachmentDefinition unavailable-network 缺失导致网络沙箱创建失败。 |
| 20 | 通过 | 通过 | [28edc9f7ca954a97](c05/run-20-28edc9f7ca954a97/report.md) | 明确识别 NetworkAttachmentDefinition unavailable-network 缺失导致网络沙箱创建失败。 |
| 21 | 通过 | 通过 | [dcb668b664264bd8](c05/run-21-dcb668b664264bd8/report.md) | 明确识别 NetworkAttachmentDefinition unavailable-network 缺失导致网络沙箱创建失败。 |
| 22 | 通过 | 通过 | [4aa68c0a09af446c](c05/run-22-4aa68c0a09af446c/report.md) | 明确识别 NetworkAttachmentDefinition unavailable-network 缺失导致网络沙箱创建失败。 |
| 23 | 通过 | 通过 | [7ad8a5f8df894f24](c05/run-23-7ad8a5f8df894f24/report.md) | 明确识别 NetworkAttachmentDefinition unavailable-network 缺失导致网络沙箱创建失败。 |
| 24 | 通过 | 通过 | [e49d586cab774800](c05/run-24-e49d586cab774800/report.md) | 明确识别 NetworkAttachmentDefinition unavailable-network 缺失导致网络沙箱创建失败。 |
| 25 | 通过 | 通过 | [ad054df83c964240](c05/run-25-ad054df83c964240/report.md) | 明确识别 NetworkAttachmentDefinition unavailable-network 缺失导致网络沙箱创建失败。 |
| 26 | 通过 | 通过 | [5f5fb7db9b5642cf](c05/run-26-5f5fb7db9b5642cf/report.md) | 明确识别 NetworkAttachmentDefinition unavailable-network 缺失导致网络沙箱创建失败。 |
| 27 | 通过 | 通过 | [c9df4cc488a94086](c05/run-27-c9df4cc488a94086/report.md) | 明确识别 NetworkAttachmentDefinition unavailable-network 缺失导致网络沙箱创建失败。 |
| 28 | 未通过 | 通过 | [f5807d384e074ce5](c05/run-28-f5807d384e074ce5/report.md) | 主机制与资源名称明确正确，未写 Multus 产品名不影响结论；脚本要求 Multus 导致低估。 |
| 29 | 通过 | 通过 | [119ea61b5e944719](c05/run-29-119ea61b5e944719/report.md) | 明确识别 NetworkAttachmentDefinition unavailable-network 缺失导致网络沙箱创建失败。 |
| 30 | 通过 | 通过 | [06e380b3c13241c4](c05/run-30-06e380b3c13241c4/report.md) | 明确识别 NetworkAttachmentDefinition unavailable-network 缺失导致网络沙箱创建失败。 |
| 31 | 通过 | 通过 | [76b5ed340fb94317](c05/run-31-76b5ed340fb94317/report.md) | 明确识别 NetworkAttachmentDefinition unavailable-network 缺失导致网络沙箱创建失败。 |
| 32 | 通过 | 通过 | [983b4106aa82436b](c05/run-32-983b4106aa82436b/report.md) | 明确识别 NetworkAttachmentDefinition unavailable-network 缺失导致网络沙箱创建失败。 |
| 33 | 未通过 | 通过 | [0a66b33915284c84](c05/run-33-0a66b33915284c84/report.md) | 主机制与资源名称明确正确，未写 Multus 产品名不影响结论；脚本要求 Multus 导致低估。 |
| 34 | 通过 | 通过 | [385b0d19895c4086](c05/run-34-385b0d19895c4086/report.md) | 明确识别 NetworkAttachmentDefinition unavailable-network 缺失导致网络沙箱创建失败。 |
| 35 | 通过 | 通过 | [73acacb894104f81](c05/run-35-73acacb894104f81/report.md) | 明确识别 NetworkAttachmentDefinition unavailable-network 缺失导致网络沙箱创建失败。 |
| 36 | 通过 | 通过 | [9074b2ef53464137](c05/run-36-9074b2ef53464137/report.md) | 明确识别 NetworkAttachmentDefinition unavailable-network 缺失导致网络沙箱创建失败。 |
| 37 | 通过 | 通过 | [b5c581df2f934d0f](c05/run-37-b5c581df2f934d0f/report.md) | 明确识别 NetworkAttachmentDefinition unavailable-network 缺失导致网络沙箱创建失败。 |
| 38 | 通过 | 通过 | [69e03c0ee0944fef](c05/run-38-69e03c0ee0944fef/report.md) | 明确识别 NetworkAttachmentDefinition unavailable-network 缺失导致网络沙箱创建失败。 |
| 39 | 通过 | 通过 | [11992a5fb3a2439f](c05/run-39-11992a5fb3a2439f/report.md) | 明确识别 NetworkAttachmentDefinition unavailable-network 缺失导致网络沙箱创建失败。 |
| 40 | 通过 | 通过 | [e03efffb78b34de2](c05/run-40-e03efffb78b34de2/report.md) | 明确识别 NetworkAttachmentDefinition unavailable-network 缺失导致网络沙箱创建失败。 |
| 41 | 通过 | 通过 | [157cbd4e176545b4](c05/run-41-157cbd4e176545b4/report.md) | 明确识别 NetworkAttachmentDefinition unavailable-network 缺失导致网络沙箱创建失败。 |
| 42 | 通过 | 通过 | [bf605f143c68470a](c05/run-42-bf605f143c68470a/report.md) | 明确识别 NetworkAttachmentDefinition unavailable-network 缺失导致网络沙箱创建失败。 |
| 43 | 通过 | 通过 | [d1bbeef931d0433f](c05/run-43-d1bbeef931d0433f/report.md) | 明确识别 NetworkAttachmentDefinition unavailable-network 缺失导致网络沙箱创建失败。 |
| 44 | 通过 | 通过 | [d496513908cb4799](c05/run-44-d496513908cb4799/report.md) | 明确识别 NetworkAttachmentDefinition unavailable-network 缺失导致网络沙箱创建失败。 |
| 45 | 通过 | 通过 | [59d30c4c3681492b](c05/run-45-59d30c4c3681492b/report.md) | 明确识别 NetworkAttachmentDefinition unavailable-network 缺失导致网络沙箱创建失败。 |
| 46 | 通过 | 通过 | [4dde2c834cf94dda](c05/run-46-4dde2c834cf94dda/report.md) | 明确识别 NetworkAttachmentDefinition unavailable-network 缺失导致网络沙箱创建失败。 |
| 47 | 通过 | 通过 | [82b2da4eddaf404b](c05/run-47-82b2da4eddaf404b/report.md) | NAD 缺失主机制正确；注解键多写了 cni 段，不能直接复制该键作为修复命令。 |
| 48 | 通过 | 通过 | [2d83dfdf5a7c40a7](c05/run-48-2d83dfdf5a7c40a7/report.md) | 明确识别 NetworkAttachmentDefinition unavailable-network 缺失导致网络沙箱创建失败。 |
| 49 | 通过 | 通过 | [7e74414175ee413f](c05/run-49-7e74414175ee413f/report.md) | 明确识别 NetworkAttachmentDefinition unavailable-network 缺失导致网络沙箱创建失败。 |
| 50 | 通过 | 通过 | [e9c25c238255416d](c05/run-50-e9c25c238255416d/report.md) | 明确识别 NetworkAttachmentDefinition unavailable-network 缺失导致网络沙箱创建失败。 |

### c06

逐份阅读 50 份。允许缺少具体堆栈/退出码措辞，但明确错误的内存分配或入口点机制不通过；额外集群异常与信号混淆待复核。

| # | 原脚本 | 人工意见 | 原始报告 | 理由 |
|---:|---|---|---|---|
| 1 | 通过 | 通过 | [f1337c1f6e99408d](c06/run-01-f1337c1f6e99408d/report.md) | 识别应用运行时进程非零退出导致反复重启；不能据此确认具体异常堆栈，部分报告对此过度推断。 |
| 2 | 通过 | 通过 | [f5e85098d12844ba](c06/run-02-f5e85098d12844ba/report.md) | 识别应用运行时进程非零退出导致反复重启；不能据此确认具体异常堆栈，部分报告对此过度推断。 |
| 3 | 通过 | 通过 | [e66252f7b7744e27](c06/run-03-e66252f7b7744e27/report.md) | 识别应用运行时进程非零退出导致反复重启；不能据此确认具体异常堆栈，部分报告对此过度推断。 |
| 4 | 未通过 | 通过 | [cace7e5893634e42](c06/run-04-cace7e5893634e42/report.md) | 主要机制已明确为应用运行时退出；精确退出码措辞、堆栈缺失或排除 OOM 的表述不应否定这一机制。 |
| 5 | 通过 | 通过 | [3c84b7c0922e44db](c06/run-05-3c84b7c0922e44db/report.md) | 识别应用运行时进程非零退出导致反复重启；不能据此确认具体异常堆栈，部分报告对此过度推断。 |
| 6 | 通过 | 通过 | [edd1dbe3f45c4a45](c06/run-06-edd1dbe3f45c4a45/report.md) | 识别应用运行时进程非零退出导致反复重启；不能据此确认具体异常堆栈，部分报告对此过度推断。 |
| 7 | 通过 | 通过 | [b01290d23b5646c7](c06/run-07-b01290d23b5646c7/report.md) | 识别应用运行时进程非零退出导致反复重启；不能据此确认具体异常堆栈，部分报告对此过度推断。 |
| 8 | 通过 | 通过 | [2df5cba55bc646b4](c06/run-08-2df5cba55bc646b4/report.md) | 识别应用运行时进程非零退出导致反复重启；不能据此确认具体异常堆栈，部分报告对此过度推断。 |
| 9 | 通过 | 通过 | [604c39ac48c84e9e](c06/run-09-604c39ac48c84e9e/report.md) | 识别应用运行时进程非零退出导致反复重启；不能据此确认具体异常堆栈，部分报告对此过度推断。 |
| 10 | 通过 | 不通过 | [8c2e19f102ac4433](c06/run-10-8c2e19f102ac4433/report.md) | 把 allocated_mib=0 当作内存分配故障并确认为根因，错误机制被脚本放过。 |
| 11 | 通过 | 通过 | [e4bf1cabbd474f50](c06/run-11-e4bf1cabbd474f50/report.md) | 识别应用运行时进程非零退出导致反复重启；不能据此确认具体异常堆栈，部分报告对此过度推断。 |
| 12 | 通过 | 通过 | [387e2b271fb949db](c06/run-12-387e2b271fb949db/report.md) | 识别应用运行时进程非零退出导致反复重启；不能据此确认具体异常堆栈，部分报告对此过度推断。 |
| 13 | 未通过 | 通过 | [87189fed09d3452d](c06/run-13-87189fed09d3452d/report.md) | 主要机制已明确为应用运行时退出；精确退出码措辞、堆栈缺失或排除 OOM 的表述不应否定这一机制。 |
| 14 | 通过 | 通过 | [22b5415d23ba4a6b](c06/run-14-22b5415d23ba4a6b/report.md) | 识别应用运行时进程非零退出导致反复重启；不能据此确认具体异常堆栈，部分报告对此过度推断。 |
| 15 | 未通过 | 通过 | [cd0974b2a77d4667](c06/run-15-cd0974b2a77d4667/report.md) | 主要机制已明确为应用运行时退出；精确退出码措辞、堆栈缺失或排除 OOM 的表述不应否定这一机制。 |
| 16 | 通过 | 不通过 | [9c88f92591db4eb0](c06/run-16-9c88f92591db4eb0/report.md) | 把已处理 /work 请求的运行时退出确认为应用入口点错误；exitCode=2 不足以证明命令/语法/入口错误。 |
| 17 | 通过 | 通过 | [d7f8c4a5b80640dc](c06/run-17-d7f8c4a5b80640dc/report.md) | 识别应用运行时进程非零退出导致反复重启；不能据此确认具体异常堆栈，部分报告对此过度推断。 |
| 18 | 通过 | 通过 | [5ec2609814bf4357](c06/run-18-5ec2609814bf4357/report.md) | 识别应用运行时进程非零退出导致反复重启；不能据此确认具体异常堆栈，部分报告对此过度推断。 |
| 19 | 通过 | 通过 | [868d07b35e914e72](c06/run-19-868d07b35e914e72/report.md) | 识别应用运行时进程非零退出导致反复重启；不能据此确认具体异常堆栈，部分报告对此过度推断。 |
| 20 | 通过 | 通过 | [42d1eccbdbf9461d](c06/run-20-42d1eccbdbf9461d/report.md) | 识别应用运行时进程非零退出导致反复重启；不能据此确认具体异常堆栈，部分报告对此过度推断。 |
| 21 | 未通过 | 通过 | [d4eadc980ce648ff](c06/run-21-d4eadc980ce648ff/report.md) | 主要机制已明确为应用运行时退出；精确退出码措辞、堆栈缺失或排除 OOM 的表述不应否定这一机制。 |
| 22 | 通过 | 通过 | [f4ac3aa03ad24e3b](c06/run-22-f4ac3aa03ad24e3b/report.md) | 识别应用运行时进程非零退出导致反复重启；不能据此确认具体异常堆栈，部分报告对此过度推断。 |
| 23 | 通过 | 通过 | [66fed2bdbfb24d99](c06/run-23-66fed2bdbfb24d99/report.md) | 识别应用运行时进程非零退出导致反复重启；不能据此确认具体异常堆栈，部分报告对此过度推断。 |
| 24 | 未通过 | 待复核 | [dd5d587e6aad458e](c06/run-24-dd5d587e6aad458e/report.md) | 将 Exit Code 2 当作终止信号并怀疑探针触发，且把 143 与 OOM 混同；主动退出与外部终止机制混乱。 |
| 25 | 通过 | 通过 | [d540b7c1e8a64ff8](c06/run-25-d540b7c1e8a64ff8/report.md) | 识别应用运行时进程非零退出导致反复重启；不能据此确认具体异常堆栈，部分报告对此过度推断。 |
| 26 | 通过 | 通过 | [54faf76846594368](c06/run-26-54faf76846594368/report.md) | 识别应用运行时进程非零退出导致反复重启；不能据此确认具体异常堆栈，部分报告对此过度推断。 |
| 27 | 未通过 | 通过 | [5eb7abfa9a234931](c06/run-27-5eb7abfa9a234931/report.md) | 主要机制已明确为应用运行时退出；精确退出码措辞、堆栈缺失或排除 OOM 的表述不应否定这一机制。 |
| 28 | 通过 | 通过 | [cd64e80ed962475a](c06/run-28-cd64e80ed962475a/report.md) | 识别应用运行时进程非零退出导致反复重启；不能据此确认具体异常堆栈，部分报告对此过度推断。 |
| 29 | 通过 | 通过 | [b26e59d329cc4834](c06/run-29-b26e59d329cc4834/report.md) | 识别应用运行时进程非零退出导致反复重启；不能据此确认具体异常堆栈，部分报告对此过度推断。 |
| 30 | 通过 | 通过 | [364f0a89f6c8496d](c06/run-30-364f0a89f6c8496d/report.md) | 识别应用运行时进程非零退出导致反复重启；不能据此确认具体异常堆栈，部分报告对此过度推断。 |
| 31 | 未通过 | 通过 | [eef8bc38fc244743](c06/run-31-eef8bc38fc244743/report.md) | 主要机制已明确为应用运行时退出；精确退出码措辞、堆栈缺失或排除 OOM 的表述不应否定这一机制。 |
| 32 | 通过 | 通过 | [5ef12ef2c1d142b0](c06/run-32-5ef12ef2c1d142b0/report.md) | 识别应用运行时进程非零退出导致反复重启；不能据此确认具体异常堆栈，部分报告对此过度推断。 |
| 33 | 通过 | 通过 | [812ac1a12faa4d0c](c06/run-33-812ac1a12faa4d0c/report.md) | 识别应用运行时进程非零退出导致反复重启；不能据此确认具体异常堆栈，部分报告对此过度推断。 |
| 34 | 未通过 | 通过 | [b87c0319024c43ea](c06/run-34-b87c0319024c43ea/report.md) | 主要机制已明确为应用运行时退出；精确退出码措辞、堆栈缺失或排除 OOM 的表述不应否定这一机制。 |
| 35 | 通过 | 通过 | [e7d21c61e9dc4260](c06/run-35-e7d21c61e9dc4260/report.md) | 识别应用运行时进程非零退出导致反复重启；不能据此确认具体异常堆栈，部分报告对此过度推断。 |
| 36 | 通过 | 通过 | [0b4854d62e404236](c06/run-36-0b4854d62e404236/report.md) | 识别应用运行时进程非零退出导致反复重启；不能据此确认具体异常堆栈，部分报告对此过度推断。 |
| 37 | 未通过 | 通过 | [e8ec474857d94e64](c06/run-37-e8ec474857d94e64/report.md) | 主要机制已明确为应用运行时退出；精确退出码措辞、堆栈缺失或排除 OOM 的表述不应否定这一机制。 |
| 38 | 未通过 | 通过 | [5e4ea5a211474979](c06/run-38-5e4ea5a211474979/report.md) | 主要机制已明确为应用运行时退出；精确退出码措辞、堆栈缺失或排除 OOM 的表述不应否定这一机制。 |
| 39 | 通过 | 通过 | [da269c06b8924ab5](c06/run-39-da269c06b8924ab5/report.md) | 识别应用运行时进程非零退出导致反复重启；不能据此确认具体异常堆栈，部分报告对此过度推断。 |
| 40 | 未通过 | 通过 | [1efdd42f5b064827](c06/run-40-1efdd42f5b064827/report.md) | 主要机制已明确为应用运行时退出；精确退出码措辞、堆栈缺失或排除 OOM 的表述不应否定这一机制。 |
| 41 | 通过 | 通过 | [27aa19bee29344ca](c06/run-41-27aa19bee29344ca/report.md) | 识别应用运行时进程非零退出导致反复重启；不能据此确认具体异常堆栈，部分报告对此过度推断。 |
| 42 | 通过 | 通过 | [595143ba3b444a65](c06/run-42-595143ba3b444a65/report.md) | 识别应用运行时进程非零退出导致反复重启；不能据此确认具体异常堆栈，部分报告对此过度推断。 |
| 43 | 通过 | 通过 | [c3e3a909f140423b](c06/run-43-c3e3a909f140423b/report.md) | 识别应用运行时进程非零退出导致反复重启；不能据此确认具体异常堆栈，部分报告对此过度推断。 |
| 44 | 通过 | 通过 | [89768ad95f214313](c06/run-44-89768ad95f214313/report.md) | 识别应用运行时进程非零退出导致反复重启；不能据此确认具体异常堆栈，部分报告对此过度推断。 |
| 45 | 未通过 | 待复核 | [fe5e630e7aa544b7](c06/run-45-fe5e630e7aa544b7/report.md) | c06 运行时退出机制正确，另有 Prometheus OOM 诊断；全局问题下须独立核查额外异常真实性与时间范围。 |
| 46 | 通过 | 通过 | [20bb58fb16b446ab](c06/run-46-20bb58fb16b446ab/report.md) | 识别应用运行时进程非零退出导致反复重启；不能据此确认具体异常堆栈，部分报告对此过度推断。 |
| 47 | 未通过 | 通过 | [cfe65a075be94999](c06/run-47-cfe65a075be94999/report.md) | 主要机制已明确为应用运行时退出；精确退出码措辞、堆栈缺失或排除 OOM 的表述不应否定这一机制。 |
| 48 | 通过 | 通过 | [b3cd5856e60c4286](c06/run-48-b3cd5856e60c4286/report.md) | 识别应用运行时进程非零退出导致反复重启；不能据此确认具体异常堆栈，部分报告对此过度推断。 |
| 49 | 通过 | 通过 | [4a265bf8873f4d0d](c06/run-49-4a265bf8873f4d0d/report.md) | 识别应用运行时进程非零退出导致反复重启；不能据此确认具体异常堆栈，部分报告对此过度推断。 |
| 50 | 未通过 | 通过 | [ceafb59938304c71](c06/run-50-ceafb59938304c71/report.md) | 主要机制已明确为应用运行时退出；精确退出码措辞、堆栈缺失或排除 OOM 的表述不应否定这一机制。 |

### c07

配置缺失导致 Exit Code 78 的主要机制普遍正确；配置缺失不等于已证明 workload-code 的具体键/文件缺失，/work 是请求路径不是已证实的配置文件。另有额外 Prometheus 异常需独立复核。

| # | 原脚本 | 人工意见 | 原始报告 | 理由 |
|---:|---|---|---|---|
| 1 | 通过 | 通过 | [38ae13177ef74ee5](c07/run-01-38ae13177ef74ee5/report.md) | 识别 CONFIG_MISSING/config_missing_exit 对应的配置类失败导致进程退出；具体配置来源和启动/请求时机的扩展解释不视为已证实。 |
| 2 | 通过 | 通过 | [eae68a447b844b1a](c07/run-02-eae68a447b844b1a/report.md) | 识别 CONFIG_MISSING/config_missing_exit 对应的配置类失败导致进程退出；具体配置来源和启动/请求时机的扩展解释不视为已证实。 |
| 3 | 通过 | 通过 | [b023481121a94806](c07/run-03-b023481121a94806/report.md) | 识别 CONFIG_MISSING/config_missing_exit 对应的配置类失败导致进程退出；具体配置来源和启动/请求时机的扩展解释不视为已证实。 |
| 4 | 通过 | 通过 | [b3f99685476a47f0](c07/run-04-b3f99685476a47f0/report.md) | 识别 CONFIG_MISSING/config_missing_exit 对应的配置类失败导致进程退出；具体配置来源和启动/请求时机的扩展解释不视为已证实。 |
| 5 | 通过 | 通过 | [9f878c71266e418e](c07/run-05-9f878c71266e418e/report.md) | 识别 CONFIG_MISSING/config_missing_exit 对应的配置类失败导致进程退出；具体配置来源和启动/请求时机的扩展解释不视为已证实。 |
| 6 | 通过 | 待复核 | [63bd069a365846c6](c07/run-06-63bd069a365846c6/report.md) | 配置类主机制正确，但肯定断言 workload-code 中配置文件/键缺失；现有结论未给出此具体修复目标的证明，需复核。 |
| 7 | 通过 | 通过 | [19095cff78af439c](c07/run-07-19095cff78af439c/report.md) | 识别 CONFIG_MISSING/config_missing_exit 对应的配置类失败导致进程退出；具体配置来源和启动/请求时机的扩展解释不视为已证实。 |
| 8 | 通过 | 通过 | [4144bea4e8074641](c07/run-08-4144bea4e8074641/report.md) | 识别 CONFIG_MISSING/config_missing_exit 对应的配置类失败导致进程退出；具体配置来源和启动/请求时机的扩展解释不视为已证实。 |
| 9 | 通过 | 通过 | [035889ff17d84f57](c07/run-09-035889ff17d84f57/report.md) | 识别 CONFIG_MISSING/config_missing_exit 对应的配置类失败导致进程退出；具体配置来源和启动/请求时机的扩展解释不视为已证实。 |
| 10 | 通过 | 通过 | [32e6484ae7cc4bb4](c07/run-10-32e6484ae7cc4bb4/report.md) | 识别 CONFIG_MISSING/config_missing_exit 对应的配置类失败导致进程退出；具体配置来源和启动/请求时机的扩展解释不视为已证实。 |
| 11 | 通过 | 通过 | [b0dd77041f10411f](c07/run-11-b0dd77041f10411f/report.md) | 识别 CONFIG_MISSING/config_missing_exit 对应的配置类失败导致进程退出；具体配置来源和启动/请求时机的扩展解释不视为已证实。 |
| 12 | 通过 | 通过 | [e637fd5181174b82](c07/run-12-e637fd5181174b82/report.md) | 识别 CONFIG_MISSING/config_missing_exit 对应的配置类失败导致进程退出；具体配置来源和启动/请求时机的扩展解释不视为已证实。 |
| 13 | 通过 | 通过 | [f1c771c503cf4b12](c07/run-13-f1c771c503cf4b12/report.md) | 识别 CONFIG_MISSING/config_missing_exit 对应的配置类失败导致进程退出；具体配置来源和启动/请求时机的扩展解释不视为已证实。 |
| 14 | 通过 | 待复核 | [6f25a721185844a6](c07/run-14-6f25a721185844a6/report.md) | 配置类主机制正确，但肯定断言 workload-code 中配置文件/键缺失；现有结论未给出此具体修复目标的证明，需复核。 |
| 15 | 通过 | 通过 | [4afb303c63c64751](c07/run-15-4afb303c63c64751/report.md) | 识别 CONFIG_MISSING/config_missing_exit 对应的配置类失败导致进程退出；具体配置来源和启动/请求时机的扩展解释不视为已证实。 |
| 16 | 通过 | 通过 | [536ae36b499b45eb](c07/run-16-536ae36b499b45eb/report.md) | 识别 CONFIG_MISSING/config_missing_exit 对应的配置类失败导致进程退出；具体配置来源和启动/请求时机的扩展解释不视为已证实。 |
| 17 | 通过 | 通过 | [5828c3fd66ef497c](c07/run-17-5828c3fd66ef497c/report.md) | 识别 CONFIG_MISSING/config_missing_exit 对应的配置类失败导致进程退出；具体配置来源和启动/请求时机的扩展解释不视为已证实。 |
| 18 | 未通过 | 待复核 | [2d51fe6facbf4c4e](c07/run-18-2d51fe6facbf4c4e/report.md) | c07 主机制正确；另将 Prometheus many-to-many 规则错误确认为 OOM 成因，额外异常的因果链和范围需要独立核查。 |
| 19 | 通过 | 通过 | [856c1c6358e745b6](c07/run-19-856c1c6358e745b6/report.md) | 识别 CONFIG_MISSING/config_missing_exit 对应的配置类失败导致进程退出；具体配置来源和启动/请求时机的扩展解释不视为已证实。 |
| 20 | 通过 | 通过 | [89b51106649f469d](c07/run-20-89b51106649f469d/report.md) | 识别 CONFIG_MISSING/config_missing_exit 对应的配置类失败导致进程退出；具体配置来源和启动/请求时机的扩展解释不视为已证实。 |
| 21 | 通过 | 通过 | [64524805e1194bd0](c07/run-21-64524805e1194bd0/report.md) | 识别 CONFIG_MISSING/config_missing_exit 对应的配置类失败导致进程退出；具体配置来源和启动/请求时机的扩展解释不视为已证实。 |
| 22 | 通过 | 通过 | [f3c95ec351b74c3c](c07/run-22-f3c95ec351b74c3c/report.md) | 识别 CONFIG_MISSING/config_missing_exit 对应的配置类失败导致进程退出；具体配置来源和启动/请求时机的扩展解释不视为已证实。 |
| 23 | 未通过 | 通过 | [828b1e6217ba4b2a](c07/run-23-828b1e6217ba4b2a/report.md) | 配置缺失、退出码 78 已明确；未观察到 OOM 是排除项，不应被当成额外根因。 |
| 24 | 通过 | 待复核 | [1129ce34ecca4482](c07/run-24-1129ce34ecca4482/report.md) | 配置类主机制正确，但肯定断言 workload-code 中配置文件/键缺失；现有结论未给出此具体修复目标的证明，需复核。 |
| 25 | 通过 | 通过 | [8e57a297c3d7404a](c07/run-25-8e57a297c3d7404a/report.md) | 识别 CONFIG_MISSING/config_missing_exit 对应的配置类失败导致进程退出；具体配置来源和启动/请求时机的扩展解释不视为已证实。 |
| 26 | 通过 | 通过 | [3d497b75512a4836](c07/run-26-3d497b75512a4836/report.md) | 识别 CONFIG_MISSING/config_missing_exit 对应的配置类失败导致进程退出；具体配置来源和启动/请求时机的扩展解释不视为已证实。 |
| 27 | 通过 | 通过 | [7ea52c4eb4d94846](c07/run-27-7ea52c4eb4d94846/report.md) | 识别 CONFIG_MISSING/config_missing_exit 对应的配置类失败导致进程退出；具体配置来源和启动/请求时机的扩展解释不视为已证实。 |
| 28 | 通过 | 通过 | [9f839dfcf3c14231](c07/run-28-9f839dfcf3c14231/report.md) | 识别 CONFIG_MISSING/config_missing_exit 对应的配置类失败导致进程退出；具体配置来源和启动/请求时机的扩展解释不视为已证实。 |
| 29 | 通过 | 通过 | [c8d196e55db54064](c07/run-29-c8d196e55db54064/report.md) | 识别 CONFIG_MISSING/config_missing_exit 对应的配置类失败导致进程退出；具体配置来源和启动/请求时机的扩展解释不视为已证实。 |
| 30 | 通过 | 通过 | [addfb0b549a84a7a](c07/run-30-addfb0b549a84a7a/report.md) | 识别 CONFIG_MISSING/config_missing_exit 对应的配置类失败导致进程退出；具体配置来源和启动/请求时机的扩展解释不视为已证实。 |
| 31 | 通过 | 通过 | [a8c4a1ec29b6487d](c07/run-31-a8c4a1ec29b6487d/report.md) | 识别 CONFIG_MISSING/config_missing_exit 对应的配置类失败导致进程退出；具体配置来源和启动/请求时机的扩展解释不视为已证实。 |
| 32 | 通过 | 通过 | [db9303051c7d42b3](c07/run-32-db9303051c7d42b3/report.md) | 识别 CONFIG_MISSING/config_missing_exit 对应的配置类失败导致进程退出；具体配置来源和启动/请求时机的扩展解释不视为已证实。 |
| 33 | 通过 | 通过 | [c7fbbffde1894e6f](c07/run-33-c7fbbffde1894e6f/report.md) | 识别 CONFIG_MISSING/config_missing_exit 对应的配置类失败导致进程退出；具体配置来源和启动/请求时机的扩展解释不视为已证实。 |
| 34 | 通过 | 通过 | [173fabd869c043a8](c07/run-34-173fabd869c043a8/report.md) | 识别 CONFIG_MISSING/config_missing_exit 对应的配置类失败导致进程退出；具体配置来源和启动/请求时机的扩展解释不视为已证实。 |
| 35 | 通过 | 通过 | [4b94dc77e1bd48f7](c07/run-35-4b94dc77e1bd48f7/report.md) | 识别 CONFIG_MISSING/config_missing_exit 对应的配置类失败导致进程退出；具体配置来源和启动/请求时机的扩展解释不视为已证实。 |
| 36 | 通过 | 通过 | [a941ab59a3a1464b](c07/run-36-a941ab59a3a1464b/report.md) | 识别 CONFIG_MISSING/config_missing_exit 对应的配置类失败导致进程退出；具体配置来源和启动/请求时机的扩展解释不视为已证实。 |
| 37 | 通过 | 通过 | [271bd8163d194610](c07/run-37-271bd8163d194610/report.md) | 识别 CONFIG_MISSING/config_missing_exit 对应的配置类失败导致进程退出；具体配置来源和启动/请求时机的扩展解释不视为已证实。 |
| 38 | 通过 | 通过 | [34a74808f3164619](c07/run-38-34a74808f3164619/report.md) | 识别 CONFIG_MISSING/config_missing_exit 对应的配置类失败导致进程退出；具体配置来源和启动/请求时机的扩展解释不视为已证实。 |
| 39 | 通过 | 通过 | [4c78f158e7744a04](c07/run-39-4c78f158e7744a04/report.md) | 识别 CONFIG_MISSING/config_missing_exit 对应的配置类失败导致进程退出；具体配置来源和启动/请求时机的扩展解释不视为已证实。 |
| 40 | 通过 | 通过 | [8f838f9e14dc46a0](c07/run-40-8f838f9e14dc46a0/report.md) | 识别 CONFIG_MISSING/config_missing_exit 对应的配置类失败导致进程退出；具体配置来源和启动/请求时机的扩展解释不视为已证实。 |
| 41 | 通过 | 待复核 | [86098c6c48c84959](c07/run-41-86098c6c48c84959/report.md) | 配置类主机制正确，但肯定断言 workload-code 中配置文件/键缺失；现有结论未给出此具体修复目标的证明，需复核。 |
| 42 | 通过 | 通过 | [a149f2d120b84351](c07/run-42-a149f2d120b84351/report.md) | 识别 CONFIG_MISSING/config_missing_exit 对应的配置类失败导致进程退出；具体配置来源和启动/请求时机的扩展解释不视为已证实。 |
| 43 | 未通过 | 通过 | [9874791fe49c40d5](c07/run-43-9874791fe49c40d5/report.md) | config_missing_exit 与配置缺失的主动退出机制已明确；未使用完全一致的 CONFIG_MISSING 大写字串不改变机制。 |
| 44 | 通过 | 通过 | [2189492a091847e9](c07/run-44-2189492a091847e9/report.md) | 识别 CONFIG_MISSING/config_missing_exit 对应的配置类失败导致进程退出；具体配置来源和启动/请求时机的扩展解释不视为已证实。 |
| 45 | 通过 | 通过 | [95d2a111537c4dba](c07/run-45-95d2a111537c4dba/report.md) | 识别 CONFIG_MISSING/config_missing_exit 对应的配置类失败导致进程退出；具体配置来源和启动/请求时机的扩展解释不视为已证实。 |
| 46 | 通过 | 通过 | [554cd289579341aa](c07/run-46-554cd289579341aa/report.md) | 识别 CONFIG_MISSING/config_missing_exit 对应的配置类失败导致进程退出；具体配置来源和启动/请求时机的扩展解释不视为已证实。 |
| 47 | 通过 | 待复核 | [ec37cb389e5049c3](c07/run-47-ec37cb389e5049c3/report.md) | 把请求路径 /work 确认为缺失的配置文件，具体对象类型错误；不能把关键词命中等同完整正确。 |
| 48 | 通过 | 通过 | [4d8d5097412542e3](c07/run-48-4d8d5097412542e3/report.md) | 识别 CONFIG_MISSING/config_missing_exit 对应的配置类失败导致进程退出；具体配置来源和启动/请求时机的扩展解释不视为已证实。 |
| 49 | 通过 | 通过 | [08928d99d0dd4075](c07/run-49-08928d99d0dd4075/report.md) | 识别 CONFIG_MISSING/config_missing_exit 对应的配置类失败导致进程退出；具体配置来源和启动/请求时机的扩展解释不视为已证实。 |
| 50 | 通过 | 通过 | [59c573d7fd7f4f2f](c07/run-50-59c573d7fd7f4f2f/report.md) | 识别 CONFIG_MISSING/config_missing_exit 对应的配置类失败导致进程退出；具体配置来源和启动/请求时机的扩展解释不视为已证实。 |

### c08

主要内存超限终止机制普遍正确。不能由 allocated_mib<64Mi 直接证明超过限制，应用分配量不同于容器总内存；泄漏和 Limit 合理性未做代码级独立认证。

| # | 原脚本 | 人工意见 | 原始报告 | 理由 |
|---:|---|---|---|---|
| 1 | 通过 | 通过 | [06808c8c78c8404a](c08/run-01-06808c8c78c8404a/report.md) | 主要机制为请求驱动内存增长触及 64Mi 限制而被杀；未把泄漏细节、峰值精度或仅扩容即可修复视为已证实。 |
| 2 | 通过 | 通过 | [b678864050b641b4](c08/run-02-b678864050b641b4/report.md) | 主要机制为请求驱动内存增长触及 64Mi 限制而被杀；未把泄漏细节、峰值精度或仅扩容即可修复视为已证实。 |
| 3 | 通过 | 通过 | [3716312a211642b5](c08/run-03-3716312a211642b5/report.md) | 主要机制为请求驱动内存增长触及 64Mi 限制而被杀；未把泄漏细节、峰值精度或仅扩容即可修复视为已证实。 |
| 4 | 通过 | 通过 | [bb352188770c46c4](c08/run-04-bb352188770c46c4/report.md) | 主要机制为请求驱动内存增长触及 64Mi 限制而被杀；未把泄漏细节、峰值精度或仅扩容即可修复视为已证实。 |
| 5 | 通过 | 待复核 | [df4736cbb3344156](c08/run-05-df4736cbb3344156/report.md) | 主机制 OOM 正确，但把 245760 bytes 声称为远超 64Mi；这是明确的数值证据错误，不能认可其完整证据链。 |
| 6 | 通过 | 通过 | [29fd368953d9423e](c08/run-06-29fd368953d9423e/report.md) | 主要机制为请求驱动内存增长触及 64Mi 限制而被杀；未把泄漏细节、峰值精度或仅扩容即可修复视为已证实。 |
| 7 | 通过 | 通过 | [86522d2b4c1045b2](c08/run-07-86522d2b4c1045b2/report.md) | 主要机制为请求驱动内存增长触及 64Mi 限制而被杀；未把泄漏细节、峰值精度或仅扩容即可修复视为已证实。 |
| 8 | 通过 | 通过 | [fba85feeb1c44df9](c08/run-08-fba85feeb1c44df9/report.md) | 主要机制为请求驱动内存增长触及 64Mi 限制而被杀；未把泄漏细节、峰值精度或仅扩容即可修复视为已证实。 |
| 9 | 通过 | 通过 | [0122f1656e6f4db3](c08/run-09-0122f1656e6f4db3/report.md) | 主要机制为请求驱动内存增长触及 64Mi 限制而被杀；未把泄漏细节、峰值精度或仅扩容即可修复视为已证实。 |
| 10 | 通过 | 通过 | [c0f6377a185c4a4b](c08/run-10-c0f6377a185c4a4b/report.md) | 主要机制为请求驱动内存增长触及 64Mi 限制而被杀；未把泄漏细节、峰值精度或仅扩容即可修复视为已证实。 |
| 11 | 通过 | 通过 | [58e304e40d1a4bfd](c08/run-11-58e304e40d1a4bfd/report.md) | 主要机制为请求驱动内存增长触及 64Mi 限制而被杀；未把泄漏细节、峰值精度或仅扩容即可修复视为已证实。 |
| 12 | 通过 | 通过 | [2381029ed0d540db](c08/run-12-2381029ed0d540db/report.md) | 主要机制为请求驱动内存增长触及 64Mi 限制而被杀；未把泄漏细节、峰值精度或仅扩容即可修复视为已证实。 |
| 13 | 通过 | 通过 | [647303dbe33b40e0](c08/run-13-647303dbe33b40e0/report.md) | 主要机制为请求驱动内存增长触及 64Mi 限制而被杀；未把泄漏细节、峰值精度或仅扩容即可修复视为已证实。 |
| 14 | 通过 | 通过 | [186bf521faeb43da](c08/run-14-186bf521faeb43da/report.md) | 主要机制为请求驱动内存增长触及 64Mi 限制而被杀；未把泄漏细节、峰值精度或仅扩容即可修复视为已证实。 |
| 15 | 通过 | 通过 | [6d6c5ece25ac4b45](c08/run-15-6d6c5ece25ac4b45/report.md) | 主要机制为请求驱动内存增长触及 64Mi 限制而被杀；未把泄漏细节、峰值精度或仅扩容即可修复视为已证实。 |
| 16 | 通过 | 通过 | [dfa3f8be57b24c08](c08/run-16-dfa3f8be57b24c08/report.md) | 主要机制为请求驱动内存增长触及 64Mi 限制而被杀；未把泄漏细节、峰值精度或仅扩容即可修复视为已证实。 |
| 17 | 通过 | 通过 | [cf0d9ec9d5fa41e3](c08/run-17-cf0d9ec9d5fa41e3/report.md) | 主要机制为请求驱动内存增长触及 64Mi 限制而被杀；未把泄漏细节、峰值精度或仅扩容即可修复视为已证实。 |
| 18 | 通过 | 通过 | [f5475222c5a34903](c08/run-18-f5475222c5a34903/report.md) | 主要机制为请求驱动内存增长触及 64Mi 限制而被杀；未把泄漏细节、峰值精度或仅扩容即可修复视为已证实。 |
| 19 | 通过 | 通过 | [34463a22b25748d4](c08/run-19-34463a22b25748d4/report.md) | 主要机制为请求驱动内存增长触及 64Mi 限制而被杀；未把泄漏细节、峰值精度或仅扩容即可修复视为已证实。 |
| 20 | 通过 | 通过 | [06eecf4fd8d14644](c08/run-20-06eecf4fd8d14644/report.md) | 主要机制为请求驱动内存增长触及 64Mi 限制而被杀；未把泄漏细节、峰值精度或仅扩容即可修复视为已证实。 |
| 21 | 通过 | 通过 | [6fe88439f4794f2f](c08/run-21-6fe88439f4794f2f/report.md) | 主要机制为请求驱动内存增长触及 64Mi 限制而被杀；未把泄漏细节、峰值精度或仅扩容即可修复视为已证实。 |
| 22 | 通过 | 通过 | [0e73f9100a11479f](c08/run-22-0e73f9100a11479f/report.md) | 主要机制为请求驱动内存增长触及 64Mi 限制而被杀；未把泄漏细节、峰值精度或仅扩容即可修复视为已证实。 |
| 23 | 通过 | 通过 | [3dd0460d95444370](c08/run-23-3dd0460d95444370/report.md) | 主要机制为请求驱动内存增长触及 64Mi 限制而被杀；未把泄漏细节、峰值精度或仅扩容即可修复视为已证实。 |
| 24 | 通过 | 通过 | [e6e46e4a0d8444f0](c08/run-24-e6e46e4a0d8444f0/report.md) | 主要机制为请求驱动内存增长触及 64Mi 限制而被杀；未把泄漏细节、峰值精度或仅扩容即可修复视为已证实。 |
| 25 | 通过 | 通过 | [782982b2d8c54f9f](c08/run-25-782982b2d8c54f9f/report.md) | 主要机制为请求驱动内存增长触及 64Mi 限制而被杀；未把泄漏细节、峰值精度或仅扩容即可修复视为已证实。 |
| 26 | 通过 | 通过 | [142581aaee584211](c08/run-26-142581aaee584211/report.md) | 主要机制为请求驱动内存增长触及 64Mi 限制而被杀；未把泄漏细节、峰值精度或仅扩容即可修复视为已证实。 |
| 27 | 通过 | 通过 | [7907c780109f4bc1](c08/run-27-7907c780109f4bc1/report.md) | 主要机制为请求驱动内存增长触及 64Mi 限制而被杀；未把泄漏细节、峰值精度或仅扩容即可修复视为已证实。 |
| 28 | 通过 | 通过 | [1e7f76ae0b6b44aa](c08/run-28-1e7f76ae0b6b44aa/report.md) | 主要机制为请求驱动内存增长触及 64Mi 限制而被杀；未把泄漏细节、峰值精度或仅扩容即可修复视为已证实。 |
| 29 | 通过 | 通过 | [ef42fb78bcad4740](c08/run-29-ef42fb78bcad4740/report.md) | 主要机制为请求驱动内存增长触及 64Mi 限制而被杀；未把泄漏细节、峰值精度或仅扩容即可修复视为已证实。 |
| 30 | 通过 | 通过 | [8d72e4e175f44924](c08/run-30-8d72e4e175f44924/report.md) | 主要机制为请求驱动内存增长触及 64Mi 限制而被杀；未把泄漏细节、峰值精度或仅扩容即可修复视为已证实。 |
| 31 | 通过 | 通过 | [8be3013e9a0c47f5](c08/run-31-8be3013e9a0c47f5/report.md) | 主要机制为请求驱动内存增长触及 64Mi 限制而被杀；未把泄漏细节、峰值精度或仅扩容即可修复视为已证实。 |
| 32 | 通过 | 通过 | [157685349b494b1b](c08/run-32-157685349b494b1b/report.md) | 主要机制为请求驱动内存增长触及 64Mi 限制而被杀；未把泄漏细节、峰值精度或仅扩容即可修复视为已证实。 |
| 33 | 通过 | 通过 | [da4a9f59cab145d7](c08/run-33-da4a9f59cab145d7/report.md) | 主要机制为请求驱动内存增长触及 64Mi 限制而被杀；未把泄漏细节、峰值精度或仅扩容即可修复视为已证实。 |
| 34 | 未通过 | 通过 | [0ed04c30b1b44be4](c08/run-34-0ed04c30b1b44be4/report.md) | 明确描述内存增长超过 64Mi 后被内核强制终止；未写 OOMKilled 精确名称并不改变机制，属于脚本漏判。 |
| 35 | 通过 | 通过 | [8c6ba8ff07e94a0b](c08/run-35-8c6ba8ff07e94a0b/report.md) | 主要机制为请求驱动内存增长触及 64Mi 限制而被杀；未把泄漏细节、峰值精度或仅扩容即可修复视为已证实。 |
| 36 | 通过 | 通过 | [f2e0e7b37cf94690](c08/run-36-f2e0e7b37cf94690/report.md) | 主要机制为请求驱动内存增长触及 64Mi 限制而被杀；未把泄漏细节、峰值精度或仅扩容即可修复视为已证实。 |
| 37 | 通过 | 通过 | [da9f0c8425aa48d0](c08/run-37-da9f0c8425aa48d0/report.md) | 主要机制为请求驱动内存增长触及 64Mi 限制而被杀；未把泄漏细节、峰值精度或仅扩容即可修复视为已证实。 |
| 38 | 未通过 | 通过 | [dfb91900a617483f](c08/run-38-dfb91900a617483f/report.md) | 明确描述内存增长超过 64Mi 后被内核强制终止；未写 OOMKilled 精确名称并不改变机制，属于脚本漏判。 |
| 39 | 通过 | 通过 | [9620ed9fd8aa4f2c](c08/run-39-9620ed9fd8aa4f2c/report.md) | 主要机制为请求驱动内存增长触及 64Mi 限制而被杀；未把泄漏细节、峰值精度或仅扩容即可修复视为已证实。 |
| 40 | 通过 | 通过 | [429c3e17f9f84648](c08/run-40-429c3e17f9f84648/report.md) | 主要机制为请求驱动内存增长触及 64Mi 限制而被杀；未把泄漏细节、峰值精度或仅扩容即可修复视为已证实。 |
| 41 | 通过 | 通过 | [53d3ec8afa1a4b79](c08/run-41-53d3ec8afa1a4b79/report.md) | 主要机制为请求驱动内存增长触及 64Mi 限制而被杀；未把泄漏细节、峰值精度或仅扩容即可修复视为已证实。 |
| 42 | 通过 | 通过 | [7f8695276d31417a](c08/run-42-7f8695276d31417a/report.md) | 主要机制为请求驱动内存增长触及 64Mi 限制而被杀；未把泄漏细节、峰值精度或仅扩容即可修复视为已证实。 |
| 43 | 通过 | 通过 | [f99276d9b04a4586](c08/run-43-f99276d9b04a4586/report.md) | 主要机制为请求驱动内存增长触及 64Mi 限制而被杀；未把泄漏细节、峰值精度或仅扩容即可修复视为已证实。 |
| 44 | 通过 | 通过 | [7f8ed952f24d4949](c08/run-44-7f8ed952f24d4949/report.md) | 主要机制为请求驱动内存增长触及 64Mi 限制而被杀；未把泄漏细节、峰值精度或仅扩容即可修复视为已证实。 |
| 45 | 通过 | 通过 | [0be4c726c45a479e](c08/run-45-0be4c726c45a479e/report.md) | 主要机制为请求驱动内存增长触及 64Mi 限制而被杀；未把泄漏细节、峰值精度或仅扩容即可修复视为已证实。 |
| 46 | 通过 | 通过 | [7dd74c9abd224784](c08/run-46-7dd74c9abd224784/report.md) | 主要机制为请求驱动内存增长触及 64Mi 限制而被杀；未把泄漏细节、峰值精度或仅扩容即可修复视为已证实。 |
| 47 | 通过 | 通过 | [116be82b23b54677](c08/run-47-116be82b23b54677/report.md) | 主要机制为请求驱动内存增长触及 64Mi 限制而被杀；未把泄漏细节、峰值精度或仅扩容即可修复视为已证实。 |
| 48 | 通过 | 通过 | [a884015b2bf941e3](c08/run-48-a884015b2bf941e3/report.md) | 主要机制为请求驱动内存增长触及 64Mi 限制而被杀；未把泄漏细节、峰值精度或仅扩容即可修复视为已证实。 |
| 49 | 未通过 | 通过 | [772c116051a54e0f](c08/run-49-772c116051a54e0f/report.md) | 明确描述内存增长超过 64Mi 后被内核强制终止；未写 OOMKilled 精确名称并不改变机制，属于脚本漏判。 |
| 50 | 通过 | 通过 | [355c1a0df63a481a](c08/run-50-355c1a0df63a481a/report.md) | 主要机制为请求驱动内存增长触及 64Mi 限制而被杀；未把泄漏细节、峰值精度或仅扩容即可修复视为已证实。 |

### c09

503 就绪失败机制大多正确，不能将缺少下游身份与未识别探针机制混为一谈。许多报告将 /work 与 /ready 混写，主机制通过不代表路径或真实下游故障已核实。

| # | 原脚本 | 人工意见 | 原始报告 | 理由 |
|---:|---|---|---|---|
| 1 | 通过 | 通过 | [3e7bebc11e0c4eb3](c09/run-01-3e7bebc11e0c4eb3/report.md) | 主要机制为应用返回 503 导致就绪探针失败；具体外部依赖未证实，/work 流量不可直接当作 /ready 探针配置。 |
| 2 | 未通过 | 通过 | [542f54c706b8415f](c09/run-02-542f54c706b8415f/report.md) | 已说明健康/就绪检查返回 503 导致未就绪；未定位真实下游或精确字串不应抹去正确的主要机制，脚本漏判。 |
| 3 | 通过 | 通过 | [54f2be9b21e84f48](c09/run-03-54f2be9b21e84f48/report.md) | 主要机制为应用返回 503 导致就绪探针失败；具体外部依赖未证实，/work 流量不可直接当作 /ready 探针配置。 |
| 4 | 通过 | 通过 | [0f5be6efafb84398](c09/run-04-0f5be6efafb84398/report.md) | 主要机制为应用返回 503 导致就绪探针失败；具体外部依赖未证实，/work 流量不可直接当作 /ready 探针配置。 |
| 5 | 通过 | 通过 | [130a8b810576414c](c09/run-05-130a8b810576414c/report.md) | 主要机制为应用返回 503 导致就绪探针失败；具体外部依赖未证实，/work 流量不可直接当作 /ready 探针配置。 |
| 6 | 通过 | 通过 | [4905a22b4bc7422a](c09/run-06-4905a22b4bc7422a/report.md) | 主要机制为应用返回 503 导致就绪探针失败；具体外部依赖未证实，/work 流量不可直接当作 /ready 探针配置。 |
| 7 | 通过 | 通过 | [0a715c0d0fd34d84](c09/run-07-0a715c0d0fd34d84/report.md) | 主要机制为应用返回 503 导致就绪探针失败；具体外部依赖未证实，/work 流量不可直接当作 /ready 探针配置。 |
| 8 | 通过 | 通过 | [9e93f2083d364cf1](c09/run-08-9e93f2083d364cf1/report.md) | 主要机制为应用返回 503 导致就绪探针失败；具体外部依赖未证实，/work 流量不可直接当作 /ready 探针配置。 |
| 9 | 通过 | 通过 | [e4b6a0a7adc94b86](c09/run-09-e4b6a0a7adc94b86/report.md) | 主要机制为应用返回 503 导致就绪探针失败；具体外部依赖未证实，/work 流量不可直接当作 /ready 探针配置。 |
| 10 | 通过 | 通过 | [77721463c8564621](c09/run-10-77721463c8564621/report.md) | 主要机制为应用返回 503 导致就绪探针失败；具体外部依赖未证实，/work 流量不可直接当作 /ready 探针配置。 |
| 11 | 未通过 | 通过 | [9d1e9de2743745a4](c09/run-11-9d1e9de2743745a4/report.md) | 已说明健康/就绪检查返回 503 导致未就绪；未定位真实下游或精确字串不应抹去正确的主要机制，脚本漏判。 |
| 12 | 通过 | 不通过 | [90cad484f4c64c60](c09/run-12-90cad484f4c64c60/report.md) | 将目标 Pod 自身的 172.16.104.35:8080 当作故障外部依赖，错误锁定根因实体，被脚本放过。 |
| 13 | 通过 | 通过 | [70749d8f195b47f8](c09/run-13-70749d8f195b47f8/report.md) | 主要机制为应用返回 503 导致就绪探针失败；具体外部依赖未证实，/work 流量不可直接当作 /ready 探针配置。 |
| 14 | 通过 | 通过 | [451b9a692190423b](c09/run-14-451b9a692190423b/report.md) | 主要机制为应用返回 503 导致就绪探针失败；具体外部依赖未证实，/work 流量不可直接当作 /ready 探针配置。 |
| 15 | 通过 | 通过 | [7dcd2a9189274c17](c09/run-15-7dcd2a9189274c17/report.md) | 主要机制为应用返回 503 导致就绪探针失败；具体外部依赖未证实，/work 流量不可直接当作 /ready 探针配置。 |
| 16 | 未通过 | 通过 | [dec6fa329c434897](c09/run-16-dec6fa329c434897/report.md) | 已说明健康/就绪检查返回 503 导致未就绪；未定位真实下游或精确字串不应抹去正确的主要机制，脚本漏判。 |
| 17 | 通过 | 通过 | [3db176e1b55b446e](c09/run-17-3db176e1b55b446e/report.md) | 主要机制为应用返回 503 导致就绪探针失败；具体外部依赖未证实，/work 流量不可直接当作 /ready 探针配置。 |
| 18 | 通过 | 通过 | [5fa0634c80994de0](c09/run-18-5fa0634c80994de0/report.md) | 主要机制为应用返回 503 导致就绪探针失败；具体外部依赖未证实，/work 流量不可直接当作 /ready 探针配置。 |
| 19 | 通过 | 通过 | [de797b8359a24af1](c09/run-19-de797b8359a24af1/report.md) | 主要机制为应用返回 503 导致就绪探针失败；具体外部依赖未证实，/work 流量不可直接当作 /ready 探针配置。 |
| 20 | 通过 | 通过 | [f3e0d73474d94d30](c09/run-20-f3e0d73474d94d30/report.md) | 主要机制为应用返回 503 导致就绪探针失败；具体外部依赖未证实，/work 流量不可直接当作 /ready 探针配置。 |
| 21 | 通过 | 通过 | [931e8386d4b44e6c](c09/run-21-931e8386d4b44e6c/report.md) | 主要机制为应用返回 503 导致就绪探针失败；具体外部依赖未证实，/work 流量不可直接当作 /ready 探针配置。 |
| 22 | 未通过 | 通过 | [7bfa64f7248f47ed](c09/run-22-7bfa64f7248f47ed/report.md) | 已说明健康/就绪检查返回 503 导致未就绪；未定位真实下游或精确字串不应抹去正确的主要机制，脚本漏判。 |
| 23 | 通过 | 通过 | [97134487c5284e89](c09/run-23-97134487c5284e89/report.md) | 主要机制为应用返回 503 导致就绪探针失败；具体外部依赖未证实，/work 流量不可直接当作 /ready 探针配置。 |
| 24 | 通过 | 通过 | [907d4209a852407f](c09/run-24-907d4209a852407f/report.md) | 主要机制为应用返回 503 导致就绪探针失败；具体外部依赖未证实，/work 流量不可直接当作 /ready 探针配置。 |
| 25 | 通过 | 通过 | [6e170532294f4531](c09/run-25-6e170532294f4531/report.md) | 主要机制为应用返回 503 导致就绪探针失败；具体外部依赖未证实，/work 流量不可直接当作 /ready 探针配置。 |
| 26 | 通过 | 通过 | [dcf81fe7ead540f3](c09/run-26-dcf81fe7ead540f3/report.md) | 主要机制为应用返回 503 导致就绪探针失败；具体外部依赖未证实，/work 流量不可直接当作 /ready 探针配置。 |
| 27 | 通过 | 通过 | [0c0ad3a6a81846e1](c09/run-27-0c0ad3a6a81846e1/report.md) | 主要机制为应用返回 503 导致就绪探针失败；具体外部依赖未证实，/work 流量不可直接当作 /ready 探针配置。 |
| 28 | 通过 | 待复核 | [3d798f059b30402a](c09/run-28-3d798f059b30402a/report.md) | 主机制为 503 就绪失败，但将 allocated_mib=0 视为异常并推测内存初始化失败导致依赖不可用，需核实而非当作因果证据。 |
| 29 | 通过 | 通过 | [92e2145d88b64fdc](c09/run-29-92e2145d88b64fdc/report.md) | 主要机制为应用返回 503 导致就绪探针失败；具体外部依赖未证实，/work 流量不可直接当作 /ready 探针配置。 |
| 30 | 通过 | 通过 | [99c2f012b29443fb](c09/run-30-99c2f012b29443fb/report.md) | 主要机制为应用返回 503 导致就绪探针失败；具体外部依赖未证实，/work 流量不可直接当作 /ready 探针配置。 |
| 31 | 通过 | 通过 | [5cafa123668a4458](c09/run-31-5cafa123668a4458/report.md) | 主要机制为应用返回 503 导致就绪探针失败；具体外部依赖未证实，/work 流量不可直接当作 /ready 探针配置。 |
| 32 | 通过 | 通过 | [3f1680e6104e4a0f](c09/run-32-3f1680e6104e4a0f/report.md) | 主要机制为应用返回 503 导致就绪探针失败；具体外部依赖未证实，/work 流量不可直接当作 /ready 探针配置。 |
| 33 | 通过 | 通过 | [c930f9afa05f46eb](c09/run-33-c930f9afa05f46eb/report.md) | 主要机制为应用返回 503 导致就绪探针失败；具体外部依赖未证实，/work 流量不可直接当作 /ready 探针配置。 |
| 34 | 未通过 | 通过 | [e194edf175964afd](c09/run-34-e194edf175964afd/report.md) | 已说明健康/就绪检查返回 503 导致未就绪；未定位真实下游或精确字串不应抹去正确的主要机制，脚本漏判。 |
| 35 | 通过 | 通过 | [ed8432fdca9340dc](c09/run-35-ed8432fdca9340dc/report.md) | 主要机制为应用返回 503 导致就绪探针失败；具体外部依赖未证实，/work 流量不可直接当作 /ready 探针配置。 |
| 36 | 未通过 | 通过 | [54e91f6cd7884be0](c09/run-36-54e91f6cd7884be0/report.md) | 已说明健康/就绪检查返回 503 导致未就绪；未定位真实下游或精确字串不应抹去正确的主要机制，脚本漏判。 |
| 37 | 通过 | 通过 | [d3974619aeca43c6](c09/run-37-d3974619aeca43c6/report.md) | 主要机制为应用返回 503 导致就绪探针失败；具体外部依赖未证实，/work 流量不可直接当作 /ready 探针配置。 |
| 38 | 通过 | 通过 | [7bfa00ef08da46da](c09/run-38-7bfa00ef08da46da/report.md) | 主要机制为应用返回 503 导致就绪探针失败；具体外部依赖未证实，/work 流量不可直接当作 /ready 探针配置。 |
| 39 | 通过 | 通过 | [50eaf50f87ef4d19](c09/run-39-50eaf50f87ef4d19/report.md) | 主要机制为应用返回 503 导致就绪探针失败；具体外部依赖未证实，/work 流量不可直接当作 /ready 探针配置。 |
| 40 | 通过 | 通过 | [6f4ac32d9036452c](c09/run-40-6f4ac32d9036452c/report.md) | 主要机制为应用返回 503 导致就绪探针失败；具体外部依赖未证实，/work 流量不可直接当作 /ready 探针配置。 |
| 41 | 未通过 | 通过 | [9e1b5e2ff2074179](c09/run-41-9e1b5e2ff2074179/report.md) | 已说明健康/就绪检查返回 503 导致未就绪；未定位真实下游或精确字串不应抹去正确的主要机制，脚本漏判。 |
| 42 | 通过 | 通过 | [ea7968595a1c4d5d](c09/run-42-ea7968595a1c4d5d/report.md) | 主要机制为应用返回 503 导致就绪探针失败；具体外部依赖未证实，/work 流量不可直接当作 /ready 探针配置。 |
| 43 | 未通过 | 通过 | [1c62a2bcc92f4dcf](c09/run-43-1c62a2bcc92f4dcf/report.md) | 已说明健康/就绪检查返回 503 导致未就绪；未定位真实下游或精确字串不应抹去正确的主要机制，脚本漏判。 |
| 44 | 通过 | 通过 | [6a62de7f165c4408](c09/run-44-6a62de7f165c4408/report.md) | 主要机制为应用返回 503 导致就绪探针失败；具体外部依赖未证实，/work 流量不可直接当作 /ready 探针配置。 |
| 45 | 通过 | 通过 | [da36e1ed61024b72](c09/run-45-da36e1ed61024b72/report.md) | 主要机制为应用返回 503 导致就绪探针失败；具体外部依赖未证实，/work 流量不可直接当作 /ready 探针配置。 |
| 46 | 通过 | 通过 | [e429a5fda5264027](c09/run-46-e429a5fda5264027/report.md) | 主要机制为应用返回 503 导致就绪探针失败；具体外部依赖未证实，/work 流量不可直接当作 /ready 探针配置。 |
| 47 | 通过 | 通过 | [13b9dee402b1409e](c09/run-47-13b9dee402b1409e/report.md) | 主要机制为应用返回 503 导致就绪探针失败；具体外部依赖未证实，/work 流量不可直接当作 /ready 探针配置。 |
| 48 | 通过 | 通过 | [b0e964053d1744db](c09/run-48-b0e964053d1744db/report.md) | 主要机制为应用返回 503 导致就绪探针失败；具体外部依赖未证实，/work 流量不可直接当作 /ready 探针配置。 |
| 49 | 通过 | 通过 | [f57a2c2ed18a4cf0](c09/run-49-f57a2c2ed18a4cf0/report.md) | 主要机制为应用返回 503 导致就绪探针失败；具体外部依赖未证实，/work 流量不可直接当作 /ready 探针配置。 |
| 50 | 通过 | 通过 | [11a251d55db24357](c09/run-50-11a251d55db24357/report.md) | 主要机制为应用返回 503 导致就绪探针失败；具体外部依赖未证实，/work 流量不可直接当作 /ready 探针配置。 |

### c10

低分不能主要归咎脚本：大量结论把 Exit 137+96Mi 当成 OOM 的充分证据，并倒置探针失败和进程终止的因果。另有少量漏判和无依据的探针配置归因。

| # | 原脚本 | 人工意见 | 原始报告 | 理由 |
|---:|---|---|---|---|
| 1 | 未通过 | 待复核 | [6ed869afd7044dc0](c10/run-01-6ed869afd7044dc0/report.md) | 探针导致重启方向正确，但把业务 /work 正常、探针失败直接确认为路径/超时等配置错误；应用故意返回 500 不等于探针配置错。 |
| 2 | 未通过 | 不通过 | [a5569f5c4baa4b3e](c10/run-02-a5569f5c4baa4b3e/report.md) | 明确把存活探针失败导致的终止误归为 OOM/内存不足，或未收敛到存活探针机制。 |
| 3 | 未通过 | 待复核 | [3944563daac04848](c10/run-03-3944563daac04848/report.md) | 提及存活探针造成终止，但又明确无法在探针 Kill 和 OOM 之间判定，结论未稳定收敛。 |
| 4 | 通过 | 通过 | [0314978a08124888](c10/run-04-0314978a08124888/report.md) | 确认存活探针端点失败导致 kubelet 终止和重启；未知 500 内部代码细节不否定此机制，不能由 Running 推断故障已修复。 |
| 5 | 未通过 | 待复核 | [f813391ae8944334](c10/run-05-f813391ae8944334/report.md) | 探针导致重启方向正确，但把业务 /work 正常、探针失败直接确认为路径/超时等配置错误；应用故意返回 500 不等于探针配置错。 |
| 6 | 未通过 | 不通过 | [b5d66265d5cd417c](c10/run-06-b5d66265d5cd417c/report.md) | 明确把存活探针失败导致的终止误归为 OOM/内存不足，或未收敛到存活探针机制。 |
| 7 | 未通过 | 不通过 | [477cb50b9c29461b](c10/run-07-477cb50b9c29461b/report.md) | 明确把存活探针失败导致的终止误归为 OOM/内存不足，或未收敛到存活探针机制。 |
| 8 | 通过 | 通过 | [ef82ee83e2f9407f](c10/run-08-ef82ee83e2f9407f/report.md) | 确认存活探针端点失败导致 kubelet 终止和重启；未知 500 内部代码细节不否定此机制，不能由 Running 推断故障已修复。 |
| 9 | 通过 | 待复核 | [10940b0b03114f4b](c10/run-09-10940b0b03114f4b/report.md) | 探针导致重启方向正确，但把业务 /work 正常、探针失败直接确认为路径/超时等配置错误；应用故意返回 500 不等于探针配置错。 |
| 10 | 未通过 | 不通过 | [048c1b2e7d0b45b0](c10/run-10-048c1b2e7d0b45b0/report.md) | 明确把存活探针失败导致的终止误归为 OOM/内存不足，或未收敛到存活探针机制。 |
| 11 | 未通过 | 不通过 | [773e640841504d69](c10/run-11-773e640841504d69/report.md) | 明确把存活探针失败导致的终止误归为 OOM/内存不足，或未收敛到存活探针机制。 |
| 12 | 通过 | 通过 | [595cea03b42a453e](c10/run-12-595cea03b42a453e/report.md) | 确认存活探针端点失败导致 kubelet 终止和重启；未知 500 内部代码细节不否定此机制，不能由 Running 推断故障已修复。 |
| 13 | 未通过 | 通过 | [b5770abec6044924](c10/run-13-b5770abec6044924/report.md) | 确认存活探针端点失败导致 kubelet 终止和重启；未知 500 内部代码细节不否定此机制，不能由 Running 推断故障已修复。 |
| 14 | 通过 | 通过 | [2f8fd2c5993c4116](c10/run-14-2f8fd2c5993c4116/report.md) | 确认存活探针端点失败导致 kubelet 终止和重启；未知 500 内部代码细节不否定此机制，不能由 Running 推断故障已修复。 |
| 15 | 未通过 | 不通过 | [c5b745b0029b4bc4](c10/run-15-c5b745b0029b4bc4/report.md) | 明确把存活探针失败导致的终止误归为 OOM/内存不足，或未收敛到存活探针机制。 |
| 16 | 通过 | 通过 | [819936b0cbfb433d](c10/run-16-819936b0cbfb433d/report.md) | 确认存活探针端点失败导致 kubelet 终止和重启；未知 500 内部代码细节不否定此机制，不能由 Running 推断故障已修复。 |
| 17 | 未通过 | 待复核 | [f7ca760edf0140b5](c10/run-17-f7ca760edf0140b5/report.md) | 提及存活探针造成终止，但又明确无法在探针 Kill 和 OOM 之间判定，结论未稳定收敛。 |
| 18 | 未通过 | 不通过 | [465b72761bcc44c5](c10/run-18-465b72761bcc44c5/report.md) | 明确把存活探针失败导致的终止误归为 OOM/内存不足，或未收敛到存活探针机制。 |
| 19 | 未通过 | 不通过 | [ed6505bb354a4f2a](c10/run-19-ed6505bb354a4f2a/report.md) | 明确把存活探针失败导致的终止误归为 OOM/内存不足，或未收敛到存活探针机制。 |
| 20 | 通过 | 通过 | [fb99eab3dccf4fdb](c10/run-20-fb99eab3dccf4fdb/report.md) | 确认存活探针端点失败导致 kubelet 终止和重启；未知 500 内部代码细节不否定此机制，不能由 Running 推断故障已修复。 |
| 21 | 未通过 | 通过 | [a003be2518b04e1d](c10/run-21-a003be2518b04e1d/report.md) | 确认存活探针端点失败导致 kubelet 终止和重启；未知 500 内部代码细节不否定此机制，不能由 Running 推断故障已修复。 |
| 22 | 未通过 | 不通过 | [bbdc11dddf0741ea](c10/run-22-bbdc11dddf0741ea/report.md) | 明确把存活探针失败导致的终止误归为 OOM/内存不足，或未收敛到存活探针机制。 |
| 23 | 未通过 | 不通过 | [ff719879834f4f57](c10/run-23-ff719879834f4f57/report.md) | 明确把存活探针失败导致的终止误归为 OOM/内存不足，或未收敛到存活探针机制。 |
| 24 | 通过 | 通过 | [297d13622b6c4e7d](c10/run-24-297d13622b6c4e7d/report.md) | 确认存活探针端点失败导致 kubelet 终止和重启；未知 500 内部代码细节不否定此机制，不能由 Running 推断故障已修复。 |
| 25 | 未通过 | 不通过 | [8fc23f6dff4c4e98](c10/run-25-8fc23f6dff4c4e98/report.md) | 明确把存活探针失败导致的终止误归为 OOM/内存不足，或未收敛到存活探针机制。 |
| 26 | 未通过 | 不通过 | [babbac6907b941d0](c10/run-26-babbac6907b941d0/report.md) | 明确把存活探针失败导致的终止误归为 OOM/内存不足，或未收敛到存活探针机制。 |
| 27 | 通过 | 通过 | [00ff4012a5514634](c10/run-27-00ff4012a5514634/report.md) | 确认存活探针端点失败导致 kubelet 终止和重启；未知 500 内部代码细节不否定此机制，不能由 Running 推断故障已修复。 |
| 28 | 未通过 | 不通过 | [c2c4dcf905c341c1](c10/run-28-c2c4dcf905c341c1/report.md) | 只确认 SIGKILL/异常终止，继续在 OOM、外部 Kill 等假设之间徘徊，未确认本 Case 存活探针失败的主要机制。 |
| 29 | 未通过 | 不通过 | [e4514d1efff24cc5](c10/run-29-e4514d1efff24cc5/report.md) | 明确把存活探针失败导致的终止误归为 OOM/内存不足，或未收敛到存活探针机制。 |
| 30 | 通过 | 不通过 | [fa163027a415434c](c10/run-30-fa163027a415434c/report.md) | 主要根因被确定为 96Mi 内存不足，虽然出现探针 500 关键词仍属错误上游因果，脚本误判通过。 |
| 31 | 通过 | 通过 | [65ac9509eef34cf1](c10/run-31-65ac9509eef34cf1/report.md) | 确认存活探针端点失败导致 kubelet 终止和重启；未知 500 内部代码细节不否定此机制，不能由 Running 推断故障已修复。 |
| 32 | 未通过 | 待复核 | [447e5d9db21a4a7e](c10/run-32-447e5d9db21a4a7e/report.md) | 同份报告分别给出内存不足/OOM 和探针失败根因，须核对各实体及重复分组，不能强行按一个正确词判通过。 |
| 33 | 通过 | 通过 | [08c7ed39b4b14d98](c10/run-33-08c7ed39b4b14d98/report.md) | 确认存活探针端点失败导致 kubelet 终止和重启；未知 500 内部代码细节不否定此机制，不能由 Running 推断故障已修复。 |
| 34 | 未通过 | 不通过 | [d4942084644f4b10](c10/run-34-d4942084644f4b10/report.md) | 明确把存活探针失败导致的终止误归为 OOM/内存不足，或未收敛到存活探针机制。 |
| 35 | 未通过 | 不通过 | [9046769b26864745](c10/run-35-9046769b26864745/report.md) | 只确认 SIGKILL/异常终止，继续在 OOM、外部 Kill 等假设之间徘徊，未确认本 Case 存活探针失败的主要机制。 |
| 36 | 通过 | 待复核 | [4f7740f082af41d2](c10/run-36-4f7740f082af41d2/report.md) | 探针导致重启方向正确，但把业务 /work 正常、探针失败直接确认为路径/超时等配置错误；应用故意返回 500 不等于探针配置错。 |
| 37 | 未通过 | 不通过 | [26390adda6e642d9](c10/run-37-26390adda6e642d9/report.md) | 只确认 SIGKILL/异常终止，继续在 OOM、外部 Kill 等假设之间徘徊，未确认本 Case 存活探针失败的主要机制。 |
| 38 | 未通过 | 不通过 | [3ae44c8f576b475d](c10/run-38-3ae44c8f576b475d/report.md) | 明确把存活探针失败导致的终止误归为 OOM/内存不足，或未收敛到存活探针机制。 |
| 39 | 未通过 | 不通过 | [400cce1239cd4708](c10/run-39-400cce1239cd4708/report.md) | 只确认 SIGKILL/异常终止，继续在 OOM、外部 Kill 等假设之间徘徊，未确认本 Case 存活探针失败的主要机制。 |
| 40 | 通过 | 通过 | [593b6220fe7a4e9b](c10/run-40-593b6220fe7a4e9b/report.md) | 确认存活探针端点失败导致 kubelet 终止和重启；未知 500 内部代码细节不否定此机制，不能由 Running 推断故障已修复。 |
| 41 | 通过 | 通过 | [5354403c2c3a450a](c10/run-41-5354403c2c3a450a/report.md) | 确认存活探针端点失败导致 kubelet 终止和重启；未知 500 内部代码细节不否定此机制，不能由 Running 推断故障已修复。 |
| 42 | 未通过 | 不通过 | [f844a6e8a5644e4d](c10/run-42-f844a6e8a5644e4d/report.md) | 明确把存活探针失败导致的终止误归为 OOM/内存不足，或未收敛到存活探针机制。 |
| 43 | 未通过 | 不通过 | [af71d58dd75c49b0](c10/run-43-af71d58dd75c49b0/report.md) | 明确把存活探针失败导致的终止误归为 OOM/内存不足，或未收敛到存活探针机制。 |
| 44 | 未通过 | 不通过 | [c7046e7e68de44e0](c10/run-44-c7046e7e68de44e0/report.md) | 明确把存活探针失败导致的终止误归为 OOM/内存不足，或未收敛到存活探针机制。 |
| 45 | 通过 | 待复核 | [e5b39fbf65c44bec](c10/run-45-e5b39fbf65c44bec/report.md) | 探针导致重启方向正确，但把业务 /work 正常、探针失败直接确认为路径/超时等配置错误；应用故意返回 500 不等于探针配置错。 |
| 46 | 未通过 | 不通过 | [4aab8b48def74313](c10/run-46-4aab8b48def74313/report.md) | 明确把存活探针失败导致的终止误归为 OOM/内存不足，或未收敛到存活探针机制。 |
| 47 | 未通过 | 通过 | [3c4b09dc10ca4b52](c10/run-47-3c4b09dc10ca4b52/report.md) | 确认存活探针端点失败导致 kubelet 终止和重启；未知 500 内部代码细节不否定此机制，不能由 Running 推断故障已修复。 |
| 48 | 未通过 | 通过 | [5bb155d65451412d](c10/run-48-5bb155d65451412d/report.md) | 确认存活探针端点失败导致 kubelet 终止和重启；未知 500 内部代码细节不否定此机制，不能由 Running 推断故障已修复。 |
| 49 | 未通过 | 通过 | [b8d54dfdf07044d7](c10/run-49-b8d54dfdf07044d7/report.md) | 确认存活探针端点失败导致 kubelet 终止和重启；未知 500 内部代码细节不否定此机制，不能由 Running 推断故障已修复。 |
| 50 | 未通过 | 不通过 | [e8de5026b4104eee](c10/run-50-e8de5026b4104eee/report.md) | 明确把存活探针失败导致的终止误归为 OOM/内存不足，或未收敛到存活探针机制。 |

### c11

finalizer 主机制与退出诱因需分离。部分未通过报告只是缺少控制器细节；另一些确实未确认 finalizer。大量已通过报告仍把 137 当 OOM、把容器退出当 Pod 自动删除触发，属于需要单独披露的解释缺陷。

| # | 原脚本 | 人工意见 | 原始报告 | 理由 |
|---:|---|---|---|---|
| 1 | 通过 | 通过 | [8226ca53b56d402a](c11/run-01-8226ca53b56d402a/report.md) | 明确识别 aiops.lab/hold/finalizer 阻塞对象删除；具体控制器故障未证实，137 不等于 OOM，容器退出也不会自动触发 Pod 删除。 |
| 2 | 通过 | 通过 | [f0f030e4711848a3](c11/run-02-f0f030e4711848a3/report.md) | 明确识别 aiops.lab/hold/finalizer 阻塞对象删除；具体控制器故障未证实，137 不等于 OOM，容器退出也不会自动触发 Pod 删除。 |
| 3 | 通过 | 通过 | [c8e7d4aa715e4c38](c11/run-03-c8e7d4aa715e4c38/report.md) | 明确识别 aiops.lab/hold/finalizer 阻塞对象删除；具体控制器故障未证实，137 不等于 OOM，容器退出也不会自动触发 Pod 删除。 |
| 4 | 通过 | 通过 | [6139a4c7a28c4089](c11/run-04-6139a4c7a28c4089/report.md) | 明确识别 aiops.lab/hold/finalizer 阻塞对象删除；具体控制器故障未证实，137 不等于 OOM，容器退出也不会自动触发 Pod 删除。 |
| 5 | 通过 | 通过 | [4e6f130c786d4639](c11/run-05-4e6f130c786d4639/report.md) | 明确识别 aiops.lab/hold/finalizer 阻塞对象删除；具体控制器故障未证实，137 不等于 OOM，容器退出也不会自动触发 Pod 删除。 |
| 6 | 通过 | 通过 | [2ef709233be84fad](c11/run-06-2ef709233be84fad/report.md) | 明确识别 aiops.lab/hold/finalizer 阻塞对象删除；具体控制器故障未证实，137 不等于 OOM，容器退出也不会自动触发 Pod 删除。 |
| 7 | 通过 | 通过 | [1ed00925a11c4acc](c11/run-07-1ed00925a11c4acc/report.md) | 明确识别 aiops.lab/hold/finalizer 阻塞对象删除；具体控制器故障未证实，137 不等于 OOM，容器退出也不会自动触发 Pod 删除。 |
| 8 | 通过 | 通过 | [032b3a58abc54adb](c11/run-08-032b3a58abc54adb/report.md) | 明确识别 aiops.lab/hold/finalizer 阻塞对象删除；具体控制器故障未证实，137 不等于 OOM，容器退出也不会自动触发 Pod 删除。 |
| 9 | 通过 | 通过 | [3a6411defaa349a6](c11/run-09-3a6411defaa349a6/report.md) | 明确识别 aiops.lab/hold/finalizer 阻塞对象删除；具体控制器故障未证实，137 不等于 OOM，容器退出也不会自动触发 Pod 删除。 |
| 10 | 通过 | 待复核 | [64c9abd2d67d4007](c11/run-10-64c9abd2d67d4007/report.md) | 将 OOM 写成已确认根因，finalizer 仅作为正式 RCA 的推测/补充；根因重心与证据资格存在矛盾。 |
| 11 | 通过 | 通过 | [a028a4c5f926482e](c11/run-11-a028a4c5f926482e/report.md) | 明确识别 aiops.lab/hold/finalizer 阻塞对象删除；具体控制器故障未证实，137 不等于 OOM，容器退出也不会自动触发 Pod 删除。 |
| 12 | 通过 | 通过 | [3b140ada760b4d40](c11/run-12-3b140ada760b4d40/report.md) | 明确识别 aiops.lab/hold/finalizer 阻塞对象删除；具体控制器故障未证实，137 不等于 OOM，容器退出也不会自动触发 Pod 删除。 |
| 13 | 通过 | 通过 | [033f20f72a0a4e64](c11/run-13-033f20f72a0a4e64/report.md) | 明确识别 aiops.lab/hold/finalizer 阻塞对象删除；具体控制器故障未证实，137 不等于 OOM，容器退出也不会自动触发 Pod 删除。 |
| 14 | 通过 | 通过 | [c0e13a87dd7246c8](c11/run-14-c0e13a87dd7246c8/report.md) | 明确识别 aiops.lab/hold/finalizer 阻塞对象删除；具体控制器故障未证实，137 不等于 OOM，容器退出也不会自动触发 Pod 删除。 |
| 15 | 通过 | 通过 | [9a76d007d3ce4454](c11/run-15-9a76d007d3ce4454/report.md) | 明确识别 aiops.lab/hold/finalizer 阻塞对象删除；具体控制器故障未证实，137 不等于 OOM，容器退出也不会自动触发 Pod 删除。 |
| 16 | 通过 | 通过 | [875942fd80c74db1](c11/run-16-875942fd80c74db1/report.md) | 明确识别 aiops.lab/hold/finalizer 阻塞对象删除；具体控制器故障未证实，137 不等于 OOM，容器退出也不会自动触发 Pod 删除。 |
| 17 | 通过 | 通过 | [1ff4bc1b9f564afd](c11/run-17-1ff4bc1b9f564afd/report.md) | 明确识别 aiops.lab/hold/finalizer 阻塞对象删除；具体控制器故障未证实，137 不等于 OOM，容器退出也不会自动触发 Pod 删除。 |
| 18 | 未通过 | 不通过 | [6fbeacb612664e77](c11/run-18-6fbeacb612664e77/report.md) | 错误确认内存不足/OOM；未确认 finalizer 是删除阻塞点，不能以出现候选词算通过。 |
| 19 | 通过 | 通过 | [a225d66b7bf74b5d](c11/run-19-a225d66b7bf74b5d/report.md) | 明确识别 aiops.lab/hold/finalizer 阻塞对象删除；具体控制器故障未证实，137 不等于 OOM，容器退出也不会自动触发 Pod 删除。 |
| 20 | 通过 | 通过 | [ccb4fd56a3a74a37](c11/run-20-ccb4fd56a3a74a37/report.md) | 明确识别 aiops.lab/hold/finalizer 阻塞对象删除；具体控制器故障未证实，137 不等于 OOM，容器退出也不会自动触发 Pod 删除。 |
| 21 | 未通过 | 不通过 | [8826d7177e4e4b6a](c11/run-21-8826d7177e4e4b6a/report.md) | 明确表示无法确认 finalizer 存在或具体删除阻塞机制，仅确认 Terminating 现象，诊断未完成。 |
| 22 | 未通过 | 不通过 | [35945d3aa8074dae](c11/run-22-35945d3aa8074dae/report.md) | 明确表示无法确认 finalizer 存在或具体删除阻塞机制，仅确认 Terminating 现象，诊断未完成。 |
| 23 | 通过 | 通过 | [22fac193bc2049b4](c11/run-23-22fac193bc2049b4/report.md) | 明确识别 aiops.lab/hold/finalizer 阻塞对象删除；具体控制器故障未证实，137 不等于 OOM，容器退出也不会自动触发 Pod 删除。 |
| 24 | 未通过 | 不通过 | [5926575d0a064134](c11/run-24-5926575d0a064134/report.md) | 错误确认内存不足/OOM；未确认 finalizer 是删除阻塞点，不能以出现候选词算通过。 |
| 25 | 通过 | 待复核 | [a5849edc7a9448ba](c11/run-25-a5849edc7a9448ba/report.md) | 开头确认 finalizer，末尾却将最终根因改为未知外部资源不可达；主机制和最终断言不一致。 |
| 26 | 未通过 | 通过 | [d2c86a21442a4bbd](c11/run-26-d2c86a21442a4bbd/report.md) | 删除被 aiops.lab/hold 阻塞的机制明确；控制器详情未知、OOM 排除/假设或终态拦截器同义表述不应导致漏判。 |
| 27 | 通过 | 通过 | [a7113265c1d14e7d](c11/run-27-a7113265c1d14e7d/report.md) | 明确识别 aiops.lab/hold/finalizer 阻塞对象删除；具体控制器故障未证实，137 不等于 OOM，容器退出也不会自动触发 Pod 删除。 |
| 28 | 通过 | 待复核 | [857106c9948d4549](c11/run-28-857106c9948d4549/report.md) | 将 OOM 写成已确认根因，finalizer 仅作为正式 RCA 的推测/补充；根因重心与证据资格存在矛盾。 |
| 29 | 通过 | 通过 | [f4ed46c6cd14499a](c11/run-29-f4ed46c6cd14499a/report.md) | 明确识别 aiops.lab/hold/finalizer 阻塞对象删除；具体控制器故障未证实，137 不等于 OOM，容器退出也不会自动触发 Pod 删除。 |
| 30 | 通过 | 通过 | [25613e057e394b3d](c11/run-30-25613e057e394b3d/report.md) | 明确识别 aiops.lab/hold/finalizer 阻塞对象删除；具体控制器故障未证实，137 不等于 OOM，容器退出也不会自动触发 Pod 删除。 |
| 31 | 未通过 | 通过 | [f6e91587793348d7](c11/run-31-f6e91587793348d7/report.md) | 删除被 aiops.lab/hold 阻塞的机制明确；控制器详情未知、OOM 排除/假设或终态拦截器同义表述不应导致漏判。 |
| 32 | 未通过 | 通过 | [05640c2cce7149b1](c11/run-32-05640c2cce7149b1/report.md) | 删除被 aiops.lab/hold 阻塞的机制明确；控制器详情未知、OOM 排除/假设或终态拦截器同义表述不应导致漏判。 |
| 33 | 通过 | 通过 | [a6a2df3bfc2d4f79](c11/run-33-a6a2df3bfc2d4f79/report.md) | 明确识别 aiops.lab/hold/finalizer 阻塞对象删除；具体控制器故障未证实，137 不等于 OOM，容器退出也不会自动触发 Pod 删除。 |
| 34 | 通过 | 通过 | [0e8b3511db7f4c34](c11/run-34-0e8b3511db7f4c34/report.md) | 明确识别 aiops.lab/hold/finalizer 阻塞对象删除；具体控制器故障未证实，137 不等于 OOM，容器退出也不会自动触发 Pod 删除。 |
| 35 | 通过 | 通过 | [bb1fc384ddc74313](c11/run-35-bb1fc384ddc74313/report.md) | 明确识别 aiops.lab/hold/finalizer 阻塞对象删除；具体控制器故障未证实，137 不等于 OOM，容器退出也不会自动触发 Pod 删除。 |
| 36 | 通过 | 通过 | [3b973cd4f92b467c](c11/run-36-3b973cd4f92b467c/report.md) | 明确识别 aiops.lab/hold/finalizer 阻塞对象删除；具体控制器故障未证实，137 不等于 OOM，容器退出也不会自动触发 Pod 删除。 |
| 37 | 未通过 | 不通过 | [0a60b3b479534668](c11/run-37-0a60b3b479534668/report.md) | 明确表示无法确认 finalizer 存在或具体删除阻塞机制，仅确认 Terminating 现象，诊断未完成。 |
| 38 | 通过 | 通过 | [4965b8e60dbc4717](c11/run-38-4965b8e60dbc4717/report.md) | 明确识别 aiops.lab/hold/finalizer 阻塞对象删除；具体控制器故障未证实，137 不等于 OOM，容器退出也不会自动触发 Pod 删除。 |
| 39 | 通过 | 通过 | [d43ddccd17a24794](c11/run-39-d43ddccd17a24794/report.md) | 明确识别 aiops.lab/hold/finalizer 阻塞对象删除；具体控制器故障未证实，137 不等于 OOM，容器退出也不会自动触发 Pod 删除。 |
| 40 | 通过 | 通过 | [4facb85fa88749aa](c11/run-40-4facb85fa88749aa/report.md) | 明确识别 aiops.lab/hold/finalizer 阻塞对象删除；具体控制器故障未证实，137 不等于 OOM，容器退出也不会自动触发 Pod 删除。 |
| 41 | 通过 | 通过 | [2afc6469d5ea42cb](c11/run-41-2afc6469d5ea42cb/report.md) | 明确识别 aiops.lab/hold/finalizer 阻塞对象删除；具体控制器故障未证实，137 不等于 OOM，容器退出也不会自动触发 Pod 删除。 |
| 42 | 通过 | 通过 | [b3d2f05243254568](c11/run-42-b3d2f05243254568/report.md) | 明确识别 aiops.lab/hold/finalizer 阻塞对象删除；具体控制器故障未证实，137 不等于 OOM，容器退出也不会自动触发 Pod 删除。 |
| 43 | 通过 | 通过 | [e57722a84f3d4ab7](c11/run-43-e57722a84f3d4ab7/report.md) | 明确识别 aiops.lab/hold/finalizer 阻塞对象删除；具体控制器故障未证实，137 不等于 OOM，容器退出也不会自动触发 Pod 删除。 |
| 44 | 通过 | 通过 | [1be6898679034ab0](c11/run-44-1be6898679034ab0/report.md) | 明确识别 aiops.lab/hold/finalizer 阻塞对象删除；具体控制器故障未证实，137 不等于 OOM，容器退出也不会自动触发 Pod 删除。 |
| 45 | 通过 | 通过 | [e854807fe2ea428b](c11/run-45-e854807fe2ea428b/report.md) | 明确识别 aiops.lab/hold/finalizer 阻塞对象删除；具体控制器故障未证实，137 不等于 OOM，容器退出也不会自动触发 Pod 删除。 |
| 46 | 通过 | 通过 | [dfb2262b1d2848a1](c11/run-46-dfb2262b1d2848a1/report.md) | 明确识别 aiops.lab/hold/finalizer 阻塞对象删除；具体控制器故障未证实，137 不等于 OOM，容器退出也不会自动触发 Pod 删除。 |
| 47 | 通过 | 通过 | [a1a0f7b254ef47af](c11/run-47-a1a0f7b254ef47af/report.md) | 明确识别 aiops.lab/hold/finalizer 阻塞对象删除；具体控制器故障未证实，137 不等于 OOM，容器退出也不会自动触发 Pod 删除。 |
| 48 | 未通过 | 不通过 | [4ae9971eb52a40e3](c11/run-48-4ae9971eb52a40e3/report.md) | 错误确认内存不足/OOM；未确认 finalizer 是删除阻塞点，不能以出现候选词算通过。 |
| 49 | 未通过 | 通过 | [4d2e7f30423d43aa](c11/run-49-4d2e7f30423d43aa/report.md) | 删除被 aiops.lab/hold 阻塞的机制明确；控制器详情未知、OOM 排除/假设或终态拦截器同义表述不应导致漏判。 |
| 50 | 通过 | 通过 | [f8f2f34627444088](c11/run-50-f8f2f34627444088/report.md) | 明确识别 aiops.lab/hold/finalizer 阻塞对象删除；具体控制器故障未证实，137 不等于 OOM，容器退出也不会自动触发 Pod 删除。 |

## 可审计文件

- 完成验证：550 条审查记录的报告哈希及原始通过状态一致；11 个 Case README 各有50条原报告链接且全部可访问；生成前后1,103个原始 report/score/stats/summary/overview 文件哈希均未改变。测试报告层相关单元测试所在目录共106项通过。
- [manual_review.json](manual_review.json)：550份人工裁决与报告哈希。
- [metrics_review.json](metrics_review.json)：四指标独立复算、实际手册调用、计划计数比对和矛盾候选。
- [stats.json](stats.json)、[summary.md](summary.md)、[overview.txt](overview.txt)：未改写的原始成绩。
