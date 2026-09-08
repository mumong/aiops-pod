## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-2xgjz` | ContainerCreating | Pod workload-5b5fc86c8c-2xgjz stuck in ContainerCreating (Pending phase) |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod `aiops-case-03/workload-5b5fc86c8c-2xgjz` 状态 `Pending` (fact-2d5e6a4b0a34) | 确认 Pod 处于不可用状态 |
| 2 | K8s Event | kubernetes | `FailedMount` 事件：`MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` (fact-5d6b4ddbd710) | 确认挂载失败及缺失资源 |
| 3 | K8s Event | kubernetes | `timed out waiting for the condition` 持续等待挂载 (fact-ee00c6388b58) | 确认挂载阻塞导致持续重试 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` 值为 `1` (reason: `ContainerCreating`) (fact-c14607f245be) | 确认容器正处于创建等待阶段 |
| 5 | K8s Config | kubernetes | 容器 `app` 内存限制 `32Mi` (fact-36276843cd86)、CPU 限制 `50m` (fact-75c23db3d030) | 排除资源超限导致 OOM/Kill |
| 6 | Metric | prometheus | `kube_pod_container_status_restarts_total` 值为 `0` (fact-e794b26e1751) | 确认容器从未成功运行过 |

**证据印证说明：**
K8s 事件 (fact-5d6b4ddbd710) 直接给出了错误原因，Metric 状态 (fact-c14607f245be) 与事件中的挂载失败原因一致。配置信息排除了因资源不足被驱逐的可能，重启计数为 0 说明 Pod 尚未到达容器启动阶段，完全符合 `ContainerCreating` 的等待现象。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'unavailable-config' 缺失 → Pod 挂载卷 'input' (Optional: false) 失败 → kubelet MountVolume.SetUp 报错 → 容器处于 ContainerCreating 等待状态
```

### 根因结论

已确认的根因是：Pod `aiops-case-03/workload-5b5fc86c8c-2xgjz` 定义了一个名为 `input` 的卷，该卷引用 ConfigMap `unavailable-config`，且未设置 `Optional: true`。由于该 ConfigMap 在 `aiops-case-03` 命名空间中不存在，kubelet 无法完成挂载操作 (fact-5d6b4ddbd710)，导致 Pod 永久卡在 `ContainerCreating` 状态 (fact-c14607f245be, fact-ee00c6388b58)。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 36.7s
├─ 并发证据采集: 33.2s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-2xgjz: 33.2s (Evidence 23.8s, RCA 9.4s)
└─ 汇总总结: 10.1s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-2xgjz**: pod-imagepull-failed, pod-volume-mount-failed
