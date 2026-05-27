# 修复执行与人工审批使用说明

本文说明诊断完成后如何进入修复流程，以及人工审批如何让流程继续执行。

## 1. 前置条件

修复流程只在诊断接口显式开启时运行：

- 请求 `/ask` 时必须带 `remediate=true`。
- 修复审批依赖流式输出，因此必须 `stream=true`。
- 后端配置 `workflow.remediation.enabled` 需要为 `true`。
- 默认 `workflow.remediation.mode=review` 时，修复计划和每个写动作都需要人工审批。

如果只想诊断、不执行修复，不要传 `remediate=true`。

## 2. 推荐方式：交互式终端审批

在终端里运行：

```bash
cd /root/huhu/agent/combine-aiops-mcp/robusta && .venv/bin/python tools/aiops_remediate_chat.py --url http://10.2.0.48:30800 "我的集群有什么问题？"
```

运行后会持续输出诊断和修复过程。遇到审批点时会出现：

```text
[remediation] 输入 approve 同意，输入 reject 拒绝。
remediation [approve/reject]:
```

输入：

```text
approve
```

表示同意当前修复计划或当前修复动作。输入：

```text
reject
```

表示拒绝，修复流程会停止。

这个客户端做了两件事：

- 保持 `/ask?stream=true&remediate=true` 的输出流，用于展示诊断和修复过程。
- 监听终端输入，自动把 `approve/reject` 转成 `POST /remediation/approve` 请求。

## 3. 原始方式：curl 流 + 手动审批接口

如果不用交互式客户端，可以直接用原始接口。

### 3.1 启动诊断和修复流

```bash
curl --no-buffer \
  -H "Accept: text/event-stream" \
  -G "http://10.2.0.48:30800/ask" \
  --data-urlencode "q=我的集群有什么问题？" \
  --data-urlencode "stream=true" \
  --data-urlencode "remediate=true" \
  --data-urlencode "format=text"
```

当流程进入人工审批时，输出中会出现类似内容：

```text
======================================================================
🛠️ 修复审批中断
======================================================================
审批类型: plan
审批 ID: f22c9bb078a9
标题: 是否认可诊断报告中的修复方案
请调用:
curl -X POST http://<host>/remediation/approve -d run_id=9b7bf0e3d69d4991 -d approval_id=f22c9bb078a9 -d approved=true
```

这里的关键字段是：

- `run_id`: 本次诊断运行 ID，也可以理解为本次修复审批会话 ID。
- `approval_id`: 当前审批请求 ID。每次 plan/action 审批都会生成新的 `approval_id`。
- `approved`: `true` 表示同意，`false` 表示拒绝。

### 3.2 同意审批

把输出里的 `run_id` 和 `approval_id` 填入审批接口：

```bash
curl -X POST "http://10.2.0.48:30800/remediation/approve" \
  -d run_id=9b7bf0e3d69d4991 \
  -d approval_id=f22c9bb078a9 \
  -d approved=true \
  -d reviewer=operator
```

成功返回：

```json
{"success":true,"run_id":"9b7bf0e3d69d4991","approval_id":"f22c9bb078a9","approved":true}
```

### 3.3 拒绝审批

```bash
curl -X POST "http://10.2.0.48:30800/remediation/approve" \
  -d run_id=9b7bf0e3d69d4991 \
  -d approval_id=f22c9bb078a9 \
  -d approved=false \
  -d reviewer=operator \
  -d reason="修复方案不符合预期"
```

拒绝后当前修复流程会停止，输出 `remediation_finished`，状态通常为 `rejected`。

## 4. 为什么普通 curl 里直接输入 approve 不生效

普通 `curl --no-buffer /ask` 是单向输出流：

```text
后端诊断输出 -> curl -> 终端显示
```

你在终端里输入的 `approve` 只是写到了当前终端，不会自动变成 HTTP 请求发给后端。后端真正等待的是：

```text
POST /remediation/approve
```

因此原始 curl 模式下必须手动调用审批接口；如果想在同一个终端直接输入 `approve/reject`，请使用 `tools/aiops_remediate_chat.py`。

## 5. 审批阶段

修复流程通常至少有两个审批点：

