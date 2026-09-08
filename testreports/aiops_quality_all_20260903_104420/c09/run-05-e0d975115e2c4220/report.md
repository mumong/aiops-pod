## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-cfzz6` | NotReady | Pod aiops-case-09/workload-5f4fb9ff45-cfzz6 处于 NotReady 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Event | `Readiness probe failed: Get "http://172.16.104.26:8080/ready": dial tcp 172.16.104.26:8080: connect: connection refused` | 揭示应用容器启动或初始化阶段未准备好，TCP 端口无可连接监听。 |
| 2 | K8s Event | Event | `Readiness probe failed: HTTP probe failed with statuscode: 503` | 揭示应用进程已响应，但应用逻辑（HTTP 层）显式拒绝就绪请求。 |
| 3 | K8s Event | Pod Conditions | `Ready: False, ContainersNotReady, reason: containers with unready status: [app]` | 确认为容器 `app` 导致 Pod 整体处于 NotReady 状态。 |
| 4 | Logging | ES Logs | Pattern: `dependency unavailable`, `http_status: 503`, `path: /work`, occurrence: 14 (17:59:22 - 18:00:56) | 证明应用代码内部确实发生了依赖获取失败并返回 503，对应 /work 业务端点。 |
| 5 | Tracing | Tempo Spans | `GET /work` response 503, `aiops.observed_mode: readiness_fail`, trace_ids: `ea8623e7...`, `d882babe...` | 关联日志中的依赖错误到具体的 Readiness Probe 失败，确认就绪探针端点受依赖不可用影响。 |
| 6 | Tracing | Deepflow Flows | L7 Flow: `GET /work` -> 503, `src_ip: 172.16.104.19` -> `dst_ip: 172.16.104.26`, count: 11 | 提供网络侧视角的独立证据，确认流量到达了 Pod IP 并收到 503 响应。 |
| 7 | Metric | Prometheus | `kube_pod_container_status_restarts_total: 0` for container `app` | 排除因容器重启（CrashLoopBackOff）导致的短暂不可用。 |

**证据关联：**
Kubernetes 探针记录显示应用从 TCP 拒绝转变为 HTTP 503，结合 Logging 中连续出现 14 次 `dependency unavailable` 和 Tracing 中确认 `aiops.observed_mode: readiness_fail`，强证据表明应用容器已启动但受限于外部依赖不可用，导致应用层主动返回 503 拒绝服务。

## 🎯 根因分析 · g1

### 因果链

```text
下游依赖服务不可用或响应异常 → 应用逻辑无法获取必要资源/校验失败 → 应用返回 HTTP 503 (依赖不可用) → kubelet Readiness Probe 判定失败 → Pod 状态转为 NotReady
```

### 根因结论

- **已确认的根因**：应用容器 `app` 虽然已经启动，但其依赖的下游服务不可用（日志明确捕获 `dependency unavailable`）。这导致应用就绪探针（HTTP `/ready`）持续返回 `503` 状态码，被 Kubernetes 判定为不健康，从而使 Pod 保持 `NotReady` 状态。此结论得到 K8s 探针事件（事实 #1, #2）、应用层错误日志（事实 #4）和分布式追踪（事实 #5, #6）的多重印证。
- **未确认的部分**：输入事实中未明确指明是哪一个具体的下游依赖（如数据库、缓存或特定 API）不可用，也未提供该下游依赖自身的宕机或网络故障证据，仅知其状态为不可用。

---

## 📊 性能统计

```text
├─ 总耗时: 2.5m
├─ 问题定位: 18.0s
├─ 并发证据采集: 117.3s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-cfzz6: 117.3s (Evidence 106.5s, RCA 10.6s)
└─ 汇总总结: 12.8s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-cfzz6**: pod-notready-probe-failed
