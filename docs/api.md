# HTTP API：查询、诊断、修复与审批

[返回 README](../README.md)。前端的每个点击都对应下面的 HTTP 接口，脚本、curl 和其他 Agent 可以走同一套流程。流程与边界见[核心流程与模块架构](ARCHITECTURE.md)。

## 1. 身份与会话

| 概念 | 说明 |
|---|---|
| API 令牌（推荐给脚本 / Agent） | 请求头 `Authorization: Bearer <token>` 或 `X-AIOps-API-Token: <token>`。令牌配置在 Secret `AIOPS_API_TOKENS`（`name=token,...`），每个 name 是一个独立身份，记录归属于它，审批人默认就是这个 name 并写入审计；令牌不匹配返回 401。带令牌时不需要 cookie |
| `session_id` | 调用方自取的会话 ID，16–128 字符（字母、数字、`_`、`-`）。同一会话内的问答构成上下文，"修复刚刚的问题"靠它找到上一轮诊断 |
| owner cookie（浏览器） | 首次带 `session_id` 调用 `/ask` 或 `/query` 时，服务端下发 HttpOnly cookie `aiops_query_owner`（64 位十六进制）。诊断记录、修复任务和审批都绑定这个身份；**之后的修复接口必须带上同一个 cookie**，否则返回 401 |
| curl 用法 | `-c jar.txt -b jar.txt` 保存并回传 cookie |

```bash
B=http://10.2.0.48:30800
S=my-api-session-0001
# 方式一：API 令牌（下文的 -c/-b 换成 -H "$AUTH" 即可）
AUTH="Authorization: Bearer <AIOPS_API_TOKENS 中的令牌>"
# 方式二：cookie jar
J=jar.txt
```

## 2. 快速查询

```bash
curl -N -c $J -b $J -X POST $B/query \
  -d 'q=查询各节点的 CPU 和内存使用率' -d session_id=$S -d stream=true -d format=sse
```

`stream=false&format=text` 返回纯文本；SSE 的 `final` 事件包含 `answer`、`query_answer`、`run_id`。

## 3. 深度诊断

```bash
curl -N -c $J -b $J -X POST $B/ask \
  -d 'q=我的集群 pod 有什么问题' -d session_id=$S -d stream=true -d format=sse
```

`final` 事件中：

| 字段 | 含义 |
|---|---|
| `run_id` | 诊断 ID（下文记为 `D`） |
| `diagnosis_cases` | 每个异常组的结论（`outcome`：abnormal / recovered / healthy / inconclusive） |
| `repair_record` | `{run_id, kind:"diagnosis", repairable}`；`repairable=false` 表示没有需要修复的组 |

## 4. 生成修复方案（等同于报告下的"生成自动修复方案"）

三种入口创建的是**同一种按组修复批次**（每个异常组一个独立规划任务，并发规划、各自审批）：

```bash
# a) 诊断后单独发起
curl -b $J -H 'Content-Type: application/json' -X POST $B/repair/batches \
  -d '{"diagnosis_run_id":"D"}'

# b) 诊断时一并发起：诊断完成后自动建批次，final.repair_batch 返回批次
curl -N -c $J -b $J -X POST $B/ask -d 'q=我的集群 pod 有什么问题' \
  -d session_id=$S -d repair=plan -d stream=true -d format=sse

# c) 对话发起：同一会话里说"修复刚刚的问题"或"修复 aiops-case-11 的 workload"
#    会话已有分组诊断时，按诊断的异常组（或你点名的 Pod 所在组）建批次，final.repair_batch 返回批次
curl -N -c $J -b $J -X POST $B/ask -d 'q=修复刚刚的问题' -d session_id=$S -d stream=true -d format=sse
```

带 `repair=plan` 时，如果会话里还没有诊断（例如直接说"诊断并修复 xx"），会先做深度诊断再自动建批次，审批一律走批次；不带 `repair=plan` 的对话行为不变。

`repair=on_request`（`/ask` 与 `/query` 都支持，A2A 适配器每次都带）：只有请求本身是修复（路由判断为 remediation）时才这样做——会话中尚无诊断则先诊断再建批次；普通查询和诊断不建批次、不出现审批。网页前端不带这个参数，行为不变。只有诊断结论为 abnormal / inconclusive 的组会生成任务；全部 healthy / recovered 时返回 409"未发现需要修复的异常组"。同一诊断、同一组选择重复发起，返回同一个批次。

## 5. 查看方案、审批、观察结果

```bash
# 批次：各组 job_id、status、pending_approval_id
curl -b $J $B/repair/batches/batch-D

# 订阅批次变化（SSE）：每次变化一条 event: batch，全部结束后 event: end
curl -N -b $J $B/repair/batches/batch-D/events

# 单个任务：plan（targets / actions / assessments / answer）、status、approval
curl -b $J $B/repair/jobs/<job_id>

# 审批（等同于点击"批准"/"拒绝"）：approval_id 取自 pending_approval_id 或 job.approval.approval_id
curl -b $J -H 'Content-Type: application/json' -X POST $B/repair/jobs/<job_id>/approve \
  -d '{"approval_id":"<approval_id>","approved":true,"reviewer":"boss","reason":"已核对命令"}'

# 修改方案（等同于"通过对话修改方案"）：生成 v+1，旧审批作废
curl -b $J -H 'Content-Type: application/json' -X POST $B/repair/jobs/<job_id>/feedback \
  -d '{"version":1,"feedback":"不要补 Secret 值，改为修正引用的 key"}'

# 取消
curl -b $J -X POST $B/repair/jobs/<job_id>/cancel
```

