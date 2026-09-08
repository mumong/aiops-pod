## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-cfzz6` | NotReady | app容器依赖不可用导致就绪探针(HTTP GET /work)持续返回503，从而触发Kubernetes未就绪条件 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod Phase | `status=Running`, `Ready=False`, `ContainersNotReady` | 确认 Pod 进程存活但未通过就绪条件 |
| 2 | K8s Event | kubelet | `Readiness probe failed: HTTP probe failed with statuscode: 503` (累计 1973 次) | 直接证据：就绪探针（针对 `/work`）持续返回 503 |
| 3 | K8s Config | Container Resource Limit | `cpu=200m`, `memory=96Mi` | 排除资源硬性限制导致的异常（且重启次数为 0） |
| 4 | Logging | ES (聚合模式) | `dependency unavailable`, `http_status=503`, `path=/work`, 窗口 `19:32:22Z` - `19:32:54Z` | 证实应用内部逻辑在接收 `/work` 请求时因依赖缺失主动拒绝 |
| 5 | Tracing | Tempo (Span) | `GET /work` → `503`, trace_id `5233b5f7056756526bbf9cc08cca7374` | 将日志中的错误与具体的 HTTP 调用链路对应 |
| 6 | Tracing | DeepFlow (L7 Flow) | `GET /work`, `response_code=503`, `dst_ip=172.16.104.26`, 窗口 `03:09:55` - `03:27:30` | 在独立的时间窗口确认该 Pod 的 `/work` 接口持续对外返回 503 |
| 7 | Metric | Prometheus | `kube_pod_container_status_restarts_total=0` (app 容器) | 证实应用运行平稳，非进程崩溃或重启循环导致 |

**证据互证情况：**
K8s 的探针事件（#2）直接验证了 Pod 状态为 NotReady 的原因。日志（#4）与 Tempo 追踪（#5）在 `trace_id=5233b5f7056756526bbf9cc08cca7374` 处形成闭环，证明了导致探针失败的请求确实是由应用因依赖不可用而返回的。DeepFlow 流量记录（#6）在后续时间段重复了相同的 503 模式，排除了偶发性错误。重启计数（#7）和资源配置（#3）排除了因资源超限导致进程不稳定的可能性。

## 🎯 根因分析 · g1

### 因果链

```text
应用依赖服务不可用（未确认具体依赖名） → 应用服务处理 /work 时返回 HTTP 503 (dependency unavailable) → 容器就绪探针（HTTP GET /work）持续接收 503 → Kubernetes 判定 Pod 未就绪 (ContainersNotReady)
```

### 根因结论

已确认根因：`aiops-case-09/workload-5f4fb9ff45-cfzz6` 的 `app` 容器内部存在未被满足的外部依赖。

证据表明，当应用尝试访问该依赖并接收请求（特别是 `/work` 路由）时，应用返回 `HTTP 503` 并记录日志 `dependency unavailable`。Kubernetes 的配置了针对 `/work` 路径的就绪探针，该探针因持续收到 503 响应而被标记为失败，进而导致 Pod 整体处于 `NotReady` 状态。

目前的证据不足以进一步定位是哪一个具体的下游依赖服务（日志仅笼统提示 `dependency unavailable`），也无法提供应用启动后无法访问该依赖的根本原因（缺乏启动前或早期的调试日志）。

---

## 📊 性能统计

```text
├─ 总耗时: 2.5m
├─ 问题定位: 16.6s
├─ 并发证据采集: 122.8s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-cfzz6: 122.8s (Evidence 114.8s, RCA 7.9s)
└─ 汇总总结: 12.8s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-cfzz6**: pod-notready-probe-failed
