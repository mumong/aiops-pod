## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-sbqvc` | Running | Pod workload-79d9f8fd88-sbqvc 发生非正常退出并重启 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning Unhealthy 25s (x6 over 115s)  kubelet  Liveness probe failed: HTTP probe failed with statuscode: 500` | 直接触发容器终止的异常事件，确认探针状态为 500 |
| 2 | K8s State | kubernetes | `container.last_terminated_reason: Error` | 确认容器上次退出的状态为非正常退出 |
| 3 | K8s State | kubernetes | `container.last_exit_code: 137` | 提供进程终止的具体代码，通常对应 SIGKILL |
| 4 | K8s State | kubernetes | `container.restart_count: 2` | 确认故障导致的重复重启行为 |
| 5 | Metric | prometheus | `kube_pod_container_resource_limits(memory): 100663296 bytes` | 提供内存硬限制数值作为背景，且未检测到 OOM 相关指标 |
| 6 | Logging | elasticsearch | `pattern: {http_status: 200, path: "/work", ...} (8 times)` | 业务路径 `/work` 在崩溃前持续正常返回，与探针失败形成现象差异 |
| 7 | Tracing | tempo | `span: GET /work, status_code: 200, span_id: f92048917ca9bc53` | 确认 20:10 左右业务请求处理正常，证明应用非整体不可用 |

**证据说明**：
1. K8s 事件与状态证据（#1-#4）形成完整闭环：探针 500 触发 Kubelet Kill 动作，容器以 Exit 137 退出并触发重启，与 Metric 的 restart 计数一致。
2. Logging 与 Tracing 证据（#6-#7）与 K8s 现象存在逻辑差异：正常业务请求返回 200 与探针返回 500 并存，提示异常可能是特定于探针路径的处理逻辑崩溃，而非应用完全挂死。

## 🎯 根因分析 · g1

### 因果链

```text
应用主进程异常退出（前置原因未确认） → Liveness Probe HTTP 探测返回 500 失败 → Kubelet 执行 Container Kill (Exit Code 137) → Pod 状态变更为 Running (已恢复)
```

### 根因结论

**已确认的根因**：容器因探针探测失败被 Kubelet 强制终止。
Kubernetes Liveness Probe（探针）探测到 HTTP 状态码 500，判定容器不健康（#1），随后 Kubelet 执行 Kill 动作，导致容器以 Exit 137 状态退出并重启（#2, #3, #4）。

**未确认的部分**：
1. **Exit 137 的具体前置原因**：Exit 137 通常意味着进程收到 SIGKILL 信号，可能是因 OOMKilled 或应用内部严重错误（如 panic/segfault）。当前证据显示内存限制为 96Mi（#5），但未检测到明确的 OOM 指标，且应用此前能正常处理业务请求（#6, #7）。需查看应用层 stderr 日志或 core dump 以确认是资源耗尽导致的无响应还是代码崩溃。
2. **探针失败逻辑差异原因**：应用能正常响应 `/work` 路径（200），但探针路径返回 500。需确认探针路径（如 `/health`）的业务逻辑与主业务是否存在差异，或探针探测时应用内部状态是否已受损。

---

## 📊 性能统计

```text
├─ 总耗时: 2.8m
├─ 问题定位: 17.8s
├─ 并发证据采集: 138.5s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-sbqvc: 138.5s (Evidence 125.6s, RCA 12.7s)
└─ 汇总总结: 12.9s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-sbqvc**: pod-oomkilled
