## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-5mlnc` | NotReady | Pod `aiops-case-09/workload-5f4fb9ff45-5mlnc` 状态为 NotReady |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s | `ContainersReady=False`, `Ready=False`, `ContainersNotReady` (fact-346c09ca731b) | 确证应用容器进程存在，但未能通过就绪检查 |
| 2 | K8s Event | K8s | `Readiness probe failed: HTTP probe failed with statuscode: 503` (fact-db94cc7cee73) | 明确探针因应用返回 503 状态码而连续失败 |
| 3 | K8s Event | K8s | `Readiness probe failed: Get "http://172.16.104.16:8080/ready": dial tcp 172.16.104.16:8080: connect: connection refused` (fact-fb088f05185a) | 补充探针在不同时间点的连接被拒状态，反映应用服务不稳定 |
| 4 | K8s Config | K8s | Container `app` CPU Request 20m, Limit 200m; Memory Request 24Mi, Limit 96Mi (fact-02c6e9cc2a39, fact-85e416e8ce2d) | 排除资源硬性限制或突发过载，故障非由资源配额瓶颈引起 |
| 5 | Logging | ELK | Pattern `dependency unavailable` (HTTP 503, Path `/work`) 连续出现 8 次 (fact-1aafdf0090a7) | 确认应用在 `/work` 路径下因依赖不可用主动向请求方返回 503 |
| 6 | Tracing | Tempo | Span `GET /work` 返回 `http.response.status_code: 503`，状态标记为 `readiness_fail` (fact-0485543e9ed5) | 链路追踪直接定位到应用服务逻辑层在就绪请求中返回错误 |
| 7 | Tracing | Deepflow | L7 Flow 11 次请求至 `172.16.104.16:8080` 均返回 `response_code: 503`，持续时间 12ms-99ms (fact-4b74c185e7f4) | 外部流量验证了应用服务持续不可用，且具备明确的服务响应 |

**证据综合：**
Kubernetes 事件证实就绪探针（读/写路径）在 8080 端口遭遇 `503` 状态码与 `Connection Refused`（证据 2、3、7），导致 Pod `Ready` 状态变更为 `False`（证据 1）。应用日志明确指出 `/work` 路径返回 503 的原因为 `dependency unavailable`（证据 5），Tempo 链路与 Deepflow L7 流量数据一致佐证了应用层主动拒绝请求（证据 6、7）。资源配置显示无瓶颈（证据 4），结合 `restart_count=0`，故障定性为应用内部逻辑或依赖故障而非容器重启。

## 🎯 根因分析 · g1

### 因果链
```text
应用内部依赖不可用 (dependency unavailable) → 应用服务进程无法处理 HTTP 请求 → 容器返回 HTTP 503 状态码或拒绝连接 → Pod Readiness Probe 连续失败并剔除服务流量
```

### 根因结论
已确认根因为应用内部逻辑异常或其依赖组件不可用。
证据显示应用进程正在运行（Pod 状态 Running），但应用服务（监听在 `172.16.104.16:8080`）在处理就绪探针探测请求及正常业务请求（`/work` 路径）时，持续返回 HTTP 503 状态码，并伴有日志 `dependency unavailable`（证据 5、6、7）。Kubelet 的 Readiness Probe 因连续检测到 503 及偶发的 `connection refused`（证据 2、3），判定容器未就绪，从而将 Pod 的 `Ready` 条件置为 `False`（证据 1）。这导致该 Pod 被 Kubernetes 服务模型剔除，不再接收外部流量。故障并非由资源限制或 Pod 启动失败引起，而是应用层面的功能性服务中断。

---

## 📊 性能统计

```text
├─ 总耗时: 2.3m
├─ 问题定位: 20.3s
├─ 并发证据采集: 105.9s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-5mlnc: 105.9s (Evidence 94.8s, RCA 11.0s)
└─ 汇总总结: 14.5s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-5mlnc**: pod-notready-probe-failed
