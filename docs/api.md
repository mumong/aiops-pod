# HTTP API：查询、诊断、修复与审批

[返回 README](../README.md)。前端的每个点击都对应下面的 HTTP 接口，脚本、curl 和其他 Agent 可以走同一套流程。流程与边界见[核心流程与模块架构](ARCHITECTURE.md)。

## 1. 身份与会话

| 概念 | 说明 |
|---|---|
| `session_id` | 调用方自取的会话 ID，16–128 字符（字母、数字、`_`、`-`）。同一会话内的问答构成上下文，"修复刚刚的问题"靠它找到上一轮诊断 |
| owner cookie | 首次带 `session_id` 调用 `/ask` 或 `/query` 时，服务端下发 HttpOnly cookie `aiops_query_owner`（64 位十六进制）。诊断记录、修复任务和审批都绑定这个身份；**之后的修复接口必须带上同一个 cookie**，否则返回 401 |
| curl 用法 | `-c jar.txt -b jar.txt` 保存并回传 cookie |

```bash
B=http://10.2.0.48:30800
J=jar.txt
S=my-api-session-0001
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

只有诊断结论为 abnormal / inconclusive 的组会生成任务；全部 healthy / recovered 时返回 409"未发现需要修复的异常组"。同一诊断、同一组选择重复发起，返回同一个批次。

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

## 7. 待办：A2A 与 API 身份（已记录，未实现）

现状：A2A 适配器（[a2a](a2a.md)）只有查询与诊断两个技能，调用 `/ask`、`/query` 时不带 `session_id` 和 cookie，因此：没有会话上下文、不保存诊断记录、无法发起修复；审批事件不转发，也没有使用 A2A 的 `input-required` 状态；修复路由会返回"人工修复需要会话归属"。

| # | 待办 | 说明 |
|---|---|---|
| 1 | API 身份不依赖 cookie | 增加请求头方式（如 API 令牌映射 owner），审批人即调用方身份并写入审计 |
| 2 | A2A 会话映射 | A2A `contextId` → `session_id`，认证主体 → owner，使多轮"修复刚刚的问题"成立 |
| 3 | A2A 修复技能 | 新增 `kubernetes-repair`：内部调用 `/repair/batches`，把任务进度作为 A2A 状态更新 |
| 4 | A2A 人工审批 | 任务 `awaiting_approval` 时 A2A 任务转 `input-required`，附各组方案与 `approval_id`；调用方在同一任务回复 `{approval_id, approved, reviewer}`，适配器调用 `/repair/jobs/{id}/approve` 后继续 |
| 5 | 无诊断时的对话修复 | 会话没有诊断就说"修复…"时，仍由单个 Agent 现场调查规划；建议先自动做该 Pod 的诊断再进入按组批次，控制器链按请求中的 Pod 直接解析 |
| 6 | 编造配置值 | 方案写入 Secret / ConfigMap 的值必须来自证据或用户输入（run d09fc5c84ff54eb8 曾补了一个虚构的 Secret 值） |
| 7 | 死代码清理 | `client._maybe_compact_runtime_context` 等旧运行时压缩路径无调用方 |
