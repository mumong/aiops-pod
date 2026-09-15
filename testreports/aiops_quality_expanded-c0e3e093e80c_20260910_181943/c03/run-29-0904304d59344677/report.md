## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-xn974` | ContainerCreating | Pod aiops-case-03/workload-5b5fc86c8c-xn974 卡在 ContainerCreating 状态，Pod 处于 Pending 阶段，容器未启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning FailedMount ... MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` | 直接指向容器因找不到 ConfigMap 无法挂载卷，导致启动阻塞。 |
| 2 | K8s Event | Kubernetes | `Warning FailedMount ... Unable to attach or mount volumes: unmounted volumes=[input]... timed out waiting for the condition` | 证实挂载超时，为同一挂载失败机制引发的后续表现。 |
| 3 | K8s Config | Kubernetes | Volume "input" 挂载失败 (事实关联至上述 `unavailable-config` 缺失) | 提供了失败的具体 Volume 名称和前置依赖对象。 |
| 4 | K8s State | Kubernetes | Pod phase: `Pending`; condition: `ContainersNotReady` | 证实容器长期处于等待启动的状态，与挂载失败导致容器无法初始化一致。 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` = `1`, label: `reason="ContainerCreating"` | 确认容器在监控侧处于 `ContainerCreating` 等待阶段，且未发生过重启 (重启为 0)。 |

以上证据链闭环：Prometheus 监控确认容器处于 `ContainerCreating` 且未重启，这与 K8s 事件日志中报告的因 `unavailable-config` ConfigMap 缺失导致 `FailedMount` 完全吻合。ConfigMap 的缺失是导致 Volume 挂载超时、进而使 Pod 卡在 `Pending` 状态的唯一物理证据。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'unavailable-config' 不存在 → MountVolume.SetUp 挂载失败 → 容器卡在 ContainerCreating 等待挂载 → Pod 处于 Pending 状态且不可用
```

### 根因结论

**已确认根因**：Pod 定义中指定的 ConfigMap `unavailable-config` 在集群中不存在。
**影响说明**：该缺失导致挂载卷 `input` 的操作在 kubelet 端持续失败，进而阻塞了容器的初始化过程，表现为 Pod 长期处于 `Pending` 状态且容器处于 `ContainerCreating` 等待阶段（证据编号 1、2、3）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 37.1s
├─ 并发证据采集: 40.3s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-xn974: 40.3s (Evidence 31.8s, RCA 8.4s)
└─ 汇总总结: 7.6s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-xn974**: pod-volume-mount-failed, pod-imagepull-failed, pod-sandbox-create-failed
