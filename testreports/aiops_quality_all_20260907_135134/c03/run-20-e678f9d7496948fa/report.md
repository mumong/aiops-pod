## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-2xgjz` | ContainerCreating | Pod workload-5b5fc86c8c-2xgjz 卡在 ContainerCreating/Pending 状态，容器未启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | pod.status: Pending (fact-abc4d3b887ac) | 描述 Pod 当前的停滞状态 |
| 2 | K8s Event | kubernetes | FailedMount: MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found (fact-f25f2c97dbaf) | 直接指出根因：缺少 ConfigMap |
| 3 | K8s Event | kubernetes | FailedMount: unmounted volumes=[input]: timed out waiting for the condition (fact-a885bc220824) | 证实挂载动作在超时 |
| 4 | Metric | prometheus | kube_pod_container_status_waiting_reason {container="app", reason="ContainerCreating"} = 1 (fact-dbfddef47055) | 佐证容器处于等待状态 |
| 5 | K8s Config | kubernetes | container.resource_limit.memory=32Mi (fact-00ee60ec427a) | 排除 OOMKilled 等资源硬限制导致的状态异常 |

**证据分析**：
证据 1 确认了 Pod 的整体状态，证据 2 和 3 提供了明确的故障细节，直接关联到“input”卷的挂载失败，其核心原因是引用了不存在的 ConfigMap `unavailable-config`。证据 4 从指标维度交叉验证了容器处于 ContainerCreating 的等待阶段。证据 5 排除了内存限制导致的资源冲突。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'unavailable-config' 在 namespace 'aiops-case-03' 中不存在 → Pod spec 强制挂载该卷 (Optional: false) → kubelet 挂载卷失败 (MountVolume.SetUp failed) → Pod 卡在 Pending / ContainerCreating 状态
```

### 根因结论

**已确认根因**：Pod 定义中引用了一个在 `aiops-case-03` 命名空间中不存在的 ConfigMap `unavailable-config`。由于该卷配置了强制挂载（即 `Optional: false`），kubelet 在启动容器前无法完成卷挂载，直接导致 `MountVolume.SetUp failed`，Pod 因此停滞在 Pending/ContainerCreating 状态。

**证据支撑**：
- `FailedMount` 事件原文（fact-f25f2c97dbaf）明确报出 `configmap "unavailable-config" not found`。
- Pod 状态（fact-abc4d3b887ac）和容器等待原因（fact-4f22d17b57e6）与上述挂载失败逻辑一致。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 18.2s
├─ 并发证据采集: 41.7s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-2xgjz: 41.7s (Evidence 32.8s, RCA 8.8s)
└─ 汇总总结: 9.1s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-2xgjz**: pod-volume-mount-failed, pod-sandbox-create-failed, pod-imagepull-failed
