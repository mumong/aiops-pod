## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v05/workload` | ContainerCreating | Pod aiops-case-v05/workload 的 Volume 'input' 配置引用了 ConfigMap 'workload-input' 中不存在的 Key 'unavailable-key'，导致 kubelet 持续挂载失败 (FailedMount)，容器无法进入 Running 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | pod.phase | phase: Pending | 确认 Pod 处于 Pending 状态，未进入运行阶段 |
| 2 | K8s State | pod.condition | ContainersReady: False (ContainersNotReady), Ready: False (ContainersNotReady) | 确认容器不就绪，且 Pod 核心就绪条件未满足 |
| 3 | K8s State | container.waiting_reason | container: app, reason: ContainerCreating | 明确应用容器卡在挂载/准备阶段 |
| 4 | K8s Event | event.message | "MountVolume.SetUp failed for volume \"input\" : configmap references non-existent config key: unavailable-key" | 直接证据：指出 Volume 'input' 引用的 Key 'unavailable-key' 在 ConfigMap 中不存在 |
| 5 | K8s Event | event.message | "Unable to attach or mount volumes: unmounted volumes=[input]... timed out waiting for the condition" | 佐证挂载失败导致的超时现象，与 #4 形成机制闭环 |
| 6 | Metric | kube_pod_container_status_waiting_reason | value: 1 (reason: ContainerCreating) | 数值层面确认容器处于 ContainerCreating 等待态 |

**证据印证说明：**
- Kubernetes 状态与事件（#1-#4）高度一致：Pod 处于 Pending/ContainerCreating 状态（#1, #3），根本原因为挂载失败（#4），具体失败原因是配置项 Key 缺失（#4），进而导致了超时挂载报错（#5）。
- Metric 数据（#6）作为补充验证，其 `value: 1` 和 `reason: ContainerCreating` 与 K8s State 中的等待原因（#3）完全吻合。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 配置错误（引用不存在的 Key 'unavailable-key'） → 挂载失败机制（FailedMount） → 容器状态等待（ContainerCreating） → Pod 状态 Pending / 现象：应用未就绪
```

### 根因结论

**已确认的根因：**
Pod `aiops-case-v05/workload` 的 Volume `input` 错误引用了 ConfigMap `workload-input` 中不存在的 Key `unavailable-key`。这一配置错误直接导致 kubelet 挂载卷失败（事实 #4），容器无法启动并长期停留在 `ContainerCreating` 状态（事实 #3, #6），最终表现为 Pod 处于 `Pending` 状态（事实 #1, #2）。证据链完整，因果关系明确。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 21.3s
├─ 并发证据采集: 40.1s
│  └─ g1 aiops-case-v05/workload: 40.1s (Evidence 34.5s, RCA 5.4s)
└─ 汇总总结: 8.7s
```

📋 Runbook 参考

- **g1 aiops-case-v05/workload**: pod-volume-mount-failed
