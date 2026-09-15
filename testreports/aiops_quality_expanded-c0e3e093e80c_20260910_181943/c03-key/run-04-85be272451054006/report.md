## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v05/workload` | ContainerCreating | aiops-case-v05/workload is stuck in phase Pending with container state Waiting (Reason: ContainerCreating). |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `MountVolume.SetUp failed for volume "input" : configmap references non-existent config key: unavailable-key` | 确证挂载失败直接原因为 ConfigMap 键不存在，阻断容器创建 |
| 2 | K8s State | kubelet | Container `app` Waiting Reason: `ContainerCreating`; Pod Phase: `Pending` | 确认 Pod 长期停留在容器创建前阶段，未进入运行态 |
| 3 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"}` = `1` | 独立确认容器处于 `ContainerCreating` 状态，与事件事实一致 |
| 4 | K8s Config | kubelet | CPU Request: `5m`, Limit: `50m`；Memory Request: `8Mi`, Limit: `32Mi` | 资源限制配置本身不构成挂载或启动障碍 |

**证据链说明**：
- 证据 1（Mount 报错）与证据 2（状态停滞）在时间线上高度吻合，明确指出了 `kubelet` 在卷挂载阶段的阻塞点。
- 证据 3（Prometheus 监控）独立佐证了容器未能进入 Running 阶段的事实，排除单一 kubelet 日志偏差的可能性。

## 🎯 根因分析 · g1

### 因果链
```text
Pod Spec 配置了指向 ConfigMap 'workload-input' 中不存在的键 'unavailable-key' → kubelet 挂载卷 'input' 时触发键值校验失败 → 挂载失败阻塞容器运行时初始化 → Pod 永久停留在 Waiting (ContainerCreating) 状态
```

### 根因结论
已确认根因为 **应用配置错误导致卷挂载失败**。具体而言，Pod 规范引用了 ConfigMap `workload-input` 中的键 `unavailable-key`，但该键在目标 ConfigMap 中并不存在（见证据 #1）。此配置缺陷导致 `kubelet` 无法成功挂载卷，进而使得容器初始化流程被强制阻断，表现为 Pod 持续处于 `ContainerCreating` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 17.2s
├─ 并发证据采集: 81.6s
│  └─ g1 aiops-case-v05/workload: 81.6s (Evidence 72.4s, RCA 9.1s)
└─ 汇总总结: 7.3s
```

📋 Runbook 参考

- **g1 aiops-case-v05/workload**: pod-volume-mount-failed
