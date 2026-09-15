## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-5mlnc` | NotReady | 应用服务内部依赖缺失或不可用，导致 /work 端点返回 HTTP 503 错误，进而触发就绪探针连续失败使 Pod 处于 NotReady 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `pod.condition` (fact-23d2b557df27) | ContainersReady: False, Ready: False | 确认应用容器未就绪，Pod 处于异常状态。 |
| 2 | K8s Event | `event.message` (fact-235c344a0c1d) | Readiness probe failed: HTTP probe failed with statuscode: 503 | 证实就绪探针在 36 分钟内连续失败，触发原因与 HTTP 503 直接相关。 |
| 3 | K8s Event | `event.message` (fact-ad4058d06fe4) | Get "http://172.16.104.16:8080/ready": dial tcp 172.16.104.16:8080: connect: connection refused | 提供早期网络层故障事实，表明在探针 HTTP 503 报错前或同时存在连接被拒的情况。 |
| 4 | Metric | `kube_pod_container_status_restarts_total` (fact-57ab38bf8f0e) | app 容器重启次数: 0 | 排除因 OOMKilled 或 CrashLoopBackOff 导致的不稳定。 |
| 5 | Logging | `log.message` (fact-1516825777ac) | `dependency unavailable`, HTTP 503, path: `/work` (8 次重复) | 直接定位故障根因为应用内部逻辑报错，而非网络连通性故障。 |
| 6 | Tracing | `application_span` (fact-224c2dfe1934) | GET /work 返回 503 (tempo)；9 次 HTTP GET /work 503 流量 (Deepflow) | 从流量层面证实业务请求 `/work` 端点持续返回错误，与日志模式完全一致。 |

**证据关联说明**：
K8s 事件 (行 2, 3) 描述 Pod 层面的探针失效，但日志 (行 5) 和链路追踪 (行 6) 提供了明确的应用层诊断——`/work` 端点因 `dependency unavailable` 返回 503。结合 0 重启记录 (行 4)，证明应用进程存活但功能异常，导致探针持续失败。

## 🎯 根因分析 · g1

### 因果链

```text
应用内部依赖不可用 (dependency unavailable) → /work 端点业务逻辑拒绝服务，返回 HTTP 503 → 就绪探针连续收到 503 非 2xx 响应 → Pod 进入 NotReady 状态，无法接收外部流量
```

### 根因结论

**已确认根因**：应用服务内部逻辑依赖缺失或异常，导致 `/work` 端点返回 HTTP 503，进而使得 Kubernetes 就绪探针连续探测失败，Pod 被标记为 `NotReady`。

**证据支持**：
- 日志证据 (fact-1516825777ac) 明确记录 `dependency unavailable` 及 `http_status: 503`；
- 链路追踪 (fact-224c2dfe1934) 和流数据证实 `/work` 端点请求均返回 503；
- K8s 探针事件 (fact-235c344a0c1d) 将探针失败与 503 状态码直接挂钩。

**未确认项**：日志及探针记录中未包含 `dependency unavailable` 背后具体的缺失资源标识（如具体的数据库、缓存或下游 API 名称），无法断定是哪个特定外部组件导致应用报错。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 17.1s
├─ 并发证据采集: 77.8s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-5mlnc: 77.8s (Evidence 69.3s, RCA 8.3s)
└─ 汇总总结: 12.7s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-5mlnc**: pod-notready-probe-failed
