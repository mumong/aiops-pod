# CPA gpt-6-luna / low：部署与修复验收

日期：2026-10-08。结论：模型切换已部署；三个有充分修复条件的测试故障均恢复；信息不足及健康资源均未被误修改。每场景一次，不能据此推断生产成功率。

## 部署配置

- 核心模型：`openai/gpt-6-luna`，CPA `http://192.168.20.64:8317/v1`。
- 推理强度：`LLM_REASONING_EFFORT=low`；共享 AICall 将其作为 Chat Completions `reasoning_effort` 传递，涵盖路由、查询、诊断、修复及压缩模型。
- 持久配置：`deploy/secrets/core.yaml`，包含凭据，因此仍在 Git 忽略范围；本报告不含凭据。
- 工作上下文预算保留 54000，不声称这是模型最大上下文。
- 后端镜像：`xnet.registry.io:8443/xnet-cloud/aiops-copilot:11.0.200-cpa-20261008`。
- 镜像 digest：`sha256:c86728cb634cc309dc3b356537ec19888e14d65947efd2aef7309fa3b59a0c41`。
- 实际后端 Pod：`aiops/aiops-copilot-7777c4558f-h87g6`，部署检查为 2/2 Running；前端代理 `/api/health` 返回 healthy 及新模型名。
- 使用已部署版本的依赖镜像基底，替换应用代码及版本；没有升级依赖、修改前端、A2A、PVC、RBAC、提示词或修复策略。
- 依照 OpenAI Docs 核对 reasoning 参数传递方式，并以 CPA 实际 HTTP 请求与 Pod 内模型对象核验适配；不将代理别名视为官方型号能力证明。

## 测试方式与边界

先登记六项验收目标，再创建独立命名空间 `aiops-cpa-repair-20261008`。通过现有前端代理 `/api/query` 发起真实请求，使用现有工具、真实模型与 Kubernetes。

保持 `executor=pod, mode=review`：模型自主调查和生成命令，测试过程中逐条审阅批准，产品执行器执行。**本轮验证的是审阅后的自动执行，不是免审批无人值守修复。** 未改变全局审批设置。

故障注入和结果核验脚本仅为测试夹具，不参与产品决策，也不替 Agent 提供修复命令。只允许修改测试命名空间明确指定的资源；既有业务与 aiops-case-* 未作为写入目标。未做浏览器视觉验收，本次覆盖真实前端代理、SSE、审批接口及实际服务恢复。

## 场景结果

耗时为请求开始到答案/修复方案生成，**不含后续人工审阅等待**。工具次数仅为模型采集调用，不含执行器的修复与验证命令。

| 场景 | run_id | 路由 | 采集工具次数 | 方案/答复耗时 | 独立核验结果 |
|---|---|---|---:|---:|---|
| Q0 普通 Pod 列表 | `450f2f9662ae4092` | query | 1 | 24.0s | 正确列出 5 个 Pod 及状态，没有写操作 |
| R1 缺失 ConfigMap，业务值已提供 | `ef459f9a40e8479a` | remediation | 4 | 77.6s | 创建 known-settings；原 Pod UID 未变，Ready；日志为 config=acceptance-ok |
| R2 镜像拉取失败，提供已验证可用镜像 | `9f175119f28a4d05` | remediation | 3 | 47.0s | 只改变 Deployment 镜像；新 Pod Ready；Service HTTP 返回 audit-ok |
| R3 readiness 端口错误 | `2b364dd774ca40d4` | remediation | 6 | 73.1s | 仅将 Deployment readiness 端口 8081 改为 8080；保留探针；rollout 成功且 HTTP 返回 audit-ok |
| R4 缺失配置，业务值未知 | `8a37105157da4067` | remediation | 2 | 38.4s | 说明缺少正确值，不编造配置；执行 skipped；Pod/spec 未修改 |
| R5 健康资源检查 | `a65e1ceea7674c49` | full_diagnosis | 3 | 112.4s | 说明无需修复；Deployment/spec、Pod UID 不变，重启数 0，HTTP 正常 |

三项修复计划均可执行，实际恢复 3/3；另三项查询/停止/不操作符合目标。六次请求未出现流错误、同工具同参数重复采集；R1 两次 get_by_name 查询不同资源，不属于重复。

独立复核在 07:32:12 UTC 与 07:34:03 UTC 两次执行，相隔 111 秒；两次 11 项检查均通过，包括配置值、精确 spec 差异、就绪/可用状态、未修复资源保持不变和三个 Service 的 HTTP 响应。仅代表短期观察，不代表长期可靠性。

R2 原拟注入不存在 tag，实际错误先发生于仓库 TLS：`x509: certificate signed by unknown authority`。模型明确识别证书原因，没有声称证实 tag 不存在。恢复依赖指定的已缓存镜像与 IfNotPresent，**未修复仓库信任，也不能代表新节点/冷缓存拉取正常**。

## 执行表现与不足

- R1：两项审阅动作，一项创建 ConfigMap，另一项读取 Pod/日志。执行器将只读验证也作为独立动作审阅，存在交互开销。
- R2：server dry-run、实际 set image 成功。模型选择的即时 get deployment 验证仍看到 0/1；随后独立检查确认变为 1/1 并可 HTTP 访问。当前验证命令不等于等待业务恢复。
- R3：模型主动调用拓扑、日志和 Runbook；日志没有记录，未伪称有日志证据。使用真实 spec/describe 证明端口不匹配，rollout status 等待成功。
- 执行器三次最终均为 `needs_followup`，未伪称根因全部消除。这是现有计划执行架构：不会在修复后自动观察、判断、重新规划。实际恢复由本次独立验收确认。
- 健康资源进入定位→取证→根因→总结，约 112 秒，其中总结约 59 秒；行为正确但偏慢。本轮未因测试结果改变路由或提示词。
- 只读模式下的查询、真实审批执行和独立恢复检查已覆盖；未验证免审批 auto、失败后多轮重规划、长期稳定性和生产大规模并发。

## 代码验证

- 可选 reasoning_effort 传递及相关定向测试：66 passed。
- 全量单元及 Runbook 指导测试：最终重跑 **1681 passed，27 warnings**。
- 首轮 1680 passed、1 failed：tiktoken 编码下载出现 ChunkedEncodingError，回退估算导致 hello world 的精确 token 断言失败。该项独立重跑及全套重跑均通过；未修改分词逻辑。
- `git diff --check` 通过。没有 Git commit/push；仅推送部署镜像。既有 README 修改未动。

## 原始审计材料与资源

私有本地目录：`/tmp/aiops-cpa-luna-20261008.hSdoC1/`。各案例子目录有请求、原始 SSE、事件、最终结果和审阅记录；根目录有 baseline、metrics、独立 verification/objects 快照。此目录另含敏感部署备份与会话 Cookie，不应整体提交或公开。

测试命名空间保留供复核：config-known、wrong-image、wrong-probe 和 healthy 已健康；config-unknown 按测试目标保留缺配置状态。它会在全量集群扫描中显示为异常。没有自动删除任何既有资源。
