## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v11/workload` | CreateContainerConfigError | Pod aiops-case-v11/workload 处于 Pending 阶段，容器 app 持续等待，状态为 CreateContainerConfigError |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning Failed 38m (x12 over 40m) kubelet Error: couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input` | 提供容器启动失败的确切原因，指向特定的 ConfigMap 和缺失的 key |
| 2 | K8s State | kubernetes | `container: app, waiting_reason: CreateContainerConfigError` | 确认应用容器卡在配置校验阶段，未进入运行状态 |
| 3 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="CreateContainerConfigError"} = 1` | 独立验证了 Pod 处于配置错误等待状态 |
| 4 | K8s State | kubernetes | `container: app, pod.phase: Pending` | 确认 Pod 停留在 Pending 阶段，与配置挂载失败导致无法启动一致 |
| 5 | K8s Config | kubernetes | `container: app, resource_limit.memory: 32Mi, resource_limit.cpu: 50m` | 提供资源限制上下文，但非本次异常原因 |
| 6 | K8s State | kubernetes | `container: app, restart_count: 0` | 表明容器从未成功启动过，排除应用崩溃重启的可能 |

Kubernetes 事件 (fact-49360a478a9f) 明确指出 `kubelet` 在尝试查找 key `unavailable-key` 时失败，这与容器状态 `CreateContainerConfigError` (fact-1836b9d3d775) 完美契合。Metric (fact-428e9d166965) 从观测层面确认了该状态。日志与 Tracing 维度因容器未启动而不适用 (logging/tracing status: not_applicable)，故诊断完全基于 Kubernetes 内部状态与事件。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'aiops-case-v11/workload-input' 中缺少 key 'unavailable-key' → Pod 容器配置引用该 key 导致 kubelet 校验失败 → 拒绝创建容器 (CreateContainerConfigError) → Pod 处于 Pending 状态持续等待
```

### 根因结论

已确认的根因是：Pod `aiops-case-v11/workload` 的容器 `app` 配置中引用了 ConfigMap `aiops-case-v11/workload-input` 中的 key `unavailable-key`，但该 ConfigMap 的实际数据定义中不存在此 key。

这一缺失导致 `kubelet` 在挂载环境变量/配置时校验失败（证据：K8s Event `fact-49360a478a9f` 报错 "couldn't find key unavailable-key"），进而容器无法完成初始化并进入 `CreateContainerConfigError` 状态（证据：K8s State `fact-1836b9d3d775`）。由于该错误发生在容器启动前，容器重启次数为 0（证据：`fact-99fc781d0204`）。现有证据已充分闭环，确认此配置引用错误为本次故障的唯一根因。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 20.0s
├─ 并发证据采集: 42.7s
│  └─ g1 aiops-case-v11/workload: 42.7s (Evidence 34.2s, RCA 8.4s)
└─ 汇总总结: 10.6s
```

📋 Runbook 参考

- **g1 aiops-case-v11/workload**: pod-config-error
