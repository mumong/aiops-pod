## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v05/workload` | ContainerCreating | Pod aiops-case-v05/workload 处于 ContainerCreating/Pending 状态，容器未启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `FailedMount` (Fact ID: fact-e16f653e6851): `MountVolume.SetUp failed for volume "input" : configmap references non-existent config key: unavailable-key` | 直接定位到挂载失败的根本原因是 ConfigMap 键缺失，支撑故障根因。 |
| 2 | K8s Event | Kubernetes | `FailedMount` (Fact ID: fact-ee93a3cfd5a1): `Unable to attach or mount volumes: unmounted volumes=[input]... timed out waiting for the condition` | 补充证明 `input` 卷挂载操作超时，印证配置缺陷导致的阻塞状态。 |
| 3 | K8s State | Kubernetes | `container.waiting_reason` (Fact ID: fact-4e057f8190fa): `ContainerCreating` | 描述容器当前停滞的等待原因，与挂载失败的现象一致。 |
| 4 | K8s State | Kubernetes | `pod.status` (Fact ID: fact-240c9fd16f77): `Pending` | 明确 Pod 处于调度完成但未就绪的挂起状态，符合资源挂载未通过的特征。 |
| 5 | K8s Config | Kubernetes | `resource_request.cpu` (Fact ID: fact-45b27237d69c): `5m`, `resource_request.memory` (Fact ID: fact-5b692e243fb1): `8Mi` | 资源请求量极低，排除因资源耗尽 (OOM/CPUThrottling) 导致容器无法创建的可能。 |
| 6 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` (Fact ID: fact-9803b98709ba): `reason=ContainerCreating` 且值为 `1` | 独立于 K8s 事件确认当前状态，佐证 Pod 正处于创建等待阶段。 |
| 7 | Metric | Prometheus | `kube_pod_container_status_restarts_total` (Fact ID: fact-79010b0730a6): `0` | 确认容器未启动且未发生过重启，证明问题停留在初始挂载阶段。 |

**证据关联说明**：
Kubernetes 事件 (1, 2) 明确指出挂载失败是由于引用了不存在的 ConfigMap 键，这一根本原因直接导致了容器状态被卡在 `ContainerCreating` (3, 6)，且从未进入运行或重启状态 (7)。资源配置 (5) 进一步排除了因资源不足导致启动缓慢或失败的可能性，各维度事实逻辑一致。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'workload-input' 缺失 'unavailable-key' → MountVolume.SetUp failed (FailedMount) → 容器初始化阻塞 → Pod 停滞在 ContainerCreating/Pending 状态
```

### 根因结论

已确认的根因是 **Pod 定义中引用了 ConfigMap 'workload-input' 中不存在的键 'unavailable-key'，导致 Kubelet 在挂载卷阶段发生致命错误 (FailedMount)**。

该配置错误直接阻断了容器的初始化流程。证据链闭环：
- **K8s 事件 (1, 2)** 记录挂载失败及具体的配置键缺失原因。
- **K8s 状态 (3, 4)** 与 **Metric (6, 7)** 一致显示容器因上述失败而永久卡在等待状态，未发生启动或重启。
- **资源配置 (5)** 极低，排除了其他资源调度类故障。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 36.8s
├─ 并发证据采集: 46.0s
│  └─ g1 aiops-case-v05/workload: 46.0s (Evidence 37.4s, RCA 8.5s)
└─ 汇总总结: 11.9s
```

📋 Runbook 参考

- **g1 aiops-case-v05/workload**: pod-imagepull-failed, pod-volume-mount-failed, pod-sandbox-create-failed
