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

- `mode`：
  - `read`：只允许只读操作（get、describe、logs、events、top、api-resources、explain、rollout history、auth can-i），使用 reader SA；写操作的批量规则（如 `-A`）不适用于读。
  - `exec`：`kubectl exec` 的非交互调用；`write`：其他写操作（如 `kubectl run`、`delete pod`）。两者都使用 writer SA，并按中心同一套命令规则检查：没有 `approval_id` 时需人工审批的命令被拒绝（rule `approval_required`），黑名单命令始终被拒绝。
  - 声明的 mode 必须与命令实际类型一致，否则 `403 mode_denied`。
- `compress`：可选，见"限制"。
- `timeout_s` ≤ 15。
- 拒绝（`403 mode_denied`）：`logs -f`、`-w/--watch`、`-i/-t`、`port-forward`、`proxy`、`attach`、`cp`、`edit`、`wait`、`debug`、`diff`、`rollout status`、`-f/-k` 本地文件，以及 `--kubeconfig`、`--context`、`--server`、`--token`、`--as` 等身份参数。

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

- 单个响应 stdout + stderr 原始大小 ≤ 4MB（`RUNNER_MAX_OUTPUT_BYTES`），超出截断并设置 `truncated=true`。
- 请求带 `"compress": true` 时，响应用 `encoding: "gzip+base64"` 与 `stdout_b64`、`stderr_b64` 代替 `stdout`、`stderr`（JSON 列表通常缩小到约十分之一）。
- 任务记录保留 24 小时，保存在内存和 emptyDir。
