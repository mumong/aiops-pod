# AIOps Agent 开发交接：核心能力、设计预期与当前问题

> 编写日期：2026-10-14。面向接手开发的 AI / 工程师。
> 本文基于当前源码、线上部署、运行归档及已有验证记录整理；不是新的实现方案，也不代表所有功能已通过当前模型的端到端验收。
> 运行中的请求会继续变化，本文记录的是本次审查时的状态。历史测试、当前实测、推测原因分别标明。
> 本文不包含 API Key、Secret 值、Cookie 或其他凭证。接手时使用现有环境配置，不要输出或重新生成凭证。

## 1. 产品目标与不可偏离的原则

这是 Kubernetes 可观测性与智能运维 Agent：先识别目标范围内的 Pod 异常，再自主取证、分析根因，输出有真实依据的报告；用户选择生成修复方案后，由修复 Agent 规划并通过现有审批 / 自动执行流程修复。

用户最在意的不是流程节点齐全，而是以下结果：

1. 四个异常就交付四个调查结果，不因文本提取、压缩或汇总漏掉其中一个。
2. 报告有结论、现象、真实工具证据和原因分析，不只是一句摘要。
3. 修复方案清楚展示对象、原因、操作和命令；用户反馈能实际改变指定方案。
4. 单异常和多异常使用相容的核心契约；未来扩展到 10 / 100 个对象，不把所有分支上下文一次塞给总结模型。
5. 模型 / API 断流或交付失败必须明确反映，不能将残缺分析包装成成功。

设计约束：

- **Agent 做判断，代码做确定性工程。** 异常选择、证据选择、根因与修复操作由模型决定；代码负责身份、分组投递、契约校验、预算、归档、审批、版本及命令运输。
- 不新增按 case 编号、错误名、命名空间或具体 finalizer 写死的修复脚本、隐藏兜底或强制工具调用序列。
- JSON 与普通分析文本并存。JSON 只保护下游必需的高价值信息；不把全部工具输出都变成不可压缩内容。
- 诊断报告不负责生成执行方案，**修复节点全权规划**。报告和证据负责提供依据。
- 用户反馈是高价值决策输入，但不是现场事实，也不是执行审批。不能把“修改方案”自动解释为“批准执行”。
- 不为了让演示看起来成功而伪造证据、删掉失败组、隐藏断流或忽略未知条件。
- 修改架构、路由、权限、安全策略或失败恢复机制前，说明设计及取舍，取得用户确认；不要借排障扩大实现范围。

## 2. 当前环境与版本边界

| 项目 | 本次核实状态 |
|---|---|
| 后端工作区 | `/root/huhu/agent/combine-aiops-mcp/robusta` |
| 前端工作区 | `/root/huhu/agent/combine-aiops-mcp/frountind`，注意实际目录拼写 |
| Kubernetes namespace | `aiops` |
| 后端镜像 | `xnet.registry.io:8443/xnet-cloud/aiops-copilot:12.0.3-router-language` |
| A2A sidecar 镜像 | `xnet.registry.io:8443/xnet-cloud/aiops-a2a-adapter:12.0.1` |
| 前端镜像 | `xnet.registry.io:8443/xnet-cloud/aiops-copilot-frontend:0.1.57` |
| 模型 | `Qwen3.8-27B` |
| OpenAI-compatible API | `http://10.2.0.54:4000/v1`，入口是 LiteLLM |
| 配置的模型窗口 | `MODEL_CONTEXT_WINDOW=54000`；这是本地预算配置，不等于已核实模型真实容量 |
| 当前诊断 / 修复规划并发上限 | 线上 `AIOPS_AUTONOMOUS_PARALLEL_WORKERS=5` |
| 日志 | `INFO` |
| 后端健康接口 | 容器端口 8000，`/health` |
| 前端访问 | `http://10.2.0.48:30081` |
| 运行归档 | `/tmp/aiops/reports/context_archives/<run_id>/`，在后端容器 / PVC 中 |

### 版本与脏工作区的特别提醒

- 之前多轮发布使用“线上旧镜像 + 本轮指定文件覆盖”的 overlay，避免把工作区遗留实验全部上线。
- 后来用户亲自执行 `make delete build push deploy`，完整构建发布 `12.0.1`，这次把当时完整工作区带入生产。不能认为生产仍完全等于早期受控 overlay。
- 当前 `12.0.3-router-language` 基于用户的 `12.0.1`，只覆盖 `app/core/prompts.py`、`app/core/prompt_catalog/runtime_policy.py` 和 `VERSION`。见 `deploy/Dockerfile.router-language`。
- 当前有大量未提交改动。Git 最近 checkpoint 包括 `ff1e2cdb`，但 **HEAD 不代表当前全部源码，也不代表当前线上镜像**。
- 开发前查看 `git status` 和差异，保留用户及其他 AI 的变更；不要 reset、覆盖或自动 commit / push。
- 完整构建和 overlay 构建的差异是维护风险，应单独梳理，不要在本次故障修复中顺手重构整仓库。

