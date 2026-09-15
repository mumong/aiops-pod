## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-xn974` | ContainerCreating | Pod workload-5b5fc86c8c-xn974 持续处于 Pending/ContainerCreating 状态，无法启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod 阶段 Phase=Pending, Status=Pending | 描述异常组实体处于停滞状态 |
| 2 | K8s Event | kubernetes | Warning FailedMount (x55 over 101m) MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found | 直接证明挂载失败的触发原因及持续重试频率 |
| 3 | K8s Event | kubernetes | Warning FailedMount (x45 over 99m) Unable to attach or mount volumes: unmounted volumes=[input], unattached volumes=[input]: timed out waiting for the condition | 佐证挂载卷处于不可用状态的时间跨度 |
| 4 | K8s State | kubernetes | container.waiting_reason: ContainerCreating | 确认容器因卷挂载阻塞而未进入运行阶段 |
| 5 | K8s Config | kubernetes | configMapRefs 包含 unavailable-config, optional 未设置为 true | 排除 ConfigMap 缺失为预期的降级场景 |

上述证据链清晰：Pod 定义中引用了不存在的 ConfigMap，且未将其设为可选挂载，导致 kubelet 挂载卷 "input" 持续报错。这种阻塞状态使得 Pod 长时间停留在 Pending 阶段，等待容器启动的 Metric 状态也证实了这一点。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'unavailable-config' 在 aiops-case-03 命名空间中缺失 → 
Kubelet 尝试挂载非可选的 ConfigMap 卷 'input' 失败 → 
Pod 触发 FailedMount 事件并持续重试 (x55 over 101m) → 
Pod 停留在 Pending 阶段，Container status 为 ContainerCreating
```

### 根因结论

已确认根因为：Pod `workload-5b5fc86c8c-xn974` 定义中引用的 ConfigMap `unavailable-config` 在 `aiops-case-03` 命名空间中不存在。由于卷 `input` 的挂载未被标记为 `optional`，Kubernetes 强制要求该资源存在，导致挂载操作持续失败并超时（证据 #2, #3）。这一机制性失败阻断了容器的启动流程，最终表现为 Pod 长期处于 `Pending` 状态且无法就绪。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 20.3s
├─ 并发证据采集: 35.1s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-xn974: 35.1s (Evidence 26.8s, RCA 8.3s)
└─ 汇总总结: 8.0s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-xn974**: pod-volume-mount-failed
