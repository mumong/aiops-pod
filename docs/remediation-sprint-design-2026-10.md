# 修复链路三个 Sprint 的设计与验收方案（2026-10-16）

[返回 README](../README.md)。本文是实现前的设计，覆盖 Boss 给出的三个 Sprint 的功能点与测试项；每一条写明"现状、缺口、方案、验收方式"。原则不变：不按故障类型写特判，核心参数是配置，每个能力都能被验收者看见和触发。

## 0. 现状盘点（代码事实）

| 能力 | 现状 | 位置 |
|---|---|---|
| 从诊断报告进入修复 | 已有。报告下"生成自动修复方案"→ `POST /repair/batches` → 按诊断组并行规划 → 方案卡片（对象 / 异常与处理 / 修复命令 / 风险、预演、验证、回退） | `app/core/remediation/jobs.py`、前端 `RepairWorkspace.tsx` |
| 对话调整方案 | 已有。方案下方意见框 → `POST /repair/jobs/{id}/feedback` → 新版本重新规划，旧版本进历史；旧审批作废 | `jobs.revise`、`records.supersede` |
| 人工审批 | 已有。`mode: review` 时每个动作先发审批请求，批准后才执行审批时的命令快照；倒计时到期取消不批准 | `pod_executor.py`、`approval.py`、`POST /remediation/approve` |
| 自动执行 | 已有但只能改 ConfigMap 重启生效：`mode: auto` | `deploy/configmap/config.yaml` |
| 命令安全 | 传输层：只允许单条 kubectl、禁管道/重定向、禁切换集群身份、禁 `config`；`denied_operations/allowed_operations` 可配但默认为空；exec 内层命令黑名单默认只有 `rm` | `policy.py`、`execution_guard.py` |
| 执行结果展示 | 已有：逐动作逐阶段命令与输出；终态 `needs_followup`（"命令已执行，待复查"） | `pod_executor.py`、`RepairWorkspace.tsx` |
| 超时 | 审批超时（600s → `timeout`）、单条命令 60s；没有恢复观察，没有整体执行时限 | 同上 |
| 三个场景环境 | 已有 c06（启动脚本/环境变量错）、c09（Readiness 端口错）、c11（finalizer 阻塞）；`repair_cases.py reset` 可一键重置 | `test/pod-anomaly-cases/` |

结论：Sprint 1 功能基本在，缺的是可演示的验收脚本和"异常原因"的直观展示；Sprint 2 的黑名单默认为空、开关不可在线切换、两者都没有让验收者"看得见"的入口；Sprint 3 的恢复判定与超时反馈缺失。

## 1. Sprint 1：从报告进入修复 + 对话调整

缺口与方案：

- 方案卡片补一行 **异常原因**：来自本组诊断记录（v2 记录的 `diagnosis_result.root_cause/summary`，旧记录的 `analysis` 首段），由后端在 `repair_jobs.batch/detail` 的 `target` 旁给出 `diagnosis_summary`，前端在"修复对象"下方展示。不改模型输出结构。
- 验收脚本 `scripts/acceptance/sprint1_repair_plan.sh <case>`：重置用例 → 诊断 → 建批次 → 等待 `planned` → 断言方案含 targets / actions / execute_command / 异常原因 → 提交一条修改意见 → 断言出现 v2 且 v1 进历史。输出一张结果表，非零退出即失败。

## 2. Sprint 2：高危命令黑名单 + 人工审批 / 自动执行开关

### 2.1 黑名单：规则化、默认非空、处处可见

把现有"传输检查 + 操作黑白名单 + exec 内层命令黑名单"收敛为一组**有编号的规则**，每次拒绝都带 `rule` 与 `reason`。规则只看命令形态，不看故障类型。