## 3. 已实现的核心流程

```text
用户问题 + 当前会话必要历史
    ↓ RequestRouter：生成 RequestContract
    ├─ focused → QueryCollect 自主查询 / 普通操作 → 查询结果
    ├─ full_diagnosis → Layer 定位 + LocationOutput
    │      ├─ 无待查目标，满足健康或不完整结束条件 → Conclusion
    │      ├─ 一个调查组 → Evidence → RCA → Conclusion
    │      └─ 多个调查组 → 各组独立 Evidence → 各组独立 RCA
    │                              ↓
    │                       Conclusion 总览 + 代码拼接分组正文
    ├─ remediation → 修复规划节点
    └─ clarify / stop → 澄清或终止

用户从诊断报告点击“生成修复方案”
    ↓ 保存的诊断记录，继承其分组
    ↓ 每组独立修复规划（并发上限 5）
    ↓ 方案卡片：对象、原因、依据、命令、验证条件
    ├─ 指定卡片反馈 → 仅本组 vN+1；旧版本失效
    └─ 服务端 review / auto 模式 → 命令检查 → 审批 → 执行 → 验证与结果
```

注意：当前 auto 路由中，一个调查组走串行 Evidence/RCA，多组才进入 `parallel_evidence`。配置文件有“任意异常都进入 lane”的历史注释，但不能只按注释理解，当前实际判断在 `pod_detection.after_location()`。

### 3.1 路由：按用户需要的结果，而不是关键词或对象数量

- `focused`：明确取数、状态、清单、数量、日志、知识解释及普通资源操作。
- `full_diagnosis`：主动调查有什么问题、是否健康、异常原因及影响。
- `remediation`：明确要恢复已有故障，或从现有诊断进入修复。
- `clarify / stop`：无法理解、必要指代不明确或不能继续。
- 查询所有节点 CPU / 内存应走 focused；“我的集群 Pod 有什么问题？”应走 full_diagnosis。
- 前端首页“深度诊断”建议目前主要发送问题文本；`/ask` 的 `query_mode=auto` 仍由路由 Agent 判定，UI 标签不等于强制深度模式。
- 路由提示词近期已优化，但仍由模型决策，不能保证任意表达都正确。

### 3.2 深度诊断的产品范围：Pod 异常检测

不是全栈集群健康大巡检，不能因用户泛问集群问题就无限查节点、资源、链路和历史故障。

- Running 不等于健康；还要考虑 Ready、删除状态、容器状态等当前事实。
- **最近 10 分钟有重启或其他异常线索，先调查，再决定是否 healthy。** 已核实恢复且无持续问题时可报告健康，并给依据。
- 累计重启数不等于最近 10 分钟重启数；旧 Error / Unknown 本身不意味着当前仍异常。
- 历史不完整是工具能力限制，不应单独制造异常；但查询失败、分页遗漏、冲突或真实线索未核实不能宣称健康。
- healthy 只表示本次范围的当前 / 可见近期 Pod 未解决异常未发现，不是业务绝对健康保证。
- Agent 自主选择足够的工具，避免为了走满流程重复取证。
- 代码校验健康交付的一致性、真实引用及覆盖，而不是代替 Agent 判断根因。

## 4. 结构化交接与上下文：当前设计的核心

### 4.1 三种东西必须分开

| 类别 | 用途 | 处理方式 |
|---|---|---|
| 少量高价值交接字段 | 下游知道调查谁、为何调查、关键依据、缺口 | 小型 JSON 保护，不随普通文本摘要丢失 |
| 分析文字、原始工具正文、普通历史 | 理解现场和分析过程 | 按正常策略压缩；必要时通过归档回读 |
| 完整原始归档与正式报告 | 审查、修复与用户阅读 | 持久化保存；只给需要的消费者，不全量注入每个模型 |

保护“引用在哪里、属于谁”不等于保证“核心内容一定出现于报告”。因此采证和 RCA 还需选出真正关键的事实内容，而不仅是地址。

### 4.2 按消费者需要投递，不让全量材料一直跟随

