## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v15/workload` | CrashLoopBackOff | 容器配置内存申请量(256Mi)远超资源限制(64Mi)，导致启动时触发OOMKilled |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Config | K8s State | `container.resource_limit.memory`: `64Mi` | 容器实际可用的硬资源上限 |
| 2 | K8s Config | K8s State | `container.resource_request.memory`: `8Mi` | 容器声明的资源申请量 |
| 3 | K8s Event | K8s State | `Exit Code: 137` | 进程收到 `SIGKILL` 终止信号 |
| 4 | K8s Event | K8s State | `Reason: OOMKilled` | 内核判定内存超限并执行杀进程 |
| 5 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason` = `OOMKilled` | 监控系统记录到的最后一次异常终止原因 |
| 6 | Metric | Prometheus | `kube_pod_container_status_restarts_total` = `24` | 容器异常重启的累计次数 |
| 7 | Logging | Elasticsearch | `startup allocation 256Mi` | 日志记录到的启动阶段内存申请值 |

**证据交叉印证：**
Kubernetes 状态（#3, #4）与 Prometheus 指标（#5）在“OOMKilled”这一终止原因上高度一致。关键矛盾点在于日志记录的启动分配值（#7，256Mi）远超配置中设定的硬限制（#1，64Mi），结合 Exit Code 137（#3），证实该分配行为突破了资源限额，直接触发内核强制杀进程机制。

## 🎯 根因分析 · g1

### 因果链

```text
容器配置内存申请量(256Mi)远超资源限制(64Mi) → 启动阶段触发内核 OOM 判定 → 容器被 OOMKilled 并退出(Exit Code 137) → 用户可见容器处于 CrashLoopBackOff 状态
```

### 根因结论

已确认的根因是**容器启动时的内存分配请求值（256Mi）远超设定的资源硬限制（64Mi）**。

日志中明确记录了“`startup allocation 256Mi`”（#7），而 K8s 配置中明确声明了该容器内存上限仅为 `64Mi`（#1）。这种配置上的不一致导致容器在启动阶段被 Linux OOM Killer 强制终止（#3, #4），进而引发持续的 CrashLoopBackOff 重启循环（#6）。

---

## 📊 性能统计

```text
├─ 总耗时: 4.5m
├─ 问题定位: 18.3s
├─ 并发证据采集: 243.6s
│  └─ g1 aiops-case-v15/workload: 243.6s (Evidence 237.0s, RCA 6.5s)
└─ 汇总总结: 8.4s
```

📋 Runbook 参考

- **g1 aiops-case-v15/workload**: pod-crashloop-runtime
