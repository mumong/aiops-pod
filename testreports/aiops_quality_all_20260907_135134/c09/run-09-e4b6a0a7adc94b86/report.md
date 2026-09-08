## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-7b77l` | NotReady | 应用依赖服务不可用导致Readiness Probe持续返回HTTP 503 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `kube_pod_status_condition` | `ContainersReady`: False (reason: ContainersNotReady); `Ready`: False (reason: ContainersNotReady) | 确定应用容器处于 NotReady 状态，直接表现 |
| 2 | K8s Event | `kubelet` | `Readiness probe failed: HTTP probe failed with statuscode: 503` | 确认 Readiness Probe 因 503 响应持续失败，阻止流量进入 |
| 3 | Logging | `elasticsearch` | `dependency unavailable` (http_status: 503, path: /work), 出现 8 次 | 从应用内部日志确认就绪接口 (/work) 被上游业务逻辑主动拦截并返回 503 |
| 4 | Tracing | `tempo` | `GET /work` span 返回 HTTP 503, 耗时 4ms (3715-3719 us) | 链路追踪验证了就绪检查请求的快速失败，排除了网络或底层服务挂死导致的高延迟超时 |
| 5 | Metric | `prometheus` | `kube_pod_container_status_restarts_total` = 0 | 确认容器重启次数为 0，排除了 CrashLoopBackOff 导致的不稳定 |
| 6 | K8s Config | `container.resources` | CPU request 20m / limit 200m; Memory request 24Mi / limit 96Mi | 资源配额设置较低，但无 OOMKilled 或 CPU Throttling 错误日志支持，非直接病因 |

**证据综合说明：**
*   状态 (E1) 确认了 Pod 不健康的结果，探针事件 (E2) 明确了原因是 Readiness Probe 收到 503。
*   日志 (E3) 与追踪 (E4) 提供了根本机制：应用进程本身存活且响应迅速（低延迟），但在检查依赖项时发现“依赖不可用”，因此主动返回 503 状态码。
*   指标 (E5) 排除了应用崩溃重启导致的不稳定，说明这是一个持续的业务逻辑状态问题。

## 🎯 根因分析 · g1

### 因果链

```text
下游依赖服务不可用 → /ready 端点业务检查失败 → Readiness Probe 持续返回 HTTP 503 → Pod 状态标记为 NotReady (无流量进入)
```

### 根因结论

**已确认的根因**：应用容器的 Readiness Probe 检测到其关键业务依赖服务不可用，导致就绪端点持续返回 `HTTP 503` 状态码。
这一机制导致 Kubernetes 认为容器未准备好 (`ContainersReady=False`)，从而不将其加入 Service 的 Endpoints，表现为应用服务不可用。

**支撑证据**：
*   **探针失败 (E2, E4)**：探针明确收到 503 响应。
*   **业务拦截 (E3)**：应用日志在 /work 路径下输出了 "dependency unavailable" 错误。
*   **存活状态 (E5)**：容器未重启，排除了基础设施层面的崩溃。

**未确认的未知项**：具体是哪一类下游依赖服务（如数据库、缓存或第三方 API）不可用，当前事实缺乏指向特定下游组件的线索。

---

## 📊 性能统计

```text
├─ 总耗时: 2.0m
├─ 问题定位: 21.4s
├─ 并发证据采集: 85.3s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-7b77l: 85.3s (Evidence 77.8s, RCA 7.3s)
└─ 汇总总结: 11.3s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-7b77l**: pod-notready-probe-failed
