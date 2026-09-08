## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-zz82w` | ContainerCreating | Pod workload-5b5fc86c8c-zz82w 处于 Pending/ContainerCreating 状态，Volume input 挂载持续失败 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning FailedMount MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` | 直接证明 volume 'input' 因 ConfigMap 缺失导致挂载失败 |
| 2 | K8s State | kubernetes | Pod 状态：`Pending`；Container 状态：`ContainerCreating` | 确认 Pod 卡在启动阶段，未进入 Running 状态 |
| 3 | K8s State | kubernetes | Pod Condition: `ContainersReady=False (ContainersNotReady)`, `Ready=False` | 确认容器不可用且 Pod 整体不满足就绪条件 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"} = 1` | 独立确认容器处于等待挂载资源的特定状态 |
| 5 | Metric | prometheus | `kube_pod_status_phase{phase="Pending"} = 1` | 独立确认 Pod 停留在 Pending 阶段 |

**证据分析：**
1. Kubernetes 事件（证据 1）明确指出了根因是 ConfigMap 缺失，这与容器状态（证据 2、3）和 Metrics（证据 4、5）中反映的“等待挂载”和“Pending”状态完全一致。
2. 缺失的 ConfigMap 'unavailable-config' 在输入事实中不存在，无法确认其是意外删除还是从未创建。
3. 日志和 Tracing 因容器未启动而无法获取，但不影响基于 K8s 状态和事件的结论。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'unavailable-config' 缺失 → kubelet 挂载 volume 'input' 失败 → Pod 持续 Pending → 容器无法启动
```

### 根因结论

**已确认根因：** Pod `workload-5b5fc86c8c-zz82w` 的 Volume `input` 强依赖 ConfigMap `unavailable-config`，但该 ConfigMap 在 namespace `aiops-case-03` 中不存在。这导致 kubelet 执行 `MountVolume.SetUp` 时失败，Pod 因此无法从 `Pending` 状态进入 `Running` 状态，表现为 `ContainerCreating` 持续等待。

**证据支撑：**
- K8s Event 报错 `configmap "unavailable-config" not found` 直接定位了缺失资源。
- K8s State 和 Metrics 一致显示 Pod 卡在挂载阶段，排除了启动后崩溃的可能。

**未知项：** 无法判断 ConfigMap `unavailable-config` 是意外删除还是从未创建，但这不影响挂载失败的直接原因判定。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 15.2s
├─ 并发证据采集: 47.8s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-zz82w: 47.8s (Evidence 39.5s, RCA 8.2s)
└─ 汇总总结: 9.0s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-zz82w**: pod-volume-mount-failed
