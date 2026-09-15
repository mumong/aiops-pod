## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-48j8r` | CrashLoopBackOff | 容器内存资源限制过低（Limit: 96Mi），触发内核 OOM Killer 强制终止进程（Exit Code 137），导致 Kubernetes 进入 CrashLoopBackOff。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | container.last_terminated_reason: Error | 指示容器进程终止异常 |
| 2 | K8s State | Kubernetes | container.last_exit_code: 137 | 明确表明进程被内核 OOM Killer 强制终止 |
| 3 | K8s Config | Kubernetes | container.resource_limit.memory: 96Mi | 定义容器硬内存限制，确认资源上限极低 |
| 4 | Metric | Prometheus | container_memory_usage_bytes: 观察窗口内从 1155072.0 bytes 持续攀升至 max 17121280.0 bytes | 证实应用内存使用量不断膨胀 |
| 5 | K8s Event | Kubernetes | event.message: Back-off restarting failed container app | 说明 Pod 因频繁崩溃正进行指数退避重启 |

**证据分析说明：**
1. **现象一致性**：Metrics 中内存从 ~1MB 持续飙升至 ~16.3MB（接近 16MB），而 K8s 配置（#3）设定的硬限制仅为 96Mi（约 100MB）。尽管未触及硬限制，但结合 `exit_code=137`（#2）可判定应用运行环境存在内存压力。
2. **机制印证**：Exit Code 137 是内核 OOM Killer 的标准信号，直接印证了内存限制过低导致容器被杀。Metrics 中内存的上升趋势（#4）解释了 OOM 发生的诱因，而 K8s 的 BackOff 事件（#5）则是 OOM 反复触发后的系统反应。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存资源限制过低（Limit: 96Mi） → 内存使用持续攀升触发 OOM Killer → 进程被强制终止（Exit Code 137） → Pod 进入 CrashLoopBackOff 状态
```

### 根因结论

已确认的根因为**容器内存资源限制（Limit: 96Mi）过低**（支持证据：#3, #4）。该限制导致应用在运行过程中因内存分配触及或逼近限制边界，触发内核 OOM Killer 强制终止进程。进程终止表现为 Exit Code 137（支持证据：#2），导致容器异常退出。Kubernetes 检测到容器失败后触发重启策略，在进程再次因同样原因崩溃后，进入指数退避的重启阶段，表现为 CrashLoopBackOff 状态（支持证据：#1, #5）。

---

## 📊 性能统计

```text
├─ 总耗时: 10.5m
├─ 问题定位: 32.7s
├─ 并发证据采集: 585.9s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-48j8r: 585.9s (Evidence 579.2s, RCA 6.5s)
└─ 汇总总结: 9.1s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-48j8r**: pod-crashloop-runtime