| 交接 | 核心结构 | 不应投递什么 |
|---|---|---|
| 定位 → 分组 | `LocationOutput.analysis` 普通文字 + `handoff.targets` 对象身份、问题、状态、少量引用、覆盖与 Pod assessment | 正常 Pod 的全量生命周期、日志全文、所有历史事实 |
| 父定位 → 每个 Evidence | 本组 target、原问题 / 当前任务、范围、来源引用、共享 Runbook 入口 | 其他组上下文、父节点全部工具历史、所有正常对象 |
| Evidence → RCA | `EvidenceStageOutput.analysis` + 至多 8 条 `key_facts`、6 条 `unresolved`、6 条 Runbook 引用 | 兄弟组结果、所有历史版本、所有工具全文的保护副本 |
| RCA → Conclusion | `case_index`：身份、状态、短摘要、置信描述、成果引用 | 正式报告全文、工具历史、所有事实详情 |
| RCA → 修复 | 仅当前组正式 report、cause、key_facts、unresolved、Runbook 与 evidence_index_ref | 其他组正文、从总览重新提取异常、全文聚合上下文 |

定位最小结构示意（字段值是示例，不是现场证据）：

```json
{
  "analysis": "本次定位文字；可以按普通策略压缩。",
  "handoff": {
    "contract_version": "location-handoff.v1",
    "targets": [
      {
        "target_id": "target-1",
        "entity": {"kind": "Pod", "namespace": "demo", "name": "app-abc", "uid": "observed-uid"},
        "issue": "Running 但未就绪，具体原因待查",
        "status": "investigate",
        "status_reason": "",
        "evidence_refs": ["原样复制实际工具提供的来源引用"]
      }
    ],
    "coverage": "complete",
    "coverage_note": "本次范围及分页覆盖说明"
  }
}
```

`pod_assessment` 是可选字段；健康提前结束需要满足其约定。完整 schema 以 `diagnosis_contract.py`、`pod_detection.py` 为准，勿从示例重新发明契约。

### 4.3 RCA 负责丰富报告，Conclusion 只做小总览

RCA 发布 `DiagnosisCaseOutput`，包括 outcome、summary、cause、certainty、关键事实、未知项、Runbook 引用和完整 Markdown report。

完整 report 应有：诊断结论、异常现象、真实证据表（结果 / 时间 / 来源 / 诊断作用）、原因分析、待核实与采集边界。没有某类数据就说明没采集，不补造。

代码绑定 group / target 身份，保存 `cases/result.json` 和本组 `cases/evidence-index.json`。总览模型只接收小型索引；预算不足时分批汇总索引；代码原样拼接每组正式报告，避免压缩或总览重写毁掉正文。

100 组目前验证了构造数据的输入预算、拼接、前端分页及历史恢复；**没有通过 100 个真实异常的全链路负载测试**。定位输出大小、模型服务并发 / 限流、归档和浏览器存储仍需验证。

### 4.4 普通压缩的机制与边界

- WorkingContextMiddleware 管理模型工作的历史替换；保留用户目标、核心交接、摘要、近期完整工具交互和来源入口。
- 近期工具调用与对应返回按原子组保留，不能只保留调用而丢掉返回。近期后缀预算现有实现不超过 8,000 tokens，并受窗口比例限制。
- 更早的分析及工具材料进入 LLM 摘要；原始结果仍归档，`read_context_archive` 可以按入口回读。
- 模型请求还包含 system prompt、语言约束、工具 schema、结构化结果 schema、当前消息历史，以及输出 / 安全预算；“业务 JSON 小”不等于整个请求就小。
- 单轮工具结果、近期完整后缀或摘要自身仍可能过大；保护 JSON 必须按阶段有界，不能重新从原始生命周期中恢复全量保护区。
- `identity.v1` / `stage.v1` 新路径避免自动保护所有正常 Pod 生命周期；旧契约和遗留兼容实现仍在仓库，需按实际调用路径核实。

## 5. 通用修复能力与交互约定

### 5.1 核心能力

- 修复规划继承诊断分组，不再从一大段总览文本重新发现故障。
- 每个组只读取自己的诊断成果，必要时自主读取归档证据、核实最新对象或 Runbook。
- 结构化计划应能展示目标实体、根因 / 判断依据、拟变更和执行命令、风险、缺少的信息及验证条件。
- 多组规划并发，**命令调用串行**。当前串行和忙碌对象保护主要是进程内锁，不应声称已经解决多副本跨进程执行互斥。
- 服务端配置 `review` / `auto`。用户进入修复流程后就生成方案，不先要求批准“开始规划”；批准发生在具体执行前。
- 对象身份和版本必须明确。旧 UID、过时诊断不能不加核实地用于新对象。
- 自动恢复成功不是“命令返回 0”，还要看验证条件、异常是否恢复、是否超时 / 仍待观察。

