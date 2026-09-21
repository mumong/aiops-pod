# Pod 修复路由：实现、边界与验收

2026-09-20 QUERY 写操作开放（11.0.194）：用户明确要求普通资源操作时 focused/operate 暴露现有 MCP `run_bash_command`、`kubectl_run_image`。普通操作由 QueryCollectNode 执行并结构化返回，不生成故障修复计划；用户查询/诊断意图仍无写工具。模型提示要求限定目标、写前检查、写后核实，高风险操作确认，超时先核实不重复写。MCP 危险命令拦截保留，但这不是严格的 Kubernetes 操作白名单；广泛 RBAC 下存在较高执行风险。故障修复路径的人工审批不受影响。

所有节点共用 AIOps ServiceAccount，MCP 工具使用 MCP ServiceAccount，两者 RBAC 均已是集群管理级。RBAC 不区分路由；工具是否暴露和节点是否调用工具仍按职责区分，RCA/总结不因此增加执行循环。

11.0.194 验证：1,435 项后端测试通过，部署就绪、health 模型为 openai/Qwen3.8-27B。实际 MCP `run_bash_command` 在隔离命名空间创建 mcp-write-check ConfigMap 成功，回读 probe=ok。前端端到端运行 fa67abe99ba84563 正确路由 focused/operate、节点获得 38 个工具（含写工具），但 Qwen 采集调用等待至 180 秒测试上限，未创建 query-write-check；客户端关闭，本项未通过。测试命名空间 aiops-query-write-smoke-20260920 与其中测试 ConfigMap 已申请删除；无业务资源变更。本轮未提交 Git。

2026-09-20 意图边界修正（11.0.193）：切回正式 Secret 的 `openai/Qwen3.8-27B` 模型连接配置，不再由临时 DeepSeek Secret 覆盖。普通资源创建/操作使用 focused/operate；只有明确的异常修复进入 remediation，明确深度诊断进入 full_diagnosis。查询修复状态不再次发起修复。此轮没有开放任意写工具，query 目前仍只能查询与提供操作建议，轻量写操作范围待确认。

运行 `e5e673a7215b403f` 审查：上文已明确 xnet，本轮要求在该命名空间创建 nginx 测试 Pod；模型误把创建请求归入 remediation/repair。后续无写操作，规划 actions=[]；又把“测试”与 test 命名空间混淆，要求重新确认已明确范围，且进行了与创建无关的取证。修正采用提示词边界与 operate 类型，不增加关键词强制路由。模型不应从 nginx 自动推断用户已指定资源名称。

验证：1,434 项后端测试通过；Qwen 实际接口上的五类无工具分类测试均符合预期（同会话创建→focused/operate 且 xnet、列表→focused、深度根因→full_diagnosis、明确修复→remediation、修复状态查询→focused）。该分类测试不等同于写操作执行验收。11.0.193 滚动部署通过，线上 health 确认模型为 openai/Qwen3.8-27B。

前端代理只读回归 `9726da2408c14928`：路由为 focused/query，范围 xnet 正确；路由耗时约 19.5 秒，采集调用随后长时间未结束，约 2 分 40 秒主动关闭本地测试客户端。因此不能将本轮 Qwen 完整查询体验标记为通过，也尚不能仅凭这一轮定位为模型本身故障。未为此测试执行业务写操作。

2026-09-20 后续更新（11.0.192）：查询、定位/取证、修复提示词强化按问题选择 Prometheus/Metrics、Logging、Tracing 的多维证据，路由保留相关需求，RCA/总结复用真实观测、不伪造补查。保持无工具节点职责与自主选择，不新增强制采集。执行步数上限统一为 query_collect=48、layer=32、evidence=48、remediation=64，RCA/总结不变；移除线上查询节点原先值为 40 的独立环境变量覆盖，统一使用 ConfigMap。全资源 RBAC 复查通过，人工审批与命令策略仍保留。

