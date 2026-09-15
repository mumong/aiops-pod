## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v08/workload` | CrashLoopBackOff | Pod aiops-case-v08/workload 的启动命令配置指定了一个在容器镜像中不存在的可执行文件 `/opt/app/unavailable-command`，导致容器进程启动后立即以 Exit Code 127 失败退出，进而触发 CrashLoopBackOff。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `message`: "Back-off restarting failed container app in pod workload_aiops-case-v08(00e5e755-886e-4661-9e8a-00d1e71595f6)" | 确认容器处于反复崩溃重启的异常循环状态 |
| 2 | K8s State | kubernetes | `container.last_exit_code`: `exit_code`: 127 | 标识进程启动失败的确切退出码（通常对应命令未找到） |
| 3 | Logging | elasticsearch | `log.message`: "sh: exec: line 0: /opt/app/unavailable-command: not found" | 提供确切的错误文本，验证命令 `/opt/app/unavailable-command` 在容器环境中不存在 |
| 4 | Metric | prometheus | `kube_pod_container_status_restarts_total`: `5` (trend: 2.0 → 5.0, sample_count: 4) | 确认重启行为持续发生，排除了偶发性故障，与 CrashLoopBackOff 现象一致 |

证据间形成了完整的诊断闭环：日志记录了具体的 `not found` 错误及对应的缺失文件路径（#3），该错误导致的进程退出被 K8s 捕捉并标记为 Exit Code 127（#2），最终在指标层面确认为持续且累积的重启行为（#4），共同印证了容器因启动命令配置错误而崩溃的事实。

## 🎯 根因分析 · g1

### 因果链

```text
启动命令配置错误（镜像中不存在 /opt/app/unavailable-command） → 容器进程启动立即以 Exit Code 127 失败 → K8s 触发 CrashLoopBackOff 反复重启 → 用户可见 Pod 处于 CrashLoopBackOff 状态
```

### 根因结论

已确认根因：Pod `aiops-case-v08/workload` 中 `app` 容器的启动命令（Command）配置错误。

证据 #3 (Logging) 中的原始日志 `sh: exec: line 0: /opt/app/unavailable-command: not found` 直接证实了可执行文件在容器镜像中缺失。该启动失败导致进程以 Exit Code 127 退出（证据 #2），进而触发 Kubernetes 的重启策略，最终表现为 CrashLoopBackOff 状态及持续上升的重启计数（证据 #1, #4）。现有证据充分，排除了资源不足或网络等外部因素。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 22.3s
├─ 并发证据采集: 43.0s
│  └─ g1 aiops-case-v08/workload: 43.0s (Evidence 36.6s, RCA 6.3s)
└─ 汇总总结: 8.5s
```

📋 Runbook 参考

- **g1 aiops-case-v08/workload**: pod-crashloop-runtime, pod-oomkilled