当前仓库存在旧 `RemediationPlan` 和新的 Pod 修复 / 工作区路径。旧文件中“由 conclusion 生成计划”等描述是历史遗留，当前产品预期不是让 Conclusion 生成修复命令。接手时先追实际执行路径，不要把兼容代码误当主设计。

### 5.2 人工反馈必须绑定到计划，不污染其他组

- 卡片选择具体 group，反馈绑定 `job_id + version`。
- 提交通过 `/repair/jobs/{job_id}/feedback`，不把反馈当全新普通 `/ask` 问题重新路由到 query / diagnosis。
- 反馈内容作为本组重新规划的 question，连同 previous_plan 和本组诊断传入；不需要重复复制多份。
- 新版 vN+1 替代旧版 vN；过时审批不能执行旧计划；已执行的动作不会自动回滚。
- 前端分别展示“用户修改意见”和“AI 修复方案”，不混成一段交互文字；规划说明 / 任务详情置于方案前，命令重点突出。
- 肯定答复若明确指向旧方案唯一候选动作，模型应理解为选择该动作，不能不断要求重复确认。
- 明确选择动作不等于把未知清理事实变成已证实，也不绕过执行审批和命令策略。

### 5.3 安全策略：期望与实际要分开

用户当前希望最小 demo：先生成可审阅方案，执行时重点拦截 `rm`；未知风险不要自动变成“永不生成命令”。完整安全设计属于 Sprint 3，不应在 Sprint 2 中不断扩大。

已有配置：`executor=pod`、`mode=review`、`denied_executables=[rm]`、`allowed_exec_commands=[]`。

但“只有 rm 被禁”不等于系统允许任意主机 shell：当前还存在通用运输约束，例如单条 kubectl argv、不允许切换集群 / 身份、不接受直接 shell 管道组合；容器内命令另有可解析性检查。保持这些边界与用户预期透明，不新增未确认的语义安全闸门，也不要直接删除既有约束。

未知信息时是否能生成待审阅命令仍由模型决定；程序不能按 finalizer / 探针 / CrashLoop 类型强制生成命令。反馈未生效时先检查真实输入及提示词，不写 case 特判。

### 5.4 后台任务和 A2A

- 修复工作区不是仅存在于浏览器：任务 / 方案有持久化记录，关闭页面不停止修复后台任务。
- 活跃任务不会在服务重启后盲目重放；记录保留不代表正在执行的线程可跨重启恢复。
- 修复 HTTP API 当前使用 owner Cookie 绑定访问；核心服务逻辑与 UI 解耦，但不应声称完整机器到机器鉴权 / 100 组调度已经完成。
- 已有 A2A sidecar 和 federation 组件；本轮诊断 / 修复边界审查没有证明跨 Agent 修复授权、身份和任务恢复已端到端验收。
- 普通诊断 SSE 客户端断开会触发取消；修复后台任务独立于页面连接。两类任务的生命周期不要混淆。

## 6. 当前核心演示场景及 Sprint 验收

这些是验证 Agent 通用能力的案例，不应变成代码分支。

| 实际演示对象 | 现象与已使用的证据方向 | 期望修复及验收 |
|---|---|---|
| case-04 | 当前是 CreateContainerConfigError；缺失 Secret 键 / 引用配置不一致 | 依据可信配置修正引用，容器创建并就绪 |
| case-06 | CrashLoopBackOff；启动逻辑要求 `APP_CONFIG_PATH`，Deployment 使用 `APP_CONF_PATH`；已有值需核实 | 修改变量名并保留正确路径，新 Pod 正常加载配置、Ready、健康请求成功且观察期无新增重启 |
| case-09 | Ready 0/1；Readiness 8081 与应用监听 8080 不一致 | 修正工作负载探针，新 Pod Ready，Endpoint / 请求按实际验证条件恢复 |
| case-11 | Terminating；测试 finalizer `aiops.lab/hold` 阻塞删除 | 依据当前对象与用户操作选择规划定点移除，说明未知清理风险；执行批准后验证目标 Pod 消失 |

ImagePullBackOff 是用户早期计划覆盖的场景；不能把当前 case-04 的配置错误说成镜像拉取失败。Sprint 文本曾写 CrashLoop 的“启动脚本路径错误”，后来明确案例为环境变量名称错误，交接时需区分。

