## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v08/workload` | CrashLoopBackOff | Pod aiops-case-v08/workload 处于 CrashLoopBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | Logging | Elasticsearch | `sh: exec: line 0: /opt/app/unavailable-command: not found` (2026-09-11T13:34:23.904Z) | 确定进程启动失败的直接原因（Command Not Found） |
| 2 | K8s State | Kubernetes | Exit Code: 127 | 确认进程因找不到命令而退出，与日志一致 |
| 3 | K8s Event | Kubernetes | `Warning BackOff ... Back-off restarting failed container app ... (x187 over 42m)` | 展示故障持续存在的时间跨度及高频重启状态 |
| 4 | K8s State | Kubernetes | Waiting Reason: CrashLoopBackOff | 确认容器处于 K8s 重试退避状态 |
| 5 | Metric | Prometheus | `kube_pod_container_status_restarts_total` 从 2.0 递增至 13.0 (trend_evaluable=true) | 量化证实了容器的反复崩溃与重启过程 |
| 6 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` = 1 (reason=CrashLoopBackOff) | 独立监控视角确认当前处于等待重试状态 |
| 7 | K8s Event | Kubernetes | `Annotations: cni.projectcalico.org/containerID: 4e997a29...` | 排除网络配置问题导致的启动异常 |

证据 1（日志报错）与证据 2（退出码 127）相互印证，共同指向容器启动命令路径错误。证据 3 和 5 证实了该问题导致了持续的 CrashLoopBackOff 循环，而证据 6 进一步确认了当前的等待状态。

## 🎯 根因分析 · g1

### 因果链

```text
容器启动命令 /opt/app/unavailable-command 不存在 → 进程启动失败 (Exit 127) → 触发 CrashLoopBackOff 重试机制 → Pod 处于 CrashLoopBackOff 状态
```

### 根因结论

**已确认的根因：**
Pod `aiops-case-v08/workload` 的容器 `app` 启动命令配置为执行 `/opt/app/unavailable-command`，但该文件不存在。

**证据支撑：**
1. 容器进程因找不到命令启动失败，退出码为 127（证据 1、证据 2）。
2. K8s 触发指数退避重启机制，导致 Pod 持续处于 CrashLoopBackOff 状态且重启次数已累积至 13 次（证据 3、证据 4、证据 5、证据 6）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 13.4s
├─ 并发证据采集: 46.1s
│  └─ g1 aiops-case-v08/workload: 46.1s (Evidence 37.4s, RCA 8.6s)
└─ 汇总总结: 9.1s
```

📋 Runbook 参考

- **g1 aiops-case-v08/workload**: pod-crashloop-runtime
