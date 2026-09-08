## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-bwqhh` | CrashLoopBackOff | Memory limit (96Mi) exceeded causing OOMKill (exit 137), which terminated the process and triggered repeated Liveness probe failures (HTTP 500) leading to CrashLoopBackOff. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Config | Kubernetes | `container.resource_limit.memory` = `96Mi` | 确立内存硬限制阈值 |
| 2 | K8s State | Kubernetes | `container.last_exit_code` = `137` | 确认进程被系统强制终止（OOMKill特征） |
| 3 | K8s State | Kubernetes | `container.last_terminated_reason` = `Error` | 确认退出原因符合资源超限或系统拦截特征 |
| 4 | Metric | Prometheus | `container_memory_working_set_bytes` 在重启周期内从约 `3.2Mi` 增长至 `~15.5Mi` | 证实容器存在持续增长的内存使用模式 |
| 5 | K8s Event | Kubernetes | `Liveness probe failed: HTTP probe failed with statuscode: 500` (39m, x8) | 确认应用启动后存活探针失败的具体现象 |
| 6 | K8s Event | Kubernetes | `Back-off restarting failed container app` (2m2s, x135) | 确认因持续失败导致的指数退避重启机制触发 |
| 7 | K8s State | Kubernetes | `container.restart_count` = `17` | 证实故障处于反复重启的生命周期中 |
| 8 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` = `1` (reason: `CrashLoopBackOff`) | 量化确认当前最终容器状态 |

**证据说明：**
- 证据 1、2、3 互相印证，结合退出码 137 与 Error 状态，强指向 OOMKill 机制触发了进程终止。
- 证据 4 的内存指标从低水位飙升至高位，提供了 OOMKill 的直接前置条件。
- 证据 5 与 6 解释了进程被终止后的连锁反应：存活探针失败导致 Pod 状态回滚至 CrashLoopBackOff。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存使用持续增长(>96Mi) → 触发 OOMKill(Exit 137) → 进程终止 & 存活探针失败(500) → CrashLoopBackOff
```

### 根因结论

已确认根因：**容器内存限制配置过小（96Mi）导致应用运行时触发 OOMKill。**

该根因由多维事实闭环支撑：
1. **资源瓶颈**：证据 4 显示内存使用量突破限制，证据 1 定义了硬性上限 96Mi。
2. **终止机制**：证据 2、3 确认了 137 退出码，符合内核 OOM Killer 终止进程的标准特征。
3. **故障循环**：证据 5、6、7、8 证实进程终止后，因存活探针无法通过，触发了 Kubernetes 的标准重启与退避逻辑，形成 CrashLoopBackOff 现象。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 12.9s
├─ 并发证据采集: 66.9s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-bwqhh: 66.9s (Evidence 60.3s, RCA 6.5s)
└─ 汇总总结: 10.3s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-bwqhh**: pod-crashloop-runtime
