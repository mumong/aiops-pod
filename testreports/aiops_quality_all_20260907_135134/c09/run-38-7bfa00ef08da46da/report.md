## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-7b77l` | NotReady | Pod workload-5f4fb9ff45-7b77l 处于 NotReady 状态（Phase: Running），Readiness 探针持续失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `kubernetes` | `status: Running`, `PodScheduled: True` | 确认 Pod 基础运行状态，未处于 CrashLoop 或 Pending |
| 2 | K8s Event | `kubernetes` | `Unhealthy x1558 over 76m`: `Readiness probe failed: HTTP probe failed with statuscode: 503` | 确立 Readiness 探针长期连续失败的事实 |
| 3 | K8s Config | `kubernetes` | `container: app` 资源限制 `memory: 96Mi`, `cpu: 200m` | 提供资源背景，但未触发 OOMKilled |
| 4 | K8s Event | `kubernetes` | `ContainersReady: False`, `Ready: False` (reason: `ContainersNotReady`) | 反映最终容器健康状态 |
| 5 | K8s State | `kubernetes` | `restart_count: 0` | 排除容器因 Crash/重启导致的不稳定 |
| 6 | Metric | `prometheus` | `kube_pod_container_status_restarts_total = 0`, `phase = Running` | 佐证无重启，Pod 仍在调度节点存活 |
| 7 | Logging | `elasticsearch` | Pattern: `error`, `dependency unavailable`, `http_status: 503`, `path: /work` | 直接解释 HTTP 503 的业务层成因 |
| 8 | Tracing | `deepflow` | L7 Flow: `GET /work`, `response_code: 503`, `src_ip: 172.16.104.55` -> `dst_ip: 172.16.104.35` | 证实应用端口对流量返回 503，且未展示下游调用链路（流量仅在 Pod 内部或入口层结束） |

**证据综合说明**：
- **相互印证**：Kubernetes 探针报错 HTTP 503 (#2) 与应用日志报错 `http_status: 503` (#7) 一致；Tracing 数据 #8 同样捕获到 `/work` 接口的 503 响应，确认了故障在应用服务层而非单纯的网络连通性问题。
- **关键局限**：Tracing 显示流量仅在 Pod IP 之间或入口层交互（`172.16.104.55` -> `172.16.104.35`），未观察到下游依赖调用的完整链路，因此无法直接定位是外部服务宕机还是网络策略问题。

## 🎯 根因分析 · g1

### 因果链

```text
下游依赖服务不可用（未确认具体目标） → 应用逻辑返回 HTTP 503 "dependency unavailable" → Readiness 探针连续探测失败 (503) → Pod 被标记为 NotReady
```

### 根因结论

- **已确认根因**：应用服务 `workload-5f4fb9ff45-7b77l` 的 `/work` 端点因依赖不可用（日志报错 `dependency unavailable`）而持续返回 HTTP 503 错误。这直接导致 Kubernetes Readiness 探针判定服务不健康，进而将 Pod 状态更新为 `NotReady`。
- **待补充事实**：目前证据仅能确认应用层报错，但**未能确认**具体的“依赖”是哪一个下游服务（如数据库、缓存或另一个微服务），也**未能确认**该依赖不可用的根本原因（如连接拒绝、超时或配置错误），因为 Tracing 链路在相关时间窗口内未捕获到完整的下游调用拓扑。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 16.3s
├─ 并发证据采集: 94.7s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-7b77l: 94.7s (Evidence 83.9s, RCA 10.7s)
└─ 汇总总结: 12.5s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-7b77l**: pod-notready-probe-failed
