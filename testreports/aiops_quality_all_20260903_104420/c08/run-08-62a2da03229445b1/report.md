## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-fl85h` | OOMKilled | 容器内存硬限制(64Mi)过低且应用存在内存持续增长模式，导致请求处理时触发OOM Killed并进入CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Exit Code: 137; Reason: OOMKilled (fact-682d674ae04f, fact-aa8b51ac2aa8) | 确证容器因内核 OOM Killer 终止，是直接的失败症状。 |
| 2 | K8s Config | Kubernetes | container.resource_limit.memory = 64Mi (fact-c38bf0a2d6c8) | 提供硬性资源边界，是触发 OOM 的关键配置约束。 |
| 3 | Metric | Prometheus | container_memory_working_set_bytes 在最后一次重启（fact-744a915bdae4）中从 30Mi 增长至 61.4Mi (last: 62083072 bytes) | 证实内存使用量逼近 64Mi 限制，展示了逼近阈值的增长过程。 |
| 4 | Logging | Elasticsearch | pattern: "memory allocation advanced", allocated_mib 从 10Mi 增至 38Mi (fact-53eae09f15fb et al.) | 确认应用内部存在内存分配持续增长的特征，解释了为何内存会突破阈值。 |
| 5 | K8s State | Kubernetes | waiting_reason: CrashLoopBackOff (fact-9af902b434bf); restart_count: 8 (fact-4cb5c5c7f031) | 表明系统在反复重启中未能恢复，OOM 状态持续发生。 |
| 6 | K8s Event | Kubernetes | BackOff restarting failed container app (fact-6e24bca0aae9) | 辅助证明重启失败及系统进入 BackOff 退避状态。 |

证据链通过配置硬限制（fact-2）、容器持续增长的内存使用（fact-3）与内存分配日志（fact-4）建立因果关系，最终由 Exit Code 137 和 OOMKilled 状态（fact-1）作为最终终止证据形成闭环。

## 🎯 根因分析 · g1

### 因果链

```text
应用存在内存持续增长特征 (Logging: memory allocation advanced) → 处理请求时内存使用突破 64Mi 硬限制 (K8s Config: 64Mi) → 容器被内核 OOM Killer 强制终止 (K8s State: Exit Code 137) → 触发 CrashLoopBackOff 导致服务不可用 (K8s State: CrashLoopBackOff)
```

### 根因结论

已确认的根因是容器内存硬限制（64Mi）过低且应用存在内存持续增长模式（fact-53eae09f15fb），导致处理请求时内存使用突破硬限制，触发内核 OOM Killer 强制终止容器（Exit Code 137, fact-1），进而进入 CrashLoopBackOff 重启死循环（fact-9af902b434bf）。

---

## 📊 性能统计

```text
├─ 总耗时: 2.2m
├─ 问题定位: 22.8s
├─ 并发证据采集: 97.5s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-fl85h: 97.5s (Evidence 87.7s, RCA 9.6s)
└─ 汇总总结: 10.5s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-fl85h**: pod-oomkilled