| 规则 | 默认 | 说明 |
|---|---|---|
| `transport.kubectl_only` | 固定 | 只允许单条 `kubectl`，禁止本地 shell |
| `transport.no_shell_operators` | 固定 | `; && \|\| \| > >> <` |
| `transport.no_identity_override` | 固定 | `--kubeconfig/--context/--server/--as/--token…`、`kubectl config` |
| `denied_operations` | `delete, apply, replace, edit, run, debug, drain, cordon, uncordon, taint, cp, port-forward, proxy, attach, auth, certificate` | kubectl 动词（`set/rollout` 取两段），deny 优先于 allow |
| `denied_flags` | `--force, --grace-period, --all, --all-namespaces, -A, --now, --cascade, --overwrite` | 批量 / 强制类参数 |
| `bulk_selector_on_write` | 开 | 写动词配 `-l/--selector/--field-selector` 视为批量操作，拒绝 |
| `denied_resource_kinds` | `node, namespace, clusterrole, clusterrolebinding, role, rolebinding, persistentvolume, storageclass, customresourcedefinition, mutatingwebhookconfiguration, validatingwebhookconfiguration, apiservice, priorityclass, certificatesigningrequest` | 写动词作用于这些 kind（含缩写与复数）时拒绝；读动词不受限 |
| `denied_executables` | `rm, mkfs*, dd, shutdown, reboot, halt, poweroff, init, telinit, fdisk, sfdisk, parted, wipefs, blkdiscard, nsenter, chroot, mount, umount, iptables, ip6tables, nft, kill, killall, pkill, crontab, useradd, usermod, userdel, passwd, chpasswd, su, sudo` | `kubectl exec` 内层命令，含 `sh -c` 字面量拆分 |
| `allowed_exec_commands` | 空 | 可选的内层命令白名单 |

写动词 = 除 `get, describe, logs, top, explain, events, wait, diff, api-resources, api-versions, version, auth can-i` 之外的全部动词。

执行点（三处同一实现，`policy.check_command(command, policy) -> CommandVerdict`）：

1. 规划阶段：`RepairDraft` 校验器对每条命令跑完整规则；命中即返回带规则号的错误，模型在结构化输出重试中拿到原因并可改用合规命令（例如 delete → patch finalizers）。整份方案仍然 fail-closed。
2. 执行阶段：`PodRepairExecutor` 预检所有阶段命令，命中则 `blocked` + `error_code=repair_command_denied` + `rule`，未执行任何命令（现有行为，补 `rule`）。
3. 验收入口：`GET /repair/policy`（生效策略全文、来源、开关状态）和 `POST /repair/policy/check {commands:[…]}`（逐条返回 `allowed/rule/reason/operation`，**不执行**）。前端修复面板加"命令安全检查"输入框，直接调用该接口，验收者粘贴一条 `kubectl delete ns xxx --force` 就能看到被哪条规则拦截。

审计：`repair_records/audit.jsonl` 追加写入 `command_denied / approval_decided / command_executed / mode_changed` 四类记录（时间、run/job、规则或审批人、命令摘要），供验收和事后追溯。

### 2.2 人工审批 / 自动执行开关

- 配置仍是基线：`workflow.remediation.mode`（review/auto）、`approval_timeout_seconds`。
- 新增运行时覆盖 `app/core/remediation/settings.py`：`PUT /repair/policy/mode {mode, reason, ttl_minutes}`，带 `X-AIOps-Admin-Token`（来自 Secret `AIOPS_ADMIN_TOKEN`；未配置则接口 403，开关只能走配置）。覆盖有 TTL（默认 60 分钟，上限 24 小时），到期自动回到配置值；持久化到 `repair_records/settings.json`，重启后仍按 TTL 生效。写审计。
- 执行层统一通过 `repair_settings.effective(cfg)` 取 `mode/mode_source/approval_timeout_seconds`；任务记录 `mode` 与 `mode_source`；自动模式下每个动作的 `remediation_tool_start` 事件带 `approval: "auto"`，终态 reason 写明"自动执行，未经人工审批"。
- 前端：修复面板头部显示开关状态徽标（"人工审批" / "自动执行 · 运行时覆盖，剩余 N 分钟"），管理员可输入令牌切换；切换后新建的任务按新模式执行，已在等待审批的任务不受影响（显式说明）。
- 验收脚本 `scripts/acceptance/sprint2_policy_and_switch.sh`：
  1. 黑名单：对 20 条高危命令调用 `/repair/policy/check`，全部 `allowed=false` 且 rule 非空；对 6 条合规命令全部 `allowed=true`。
  2. 审批：review 模式下建批次 → 出现 `awaiting_approval` 且 `events` 为空（未执行）→ 拒绝 → 终态 `rejected`、仍无执行事件。
  3. 开关：PUT 切 auto → 新批次直接出现 `executing` 且 `approval=null`、事件带 `approval=auto` → PUT 切回 review → 再建批次回到 `awaiting_approval`。审计文件中能看到三条 `mode_changed`。

