# Contract: aiops-edge-runner HTTP API（v1）

中心经 xnet 隧道调用：`https://xnet-management.xnet.svc:9090/proxy?clientid=<UUID>&address=<URL 编码的 http://aiops-edge-runner.aiops.svc:8090/...>`。

## 认证（所有接口，除 /healthz）

| 请求头 | 内容 |
|---|---|
| `X-AIOps-Timestamp` | Unix 秒 |
| `X-AIOps-Nonce` | 随机 16 字节，十六进制 |
| `X-AIOps-Signature` | `hex(HMAC-SHA256(key, timestamp + "\n" + nonce + "\n" + method + "\n" + path + "\n" + sha256(body)))` |

时间偏差超过 60 秒、nonce 在 5 分钟内重复、签名不匹配 → `401 {"error": "runner_auth_failed", "reason": "..."}`。

## GET /healthz

`200 {"version": "1.0.0", "api": 1, "policy_version": "<hash>", "capabilities": ["read", "exec", "jobs"]}`

## POST /v1/kubectl

请求：

```json
{"argv": ["kubectl", "get", "pods", "-A", "-o", "json"], "mode": "read", "timeout_s": 15}
```

- `mode`：`read`（只允许 get、describe、logs、events、top、api-resources、explain，使用 reader SA）或 `exec`（`kubectl exec` 的非交互调用，使用 writer SA，按命令规则检查；需要审批的命令必须带 `approval_id`）。
- `timeout_s` ≤ 15。
- 拒绝：`-f/--follow`、`-w/--watch`、`-i/-t`、`port-forward`、`proxy`、`attach`。

响应 `200`：

```json
{"exit_code": 0, "stdout": "...", "stderr": "", "truncated": false, "duration_ms": 312}
```

拒绝 `403`：`{"error": "policy_denied", "rule": "denied_executables", "command": "..."}`；`mode` 不允许 → `{"error": "mode_denied"}`。

## POST /v1/jobs

```json
{"idempotency_key": "<repair_job_id>:<action_index>", "argv": ["kubectl", "..."], "approval_id": "b8f563d97f52", "timeout_s": 300}
```

- 立即返回 `202 {"job_id": "...", "status": "running"}`；同一个 `idempotency_key` 返回同一个 `job_id`，不重复执行。
- 规则检查在提交时进行，拒绝返回 `403`（同上）。

## GET /v1/jobs/{job_id}

`200 {"job_id": "...", "status": "running|succeeded|failed", "exit_code": 0, "stdout": "...", "stderr": "", "truncated": false, "started_at": "...", "finished_at": "..."}`；不存在 → `404`。

## 限制

- 单个响应 stdout + stderr ≤ 256KB，超出截断并设置 `truncated=true`。
- 任务记录保留 24 小时，保存在内存和 emptyDir。