| Sprint | 用户认可的目标 | 可直观验收 |
|---|---|---|
| 1 | 自动修复设计；梳理三个核心异常 case 与恢复预期 | 设计及案例可审查，不重复占后续实现任务 |
| 2 | 报告进入修复；展示对象、原因、命令；对话调整方案 | 单 / 多组生成方案；指定组反馈产生可见变更；命令展示清楚 |
| 3 | 高危命令限制；人工审批 / 自动执行开关 | rm 拦截；审批前无写操作；批准正确版本才执行；模式有效 |
| 4 | 执行结果展示、验证与超时反馈 | Terminating、Ready 0/1、CrashLoop 三类恢复验证，不把命令成功等同恢复 |

当前优先修复基础稳定性与最小 demo，不要求一次做完所有高级安全、回滚、多副本调度和跨 Agent 能力。

## 7. 已确认的问题、原因链与仍需取证的部分

### 7.1 P0：换 Qwen 后模型流长期不完成

运行 `bcf5b631830844fd`，问题“查询我各个节点的 cpu 和内存使用率”：

- 北京时间 16:54:07 开始，正确路由 focused。
- 16:54:17～16:54:47，5 个工具均成功；CPU、内存、节点列表及指标标签已返回。
- 随后等待下一轮模型交付，长时间没有模型完成记录，没有最终有效查询结果。
- 17:07:17 客户端断开，后台线程 5 秒内没有结束。
- 后续日志更新：17:13:52 后台终于检查到取消，调用共耗时约 1,179 秒。**这是取消结束，不是正常完成查询。**
- 最后已完成模型轮次输入 12,623 tokens / 54,000，约 23%；本地保护检查未触发。不是已证实的上下文爆满。
- 同样问题另一次 `016ccf8b2b874473` 约 58.8 秒完成，说明是间歇性，不是查询必然不可执行。

放大问题的已确认机制：

1. `ChatOpenAI` 未显式设置单请求 timeout；当前 SDK 默认 read timeout 为 600 秒。这通常是读等待限制，不是完整 Agent 总时限，持续有片段到达可继续等待。
2. Agent 总时限是 `max_steps * 30`；查询 48 步为 24 分钟，定位 32 步为 16 分钟。
3. 取消只在 async stream 产生下一条 chunk / update 时检查；静默等待期间不能立即响应取消。
4. SSE 有定时 heartbeat，但心跳仅说明后端还在等待，不是模型语义进度。
5. Agent 主模型未明确绑定输出 token 上限；预算中的 output_reserved 不是实际 API `max_tokens`。这是待评估风险，尚不能证明它就是本次停滞原因。
6. 线程池 `with ThreadPoolExecutor` 退出会等线程结束，外层 `.result(timeout=...)` 不保证立刻回到用户；查询路径虽还有内部 `asyncio.wait_for`，仍需测试真实取消和清理。

尚未确认：Qwen 生成过久、LiteLLM 上游 / SSE 未正常结束、结构化工具调用流停滞等哪一个是底层触发源。本次访问 LiteLLM spend 日志返回 403；后端未配置 Langfuse SDK 追踪，不能补造网关结论。

### 7.2 P0：定位交付失败被转为空清单，进而降级串行

当前因果链：

```text
定位模型没有交付有效 LocationOutput
    ↓ 超时 / 输出仍为分析文字
LocationOutput.model_validate_json 失败
    ↓ 现有异常处理
diagnosis_handoff.targets = []，coverage = partial
    ↓ plan_groups
autonomous_groups = []
    ↓ after_location：组数不超过 1，且没有满足提前结束的 assessment
走 Evidence → RCA 串行路径
```

这是 **“交付失败”与“确实没有 / 只有一个调查目标”混用空数组** 的流程问题，不是 Agent 判断现场只有一个异常。

对照实际运行：

| 运行 | 模型 / 结果 |
|---|---|
| `b825b44b7f1a4b74` | GPT-6 Luna，定位交付四个 target，产生 g1～g4，实际进入并发 |
| `b1fa8b99ab734a71` | Qwen，定位交接无效，targets / groups 为空；已进入串行采证。具体无效输出原因需补查归档 / 历史日志 |
| `10709ace672f4722` | Qwen，自建只读验证；定位 960 秒超时，残留 `<think>` 分析文字而不是 JSON，校验失败，空分组后继续串行。测试浏览器此前已取消，仍出现后续节点，暴露取消传播边界 |
| `bf076fb4e79840f1` | Qwen，正确进入深度诊断；工具已查到 case-04 / 06 / 09 / 11；截至本次核查仍没有 layer.output / 分组计划，最后工具返回 17:09:31，停在定位交付之前 |

本次 bf 不能说是并发被禁用，也不能说模型只识别出三 / 一个异常。当前线上并发上限仍为 5。其最后已完成轮次输入 22,039 tokens；下一轮本地估算输入 32,387、含保留预算约 75%，保护检查未触发。

