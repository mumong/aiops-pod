## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-5mlnc` | NotReady | Pod workload-5f4fb9ff45-5mlnc 处于 NotReady 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Readiness probe failed: HTTP probe failed with statuscode: 503` (x104 over 8m8s) | 确认应用层就绪探针持续失败，是 Pod 进入 NotReady 的直接原因。 |
| 2 | K8s Event | kubelet | `Readiness probe failed: Get "http://172.16.104.16:8080/ready": dial tcp 172.16.104.16:8080: connect: connection refused` | 提供端口连接被拒绝的历史记录，支持应用进程或端口存在短暂不可用的假设。 |
| 3 | K8s Config | container | `memory_request=24Mi`, `memory_limit=96Mi`, `restart_count=0` | 排除 OOM 杀死或启动失败的常见原因，佐证应用进程处于存活但功能异常状态。 |
| 4 | Logging | elasticsearch | `dependency unavailable` (error, status 503), 8 occurrences (00:40:57 - 00:41:31) | 从业务日志层面确认为“上游依赖不可用”导致应用服务返回错误，为根因提供核心定性证据。 |
| 5 | Tracing | tempo/deepflow | Span `GET /work` (status 503), Flow 聚合 (src 172.16.104.62 -> dst 172.16.104.16, 9 occurrences, status 503) | 流量证据确认应用接收到了业务请求但处理失败，与日志错误形成闭环。 |

**证据说明：**
1. K8s 探针事件（#1, #2）从集群管控视角确认了服务不可用及状态翻转为 NotReady 的现象。
2. Logging（#4）和 Tracing（#5）均指向同一结论——应用服务自身返回了 503 错误，且日志明确指出了“上游依赖不可用”，这构成了直接失败机制，排除了底层基础设施或网络故障作为首要原因的可能。
3. 资源配置与重启计数（#3）排除了容器级别的环境干扰（如内存泄漏重启），进一步支持是应用依赖问题。

## 🎯 根因分析 · g1

### 因果链
```text
应用服务上游依赖不可用 → 就绪探针(/ready)及业务接口(/work)返回 HTTP 503 → Kubelet 检测到探针连续失败 → Pod 状态由 Ready 翻转为 NotReady
```

### 根因结论
已确认根因为**应用服务存在上游依赖不可用（dependency unavailable）**。

该根因直接导致应用服务在处理健康检查探针请求及业务请求时返回 HTTP 503 状态码（证据 #1, #4, #5）。Kubelet 检测到就绪探针持续失败后，将容器状态标记为未就绪，致使 Pod 进入 `NotReady` 状态。

**缺失的决定性事实（未确认环节）：**
日志中记录的“上游依赖不可用”未提供具体的依赖服务名、地址或网络诊断数据，因此依赖服务不可用的具体根因（例如：是依赖服务宕机、网络阻断还是配置错误）在证据链中未被捕获。

---

## 📊 性能统计

```text
├─ 总耗时: 2.0m
├─ 问题定位: 24.4s
├─ 并发证据采集: 83.4s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-5mlnc: 83.4s (Evidence 69.7s, RCA 13.6s)
└─ 汇总总结: 11.3s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-5mlnc**: pod-notready-probe-failed