### 2.3 为什么不做"每个请求自带 auto 参数"

开关是全局安全姿态，不是单次请求参数：请求级参数等于把授权交给调用方，A2A 场景下无法审计。TTL 覆盖 + 管理员令牌 + 审计是成熟的 break-glass 模式。

## 3. Sprint 3：执行结果展示 + 超时反馈 + 三场景验收

### 3.1 恢复观察（通用、只看状态）

动作全部执行完后进入 **恢复观察**（`workflow.remediation.recovery: {timeout_seconds: 180, poll_seconds: 5, settle_seconds: 20}`，0 关闭）：

- 观察对象：目标 Pod；若目标有控制器归属（方案 `targets[].owner_kind/owner_name`），再按控制器 `spec.selector.matchLabels` 取最新未删除 Pod 作为替代实例。全部用只读 `kubectl get … -o json`，走同一执行器与策略。
- 判定（只依据 Pod 状态，不含故障语义）：
  - 目标原本带 `deletionTimestamp`：目标 NotFound 即 `recovered`（有控制器时还要求替代实例 Ready）。
  - 其他：当前实例 `phase=Running` 且 `Ready=True` 且无容器 `waiting`，并在 `settle_seconds` 内重启计数不增加 → `recovered`；`phase=Succeeded` 视为恢复。
  - 超过 `timeout_seconds` 仍不满足 → `not_recovered`（超时反馈），附最后一次观测。
  - 观测本身失败 → `needs_followup`（保持现状语义）。
- 结果结构 `result.recovery = {before, after, elapsed_seconds, timed_out, checks}`，`before/after` 为 `{phase, ready, reason, restarts, deletion_timestamp, pod}`。过程事件 `remediation_recovery`（每次轮询一条，前端显示"观察中 35/180 秒 · Running Ready=false restarts=3"）。

### 3.2 超时反馈

| 超时 | 现状 | 变更 |
|---|---|---|
| 审批 | 600s，终态 `timeout` | 不变；文案明确"审批超时，未执行" |
| 单条命令 | 60s，异常文本是 subprocess 原文 | 文案改为"命令执行超时（60 秒），结果未知，请复查"；状态 `failed` 保留 |
| 恢复观察 | 无 | 新增 `not_recovered`，"超时未恢复（N 秒）"+ 最后观测 |
| 整体执行 | 无（`max_duration_seconds` 只给 react 执行器） | 执行器也遵守：超过则不再开始新动作，终态 `timeout`，说明已执行到第几个动作 |

### 3.3 三场景验收

`scripts/acceptance/sprint3_scenarios.sh <c06|c09|c11|all>`：重置用例（`repair_cases.py reset`）→ 诊断 → 建批次 → 自动批准全部审批 → 等待终态 → 断言 `recovered` 且 `kubectl` 复核（c11：Pod 消失；c09：Ready 1/1 且 EndpointSlice 就绪；c06：Running 且 120 秒无新增重启）→ 打印 before/after 表。不替模型选命令，模型选错就如实失败。

## 4. 实施顺序与发布