2026-09-20 更新：后端 11.0.191 / 前端 0.1.26 修正修复 schema 未计入压缩预检的问题，细化 11 类 Runbook 的可执行条件与前端审批排版；修复节点明确决策停止条件并将上限从 32 调至 48。RBAC 按管理员要求放开为集群管理权限，命令策略与默认人工审查保留。详见 [修复适用范围与运行审查](pod-repair-eligibility.md)。以下为 09-18 的历史验收记录。

本轮部署已完成：后端 Deployment 1/1、前端 Deployment 1/1；挂载配置确认 remediation 上限 48。后端 1,433 项测试通过（27 项已有弃用警告），前端 70 项测试、lint/build 与部署页面审批回放通过。线上只读回归 `865627878d254974` 正常完成、无预算/步数中断，不生成无限增长场景的扩容操作。本轮没有再次批准业务工作负载变更，未提交 Git；模型输出残留的证据边界问题见修复适用范围文档。

2026-09-18：后端 **11.0.189**、前端 **0.1.25** 已部署，rollout 和健康检查通过。模型为 `deepseek/deepseek-chat`，默认人工审批 600 秒；全局 auto 未开启。未提交 Git。

## 使用方式与流程

同一前端会话先查询或诊断，再输入“帮我修复刚才的 Pod”。独立 remediation 节点根据近期上下文、真实工具返回及 Runbook 制定结构化方案。旧回答只用于定位问题，Pod UID、控制器归属及当前状态需要重新核实。规划节点只暴露只读取证和 Runbook 工具，不直接执行写命令。

方案包含目标、group_id、命令、风险、验证和回退建议。程序按真实 ownerReferences 验证范围与身份，检查全部动作后显示审批卡片；批准后执行审批时的命令快照，不让模型另写命令。过期、拒绝、取消不继续未批准动作；已经执行的动作不自动回滚。

深度诊断在现有 conclusion 调用中同时输出可选 RepairDraft，不额外默认串行调用规划模型。证据完整时直接进入审查；没有可执行计划时，最新深度报告下显示“生成修复方案并审阅”，点击在同一会话按需调用修复节点，不构成执行批准。普通查询不会因正文含命令而触发写操作。

并发诊断仍按 Pod 分组；修复事件携带 group_id/action_id/stage，前端分别展示预演、执行、验证与返回。写动作顺序执行，Pod/控制器锁阻止同一进程内两个修复请求同时操作共享资源。批准一个动作不批准另一组。审批后重新检查 UID/generation，配置变化则要求重新规划。

## 配置与边界

配置位置：`deploy/configmap/config.yaml` 的 `workflow.remediation`。

| 配置 | 当前值/作用 |
|---|---|
| enabled | true，开关 |
| executor | pod，受限确定性执行器 |
| mode | review；显式 auto 才跳过人工批准，仍经过身份和命令策略 |
| approval_timeout_seconds | 600，倒计时结束不是批准 |
| allowed_operations / denied_operations | 可收紧操作范围，黑名单优先；增加名字不会自动获得新的命令解析能力 |

默认写操作为资源调整、滚动重启、仅限容器 CPU/内存 requests/limits 的 JSON Patch。禁止任意 Shell、rm、exec、delete/apply/create、批量选择器、跨集群/凭据覆盖、提权及未核实目标。dry_run 必须显式 server，verify 必须只读。服务使用自身 ServiceAccount，不复制主机管理员凭据。单个 kubectl 最长 60 秒。

不承诺自动修复所有 Pod 故障：镜像/环境变量/卷配置、finalizer、网络附属定义等不在默认写策略内；信息不足或不受支持时提供人工建议，不伪造可执行计划。无限增长程序不能仅靠增大内存根治。

审批和互斥锁为进程内状态，适用于当前单实例服务。重启会中断待审任务，应重新发起；尚不支持多副本共享审批与分布式锁。命令成功显示“待复查恢复状态”，不等于根因消除；超时也不能认定写入完全未生效。

