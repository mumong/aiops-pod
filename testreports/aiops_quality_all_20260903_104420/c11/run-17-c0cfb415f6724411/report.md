## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod 'workload' 因存在自定义 finalizer 'aiops.lab/hold' 导致删除流程阻塞，尽管容器已在 35 分钟前因 SIGKILL (Exit Code 137) 终止，Pod 对象仍停留在 Terminating 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `pod.phase` | `Terminating` (持续 35 分钟) | 确认 Pod 对象当前处于阻塞终止状态 |
| 2 | K8s Event | `Stopping container app` | 35 分钟前 kubelet 发出的 Normal 事件 | 证明容器进程在 35 分钟前已被系统级终止，后续无活动 |
| 3 | K8s State | `container.last_exit_code` / `Exit Code: 137` | `137` | 验证容器因 SIGKILL (OOMKill 等) 被强制退出，确认容器层非健康状态 |
| 4 | K8s Config | `container.resource_limit.memory` | `96Mi` | 为 Exit Code 137 提供资源受限的上下文，暗示可能由内存压力引起 |
| 5 | K8s State | `pod.condition` (ContainersReady/Ready) | `ContainersNotReady` | 佐证容器未进入或保留在正常就绪状态，状态与事件相符 |
| 6 | Metric | `kube_pod_container_status_restarts_total` | `0` | 确认该容器此前未发生过重启，排除了容器反复崩溃重建导致的现象 |
| 7 | Metric | `kube_pod_status_phase` | `1` (Running) | 确认集群监控指标当前仍将该 Pod 识别为运行中状态 |

**证据交叉验证说明：**
Kubernetes 事件记录（#2）与退出码（#3）明确显示容器进程在 35 分钟前已终结，但 Pod 的 `phase`（#1）及 Metric 状态（#7）长期停滞在 Terminating/Running。结合容器未重启的记录（#6），现象指向对象生命周期管理层面的阻塞，而非容器内部应用的逻辑故障或反复崩溃。

## 🎯 根因分析 · g1

### 因果链

```text
容器被 SIGKILL 强制终止 (Exit 137) → 容器进程死亡 → API Server 检测到自定义 finalizer 'aiops.lab/hold' → 对象回收流程被强制挂起 → Pod 呈现 Terminating 状态 (持续 35 分钟)
```

### 根因结论

**已确认的根因：** Pod `aiops-case-11/workload` 停留在 `Terminating` 状态的根本原因是其元数据中残留了自定义 finalizer `aiops.lab/hold`。

1. **触发机制**：容器进程在 35 分钟前被系统终止（Exit Code 137），这通常由资源限制（如 OOMKill）或外部强制指令导致（证据 #3, #4, #7）。
2. **直接失败**：尽管容器层已死亡且 kubelet 发出了停止事件，API Server 在清理 Pod 对象前，必须等待 finalizer 列表为空。`aiops.lab/hold` 的存在阻止了 Pod 对象的最终回收。
3. **结果**：Pod 对象卡在 `Terminating` 状态，Metric 监控仍显示其为 `Running`，且不再进行重启（重启计数为 0）。

**缺失的决定性事实**：
- 持有 `aiops.lab/hold` finalizer 的具体控制器或组件状态未识别，无法确认该 finalizer 是“主动保留”还是“控制器挂死”。
- 容器内部触发 SIGKILL (Exit 137) 的具体日志缺失，因此无法定位是 OOM、人为 Kill 还是其他应用层异常。
- 该 finalizer 具体依赖哪个上游 K8s 资源对象不明确，导致无法自动解除该阻塞。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 11.8s
├─ 并发证据采集: 45.6s
│  └─ g1 aiops-case-11/workload: 45.6s (Evidence 36.6s, RCA 8.8s)
└─ 汇总总结: 11.8s
```

📋 Runbook 参考

- 未调用 Runbook