| 审批类型 | 说明 | 是否需要审批 |
|----------|------|--------------|
| `plan` | 是否认可诊断报告中的整体修复方案 | `review` 模式需要 |
| `action` | 是否执行某一个具体写操作 | `review` 模式需要，每个写动作一次 |

示例流程：

```text
诊断完成
-> 输出结构化修复计划
-> plan 审批
-> action-1 审批
-> dry-run
-> execute
-> verify
-> 如还有动作，继续 action-2 审批
-> 修复流程结束
```

## 6. 注意事项

- 每个 `approval_id` 只对应当前这一次审批，不要复用旧的 `approval_id`。
- 如果出现新的 `action` 审批，需要再次同意或拒绝。
- 审批有超时时间，默认由 `workflow.remediation.approval_timeout_seconds` 控制。
- `approve` 只表示“同意执行当前计划或动作”，不保证诊断修复方案一定正确。
- 如果报告里的修复方案不合理，应输入 `reject` 或调用 `approved=false`，不要盲目同意。
- 修复动作会先执行 `dry_run_command`，成功后再执行 `execute_command`，最后执行 `verify_command`。

## 7. 实现架构

修复能力没有侵入原有诊断链路。原有工作流仍然先完成：

```text
layer -> evidence -> rca -> conclusion
```

只有在请求显式传入 `remediate=true`，并且后端配置 `workflow.remediation.enabled=true` 时，才会在 `conclusion` 之后追加修复执行阶段：

```text
诊断报告
  -> 从报告中解析结构化修复计划
  -> 根据配置选择 deterministic executor 或 react agent executor
  -> plan 审批
  -> action 审批
  -> kubectl dry-run / execute / verify
  -> 输出 remediation_finished
```

核心实现文件：

| 文件 | 职责 |
|------|------|
| `app/core/workflow/executor.py` | 在诊断完成后读取 `workflow.remediation` 配置，解析修复计划并选择执行器。 |
| `app/core/remediation/models.py` | 定义 `RemediationPlan`、`RemediationAction`、`RemediationRuntimeConfig`。 |
| `app/core/remediation/plans.py` | 从 Markdown 诊断报告中提取 JSON 修复计划，并做命令安全校验。 |
| `app/core/remediation/executor.py` | deterministic 固定计划执行器。 |
| `app/core/remediation/agent.py` | react/LLM 修复执行 Agent。 |
| `app/core/remediation/approval.py` | 内存态人工审批存储和等待机制。 |
| `app/api/routes.py` | 暴露 `/remediation/approve` 审批接口。 |
| `app/core/service.py` | 把修复事件渲染成终端可读的流式文本。 |
| `tools/aiops_remediate_chat.py` | 交互式终端客户端，把用户输入的 `approve/reject` 转成审批接口请求。 |

## 8. 结构化修复计划

修复执行不直接消费自然语言段落，而是从最终诊断报告里提取 `结构化修复计划` JSON。这个 JSON 通常由 conclusion 提示词生成，形态如下：

```json
{
  "remediation_available": true,
  "fix_type": "patch_workload_resources",
  "risk_level": "low",
  "requires_human_approval": true,
  "issue_groups": [
    {
      "group_id": "g1",
      "problem_type": "OOMKilled",
      "target": "aiops-e2e/Deployment/memhog",
      "auto_fixable": true,
      "strategy": "为工作负载设置合理资源限制"
    }
  ],
  "basis": [
    "kubectl describe 显示 OOMKilled / exit code 137",
    "kubectl get yaml 显示 memory limit 未设置"
  ],
  "actions": [
    {
      "id": "a1",
      "type": "kubectl_set",
      "group_id": "g1",
      "description": "为 Deployment 设置内存限制",
      "risk": "low",
      "dry_run_command": "kubectl set resources deployment/memhog -n aiops-e2e --limits=memory=512Mi --dry-run=server",
      "execute_command": "kubectl set resources deployment/memhog -n aiops-e2e --limits=memory=512Mi",
      "verify_command": "kubectl rollout status deployment/memhog -n aiops-e2e"
    }
  ],
  "stop_conditions": ["用户不认可修复方案", "dry-run 失败", "验证仍异常"]
}
```

解析过程在 `app/core/remediation/plans.py` 中完成：

