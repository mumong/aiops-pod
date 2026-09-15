## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-5mlnc` | NotReady | Application readiness endpoint returns HTTP 503 due to unavailable dependency |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning Unhealthy ... Readiness probe failed: HTTP probe failed with statuscode: 503` (fact-a480166136f1) | 确认 Pod 探针持续失败，直接导致 Pod 状态为 NotReady。 |
| 2 | K8s State | kubernetes | `type: Ready, status: False, reason: ContainersNotReady` (fact-f45686934f18) | 证实容器处于非就绪状态，排除了容器启动失败或 CrashLoopBackOff 导致的宕机。 |
| 3 | Logging | elasticsearch | `dependency unavailable` (http_status: 503, path: /work) 出现 8 次，时间跨度 `2026-09-11T02:21:46.140Z` 至 `02:22:18.279Z` (fact-a904b1b7e81a...) | 揭示应用自身检测到依赖缺失并向上层返回 503，是探针失败的根本原因。 |
| 4 | Tracing | tempo | `http.response.status_code: 503` on `/work` (trace: 8b292fde7fac8f027de4c7c28dc7afcd) (fact-3483772c6725) | 完整记录了单次失败的 HTTP 调用链路，状态码与日志 503 完全匹配。 |
| 5 | Tracing | deepflow | HTTP GET `/work` 返回 503，`src_ip: 172.16.104.62` -> `dst_ip: 172.16.104.16` (fact-8a1f66b857c4...) | 网络层观测确认了服务内部对该端点的请求持续返回 503。 |
| 6 | Metric | prometheus | `restart_count: 0` (fact-76ab4784df1b) | 排除容器因资源超卖或 OOM 崩溃重启导致的不稳定。 |

上述证据形成了闭环：K8s 探针返回 503 (事实 1) 导致 Pod 未就绪 (事实 2)；应用日志 (事实 3) 与追踪记录 (事实 4, 5) 一致表明，该 503 是应用层因“依赖不可用”主动返回的错误，而非网络故障或容器崩溃；重启数为 0 (事实 6) 进一步印证了 Pod 运行状态稳定。

## 🎯 根因分析 · g1

### 因果链

```text
外部依赖不可用 → 应用 /work 端点主动返回 503 → K8s Readiness Probe 失败 → Pod 状态变更为 NotReady
```

### 根因结论

**根因确认**：
应用 `workload-5f4fb9ff45-5mlnc` 的 `/work` 就绪端点因**外部依赖不可用 (Dependency unavailable)**，持续返回 HTTP 503 状态码。该错误被 K8s Readiness Probe 捕获，导致 Pod 被标记为 `NotReady`，进而阻止流量路由至该 Pod。

支撑依据：
1.  **现象直接来源**：K8s 事件记录探针因 `statuscode: 503` 失败 (证据 #1)，且 Pod `Ready` 状态为 `False` (证据 #2)。
2.  **根本机制**：应用日志显示在探针探测的时间窗口内，应用记录了 `dependency unavailable` 错误并返回 503 (证据 #3)；追踪数据 `8b292fde...` 和 `deepflow` 流数据也均确认了 `/work` 端点持续返回 503 (证据 #4, #5)。
3.  **排除干扰**：Pod 未发生重启 (证据 #6)，且网络目标 IP `172.16.104.16` 与 Pod 地址一致，确认是应用内部逻辑导致，非网络连通性问题。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 11.7s
├─ 并发证据采集: 89.8s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-5mlnc: 89.8s (Evidence 82.9s, RCA 6.8s)
└─ 汇总总结: 14.1s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-5mlnc**: pod-notready-probe-failed
