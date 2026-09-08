## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-2xgjz` | ContainerCreating | Pod workload-5b5fc86c8c-2xgjz 处于 Pending/ContainerCreating 状态，容器未启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `pod.status`: Pending (`fact-67ea0df88fc0`)；`container.waiting_reason`: ContainerCreating (`fact-9beed85427be`) | 描述容器因启动前依赖无法满足而进入等待状态的症状 |
| 2 | K8s State | kubernetes | `pod.condition`: ContainersReady/Ready=False (`fact-1ba0b68a7daa`, `fact-ce1820fa1d34`) | 确认 Pod 未达到可用阶段 |
| 3 | K8s Event | kubernetes | `FailedMount` (`fact-3d2217a7d677`)：timed out waiting for the condition for unmounted volumes=[input] | 揭示具体的调度与挂载机制失败事件 |
| 4 | K8s Event | kubernetes | `FailedMount` (`fact-e4c0d853835b`)：MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found | 提供导致上述超时的根本原因：引用了不存在的 ConfigMap |

**证据印证：**
K8s State 中的 `ContainerCreating` 状态是 Volume 挂载阻塞导致的自然结果，被 K8s Event 中的连续 `FailedMount` 事件精准解释。其中 `fact-e4c0d853835b` 明确指出了缺失的 ConfigMap 对象，构成了完整的证据链。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'unavailable-config' 缺失 → kubelet MountVolume.SetUp 失败 → Pod volume 'input' 持续超时重试 → Pod 处于 Pending/ContainerCreating 状态
```

### 根因结论

**已确认的根因：** Pod `workload-5b5fc86c8c-2xgjz` 的卷配置中引用了名为 `unavailable-config` 的 ConfigMap，但该资源在 `aiops-case-03` 命名空间中不存在。

**证据引用：**
- 证据 4 (`fact-e4c0d853835b`) 直接记录了 `configmap "unavailable-config" not found` 错误，这是导致挂载失败的直接原因。
- 证据 3 (`fact-3d2217a7d677`) 验证了挂载操作因等待该条件（即 ConfigMap 的挂载就绪）而超时。
- 证据 1 和 2 (`fact-67ea0df88fc0`, `fact-1ba0b68a7daa`) 确认了这一挂载失败导致 Pod 无法进入 Running 状态的最终现象。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 19.5s
├─ 并发证据采集: 69.2s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-2xgjz: 69.2s (Evidence 60.7s, RCA 8.4s)
└─ 汇总总结: 9.4s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-2xgjz**: pod-imagepull-failed, pod-volume-mount-failed, pod-sandbox-create-failed