- 先扫描 Markdown 里的 JSON fenced block。
- 支持直接 `{...}` 或 `{ "remediation_plan": {...} }` 两种形态。
- 转换成内部 `RemediationPlan` 和 `RemediationAction`。
- 如果存在多个 `issue_groups`，所有 `auto_fixable=true` 的 group 必须有对应 action。
- 每个 action 的命令都会做安全校验。

当前只允许 `kubectl` 命令，允许的动词包括：

```text
apply, create, delete, describe, get, logs, patch, rollout, scale, set, top
```

命令中禁止 shell 元字符，例如：

```text
; & | ` $ < >
```

这个限制是为了避免 LLM 生成任意 shell 命令。修复模块只允许执行可审计的 `kubectl` 单命令。

## 9. 两种执行器

### 9.1 deterministic 执行器

`RemediationExecutor` 是固定计划执行器。它不再询问 LLM 下一步，只按报告里的 `actions` 顺序执行：

```text
plan approval
  -> action approval
  -> dry_run_command
  -> execute_command
  -> verify_command
  -> 下一个 action
```

特点：

- 行为可预测，适合简单、确定的资源修复。
- 每个写动作前都可以人工审批。
- `verify_command` 输出中如果仍包含 `OOMKilled`、`CrashLoopBackOff`、`ImagePullBackOff`、`BackOff`、`0/1` 等异常标记，会返回 `needs_followup`。
- 如果所有 action 都执行并验证通过，返回 `success`。

### 9.2 react/LLM Agent 执行器

`RemediationAgentExecutor` 是当前更灵活的修复执行器。它把报告中的计划当作初始约束和参考，然后多轮读取真实工具结果，由 LLM 决定下一步。

循环结构：

```text
plan approval
  -> iteration 1:
       LLM 读取 report + remediation_plan + observations
       LLM 输出 AgentDecision JSON
       如为写命令，先 action approval
       执行 dry_run / command / verify
       记录 observation
  -> iteration 2:
       LLM 基于新 observation 决定继续验证、继续修复或结束
  -> finish success/failed/timeout
```

Agent 每一轮必须输出 JSON：

```json
{
  "decision": "run_command",
  "description": "本轮动作说明",
  "dry_run_command": "kubectl ... --dry-run=server",
  "command": "kubectl ...",
  "verify_command": "kubectl get/describe/rollout status ...",
  "risk": "low",
  "status": "",
  "reason": "为什么执行这个动作"
}
```

或者结束：

```json
{
  "decision": "finish",
  "description": "结束修复",
  "status": "success",
  "reason": "所有计划动作已验证成功"
}
```

Agent 的输入包含：

- `remediation_plan`: 结构化修复计划，包括 `issue_groups`、`basis`、`actions`。
- `report`: 最终诊断报告的尾部内容，最多保留约 8000 字符。
- `observations`: 最近几次真实命令执行结果。
- `iteration`: 当前轮次。
- `limits`: 最大轮次和最大写动作数。

Agent 不是无限自治执行。它受到几层约束：

| 约束 | 说明 |
|------|------|
| `max_iterations` | 最多思考/观察轮数，超过后失败退出。 |
| `max_write_actions` | 最多允许多少个写动作，防止重复 patch 或误操作扩大。 |
| `max_duration_seconds` | 修复阶段总耗时上限。 |
| `verify_settle_seconds` | 写动作后等待一段时间再验证，给 Deployment/Pod 重建留时间。 |
| 命令白名单 | 只能执行安全校验通过的 `kubectl` 单命令。 |
| 人工审批 | `review` 模式下 plan 和每个写动作都必须审批。 |

## 10. Agent 如何判断成功

Agent 不能只因为命令返回 0 就宣称成功。实现里有独立的终态验证逻辑：

- 如果 `verify_command` 是 `kubectl rollout status`，必须看到 `successfully rolled out`。
- 如果 `verify_command` 是 `kubectl get`，需要看到健康信号，例如 `Running` 且 `1/1` 或 `2/2`。
- 如果验证结果仍包含 `OOMKilled`、`CrashLoopBackOff`、`ImagePullBackOff`、`BackOff`、`Error`、`0/1` 等标记，不能成功。
- 如果是删除 finalizer/删除对象类修复，`kubectl get` 返回 `NotFound` 可以被视为成功，但只在命令和意图里包含 `finalizer/delete/terminating/删除/清理` 等语义时成立。
- 多异常组场景下，不能因为某一个 group 修好就提前成功。所有 `auto_fixable=true` 的 `issue_groups` 都必须被 action 覆盖并验证完成。

这也是为什么有些真实测试里设置了环境变量后，Pod 仍然 `CrashLoopBackOff` 时，修复会返回 `failed`。配置动作成功不等于业务恢复成功。

## 11. 审批中断是怎么实现的

审批不是 LangGraph 原生 `interrupt` 的直接终端输入，而是后端事件 + 审批 API 的组合。

后端执行到审批点时：

1. `ApprovalStore.create_request()` 创建 `(run_id, approval_id)`。
2. workflow stream 输出 `remediation_approval_required` 事件。
3. `app/core/service.py` 把事件渲染成终端文本和 curl 提示。
4. 执行器调用 `ApprovalStore.wait_for_decision()` 阻塞等待。
5. 用户或前端调用 `POST /remediation/approve`。
6. API 调用 `ApprovalStore.resolve()` 写入审批结果并唤醒等待线程。
7. 执行器继续或停止。

简化时序：

```text
RemediationExecutor/Agent
  -> create_request(run_id, approval_id)
  -> yield remediation_approval_required
  -> wait_for_decision()