当前结构化交付经 LangChain `ToolStrategy`，模型需要发出 LocationOutput 等结构化工具结果，而不是只在分析流里写想法。接手者应核实 Qwen + LiteLLM 的工具调用 / 结束协议，不仅检查普通聊天是否能回答。

建议讨论的方向（**未实施，需与用户确认**）：区分交付失败与合法空清单；交付失败明确终止 / 报不完整，或设计有界协议恢复。不能在未讨论的情况下用第二个模型从残缺文字再提目标，也不能按已知 case 强行造四组。

### 7.3 路由误判：已优化，有限验证通过

- `7498458d17c54260`：“我的集群 Pod 有什么问题？”被旧提示词下的 Qwen 解释为查异常清单，路由 focused，只跑 query_collect。
- 已改为按用户期望结果区分：主动查问题 / 健康属于诊断，明确列清单属于查询；范围大不等于深度高。
- 真实 Qwen 分类对照 22 个样本：旧路由 20/22，新路由 22/22；连同 scope 旧 19/22、新 22/22。
- 新版 bf 和 10709 的路由都是 full_diagnosis。**它们不并发的原因不再是路由误判，而是定位交付没有完成 / 无效。**
- 样本全部通过不保证任意中文表达或长历史指代均正确。

### 7.4 中文可见进展与原生 reasoning 不一致

- 主 Agent 提示词大部分中文，工具 description / schema 很多英文。
- `VISIBLE_OUTPUT_LANGUAGE_POLICY` 已明确简体中文进展、计划、解释字段、可见 thinking 摘要；保留命令、日志及名称原文。
- 实测 `618b0cc626bb4f75`：53 个流式文本事件，21 秒完成，最终回答中文；原生 reasoning 仍主要英文（该样本 8 个汉字、719 个拉丁字母）。
- **不能宣称“强化提示词后原生推理流中文已解决”。** 没有偷偷关闭 thinking、隐藏英文或额外翻译来伪装通过。
- UI 应展示可公开的进展 / 简短推理摘要与工具细节，不要求输出详细私有思维链；若需翻译或改模型 thinking 参数，先讨论用户体验、时延和语义边界。

### 7.5 历史问题：全量保护与汇总爆上下文

旧运行 `ab2540b7792e4c66` 压缩后仍很大（字符，不是 tokens）：定位 JSON 约 5,225；72 个 Pod 生命周期约 51,099；四组交接约 38,741；公共引用约 2,908；近期工具原文约 22,894；真正摘要仅约 2,442。

原因：保护区不仅是异常身份，还重复带上正常 Pod、全生命周期、各组事实及材料；大量内容根本不进入普通压缩。最后又把多个分支全集合给 Conclusion，摘要再短也救不了固定保护部分。

目前已改为第 4 节的分阶段投影、独立成果归档和小索引总览。历史四组真实输入：总览约 2,254～2,263 字符，各组 RCA 正文原样拼接；相应验证在旧模型 / 旧发布下通过。不能因此断言完整工作区构建后或 Qwen 下永不溢出，也不能为了彻底避免溢出改成只有一句报告。

### 7.6 历史问题：漏一个异常与分组大小写

- 早期文字定位草稿被分组 Agent 重新提取，四对象变三任务且未说明；改为保护对象清单，分组不再从长文本再发现对象。
- 曾有模型输出 `kind=pod`，代码仅接受 `Pod`，导致多目标被转串行；已在契约入口规范 Pod 大小写，不影响其他 kind，不是故障特判。
- 新路径仍依赖模型交付完整 targets；结构化不保证模型永不漏选。要验“定位选出的目标全部交接 / 有明确处置”，不要把工具全量记录当固定异常规则。

### 7.7 历史问题：工具结果过大 / 查询分页

- 生命周期工具曾返回 `result_too_large`，不是 Kubernetes 查询失败，而是证据视图超字节预算拒绝结果；保留 `conditions`、`state` 等详情会显著增加体积。
- 现在工具 schema 声明大结果可分页，需沿相同 scope / fields / filters 使用 continuation；每页覆盖不能当全局覆盖。
- `restart_count_in_window=null` 不等于 0，累计重启不能直接当窗口重启；Pod 行与容器行不是同一计数单位。
- 换 Qwen 后存在先分组统计历史终止原因、重复查分页等效率问题；不能简单删 uid 或固定强制所有查询，否则身份与近期异常判断受损。
- `list_prometheus_rules` 已在实际 MCP 加载中禁用；某些旧 READ_TOOLS 名单仍有名字，不代表线上工具可用。避免重新引入先前已撤销的专用摘要 / UI 分支。