1. 2.1 黑名单规则 + 检查接口 + 审计（后端）→ 发版。
2. 2.2 运行时开关 + 任务/执行器接线（后端）→ 发版。
3. 前端：策略徽标、开关、命令检查框、拦截规则展示、`approval=auto` 展示 → 发版。
4. 3.1/3.2 恢复观察与超时 + 前端结果区 → 发版。
5. 验收脚本三份 + 文档（GUIDE / README / 本文"验收记录"节）。

每一步都有单元测试和接口契约测试；真实集群验证用上面的脚本，Boss 亲测用前端。

## 5. 实施记录（2026-10-16）

| 项 | 版本 | 状态 |
|---|---|---|
| 2.1 规则引擎 `policy.check_command`、默认黑名单、`GET /repair/policy`、`POST /repair/policy/check`、审计 | robusta 12.0.33 | 已上线；`sprint2_policy_and_switch.sh` 接口层 8/8 通过（25 条高危全拦、6 条合规放行） |
| 2.2 运行时开关 `PUT/DELETE /repair/policy/mode`（令牌 + TTL）、任务记录 `mode_source`、事件 `approval=auto` | robusta 12.0.33 | 已上线；无令牌 403、切换与恢复写审计 |
| 前端：策略徽标、规则列表、命令安全检查、管理员切换、拦截规则与审批来源展示 | frontend 0.1.61 | 已上线 |
| 3.1/3.2 恢复观察 `recovery.py`、`recovered/not_recovered/needs_followup`、整体时限 `timeout`、命令超时文案 | robusta 12.0.34 | 已上线 |
| 前端：恢复观察进度、执行前后对比表、超时反馈、异常原因行 | frontend 0.1.62 | 已上线 |
| 1 方案卡片"异常原因（来自诊断）" | robusta 12.0.34 / frontend 0.1.62 | 已上线 |
| 验收脚本 `scripts/acceptance/` | — | 见本文 §1–§3 与部署指南 |

伴随修复：`AgentGuards.finalize_on_idle_round`（12.0.33）。请求轨迹（`requests/<node>-NNN.json`）证明模型在"证据完整、准备输出结构化结果"时发出的是旧调用的复制；一整轮无新查询即收卷交付，不再等到重复上限。

### 5.1 真实集群验收结果（2026-10-16 晚，robusta 12.0.38 / mcpstander 7.0.44 / 前端 0.1.62）

| 场景 | 诊断 | 方案 | 执行与恢复 | 复核 |
|---|---|---|---|---|
| c11 Terminating（finalizer 阻塞） | run `d61d9d5574264c50`，cause 指出 finalizer `aiops.lab/hold` | 1 个动作，review 模式审批后执行 | `recovered`：原 Pod 已完成删除 | kubectl：workload 已消失 |
| c09 Ready 0/1（Readiness 端口 8081→8080） | run `5961256484444254` | json patch readinessProbe 端口 | `recovered`：Running/Ready 且 20 秒无新增重启 | Deployment readyReplicas=1，探针端口 8080 |
| c06 CrashLoopBackOff（环境变量名 APP_CONF_PATH→APP_CONFIG_PATH） | run `b217ff12b12144d4` | json patch env[1].name | `recovered`：新 Pod Running/Ready，重启 16→0，25 秒 | Deployment 就绪，60 秒无新增重启 |

验收过程中暴露并修掉的工程缺口（全部通用，不含故障特判）：

