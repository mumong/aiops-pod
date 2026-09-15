## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v05/workload` | ContainerCreating | aiops-case-v05/workload Pod 处于 ContainerCreating (Pending) 状态且无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `fact-686a85319db1` | `Warning FailedMount ... MountVolume.SetUp failed for volume "input" : configmap references non-existent config key: unavailable-key` | 直接指出卷挂载失败的具体配置缺失原因 |
| 2 | K8s State | `fact-ab6bdb5dea65` | `Pod phase: Pending` | 确认 Pod 整体处于等待状态 |
| 3 | K8s State | `fact-bda26a3128dc` | `Container "app" waiting reason: ContainerCreating` | 定位容器卡在此阶段无法启动 |
| 4 | K8s Config | `fact-07f2a6c697ed` | `container.app resource_limit.memory: 32Mi` | 确认资源限制，排除资源溢出导致的事件 |
| 5 | Metric | `fact-1ad304d2ea3b` | `kube_pod_container_status_waiting_reason = 1 (reason: ContainerCreating)` | 确认当前等待状态的量化观测 |

**证据分析：**
事件 `fact-686a85319db1` 明确记录了 `FailedMount` 错误及缺失的 ConfigMap key，这是导致 Pod 无法进入 `Running` 状态的直接技术原因；状态 `fact-bda26a3128dc` 和指标 `fact-1ad304d2ea3b` 一致反映了该等待状态；资源配置 `fact-07f2a6c697ed` 证明资源配额本身未触发 OOM 或限流，排除了计算资源不足的因素。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'workload-input' 缺失 key 'unavailable-key' → kubelet 尝试挂载卷 'input' 失败 (FailedMount) → Pod 状态持续为 Pending/ContainerCreating → 容器无法启动
```

### 根因结论

已确认根因为 **配置错误**：Pod 定义中引用的 ConfigMap Volume `input` 包含了一个不存在的 Key `unavailable-key`（事实 `fact-686a85319db1`）。

这一配置错误导致 kubelet 在启动容器前执行卷挂载时失败，进而使 Pod 陷入 `Pending` 且容器处于 `ContainerCreating` 等待状态（事实 `fact-ab6bdb5dea65`、`fact-bda26a3128dc`）。由于容器未能启动，未产生任何日志或 Tracing 数据，现象与配置事实高度一致，证据充分。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 16.8s
├─ 并发证据采集: 37.5s
│  └─ g1 aiops-case-v05/workload: 37.5s (Evidence 29.4s, RCA 8.1s)
└─ 汇总总结: 9.0s
```

📋 Runbook 参考

- **g1 aiops-case-v05/workload**: pod-volume-mount-failed
