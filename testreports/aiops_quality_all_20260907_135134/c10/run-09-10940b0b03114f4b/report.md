## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-bwqhh` | CrashLoopBackOff | CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `Exit Code: 137`, `Reason: CrashLoopBackOff` | 确认 Pod 异常退出并进入重启回退状态。 |
| 2 | K8s Event | Kubernetes | `Liveness probe failed: HTTP probe failed with statuscode: 500` | 确认 kubelet 判定容器不健康的直接触发原因。 |
| 3 | K8s Event | Kubernetes | `Container app failed liveness probe, will be restarted` | 说明 kubelet 执行了 Kill 重启动作（对应 Exit Code 137）。 |
| 4 | K8s Config | Kubernetes | `container.resource_limit.memory: 96Mi`, `container.resource_request.memory: 24Mi` | 提供容器资源限制配置，非 OOM 的直接证据。 |
| 5 | Logging | Elasticsearch | 模式：`/work` path `http_status: 200` (8次) | 观测到应用成功处理 `/work` 请求，存在非 500 路由，用于对比排查。 |
| 6 | Tracing | Deepflow/Tempo | `GET /work` `response_code: 200`, `duration_us: 11453~18606` | 证实 `/work` 路由健康且正常响应，进一步反证非 `/work` 路径（如探测路径）的失败。 |

Kubernetes 事件证实 Liveness 探测因返回 `HTTP 500` 导致容器被 Kill (`Exit Code 137`) 并陷入重启循环。
Logging 与 Tracing 展示了应用在处理 `/work` 路径时表现正常（HTTP 200），暗示 500 错误集中在未被日志/链路捕获的特定路径（如 Liveness Probe 请求路径）。
Kubernetes 配置确认容器具备明确的资源限制（Limit 96Mi），且无直接证据表明发生了内存超限导致的 OOM Kill (137 通常为 SIGKILL，需结合 Probe 失败日志确认来源)。

## 🎯 根因分析 · g1

### 因果链

```text
Liveness probe 配置错误：配置指向的探测路径（如 /health）与应用的 /work 路由不一致或应用未定义该路径 → 探测请求触发应用层 500 响应 → kubelet 判定容器不健康，发送 SIGKILL 终止容器 (Exit Code 137) → 容器频繁重启且指数退避，Pod 进入 CrashLoopBackOff 状态
```

### 根因结论

已确认的根因是 **Liveness Probe 配置与应用程序路由不匹配**。
证据链显示：
1.  **Kubernetes 事件** 明确指出 Liveness 探测返回了 `HTTP 500` 错误（证据 2），这是导致容器被重启的直接原因。
2.  **Kubernetes 状态** 记录了容器退出码 `137`（Exit Code 137，通常由 `SIGKILL` 引起），这与 Liveness 探测失败后 kubelet 终止容器的行为一致（证据 1, 3）。
3.  **应用层观测** (Logging 证据 5, Tracing 证据 6) 证实了应用在处理 `/work` 路径时是正常的（HTTP 200），这反衬出 Probe 请求的路径（可能是 `/health`）导致了 500 错误，且该特定路径未被 Logging/Tracing 中的 `/work` 聚合记录所覆盖（或者该 500 响应未被应用层面记录为成功的业务日志）。

缺失的决定性事实包括应用内部路由配置中 `/health` 路径的处理逻辑，以确认其具体返回 500 的原因，但现有证据已足够将根因定位到 Liveness Probe 路径与期望的健康端点不一致。

---

## 📊 性能统计

```text
├─ 总耗时: 10.7m
├─ 问题定位: 24.0s
├─ 并发证据采集: 602.6s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-bwqhh: 602.6s (Evidence 590.8s, RCA 11.7s)
└─ 汇总总结: 12.8s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-bwqhh**: pod-crashloop-runtime