| 现象 | 根因 | 修复 |
|---|---|---|
| c11 首轮被判为"外部删除、非故障" | 整个诊断与规划没有任何工具输出包含 finalizer：lifecycle 工具只给 deletionTimestamp，`kubectl describe` 不显示 finalizers | mcpstander 7.0.44 lifecycle 记录增加 `finalizers / deletion_grace_period_seconds / terminating_seconds`，robusta 12.0.36 投影透传 |
| 诊断在 2 轮后被"空转收卷"截断 | 空转判定把单个重复调用也算作整轮空转 | `idle_round_min_calls: 2`（12.0.35） |
| 规划结构化交付两次失败后放弃 | 重试时模型不知道上次为何未通过校验 | 结构化重试把校验错误写进提示（12.0.35） |
| 方案把 `deployment workload-5487445f9`（ReplicaSet 名）当控制器 | 命令中的控制器名未与诊断核实的归属比对 | RepairDraft 归属一致性校验（12.0.35） |
| c06 方案把正确命令写在正文里，actions 为空，执行器只能 skipped | schema 允许无 actions 且无 assessments 的"回答" | 无 actions 必须逐目标给 assessments；正文含 kubectl 写命令而 actions 为空即拒绝（12.0.37） |
| c06 审批后 patch 被 API server 以 JSON 语法错误拒绝 | patch 内容只在执行时由 API server 校验 | `malformed_patch` 规则：规划阶段校验 JSON 语法与 json-patch 形态（12.0.38） |
| 验收脚本本身：`local a=$1 b=$((a))` 展开早于赋值；标签猜错 | 脚本缺陷 | 已修，复核改用 Deployment readyReplicas |

Sprint 2 接口层：`sprint2_policy_and_switch.sh` 8/8 通过（25 条高危命令全部拦截并带规则名，6 条合规命令放行，无令牌 403，切换/恢复写审计）。

Sprint 2 真实链路（`sprint2_policy_and_switch.sh aiops-case-04`，14/14 通过）：review 模式下任务停在 `awaiting_approval` 且无任何执行事件 → 拒绝后终态 `rejected`、仍无执行事件；管理员令牌切 auto 后新任务 `mode=auto / mode_source=runtime`，命令事件 `approval=auto`，无审批请求，`recovered`（Pending/CreateContainerConfigError → Running/Ready，25 秒）；随后恢复 review，全部写入审计。Sprint 1（`sprint1_repair_plan.sh aiops-case-04`，11/11 通过）：v1 被 v2 替代后状态 `superseded`、v2 由脚本结尾取消为 `cancelled`，均为设计内终态，case-04 在该脚本中未被修改。

### 5.2 最终验收记录（2026-10-16 22:25–22:42，robusta 12.0.40 / mcpstander 7.0.44 / 前端 0.1.62）

`scripts/acceptance/sprint3_scenarios.sh all`（含重置）一次完整运行 **13/13 通过**：c11 `9f76f1917324472d`（finalizer 移除后原 Pod 已删除）、c09 `fa733196969e49a5`（探针端口修正，readyReplicas=1）、c06 `7df6d1fde5064897`（环境变量名修正，重启 0→0）。

真实浏览器端到端（`frountind/tests/live-repair-e2e.browser.py`，Chromium 操作已部署前端，case-04）**9/9 步通过、0 页面错误**：聊天框发起诊断 143 秒完成 → 安全面板显示"人工审批"徽标与拦截规则 → 命令安全检查拦截 `kubectl delete ns demo --force`（高危动词黑名单）并放行 finalizer patch → 管理员切换为自动执行（运行时覆盖）再恢复配置值 → 生成方案（对象/异常原因/命令）→ 点击"批准此动作" → "执行后恢复观察：已恢复"，事件显示实际命令与审批 ID。截图：`live-repair-plan.png`、`live-repair.png`（验收工作目录）。

12.0.39/12.0.40 在前两轮完整运行中补上的通用护栏：模型写的验证命令失败不再终止（记录并交给恢复观察判定）；结构化交付校验失败带错误重试次数可配置（默认 2）；单目标时 group_id 自动绑定；`pod_spec_immutable` 规则（Pod spec 的 env/探针/资源等改动必须打到控制器模板，规划阶段即拒绝并给出提示）。

### 5.3 字面场景复核与结构化传输缺陷（2026-10-19，robusta 12.0.41）

