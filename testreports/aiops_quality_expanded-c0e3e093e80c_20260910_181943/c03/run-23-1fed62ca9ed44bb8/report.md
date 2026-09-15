## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-xn974` | ContainerCreating | Pod aiops-case-03/workload-5b5fc86c8c-xn974 处于 Pending/ContainerCreating 状态，无法启动应用。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` | 证实卷挂载失败的直接原因是资源缺失 |
| 2 | K8s State | pod | `status: Pending`, `ContainersReady: False` | 确认容器启动流程被阻塞在初始阶段 |
| 3 | K8s State | pod | `container.waiting_reason: ContainerCreating` | 与 K8s Event 中 FailedMount 状态一致 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` 值为 `1` (reason: `ContainerCreating`) | 外部观测再次验证了容器处于等待挂载/创建状态 |
| 5 | K8s Config | container | `resources.requests.memory: 8Mi`, `resources.limits.memory: 32Mi` | 资源请求值极低，排除因资源竞争导致调度的可能 |

**证据关联说明：**
Metric (`fact-1`) 的状态值与 K8s State (`fact-2`, `fact-3`) 中反映的容器状态完全一致。关键证据在于 K8s Event (`fact-1`) 直接指出了导致上述状态的具体技术阻碍：`ConfigMap 'unavailable-config' not found`。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 配置了引用不存在的 ConfigMap 'unavailable-config' 的卷 → Kubelet 执行 MountVolume.SetUp 时查询资源失败 → VolumeMountFailed → 容器状态停滞在 ContainerCreating，应用无法启动
```

### 根因结论

**已确认根因**：Pod `aiops-case-03/workload-5b5fc86c8c-xn974` 定义中引用的 ConfigMap `unavailable-config` 不存在（证据编号 `fact-1`）。这直接导致 Kubelet 无法挂载卷，进而阻塞了容器的创建过程（证据编号 `fact-2`, `fact-3`），最终表现为 Pod 处于 `Pending` 状态且无业务流量产生。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 27.6s
├─ 并发证据采集: 49.4s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-xn974: 49.4s (Evidence 41.3s, RCA 7.9s)
└─ 汇总总结: 7.3s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-xn974**: pod-imagepull-failed, pod-config-error, pod-volume-mount-failed