任务状态：`queued → planning → planned → awaiting_approval → executing → verifying →` 终态（`recovered` / `not_recovered` / `timeout` / `rejected` / `blocked` / `failed` / `cancelled` / `superseded` / `execution_disabled` / `interrupted`）。

审批规则与前端完全一致：每个动作单独审批，审批前先过高危命令规则（命中即 `blocked`，不执行任何命令），review 模式等待 `approval_timeout_seconds`（默认 600 秒），整体限时 `max_duration_seconds`（默认 900 秒），执行后进入恢复观察。旧接口 `POST /remediation/approve`（表单）保留兼容。

## 6. 策略与审计

```bash
curl $B/repair/policy                                   # 当前模式与规则
curl -H 'Content-Type: application/json' -X POST $B/repair/policy/check \
  -d '{"commands":["kubectl delete namespace demo"]}'   # 只判定、不执行
curl -H 'X-AIOps-Admin-Token: <token>' -H 'Content-Type: application/json' \
  -X PUT $B/repair/policy/mode -d '{"mode":"auto","ttl_minutes":30,"reason":"演练"}'
curl -H 'X-AIOps-Admin-Token: <token>' $B/repair/audit
```

## 7. A2A 调用（含修复与人工审批）

A2A 服务（Agent Card：`http://<host>:30801/.well-known/agent-card.json`）提供三个技能：`kubernetes-query`、`kubernetes-diagnosis`、`kubernetes-repair`。适配器以 Secret 中 `A2A_BACKEND_API_TOKEN`（`AIOPS_API_TOKENS` 里的 `a2a` 身份）访问后端；每个 A2A `contextId` 对应一个后端会话，所以同一上下文里"修复刚刚的问题"能找到之前的诊断。

修复流程（JSON-RPC `message/send`，`metadata.aiops_mode=repair`）：

```bash
A=http://10.2.0.48:30801
# 1) 发起：诊断（或复用本上下文的诊断）并按组生成修复方案
curl -s -X POST $A/ -H 'Content-Type: application/json' -d '{
  "jsonrpc":"2.0","id":"1","method":"message/send",
  "params":{"metadata":{"aiops_mode":"repair"},
            "message":{"kind":"message","role":"user","messageId":"m1",
                       "parts":[{"kind":"text","text":"诊断并修复 aiops-case-09 命名空间中的异常 Pod"}]}}}'
# -> result.status.state = "input-required"
#    result.status.message.parts[] 含文本（每组动作、命令、风险、回滚）和
#    DataPart {"batch_id": "...", "approvals": [{"job_id","group_id","approval_id","execute_command",...}]}

# 2) 在同一任务里回复审批（taskId / contextId 取自上一步结果）
curl -s -X POST $A/ -H 'Content-Type: application/json' -d '{
  "jsonrpc":"2.0","id":"2","method":"message/send",
  "params":{"message":{"kind":"message","role":"user","messageId":"m2",
                       "taskId":"<task id>","contextId":"<context id>",
                       "parts":[{"kind":"data","data":{"approval_id":"<approval_id>","approved":true,"reviewer":"ops-bot"}}]}}}'
#    也可用文本：{"kind":"text","text":"批准 <approval_id>"} 或 "拒绝 <approval_id>"
# -> 执行 → 恢复观察；若还有下一个待审批动作，任务再次进入 input-required；
#    全部结束后 state = "completed"，artifact kubernetes-aiops-repair.md 含每组结果（含 DataPart results）
```

安全边界与前端一致：审批前先过高危命令规则；review 模式下每个动作都要审批，超时不执行；`message/stream` 同样可用（进度以 status-update 推送）。未配置 `A2A_BACKEND_API_TOKEN` 时修复技能直接拒绝，查询与诊断不受影响。

## 8. 待办（已记录，未实现）

| # | 待办 | 说明 |
|---|---|---|
| 1 | 无诊断时的对话修复 | 会话没有诊断就说"修复…"时，仍由单个 Agent 现场调查规划；建议先自动做该 Pod 的诊断再进入按组批次，控制器链按请求中的 Pod 直接解析 |
| 2 | 编造配置值 | 方案写入 Secret / ConfigMap 的值必须来自证据或用户输入（run d09fc5c84ff54eb8 曾补了一个虚构的 Secret 值） |
| 3 | A2A 调用方身份细分 | 目前所有 A2A 调用方共用适配器的 `a2a` 身份（会话按 contextId 隔离，审批人取调用方填写的 reviewer）；如需按调用方隔离记录，可把 A2A 认证主体映射为各自的 API 身份 |
| 4 | 死代码清理 | `client._maybe_compact_runtime_context` 等旧运行时压缩路径无调用方 |
| 5 | 执行类请求 | 已实现（2026-10-20）：路由到 focused/operate，轻量路由直接执行 bash/kubectl/helm；高危规则为唯一硬闸，执行与拦截写审计；不审批。见 ARCHITECTURE §5 |
| 6 | API 令牌管理接口 | 2026-10-20 记录，优先级在网页端逻辑稳定之后。现状：令牌写死在 Secret `AIOPS_API_TOKENS`（`名字=令牌`），新增调用方需改 Secret 并重启，无过期、无单独吊销、所有调用方权限相同。设计：以 `AIOPS_ADMIN_TOKEN` 为根钥匙，提供仅管理员可调的创建（名字、权限范围只读/可修复、有效期，明文只返回一次）、列出（不含明文，含最近使用时间）、吊销（立即生效、免重启）接口；服务端只存哈希，与修复记录同目录持久化；Secret 中现有条目保留为启动时固定调用方（A2A 继续使用）；创建、吊销、认证失败写审计；权限范围在 `app/api/identity.py` 校验。不做调用方自助生成。约 1 天含测试与文档 |