需求表里 CrashLoopBackOff 一项写的是"启动脚本路径错误"，而 c06 夹具的故障是启动脚本读取配置路径的环境变量名错误。为了不让验收停在措辞上，用临时命名空间 `aiops-case-66`（c06 清单渲染后只改一处：`command` 指向不存在的 `/opt/start/bootstrap.py`，`CrashLoopBackOff` / 退出 2）跑完整链路。诊断（run `78d514ee007542c1`）准确指出 command 路径与 ConfigMap 挂载路径不一致；但修复方案三次结构化输出都被拒（job `6ec40015e1024f8a`）。

根因不在模型对该场景的理解，而在结构化交付的传输方式：`with_structured_output(method="function_calling")` 指名 `tool_choice`，vLLM 对参数做语法约束解码，Qwen3.6 在约束下不转义字符串内的双引号，首个内层引号（`-p='[{"`）就结束该字段，`actions` 整体丢失。直接对网关探测：`tool_choice` 指名 / `required` / `response_format=json_schema` 都在同一位置断掉；`tool_choice=auto` 正常转义。此前 §5.1 中"命令写在正文、actions 为空"（12.0.37）与"patch JSON 畸形"（12.0.38）两条都是同一缺陷的不同表现。

处理（通用，无场景分支）：`llm.structured_tool_choice=auto`——schema 作为唯一工具、`tool_choice=auto`，服务端 Pydantic 校验；`finish_reason=length` 的部分 JSON 按截断拒绝；写成 JSON 字符串的列表字段按原样解码；被拒回复的 `finish_reason` / usage / 原始参数归档到 `structured/<node>-rejected-NNN.json`；请求存档每条 assistant 消息附 `reasoning_tail`，用于回看重复调用前模型在想什么。复测记录见下。

12.0.41 复测（job `fb639f92ad5c4a32`）：方案完整生成，含引号的 json patch 命令原样通过校验与执行——传输缺陷已消除。暴露下一层问题：方案把 patch 打在 **ReplicaSet** `workload-7bf9698f49` 上，命令成功、Deployment 随即覆盖、恢复观察 180 秒超时如实报 `not_recovered`。根因是目标的控制器归属由模型自填（`owner_kind/owner_name`），而 Kubernetes 的规则是"受控对象的 spec 由其控制器改写"。

处理（12.0.42，`app/core/remediation/ownership.py`，通用）：规划前用只读 `kubectl get -o json` 沿 ownerReferences 把每个目标 Pod 的所有权链走到顶（Pod→ReplicaSet→Deployment、Pod→Job→CronJob、裸 Pod 无 root），作为事实 `controller_chains` 注入规划材料；`RepairDraft.with_controller_chains` 绑定本次事实：目标的 owner 字段以集群事实覆盖模型猜测，对链上受控成员（非 root）的写命令在规划阶段拒绝并指出 root（读命令不受影响，链外对象不判）。不区分工作负载类型，不解析失败时退化为不校验。

12.0.42 复测（`aiops-case-66` 重建后，run `eb5be763130846d0` / job `417b082d615f4e58`）**4/4 通过**：目标 owner 由集群事实填为 `Deployment/workload`，方案为 `kubectl patch deployment workload … /spec/template/spec/containers/0/command`，批准后新 Pod Running/Ready，恢复观察 20 秒判定 `recovered`，60 秒无新增重启，Deployment 模板 command 已是 `/opt/startup/bootstrap.py`。该场景的清单保存在 `scripts/acceptance/fixtures/c06-script-path.yaml`。

完整 Sprint 3 套件在 12.0.42 上重跑（2026-10-19 10:23–10:50，`sprint3_scenarios.sh all`，重置通过后三场景）**13/13 通过**：c11 `715bba7c0d6e4502`（finalizer 移除，原 Pod 已删除）、c09 `60e83ba5f053456a`（readyReplicas=1）、c06 `02414cf1409c4e2c`（重启 0→0）。四个夹具与 `aiops-case-66` 之后均已重置为故障态，供人工验收。

