## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-cfzz6` | NotReady | Pod aiops-case-09/workload-5f4fb9ff45-cfzz6 NotReady |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning Unhealthy 2m10s (x2078 over 102m) kubelet Readiness probe failed: HTTP probe failed with statuscode: 503` (fact-a5db99e79e9f) | 提供直接故障现象，Kubelet 持续探测失败 |
| 2 | K8s Event | kubernetes | `cni.projectcalico.org/podIP: 172.16.104.26/32` (fact-c047e3bb5dcd) | 确认 Pod 已获分配 IP，网络层连通性基础正常 |
| 3 | Logging | elasticsearch | `dependency unavailable` (503, `/work`) 连续 8 次，`allocated_mib` 始终为 0，时间窗 `2026-09-03T19:35:04` 至 `19:35:39` (fact-787807079614 等) | 证实应用侧持续无法访问依赖，且未产生内存占用，排除因资源耗尽（OOM）导致的不可用 |
| 4 | Tracing | deepflow | `GET /work` HTTP 503 请求，`src_ip: 172.16.104.19` -> `dst_ip: 172.16.104.26`，关联 trace_id `5a23e0c80f2d1e117abdc6c429c94edd` (fact-5b0f71b7b356 等) | 跨维度关联，确认应用端点 `/work` 持续返回 503 |
| 5 | Tracing | tempo | `GET /work` 返回 503，span 属性 `aiops.observed_mode: readiness_fail`，关联 trace_id `5a23e0c80f2d1e117abdc6c429c94edd` (fact-0354564c0cbf) | 确认 Readiness Probe 触发时，应用内部同样处于依赖不可用状态 |
| 6 | Metric | prometheus | `kube_pod_status_phase{phase="Running", container="app"} = 1`，`kube_pod_container_status_restarts_total{container="app"} = 0` (fact-27dfcdcf618d 等) | 排除 CrashLoopBackOff 或容器启动阶段问题，Pod 已稳定运行但处于 NotReady 状态 |

证据链逻辑：Kubelet 的 Readiness 探测（证据 #1）通过 Pod 网络（证据 #2）访问应用端点 `/work`。Trace（证据 #4、#5）与日志（证据 #3）高度吻合，均显示应用在 19:35 左右持续返回 503 `dependency unavailable`，且无内存增长。Metric（证据 #6）排除重启故障。综合判定为应用内部依赖缺失导致探测持续失败。

## 🎯 根因分析 · g1

### 因果链

```text
Application dependency unavailable (未确认) → HTTP GET on /work returns 503 → Kubelet Readiness probe failure → Pod status NotReady (0/1)
```

### 根因结论

**已确认的根因**：应用容器 `app` 在其 Readiness Probe 探测端点（映射为 `/work` 路由）上持续返回 HTTP 503。由于探测失败且持续时间远超宽限期，Kubelet 判定 Pod 未就绪（NotReady），导致 Pod 从 Service Endpoint 中移除，用户可见服务不可用。
*   **证据支撑**：Kubelet Event (fact-a5db99e79e9f)、Logging 聚合 503 (fact-787807079614)、Tracing 聚合 503 (fact-5b0f71b7b356)。
*   **未确认项**：具体的依赖对象（如数据库、下游 API 或 Sidecar）缺失，以及导致该依赖不可用的根本原因（如配置错误、目标宕机或网络策略阻断）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 18.1s
├─ 并发证据采集: 63.7s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-cfzz6: 63.7s (Evidence 55.1s, RCA 8.4s)
└─ 汇总总结: 14.5s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-cfzz6**: pod-notready-probe-failed
