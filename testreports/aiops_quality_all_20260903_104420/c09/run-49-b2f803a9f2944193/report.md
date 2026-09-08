## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-cfzz6` | NotReady | Pod NotReady: container app is in Running state but Readiness Probe failed with HTTP 503 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod `aiops-case-09/workload-5f4fb9ff45-cfzz6` 状态：`Running`，但 Ready 为 `False` | 确认 Pod 进程存活但业务入口未就绪 |
| 2 | K8s State | kubernetes | `ContainersNotReady` 原因，未就绪容器：`[app]` | 定位异常发生在 `app` 容器 |
| 3 | K8s Event | kubernetes | `Readiness probe failed: HTTP probe failed with statuscode: 503` (已发生 2701 次，持续 132 分钟) | 直接展示探针失败的确切错误 |
| 4 | Metric | prometheus | `kube_pod_container_status_restarts_total` (容器 app) 值为 0 | 确认应用进程未发生重启，排除了因崩溃重启导致的短暂不可用 |
| 5 | Logging | elasticsearch | 日志模式 `http_request` error：`dependency unavailable`，伴随 503，持续 132 分钟 (8 次聚合) | 确认业务应用层面主动返回 503，原因是依赖不可用 |
| 6 | Tracing | deepflow | L7 Flow：HTTP GET `/work` 请求，状态码 503，耗时 18630-25385μs (9 次聚合) | 从网络流量角度证实探针探测端点 `/work` 确实在持续返回 503 |

**证据分析：**
- **状态印证**：K8s 探针报告 `HTTP 503` (证据 3) 与日志 `dependency unavailable` (证据 5) 以及 Tracing 中的 `/work` 请求返回 503 (证据 6) 完全一致，证明应用本身正在运行但业务逻辑异常。
- **排除重启干扰**：指标显示重启次数为 0 (证据 4)，且 Pod 状态保持 `Running` (证据 1)，排除了容器频繁重启导致的 `CrashLoopBackOff` 场景。
- **结论指向**：所有观测均指向应用健康检查端点 `/work` 因内部依赖问题而返回 503。

## 🎯 根因分析 · g1

### 因果链

```text
应用内部依赖服务不可用 → 应用逻辑向客户端返回 HTTP 503 → K8s Readiness Probe 探测 /work 端点收到 503 响应失败 → Pod 状态变为 NotReady
```

### 根因结论

已确认的根因是：**业务应用自身存在逻辑故障或依赖缺失**。

具体表现为应用代码在健康检查接口（或业务接口 `/work`）中，由于内部某个依赖（"dependency unavailable"）不可用，主动返回了 HTTP 503 状态码。这直接导致 Kubernetes 的 Readiness Probe 探测失败，进而将 Pod 标记为 `NotReady` 状态，阻止流量转发。

**缺失的决定性事实：**
现有证据仅能确认“依赖不可用”这一抽象错误，但缺乏该依赖的具体身份信息（如是本地其他服务、数据库连接还是外部 API），因此无法进一步区分是配置错误、服务降级还是网络不通。

---

## 📊 性能统计

```text
├─ 总耗时: 2.0m
├─ 问题定位: 25.0s
├─ 并发证据采集: 80.8s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-cfzz6: 80.8s (Evidence 72.8s, RCA 7.8s)
└─ 汇总总结: 11.3s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-cfzz6**: pod-notready-probe-failed
