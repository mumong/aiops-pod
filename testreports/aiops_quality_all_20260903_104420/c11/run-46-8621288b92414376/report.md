## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod metadata.finalizers 中包含自定义条目 'aiops.lab/hold' 未完成清理，导致 Kubernetes API Server 阻塞删除操作。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod Phase & Condition | `ContainersNotReady` (containers with unready status: [app]), `ContainersReady: False` | 证实应用容器无法就绪 |
| 2 | K8s Event | Exit Code Log | `Exit Code: 137` | 指向进程被信号强制终止 |
| 3 | K8s State | Last Terminated Reason | `reason: Error`, `exit_code: 137` | 确认最近一次异常退出的性质 |
| 4 | Metric | `kube_pod_container_status_restarts_total` | 0 (at `2026-09-03T23:48:29Z`) | 排除因资源压力导致的频繁重启与自愈循环 |

**证据互证：** K8s Event (`Exit Code: 137`) 与 K8s State (`reason: Error`) 一致，确证容器因 OOMKill 或外部信号强制退出。Metric 显示 restart 次数为 0，证明退出是孤立事件，集群并未因资源耗尽陷入反复重启风暴。

## 🎯 根因分析 · g1

### 因果链

```text
Pod metadata 包含 'aiops.lab/hold' finalizer → API Server 阻止资源彻底释放 → 控制器未执行清理逻辑(unknown) → 用户可见：Pod 停滞在 Terminating 状态 77 分钟
```

### 根因结论

**已确认现象：** Pod 处于 `Terminating` 状态并停滞 77 分钟，这是 Kubernetes 删除流程中的阻塞现象（Symptom）。

**证据不足（根因未定）：** 
正式 RCA 声称根因为 `'aiops.lab/hold' finalizer` 阻塞，但 **K8s 事实维度中缺乏对该 Pod 的 `metadata.finalizers` 字段的直接观测**。现有证据（Exit 137、Container Not Ready）仅能证明应用运行异常及随后的删除操作未完成。在缺失 finalizer 状态直接证据以及对应控制器日志（Logging/Tracing 为空）的情况下，无法验证 'aiops.lab/hold' 是否确实存在或为何无法清理。当前仅能确证“删除操作被卡住”这一表象。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 17.0s
├─ 并发证据采集: 45.6s
│  └─ g1 aiops-case-11/workload: 45.6s (Evidence 38.2s, RCA 7.2s)
└─ 汇总总结: 7.7s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
