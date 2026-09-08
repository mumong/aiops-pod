## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-zz82w` | ContainerCreating | Pod `workload-5b5fc86c8c-zz82w` 的 Volume `input` 引用了 ConfigMap `unavailable-config`，该 ConfigMap 在命名空间 `aiops-case-03` 中不存在，导致 kubelet 持续挂载失败且无法启动容器。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedMount`: MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found (fact_id: fact-21955a6f9ebe, fact-271e9751fbe8) | 直接证明挂载失败原因，因 ConfigMap 不存在导致卷挂载被阻断 |
| 2 | K8s State | kubernetes | Pod 状态 `Pending`，条件 `ContainersReady=False`，原因 `ContainersNotReady` (fact_id: fact-0bf0d60a8131) | 确认 Pod 整体处于调度完成但容器未就绪的停滞状态 |
| 3 | K8s State | kubernetes | 容器 `app` 等待原因 `ContainerCreating` (fact_id: fact-edcc7a1e78be) | 确认容器生命周期卡在创建阶段，与卷挂载失败逻辑一致 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason=1`，标签 `reason: ContainerCreating` (fact_id: fact-3a746ef84857) | 独立监控数据印证容器正处于挂载/初始化等待阶段 |

**证据说明**：
Kubernetes Event (证据 1) 明确指出了根因为 ConfigMap `unavailable-config` 缺失，直接阻断了 Volume `input` 的挂载。Pod 状态 (证据 2) 和容器状态 (证据 3) 均反映挂载未通过导致的启动停滞。Metric (证据 4) 从监控维度独立确认了容器处于 `ContainerCreating` 的等待状态，与 Event 诊断的故障机制完全吻合。Logging 和 Tracing 因容器未启动而无法采集，但不影响基于 K8s 核心状态和事件的根因判定。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'unavailable-config' 不存在 → 卷挂载失败 (FailedMount) → 容器无法创建 (ContainerCreating) → Pod 状态 Pending
```

### 根因结论

**已确认根因**：
Pod `workload-5b5fc86c8c-zz82w` 定义中引用了名为 `unavailable-config` 的 ConfigMap，但该资源在命名空间 `aiops-case-03` 中并不存在。这导致 kubelet 在执行卷挂载时失败（证据 1），进而使容器一直处于 `ContainerCreating` 状态（证据 2、3、4），无法进入运行状态。

**支持证据**：
- K8s Event 明确记录了 `configmap "unavailable-config" not found` 错误 (证据 1)。
- Pod 和容器状态均表现为挂载/创建等待 (证据 2, 3)。
- Metric 确认了容器处于 `ContainerCreating` 等待状态 (证据 4)。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 42.3s
├─ 并发证据采集: 58.2s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-zz82w: 58.2s (Evidence 51.9s, RCA 6.2s)
└─ 汇总总结: 9.7s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-zz82w**: pod-imagepull-failed, pod-sandbox-create-failed
