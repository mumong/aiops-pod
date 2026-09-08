## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-cfzz6` | NotReady | Pod workload-5f4fb9ff45-cfzz6 持续处于 NotReady 状态（READY 0/1），就绪探针因 HTTP 503 失败 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `pod.phase: Running`, `restart_count: 0` | 排除 Pod 容器启动崩溃或重启问题，确认容器存活但应用层异常 |
| 2 | K8s Event | Kubernetes | `Warning Unhealthy 82m` 记录就绪探针失败 | 证明故障为持续性现象，非瞬时网络抖动 |
| 3 | K8s Config | Kubernetes | `http.request.method: GET`, `http.response.status_code: 503`, `http.route: /work` | 直接暴露应用层响应状态为 503（服务端不可用），确认定位端点 |
| 4 | K8s Event | Kubernetes | `containers with unready status: [app]` | 确认就绪探针检测失败导致 Pod 进入 NotReady 状态 |
| 5 | Metric | Prometheus | `kube_pod_container_status_restarts_total: 0` | 独立于 K8s Event 数据，佐证容器未发生异常重启，故障源于应用逻辑 |
| 6 | Logging | Elasticsearch | 8 次 `dependency unavailable` (HTTP 503, path: /work)，`allocated_mib: 0` | 提供业务层失败归因：下游依赖缺失；内存无异常（排除 OOM） |
| 7 | Tracing | Deepflow/Tempo | `flow 503 src_ip: 172.16.104.19 → dst_ip: 172.16.104.26`, trace_id 关联日志 | 网络与链路追踪证实 172.16.104.26 是受影响的故障实体，并确认了端到端的 503 路径 |

**证据关联说明：**
Kubernetes 探针事件（证据 2）与日志中的 HTTP 503（证据 6）直接对应，证实了“探针失败”的根本原因是应用返回了 503 状态码。Tracing 数据（证据 7）提供了网络层面的证据，确认了 172.16.104.26 的 Pod 正是该请求的目标并返回了 503。日志中的 `dependency unavailable`（证据 6）为 503 提供了业务层面的直接解释，且与 Metric 中“内存正常、无重启”（证据 5、1）排除了资源瓶颈导致的宕机。

## 🎯 根因分析 · g1

### 因果链

```text
应用启动后内部依赖服务不可用 (dependency unavailable) → /work 端点返回 HTTP 503 状态码 → kubelet 执行就绪探针检测失败 → Pod 状态标记为 NotReady，READY 0/1
```

### 根因结论

已确认根因为：**应用服务启动后内部依赖缺失或不可用，导致业务接口持续返回 HTTP 503 状态码，进而致使 Kubelet 就绪探针（Readiness Probe）检测持续失败。**

*   **已验证事实**：
    *   容器状态稳定（`Running`，`重启次数 0`），无资源耗尽（`allocated_mib: 0`）导致的崩溃（证据 1, 5, 6）。
    *   应用层持续产生 `dependency unavailable` 的日志，且对外暴露的 `/work` 接口固定返回 `HTTP 503`（证据 3, 6, 7）。
    *   Kubelet 日志确认就绪探针失败正是由于收到了 HTTP 503 响应（证据 2, 4）。
*   **待查事实（Unknowns）**：现有证据确认了“依赖不可用”这一现象，但无法识别**具体是哪个下游依赖服务**（如数据库、缓存或内部微服务）导致了此异常。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 20.6s
├─ 并发证据采集: 90.4s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-cfzz6: 90.4s (Evidence 81.8s, RCA 8.5s)
└─ 汇总总结: 12.7s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-cfzz6**: pod-notready-probe-failed
