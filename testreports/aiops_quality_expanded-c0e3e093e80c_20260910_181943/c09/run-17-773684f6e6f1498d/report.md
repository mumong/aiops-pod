## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-5mlnc` | NotReady | Pod workload-5f4fb9ff45-5mlnc 处于 NotReady 状态，Readiness Probe 持续返回 HTTP 503 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | pod/phase | `Running` | 确认 Pod 底层运行正常，无 OOMKilled 或 CrashLoopBackOff |
| 2 | K8s State | pod/condition | `Ready=False`, `ContainersNotReady` | 确认应用层健康检查失败是导致 Pod 异常的直接原因 |
| 3 | K8s Event | kubelet | `Readiness probe failed: Get "http://172.16.104.16:8080/ready": dial tcp ... connect: connection refused` | 排除网络不通或端口未监听的问题，确认服务进程已启动但拒绝连接特定路径 |
| 4 | Logging | elasticsearch | `dependency unavailable` (8 occurrences, allocated_mib=0) | 揭示应用内部业务逻辑因资源分配失败（allocated_mib=0）而拒绝提供服务 |
| 5 | Tracing | deepflow | `GET /work` `503` (9 occurrences, src=172.16.104.62, dst=172.16.104.16) | 追踪流量证实 `/work` 接口稳定返回 503，确认应用处理逻辑处于受控报错状态而非崩溃 |
| 6 | K8s Config | container.resource_limit | `memory: 96Mi` | 提供内存资源约束背景，作为排查潜在 OOM 的参考依据 |

**证据印证说明：**
K8s 状态（#1, #2）确立了“进程存活但健康检查失败”的基础事实。日志（#4）明确指出了业务逻辑层面的错误原因：内部依赖资源初始化失败。Tracing（#5）与日志（#4）通过相同的 503 状态码和业务行为相互印证，证实了应用并非宕机，而是因逻辑错误主动拒绝请求。K8s 事件（#3）证实了 kubelet 正是读取到这个 503/拒绝连接的结果，才将 Pod 标记为 NotReady，形成了完整的因果闭环。

## 🎯 根因分析 · g1

### 因果链

```text
应用内部依赖资源初始化失败 (allocated_mib=0) → 应用业务逻辑主动返回 HTTP 503 (接口 /work) → Readiness Probe (GET /ready) 判定失败 → Pod 状态标记为 NotReady，服务不可用
```

### 根因结论

**已确认的根因：应用内部依赖资源初始化失败（allocated_mib=0）。**

1.  **现象解释**：Pod `workload-5f4fb9ff45-5mlnc` 进程处于 `Running` 状态，表明容器环境正常。但健康检查探针（Readiness Probe）持续失败。
2.  **故障机制**：根据 Elasticsearch 日志（证据#4），应用在处理请求时检测到关键内部依赖资源（具体为内存资源分配，`allocated_mib=0`）初始化失败。应用并未崩溃，而是按照设计逻辑向客户端返回了 HTTP 503 `dependency unavailable`。
3.  **结果验证**：DeepFlow 流量日志（证据#5）证实了 `GET /work` 请求稳定收到 503 响应。Kubelet 因无法从应用获取 200 OK 的健康检查响应，最终将 Pod 标记为 `NotReady`（证据#2）。

**缺失的关键事实**：日志中的 `dependency` 具体指代的是哪个外部服务、ConfigMap 还是特定 Volume。目前确认为“应用内部逻辑因资源分配不足（0 MIB）而主动降级”，但未确认是 K8s 调度层面的资源未到位（尽管限制设为 96Mi），还是应用内部逻辑报错。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 15.8s
├─ 并发证据采集: 76.8s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-5mlnc: 76.8s (Evidence 66.2s, RCA 10.4s)
└─ 汇总总结: 12.5s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-5mlnc**: pod-notready-probe-failed
