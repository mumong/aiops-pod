## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-7b77l` | NotReady | Pod workload-5f4fb9ff45-7b77l 处于 NotReady 状态，Readiness Probe 失败 (HTTP 503)。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | K8s Event | `Readiness probe failed: HTTP probe failed with statuscode: 503` (fact-49a392fd9616) | 证明探针检测失败的确切原因，Kubelet 收到了 503 响应。 |
| 2 | K8s State | K8s State | `Ready` 状态为 `False`，原因 `ContainersNotReady`；`ContainersReady` 为 `False`；容器重启计数 `0` (fact-15518c02cbbb, fact-e163e04a2f76, fact-aeaf1e67812e) | 确认 Pod 处于 NotReady 状态且未发生重启，排除了因重启导致的临时不可用。 |
| 3 | Logging | Logging | 日志聚合呈现持续报错模式：`dependency unavailable`，`http_status: 503`，路径 `/work` (fact-24c56af49a20, 聚合 15 次) | 提供应用侧日志事实，证明应用业务逻辑正在主动向探针或服务端返回 503。 |
| 4 | Tracing | Tracing | Deepflow 聚合 L7 Flow 显示从 `172.16.104.55` 发往 Pod IP `172.16.104.35` 的 `GET /work` 请求持续返回 `503` (fact-180c1ddb06b3, 聚合 9 次)；Tempo Span 确认状态码 503 (fact-35d44011bae4) | 证实请求链路完整到达 Pod 并在应用层被拒绝，进一步确认是应用内部返回 503。 |
| 5 | Metric | Metric | 应用容器 CPU 总使用量为 `9.630196` seconds，仅 1 个样本 (fact-adb85a9e62ee) | 排除因 CPU 节流或资源耗尽导致应用无响应；CPU 使用量极低，与资源压力无关。 |

**证据关系说明：**
*   **现象与事实一致**：K8s Event (证据 #1) 直接记录了 503 错误，这与 Logging (证据 #3) 和 Tracing (证据 #4) 中应用返回 503 的事实完全吻合。
*   **排除资源瓶颈**：Metric (证据 #5) 显示 CPU 消耗极低，配合零重启计数 (证据 #2)，排除了 CPU 飙升或 OOM 导致应用假死的可能。
*   **结论指向**：应用进程正常运行并处理请求，但其内部业务逻辑主动返回了 503 错误。

## 🎯 根因分析 · g1

### 因果链

```text
应用容器内的业务依赖不可用 → 应用逻辑主动返回 HTTP 503 (dependency unavailable) → Kubelet Readiness Probe 获取 503 状态码 → Pod Ready 条件不满足，状态转为 NotReady
```

### 根因结论

**已确认的根因**：
应用容器 `app` 中的业务逻辑因**依赖服务不可用（dependency unavailable）**，持续向 `/work` 和探针接口返回 `HTTP 503` 错误。由于 Readiness Probe 依赖于该接口返回 `200 OK` 才能判定 Pod 健康，导致探针持续失败，Pod 最终被 K8s 调度器标记为 `NotReady`。

**支撑事实引用**：
*   应用日志明确抛出 `dependency unavailable` (证据 #3)；
*   Tracing 和 K8s Event 一致确认了 503 响应 (证据 #1, #4)；
*   非资源类问题 (证据 #5, #2)。

**未知/需进一步调查项**：
上游依赖的具体是哪个服务实例或组件不可用（现有日志未包含更深层的依赖报错细节，无法确认具体是哪个上游下游链路故障）。

---

## 📊 性能统计

```text
├─ 总耗时: 3.8m
├─ 问题定位: 17.9s
├─ 并发证据采集: 198.1s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-7b77l: 198.1s (Evidence 189.0s, RCA 9.0s)
└─ 汇总总结: 14.1s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-7b77l**: pod-notready-probe-failed
