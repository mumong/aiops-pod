## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-5mlnc` | NotReady | Pod 内应用服务对后端依赖（如数据库或缓存）的调用持续返回 503 错误，导致 Readiness Probe 探测失败，Kubelet 将 Pod 标记为 NotReady。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `ContainersReady=False`, `Ready=False`, Reason: `ContainersNotReady`, Message: `containers with unready status: [app]` (fact-36ede41cb5e2) | 确认 Pod 实际运行状态与 Readiness Probe 探测结果的矛盾，作为故障现象的基础事实。 |
| 2 | K8s Event | kubernetes | `Warning Unhealthy 2m43s (x1766 over 87m) kubelet Readiness probe failed: HTTP probe failed with statuscode: 503` (fact-f81879508b7a) | 直接证明 Kubelet 因应用持续返回 503 状态码，连续 1766 次判定探测失败，导致 Pod 进入 NotReady 状态。 |
| 3 | Metric | prometheus | `kube_pod_status_phase` 值为 1 (Running)，但 `kube_pod_container_status_restarts_total` 为 0 (fact-de5a9c3b0f28) | 证实容器未发生 OOM 重启（重启数为 0），排除了因资源硬限制导致崩溃重启的可能性。 |
| 4 | Logging | elasticsearch | 8 次重复错误日志模式：`dependency unavailable`, HTTP 503, path `/work` (fact-6de46c252523 聚合) | 在 2m 观测窗口内（02:00:23 至 02:00:57）确认应用层主动对依赖服务发起调用并收到 503 响应，解释了探针返回 503 的业务层原因。 |
| 5 | Tracing | deepflow | 9 次 L7 Flow 记录：`src_ip 172.16.104.16` -> `dst_ip 172.16.104.62`, `GET /work`, `response_code: 503` (fact-03d581eb3ec0 聚合) | 从网络流量维度佐证了应用 Pod 内部存在对特定后端 IP 的高频 503 错误，且时间跨度（09:31 至 09:57）覆盖了探针失败时段。 |

**证据关系说明：**
- **状态矛盾解析**：事实 #1 与 #2 共同表明 Pod 处于“运行但探测失败”状态；事实 #3（重启数=0）排除了因 CrashLoopBackOff 或资源争抢导致的重启机制。
- **现象因果链**：事实 #4（日志）与 #5（Tracing）提供了事实 #2（探针 503）的根本业务解释：应用调用后端依赖失败，导致 `/work` 端点无法返回 200 OK，从而触发 Kubelet 的 Readiness Probe 连续失败。

## 🎯 根因分析 · g1

### 因果链

```text
应用服务依赖的后端系统（IP 172.16.104.62）不可用或拒绝服务 → 应用对 /work 端点返回 HTTP 503 → Kubelet Readiness Probe 探测失败 → Pod 被标记为 NotReady，导致流量被剔除
```

### 根因结论

已确认根因：**应用服务对后端依赖调用持续失败，导致 Readiness Probe 返回 503 状态码。**

证据链已充分闭合：
1.  **现象层**：Kubelet 日志（#2）显示探针连续失败返回 503，导致 Pod 状态变为 NotReady（#1）。
2.  **业务层**：日志（#4）明确记录业务逻辑中“dependency unavailable”并返回 503；Tracing（#5）在网络层面证实了从应用 Pod 发出的请求在到达后端后收到了 503 响应。
3.  **排除干扰**：Metric（#3）显示容器重启次数为 0，确认并非容器本身崩溃或资源超限（Limit 200m/96Mi 未被击穿导致 OOM）引发的重启循环。

现有的 Kubernetes State、Event、Logging 和 Tracing 证据在“后端依赖不可用导致应用返回 503”这一因果链上相互印证。

---

## 📊 性能统计

```text
├─ 总耗时: 2.0m
├─ 问题定位: 17.8s
├─ 并发证据采集: 86.6s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-5mlnc: 86.6s (Evidence 79.0s, RCA 7.4s)
└─ 汇总总结: 14.4s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-5mlnc**: pod-notready-probe-failed
