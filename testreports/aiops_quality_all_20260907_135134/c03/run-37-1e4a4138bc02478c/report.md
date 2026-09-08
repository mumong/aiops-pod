## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-2xgjz` | ContainerCreating | Pod 的 Volume 'input' 引用了不存在的 ConfigMap 'unavailable-config'，导致 kubelet 挂载失败，容器无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `waiting_reason=ContainerCreating` | 直接反映容器因前置依赖未就绪而处于阻塞状态 |
| 2 | K8s Event | kubernetes | `FailedMount: MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` | 提供根因的直接错误证据，指明挂载失败原因 |
| 3 | K8s State | kubernetes | `pod.phase=Pending`, `ContainersNotReady` | 确认 Pod 整体处于不可用状态 |

**证据说明**：
指标与日志维度因 Pod 未进入运行状态而缺乏诊断价值。K8s 事件与状态事实相互印证：事件日志明确记录了挂载缺失 ConfigMap `unavailable-config` 的具体错误，直接解释了为什么 `ContainerCreating` 状态长期停滞且 Pod 无法 `Ready`。

## 🎯 根因分析 · g1

### 因果链

```text
未存在的 ConfigMap 'unavailable-config' → kubelet 挂载 Volume 'input' 失败 → Pod 卡在 ContainerCreating (Pending) → 容器无法启动
```

### 根因结论

已确认根因为 **Pod 依赖的 ConfigMap 'unavailable-config' 不存在**。

根据输入事实 (证据 #2)，kubelet 在执行 Volume 挂载步骤时报错 `configmap "unavailable-config" not found`，导致挂载失败。这一挂载阻塞使 Pod 无法完成容器初始化，进而停留在 `Pending` / `ContainerCreating` 状态（证据 #1, #3），表现为容器无法启动。

---

## 📊 性能统计

```text
├─ 总耗时: 9.7m
├─ 问题定位: 26.1s
├─ 并发证据采集: 547.7s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-2xgjz: 547.7s (Evidence 543.2s, RCA 4.4s)
└─ 汇总总结: 5.7s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-2xgjz**: pod-volume-mount-failed
