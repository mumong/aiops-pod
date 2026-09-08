## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-fl85h` | CrashLoopBackOff | 应用进程在请求处理中持续分配内存（日志显示 memory allocation advanced），导致容器内存使用量突破 kube-state-metrics 报告的资源硬限制 64Mi，被内核 OOM Killer 强制终止（Exit Code 137, Reason OOMKilled）。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Exit Code: 137, Reason: OOMKilled | 确认容器因内存耗尽被系统强制终止 |
| 2 | K8s Config | Kubernetes | Resource Limit (memory): 64Mi | 确认触发 OOM 的资源硬限制阈值 |
| 3 | Logging | Elasticsearch | Pattern: memory allocation advanced; Numeric fields (allocated_mib): min 16 -> max 46 | 确认应用进程内存分配持续增长且逼近限制 |
| 4 | K8s Event | Kubernetes | BackOff: Back-off restarting failed container app in pod workload-5c9c7b6489-fl85h | 确认故障具有持续性与循环性 |

**证据说明：**
日志记录的内存增长模式（16Mi 至 46Mi）与 K8s 配置的硬限制（64Mi）直接对应，内存逼近上限导致内核触发 OOM Killer 终止进程（Exit Code 137），并引发 kubelet 的 BackOff 重启循环。

## 🎯 根因分析 · g1

### 因果链

```text
应用进程在请求处理中持续分配内存 → 内存使用量突破资源硬限制 → 触发内核 OOM Killer 终止进程 → 应用进程 CrashLoopBackOff
```

### 根因结论

已确认根因：应用进程存在内存分配持续增长的行为。
日志观测到在请求处理期间，内存分配量从 16Mi 逐步增加至 46Mi。当内存消耗逼近并突破 K8s 配置的资源硬限制（64Mi）时，系统内核执行 OOM Kill 机制强制终止了容器进程（原因 OOMKilled, Exit Code 137），导致应用进入重启循环 [证据 #1, #2, #3]。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 21.6s
├─ 并发证据采集: 50.7s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-fl85h: 50.7s (Evidence 44.1s, RCA 6.5s)
└─ 汇总总结: 6.7s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-fl85h**: pod-crashloop-runtime
