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
