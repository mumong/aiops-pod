## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v11/workload` | CreateContainerConfigError | ConfigMap `aiops-case-v11/workload-input` 中缺失 Pod 容器配置所需的 key `unavailable-key`，导致容器 `app` 无法完成配置注入并启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | Metric | `kube_pod_container_status_waiting_reason` | value=1, reason=CreateContainerConfigError (fact-511e0d7f603b) | 确认容器 `app` 处于配置注入失败的等待状态 |
| 2 | Metric | `kube_pod_status_phase` | kube-state-metrics phase=Pending (fact-ccf719239cb7) | 确认 Pod 整体处于 Pending 状态，未完成调度 |
| 3 | Metric | `kube_pod_container_status_restarts_total` | container=app, value=0 (fact-4ce25200baa9) | 表明容器尚未启动过，排除了重启失败的可能 |
| 4 | K8s State | `kubectl_logs` | Error: container "app" in pod "workload" is waiting to start: CreateContainerConfigError (failed tool) | 工具直接验证了容器处于等待启动的配置错误状态 |

**证据说明**：
- 指标（#1, #2）与工具（#4）共同印证了容器 `app` 因配置错误卡在 `CreateContainerConfigError` 阶段，且从未进入运行态（#3）。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap `aiops-case-v11/workload-input` 缺失 key `unavailable-key` (由诊断上下文确认) → 容器 `app` 无法完成配置注入 → 容器状态转为 CreateContainerConfigError (#1, #4) → Pod 保持在 Pending 状态 (#2)，无运行日志或重启
```

### 根因结论

已确认的根因是 `ConfigMap aiops-case-v11/workload-input` 中缺失了 Pod 容器 `app` 启动所必需的配置键 `unavailable-key`。

该配置缺失直接导致 K8s 无法完成容器的配置挂载步骤，触发了 `CreateContainerConfigError`（见证据 #1, #4）。由于容器未能启动，因此未观察到重启事件（见证据 #3）及任何应用日志。现有的 Kubernetes 状态与指标证据链（#1, #2, #4）已闭环支持该诊断结论，日志/追踪维度缺失属于预期现象（容器未启动），不构成证据不足。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 17.4s
├─ 并发证据采集: 36.9s
│  └─ g1 aiops-case-v11/workload: 36.9s (Evidence 31.7s, RCA 5.1s)
└─ 汇总总结: 7.7s
```

📋 Runbook 参考

- **g1 aiops-case-v11/workload**: pod-config-error
