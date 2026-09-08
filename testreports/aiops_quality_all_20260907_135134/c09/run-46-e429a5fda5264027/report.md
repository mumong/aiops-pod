## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-7b77l` | NotReady | 后端依赖服务不可用导致应用持续返回 HTTP 503，致使 Readiness Probe 连续失败 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `aiops-case-09/workload-5f4fb9ff45-7b77l` 状态 `Running`，但 `ContainersReady` 和 `Ready` 均为 `False`，原因 `ContainersNotReady` | 定义故障现象：Pod 存活但服务不可见 |
| 2 | K8s Event | Kubernetes | `Warning Unhealthy Readiness probe failed: HTTP probe failed with statuscode: 503` (重复 2079 次) | 确认可观测症状：应用持续拒绝健康检查流量 |
| 3 | Logging | Elasticsearch | 聚合日志显示应用层报错 `dependency unavailable`，`http_status: 503`，`path: /work` (12条，20:37-20:38) | 提供应用内部视角的根因线索：后端依赖失败 |
| 4 | Tracing | Deepflow | L7 Flow 聚合：对端 IP `172.16.104.35` 的 GET `/work` 请求返回 `503` (9次，耗时 12-20ms) | 验证外部流量访问时的实际返回状态与日志一致 |
| 5 | K8s Config | Kubernetes | 资源限制 `memory_limit: 96Mi`，`cpu_limit: 200m`；资源请求 `memory_request: 24Mi`，`cpu_request: 20m` | 排除 OOMKilled 或 CPU 限制导致的崩溃重启 |
| 6 | Metric | Prometheus | `kube_pod_container_status_restarts_total = 0` | 佐证应用非资源耗尽导致的崩溃重启 |

**证据分析：**
Kubernetes 层面确认 Pod 存活但 Readiness Probe 持续失败（#1, #2）。追踪（#4）与日志（#3）相互印证，证明应用进程正在运行且接收到了流量，但处理业务请求（GET /work）时因“后端依赖不可用”返回了 HTTP 503。由于 Readiness Probe 依赖于该 HTTP 端口的健康响应，持续返回 503 直接导致 Probe 失败。资源监控显示无重启且资源限制充足（#5, #6），排除了容器级故障。

## 🎯 根因分析 · g1

### 因果链

```text
后端依赖服务不可用 → 应用业务逻辑返回 HTTP 503 → Readiness Probe 检测失败 → Pod 状态标记为 NotReady
```

### 根因结论

**已确认根因：** 后端依赖服务不可用。

**分析：**
应用进程正在运行（#1, #6），但其处理 `/work` 请求时因依赖缺失返回 `HTTP 503`（#3, #4）。集群的 Readiness Probe 机制配置为检测该 HTTP 端口的健康状态，持续返回 `503` 导致探针判定应用不健康（#2），进而将 Pod 状态置为 `NotReady`（#1），对外屏蔽流量。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 19.3s
├─ 并发证据采集: 69.3s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-7b77l: 69.3s (Evidence 61.8s, RCA 7.3s)
└─ 汇总总结: 10.5s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-7b77l**: pod-notready-probe-failed