### 7.8 人工反馈后仍不生成命令

- 曾发生用户明确选择移除 finalizer，模型仍反复索取清理确认、返回 actions=[]。
- 已优化通用提示词：明确操作选择覆盖旧方案待确认选择；唯一候选动作的肯定答复不能解释为“同意继续等待”。保留真实参数、对象变化、审批与风险边界。
- 历史 g4 冻结证据的真实模型回放最终 2/2 生成待审阅动作；g1 回放也生成命令。均未执行。
- 实时重查时 UID 与旧记录不同，仍返回空动作；不能把旧确认自动授权新对象，也不能宣称提示词已稳定解决任意反馈。
- Qwen 下规划 / 反馈 / 执行尚需真实验收；不要把旧模型回放或命令存在当恢复成功。

## 8. 测试事实：哪些证据能说明什么

### 已有记录，不是本文重新执行的测试

- 分阶段交接：本地相关回归 1,456；候选部署源码回归 1,166；前端 112；1 / 4 / 10 / 100 组构造测试。
- 丰富报告：本地相关回归 1,466；候选部署源码 1,239；前端 113；真实单组及四组、原始证据抽核、历史恢复通过。
- 修复反馈：真实模型冻结历史回放，执行入口禁止运行；不是当前集群恢复测试。
- 最近路由 / 语言版：相关回归 1,287，通过 22 个真实 Qwen 路由样本；真实快速查询通过，原生中文 reasoning 未通过，完整深度诊断未通过。
- 部分旧 context / evidence-view 实验有既存失败，详见专项文档；**不声称全部仓库测试都通过**。

这些测试数量来自不同时间、不同发布范围，不能相加，也不能替代当前候选源码的复验。

### 接手后的最小真实验收矩阵

| 验证项 | 必须观察的证据 |
|---|---|
| 普通节点资源查询 | focused；工具返回真实数值；最终有效结果；耗时和模型轮次可解释 |
| 正常 Pod 范围 | coverage 完整；不因旧重启过度诊断；合理 healthy / 限制说明 |
| 最近重启但当前 Ready | 先核实近期线索，不能直接忽略；恢复或未恢复有证据 |
| 单异常 | 正确对象，Evidence → RCA，完整报告、成果及目录引用 |
| 四异常 | 定位交付四个 target，四组隔离且实际并发；四份完整报告，无遗漏 |
| 10 / 100 组构造 | 总览不吃所有正文；所有组保留；失败组可见；前端分页 / 复制 / 恢复 |
| Qwen 结构化工具交付 | LocationOutput / EvidenceStageOutput / QueryAnswer 等能完整完成，非只有普通聊天通过 |
| 模型断流 / 停滞 | 明确失败或超时，不继续包装报告；后台任务可收敛，非只有 UI 消失 |
| 定位无效 JSON | 与合法零异常分开；不能空清单暗中转串行 / healthy |
| 指定组修改 | g4 的反馈只改变 g4 新版，其他组版本 / 审批不变 |
| 审批和 rm 拦截 | 批准前无写入，旧版批准无效，rm 被拦截，命令与计划一致 |
| 真实修复恢复 | 在用户允许的测试对象上，核对命令、工具输出、恢复条件和观察期；执行前取得授权 |

健康检查 200、单元测试通过、模型能聊天、只生成了命令，分别都不等于完整链路和恢复验收通过。

## 9. 建议接手顺序与代码导航

建议先做 P0 的真实取证和边界设计，再修路由之外的交付可靠性，最后做 Qwen 下修复验收。不要再次用“路由分类通过”代替完整诊断验证。

| 责任 | 主要入口 |
|---|---|
| 路由与提示词 | `app/core/workflow/nodes/request_router.py`、`app/core/prompts.py`、`app/core/prompt_catalog/` |
| 深度流程与后置分支 | `app/core/workflow/graph.py`、`pod_detection.py` |
| 定位 / 采证 / RCA 交付 | `app/core/workflow/nodes/autonomous_diagnosis.py`、`diagnosis_contract.py`、`case_result.py` |
| 并发与隔离 | `app/core/workflow/nodes/autonomous_parallel.py`、`group_runner.py`、`stage_material.py` |
| 正式报告与轻量总览 | `app/core/workflow/case_report.py`、`nodes/query_answer.py`、`reporter.py` |
| 上下文 / 压缩 / 归档 | `app/core/aicall/working_context.py`、`client.py`、`app/core/workflow/working_material.py`、`app/core/context/` |
| 模型流和取消 | `app/core/aicall/client.py`、`errors.py`、`app/core/workflow/executor.py`、`app/api/routes.py` |
| 修复规划 | `app/core/workflow/nodes/remediation.py`、`app/core/remediation/group_context.py` |
| 修复任务 / 版本 / API | `app/core/remediation/jobs.py`、`records.py`、`app/api/repair_routes.py` |
| 审批与命令执行 | `app/core/remediation/pod_executor.py`、`execution_guard.py`、`policy.py`、`approval.py`；另有历史执行器 |
| 前端 | `frountind/src/components/aiops-chat/`、`src/hooks/useChatHistory.ts` |
| 构建 / 配置 | `Makefile`、`Dockerfile`、`deploy/Dockerfile.*`、`deploy/configmap/config.yaml` |

