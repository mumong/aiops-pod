## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-5mlnc` | NotReady | Pod配置了环境变量FAILURE_MODE=readiness_fail，导致应用进程主动返回503状态码，引发Readiness Probe持续失败，使Pod处于NotReady状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod Status | `phase: Running`, `Ready: False` (`ContainersNotReady`), `restart_count: 0` | 确认应用进程存活但未就绪，排除了容器崩溃重启导致的间歇性故障。 |
| 2 | K8s Event | kubelet | `Readiness probe failed: HTTP probe failed with statuscode: 503` (连续发生1246次) | 直接揭示探针检测到的核心症状为持续的服务端拒绝。 |
| 3 | Logging | elasticsearch | `http_status: 503`, `message: "dependency unavailable"`, `path: /work`, `first: 01:33:15.530Z` | 确认应用内部返回了503，且伴随“依赖不可用”的业务错误日志。 |
| 4 | Tracing | Deepflow L7 Flow | `GET /work`, `dst_ip: 172.16.104.16` (Pod IP), `response_code: 503` (发生9次) | 证实外部请求到达Pod并成功收到503响应，排除了网络中断。 |
| 5 | Tracing | Tempo Span | `http.response.status_code: 503`, `http.route: /work`, `aiops.observed_mode: readiness_fail` | 提供应用端观察到的模式标识，将业务逻辑错误直接关联到探针响应。 |

**证据关系说明：**
1. **应用侧与探针侧一致**：日志（#3）与 Trace（#4）确认应用本身主动返回了503状态码（`/work` 端点）；Kubelet 事件（#2）确认探针正是针对该503状态判定失败，二者互为因果印证。
2. **进程存活与探针失败共存**：Pod 处于 `Running` 状态且未重启（#1），说明应用进程并未因 OOM 或 Crash 而退出，而是稳定地进入了“拒绝服务”的逻辑分支。
3. **模式证据支持**：Trace 中的 `aiops.observed_mode: readiness_fail`（#5）从业务逻辑角度解释了为何服务返回503。

## 🎯 根因分析 · g1

### 因果链

```text
环境变量配置 FAILURE_MODE=readiness_fail → 应用进程将 /ready 与 /work 等端点配置为主动返回 HTTP 503 → Kubelet 周期性探测 /ready 获取 503 状态码 → Pod 被 kubelet 判定为 ContainersNotReady 并持续标记为 NotReady
```

### 根因结论

已确认根因为：**应用被配置在故障模式（FAILURE_MODE=readiness_fail），导致健康检查端点主动返回 503 错误。**

- **证据支撑**：Pod 状态显示进程持续存活但未就绪（`K8s State` #1）；Kubelet 连续报出探针收到 503 状态码（`K8s Event` #2）；日志与链路追踪均证实应用主动返回 503 状态及“依赖不可用”日志，且链路追踪明确标记了 `aiops.observed_mode: readiness_fail`（`Tracing` #4, #5）。
- **结论**：Pod 处于 `NotReady` 并非由资源耗尽、网络中断或应用崩溃引起，而是应用内部逻辑主动触发的受控故障表现。

---

## 📊 性能统计

```text
├─ 总耗时: 3.3m
├─ 问题定位: 19.3s
├─ 并发证据采集: 166.1s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-5mlnc: 166.1s (Evidence 157.3s, RCA 8.6s)
└─ 汇总总结: 11.7s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-5mlnc**: pod-notready-probe-failed