operator/frontend
  -> POST /remediation/approve
  -> approval_store.resolve()

RemediationExecutor/Agent
  -> 收到 approved/rejected
  -> 继续执行或结束
```

`ApprovalStore` 当前是进程内内存态实现，适合单实例运行。后续如果要多副本部署，需要把它替换成 Redis、数据库或工作流持久化存储，否则不同副本之间无法共享审批状态。

## 12. 终端 approve 为什么需要客户端

普通 `curl --no-buffer /ask` 只能接收服务端输出，不能把你在终端输入的 `approve` 自动发送回后端。因此终端交互审批由 `tools/aiops_remediate_chat.py` 实现：

```text
启动 /ask?stream=true&remediate=true
  -> 持续打印服务端输出
  -> 从输出中解析 run_id 和 approval_id
  -> 等待用户输入 approve/reject
  -> 自动 POST /remediation/approve
  -> 继续打印后续输出
```

这个脚本本质上是一个轻量 CLI agent wrapper，不改变后端协议，只是把“复制 curl 审批命令”自动化。

## 13. 配置项含义

当前配置位于 `deploy/configmap/config.yaml` 的 `workflow.remediation`：

```yaml
remediation:
  enabled: true
  executor: react
  mode: review
  approval_timeout_seconds: 600
  max_iterations: 10
  max_write_actions: 10
  max_duration_seconds: 900
  verify_settle_seconds: 5
```

字段说明：

| 字段 | 含义 |
|------|------|
| `enabled` | 后端是否允许修复阶段。请求仍需传 `remediate=true` 才会执行。 |
| `executor` | `deterministic` 固定执行计划；`react` 使用 LLM 多轮观察和决策。 |
| `mode` | `review` 每个计划/写动作都要人工审批；`auto` 不审批直接执行。 |
| `approval_timeout_seconds` | 每个审批点等待多久，超时后修复结束为 `timeout`。 |
| `max_iterations` | react agent 最多进行多少轮 LLM 决策。 |
| `max_write_actions` | react agent 最多执行多少个写操作。读操作不计入。 |
| `max_duration_seconds` | react agent 总耗时上限。 |
| `verify_settle_seconds` | 执行写动作后，验证前等待多少秒。 |

建议生产或共享集群保持：

```yaml
mode: review
executor: react
```

只有在 E2E 测试或一次性实验环境中，才考虑：

```yaml
mode: auto
```

## 14. 当前设计边界

当前修复模块适合资源配置类、工作负载级别的低风险操作，例如：

- `kubectl set resources`
- `kubectl set env`
- `kubectl patch deployment/statefulset`
- `kubectl rollout status`
- 清理测试对象或 finalizer 类场景

不建议自动执行：

- 节点网络、iptables、CNI、宿主机路由修复。
- PV/PVC 数据面破坏性操作。
- 生产业务镜像、启动参数、Secret 敏感配置的高风险变更。
- 诊断报告置信度低或证据链不完整的场景。

如果报告中的 `remediation_available=false` 或 `fix_type=manual_only`，修复阶段会跳过或由 Agent 返回 `failed/manual`，不应强行执行命令。