推荐核查命令（只读，不包含凭证）：

```bash
git status --short
kubectl -n aiops get pods -o wide
kubectl -n aiops get deployment aiops-copilot \
  -o jsonpath='{range .spec.template.spec.containers[*]}{.name}{" "}{.image}{"\n"}{end}'
kubectl -n aiops logs <当前Pod> -c aiops-copilot --since=30m
kubectl -n aiops exec <当前Pod> -c aiops-copilot -- \
  find /tmp/aiops/reports/context_archives/<run_id> -type f
```

取证时优先看 request_router output、最后 node input / output、最后工具时间、budget 的 hard_guard、`parallel/plan.json` 和分支归档。node output 有“直接 output”与 `snapshot` 包装两种历史格式；某些 snapshot 不含全部文本 / events，不能因此宣称模型从未输出。

## 10. 验证脚本、参考文档与发布注意

可用脚本（先看 `--help` 和执行限制，不直接运行写操作）：

- `scripts/eval_router_live.py`：真实路由分类，不执行集群工具。
- `scripts/verify_stage_handoff.py`：检查已有实际归档的分支 / 总览材料。
- `scripts/verify_repair_handoff_live.py`：真实只读规划检查，执行禁止。
- `scripts/verify_feedback_planning_live.py`：冻结历史 / 实时只读规划，执行禁止。
- 前端 `tests/live-stage-handoff.browser.py`、`tests/live-visible-stream.browser.py`、`tests/diagnosis-history.browser.py`。
- 单元测试集合：`tests/unit/workflow`、`tests/unit/remediation`、`tests/unit/api`、`tests/unit/aicall`；先核实当前工作区基线失败。

详细历史记录：

- [分阶段交接验证](history/stage-handoff-validation-20261014.md)
- [丰富诊断报告验证](history/rich-diagnosis-report-validation-20261014.md)
- [人工反馈提示词验证](history/repair-feedback-validation-20261014.md)
- [Pod 检测边界验证](history/pod-detection-validation-20261013.md)
- [路由与中文输出验证](history/router-language-validation-20261014.md)

部署注意：

- `VERSION` 决定常规镜像 tag；`make build` 构建主服务和 A2A，`make deploy` 会更新两者镜像并递归应用本地 deploy 配置。
- `make delete` 删除后端 Deployment / Service / RBAC / Secrets / ConfigMaps，保留 namespace / PVC / PV；非必要不作为日常更新前置动作，会中断服务并覆盖配置来源。
- 完整构建曾约 45 分钟，主要卡在 pip 依赖下载且未命中缓存，不代表 Agent 执行慢；不要混为一类故障。
- 保留现有 Key、PVC 和无关配置；使用唯一版本便于回滚，不用同 tag 反复覆盖来掩盖运行版本。
- 请求代码变更后通常部署到现有 Kubernetes 让用户前端验收；本文是文档交接，不涉及新部署。

## 11. 给接手 AI 的任务摘要

优先解决：**Qwen 下模型流长时间不完成、取消不及时，以及定位结构化交付失败被空清单降级串行。**

请先从 bf / bcf / 10709 的真实记录和 LiteLLM 上游信息定位，提出有界超时、取消和交付状态设计；保留模型的诊断决策权，不按四个固定 case 构造目标，不回退到长文本重新抽取一切。

必须保留：小型阶段 handoff + 可压缩文本 + 可回读原始证据；独立分组 RCA 丰富报告；轻量总览与正文原样拼接；按组修复与版本反馈；人工审批 / 自动执行边界；并发上限 5 和命令串行；紧凑流式进展及工具详情。

交付时分别报告：当前候选源码测试、真实 Qwen 单 / 四异常链路、失败注入、前端显示、修复规划、是否实际执行恢复、部署版本与仍未验证项。不要以旧模型的成功、单元通过或 Ready 状态替代新模型验收。
