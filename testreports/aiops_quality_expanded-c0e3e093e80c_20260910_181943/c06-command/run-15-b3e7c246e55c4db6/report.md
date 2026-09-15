## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v08/workload` | CrashLoopBackOff | 容器启动命令 `sh -c exec /opt/app/unavailable-command` 指定的入口文件 `/opt/app/unavailable-command` 在当前镜像 `xnet.registry.io:8443/observability/python:3-alpine` 中不存在，导致进程启动失败（exitCode=127）并引发 CrashLoopBackOff。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `BackOff 3m38s (x72 over 18m) ... Back-off restarting failed container app` | 证实 Pod 处于反复重启失败的失控循环中 |
| 2 | K8s State | Kubernetes | `container.app.last_terminated_reason=Error`, `exit_code=127` | 核心事实：进程因命令缺失（127）异常退出 |
| 3 | K8s Config | Kubernetes | `container.app.waiting_reason=CrashLoopBackOff` | 直接展示 K8s 对当前“崩溃重启”状态的系统判定 |
| 4 | Logging | Elasticsearch | `sh: exec: line 0: /opt/app/unavailable-command: not found` | 提供致命归因：Shell 无法定位并执行镜像内文件 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` (`CrashLoopBackOff`) | 从监控系统侧印证 K8s 状态未恢复 |

**证据互证分析：**
- **K8s 维度（#1, #2, #3）** 与 **Logging 维度（#4）** 形成了完整的因果闭环：日志直接记录了“文件未找到”这一根本原因，该原因导致进程以 `exit_code=127` 退出，进而引发 K8s 的重启机制和 `CrashLoopBackOff` 状态。
- **Metric 维度（#5）** 在监控侧同步记录了相同的等待状态，排除了数据采集盲区或单一维度故障的可能性。

## 🎯 根因分析 · g1

```text
容器镜像中缺失 /opt/app/unavailable-command 文件 → 入口命令尝试执行不存在的路径导致 sh 返回 127 退出码 → 容器启动即终止并触发 kubelet 重启机制 → Pod 进入 CrashLoopBackOff 状态
```

### 根因结论

已确认的根因为：**容器启动命令（`/opt/app/unavailable-command`）在当前使用的镜像 `xnet.registry.io:8443/observability/python:3-alpine` 中不存在。**

该配置错误导致容器进程在启动瞬间被 Shell 拒绝执行（退出码 127），触发 Kubernetes 的指数级重启策略，最终表现为 Pod 持续处于 `CrashLoopBackOff` 状态。诊断依据为：
- 直接原因日志：`sh: exec: line 0: /opt/app/unavailable-command: not found`（证据 #4）；
- 异常终止状态：`exit_code=127` 与 `terminated_reason=Error`（证据 #2）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 17.0s
├─ 并发证据采集: 40.4s
│  └─ g1 aiops-case-v08/workload: 40.4s (Evidence 32.2s, RCA 8.1s)
└─ 汇总总结: 9.0s
```

📋 Runbook 参考

- **g1 aiops-case-v08/workload**: pod-crashloop-runtime
