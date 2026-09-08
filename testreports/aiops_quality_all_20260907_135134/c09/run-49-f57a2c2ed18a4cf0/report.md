## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-7b77l` | NotReady | 应用服务因依赖不可用（dependency unavailable）持续返回 HTTP 503 错误，导致 Readiness Probe 失败，进而引发 Pod 处于 NotReady 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `Pod aiops-case-09/workload-5f4fb9ff45-7b77l` 状态 `Running`，`Ready` 条件为 `False` (`ContainersNotReady: [app]`) | 确认应用运行但健康检查失败的事实 |
| 2 | K8s Event | kubernetes | `Warning Unhealthy 91s (x2391 over 116m) kubelet Readiness probe failed: HTTP probe failed with statuscode: 503` | 提供故障持续时间和频率的直接观测证据 |
| 3 | Metric | prometheus | `kube_pod_container_status_restarts_total` 当前值 `0` | 排除应用崩溃重启导致的启动失败，确认服务处于假死状态 |
| 4 | Logging | elasticsearch | 日志模式 `dependency unavailable, http_status: 503` 在 `2026-09-07T20:50:59.562Z` 至 `2026-09-07T20:51:35.720Z` 窗口内出现 8 次，`numeric_fields` 显示内存分配为 `0` | 确认应用自身逻辑返回 503 的根本原因是依赖不可用 |
| 5 | Tracing | deepflow | 聚合等效 L7 Flow：`HTTP GET /work` 从 `172.16.104.55` 到 Pod IP `172.16.104.35`，响应码 `503`，持续 25 分钟 | 从网络层验证健康检查请求与响应结果，关联 Pod 与 Probe 的因果关系 |

证据印证：应用进程未重启（Metric 0次）且处于运行状态（K8s State），但健康检查接口 `/work` 持续返回 503（Logging & Tracing），触发 kubelet 连续失败报警（K8s Event），最终导致 Pod 失去 Ready 状态。各维度事实相互闭合，确认故障源于应用层依赖问题而非基础设施或容器生命周期故障。

## 🎯 根因分析 · g1

```text
应用服务依赖不可用 → 应用向 /work 返回 HTTP 503 → kubelet Readiness Probe 持续失败 (2391次) → Pod NotReady
```

### 根因结论
已确认根因为：**应用服务依赖不可用（dependency unavailable）**。
该故障导致 `/work` 接口持续返回 `HTTP 503`（日志与流量证据），进而致使 `kubelet` 的 `Readiness Probe` 检测失败（K8s Event 证据，共 2391 次），最终导致 Pod 状态变为 `NotReady`。现有证据链（日志模式、K8s 事件、网络流量）完整闭合，确认应用自身健康逻辑被下游依赖阻断是引发当前异常的根本原因。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 15.4s
├─ 并发证据采集: 85.6s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-7b77l: 85.6s (Evidence 78.2s, RCA 7.0s)
└─ 汇总总结: 10.3s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-7b77l**: pod-notready-probe-failed