## 工具能力评审

| 能力 | 当前 Codex 环境 | 当前 AIOps |
|---|---|---|
| Kubernetes 与可观测性取证 | 主机工具、网络与已有凭据 | K8s、Metrics、Logging、Tracing、Topology 只读工具 |
| 读取处置手册 | 项目文件 | Runbook 目录与 fetch_runbook |
| 变更工作负载 | 获授权后通过主机 kubectl | 经人工/auto 策略的有限 Pod/控制器命令 |
| 主机文件、Docker、任意 Shell、SSH | 按当前环境实际权限提供 | 本轮未向 Agent 新增这些能力 |

MCP 中有 bash 工具源码，不代表修复 Agent 已暴露该工具。当前 Pod 修复无需新增宿主机 Shell/SSH 权限；未来扩展逐项评审，不通过放开任意命令实现。

DeepSeek 使用独立 `aiops-deepseek-remediation` Secret，仅接管模型配置三项；原 Secret 保留，未输出密钥。

## 验收证据

| 要求 | 结果 |
|---|---|
| 最近会话与修复路由 | 查询 `0d83839ae39242ab` 后，追问 `84c45b9393f54cd2` 正确路由 remediation，实际读取 Runbook |
| 人工批准并真实修复 | `38083567dfa84191` 经前端 API 代理审批，隔离 bounded-oom memory limit 64Mi→128Mi；rollout 成功，新 Pod Running/0 重启 |
| 拒绝且不写入 | `84c45b9393f54cd2` 审批 API success，终态 rejected；无 execute 事件，前后 Deployment spec 相同 |
| auto 与双组真实执行 | `isolated-auto-two-groups` 在服务 Pod 内调用相同执行器；两组分别 server dry-run→execute→rollout，无审批；新 Pod 均 1/1 Running、0 重启，CPU/requests 不变；全局仍为 review |
| 深度并发诊断 | `79e3f5c047f849f7` 实际执行 layer→parallel_evidence→conclusion 并读取 Runbook。本次没有可执行 draft，未写入，不能称为深度直接修复成功 |
| 复用总结与配置传递 | 单测验证一次 conclusion 同时生成报告和计划；完整 WorkflowExecutor 测试覆盖 review/auto、owner、超时、策略和目标范围传递 |
| 前端审批与按需入口 | 已部署页面浏览器回放通过：final 后审批、倒计时不批准、有效批准、双组执行结果和截断提示；深度按钮使用同 session 发起后续请求，不发送批准 |
| 黑白名单及竞态 | 测试覆盖越界、隐藏写 verify、Shell/凭据注入、跨会话/重复/过期批准、配置变化、共享资源冲突、取消及失败阶段 |
| 自动验证 | 后端 1,428 项通过；前端 70 项通过，lint/build 通过；构建有已有 chunk 大小提示，不阻止发布 |

浏览器回放是受控事件测试，不替代真实集群执行。真实 auto 测试直接走服务 Pod 执行器，不等于全局 auto 下的大模型端到端测试。配合 workflow 配置测试分别覆盖展示、实际执行与连接。

对应实现与测试：`app/core/workflow/nodes/remediation.py`、`app/core/remediation/pod_executor.py`、`policy.py`、`tests/unit/workflow/test_remediation_node.py`、`tests/unit/remediation/`；前端 `tests/remediation-review.browser.py`。

SSE 留存于当前机器：`/tmp/aiops-fixture-repair-20260918.json`、`/tmp/aiops-repair-followup-reject.json`、`/tmp/aiops-deep-repair-review.json`，不是永久审计存储。后端 run 归档保存原工具证据与独立修复节点计划。

测试命名空间 `aiops-repair-smoke-20260918` 已清理并确认删除，仅包含本轮两个无数据卷测试工作负载及其派生资源；未删除原有 case 或业务资源。测试运行记录保留，测试 Pod 本身不能恢复原运行状态，可按 fixture 定义重建。
