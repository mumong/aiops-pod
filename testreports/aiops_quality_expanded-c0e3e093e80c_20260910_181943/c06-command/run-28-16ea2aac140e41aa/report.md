## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v08/workload` | CrashLoopBackOff | Pod配置了不存在的可执行文件路径 `/opt/app/unavailable-command`，导致容器启动时以退出码127失败并触发CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_reason: CrashLoopBackOff` (fact-703adf949944) | 确认 Pod 当前处于重启循环状态 |
| 2 | K8s State | Kubernetes | `container.last_exit_code: 127` (fact-78689a39b5fb) | 明确容器非正常终止，退出码 127 指向“命令未找到” |
| 3 | K8s Event | Kubernetes | `BackOff restarting failed container app in pod workload_aiops-case-v08(...)` (fact-7ffde8ad6695) | 描述 kubelet 正在退避重启异常容器 |
| 4 | Logging | Elasticsearch | `sh: exec: line 0: /opt/app/unavailable-command: not found` (fact-13cb3242823d) | **决定性证据**：日志明确指出了失败的具体命令及原因 |
| 5 | Metric | Prometheus | `kube_pod_container_status_restarts_total: 11` (fact-6256e4c547fb) | 辅助证据：反映该问题已持续一段时间且反复发生 |

**证据总结**：
Kubernetes 状态确认 Pod 处于 `CrashLoopBackOff` 状态且容器最近一次退出了 `127` 码；Elasticsearch 日志提供了直接解释，指明是执行 `/opt/app/unavailable-command` 时发生 `not found` 错误。两者在异常现象（重启）和根本原因（命令缺失）上完全印证。

## 🎯 根因分析 · g1

### 因果链

```text
镜像中缺少或路径错误 `/opt/app/unavailable-command` → 容器进程启动失败，退出码 127 → kubelet 触发重启机制并进入 BackOff → Pod 状态变为 CrashLoopBackOff
```

### 根因结论

**已确认的根因**：
Pod 配置了不可用的可执行文件路径 `/opt/app/unavailable-command`，导致容器无法启动并立即以退出码 127 失败，进而触发 Kubernetes 的重启策略。该结论直接由日志事实 `fact-13cb3242823d` 确认，并由 `fact-78689a39b5fb` (Exit Code 127) 和 `fact-703adf949944` (CrashLoopBackOff) 证实。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 31.8s
├─ 并发证据采集: 32.3s
│  └─ g1 aiops-case-v08/workload: 32.3s (Evidence 26.8s, RCA 5.4s)
└─ 汇总总结: 8.7s
```

📋 Runbook 参考

- **g1 aiops-case-v08/workload**: pod-crashloop-runtime, pod-oomkilled
