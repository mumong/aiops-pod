## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-2xgjz` | ContainerCreating | Pod aiops-case-03/workload-5b5fc86c8c-2xgjz 持续处于 ContainerCreating 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | ContainerWaiting reason: ContainerCreating | 确认异常发生的具体阶段 |
| 2 | K8s Config | Kubernetes | container.resource_limit.memory: 32Mi | 确认资源限制，非 OOMKill 风险 |
| 3 | K8s Config | Kubernetes | container.resource_limit.cpu: 50m | 确认资源限制，非 CPU 限流风险 |
| 4 | K8s State | Kubernetes | Pod.phase: Pending | 确认 Pod 尚未进入 Running |
| 5 | K8s Event | Kubernetes | ContainersReady status: False, reason: ContainersNotReady | 确认容器尚未启动就绪 |
| 6 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` = 1 (labels: container=app, reason=ContainerCreating) | 确认 Waiting 状态的唯一性，与 K8s State 一致 |
| 7 | Metric | Prometheus | `kube_pod_status_phase` = 1 (labels: phase=Pending) | 进一步确认 Pod 整体处于 Pending 状态 |
| 8 | Metric | Prometheus | `kube_pod_container_status_restarts_total` = 0 | 确认容器无启动记录，非 CrashLoopBackOff |

证据表明，Pod 处于 `Pending` 且容器等待原因为 `ContainerCreating`，且重启次数为 0。这明确指向容器运行时在创建和挂载阶段受阻，而非运行时异常（如 OOM 或 OOM Kill）。日志与 Tracing 维度因容器未启动而确实为空，不影响当前阻塞阶段的根因定位。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'unavailable-config' 在 namespace 'aiops-case-03' 中不存在 → Volume 'input' 挂载失败 (MountVolume.SetUp failed) → Pod 卡在 ContainerCreating 状态 → 用户可见 Pod 持续处于 Waiting 状态
```

### 根因结论

**已确认的根因：Pod 定义的 Volume 'input' 引用的 ConfigMap 'unavailable-config' 缺失。**

*   **事实依据**：该根因直接解释了为何 Pod 会卡在 `ContainerCreating` 阶段（对应 K8s State `fact-f9a1359dab5a` 与 Metric `fact-7ea26081df44` 的观察）。Volume 挂载失败会导致 Kubelet 无法完成容器的初始化和挂载，从而无法进入 Running 状态。
*   **现象解释**：`ContainerCreating` 状态通常涉及镜像拉取、Volume 挂载等步骤。在此案例中，由于配置了不存在 ConfigMap 的 Volume，挂载操作在 Kubelet 侧失败，导致容器一直处于准备阶段。
*   **证据互证**：
    *   资源限制（32Mi 内存，50m CPU）与 0 次重启排除了资源耗尽导致的崩溃。
    *   Pod 状态 `Pending` 与 `ContainerCreating` 相互印证，说明调度已发生但容器运行时环境构建未完成。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 42.4s
├─ 并发证据采集: 45.6s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-2xgjz: 45.6s (Evidence 39.5s, RCA 6.0s)
└─ 汇总总结: 10.1s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-2xgjz**: pod-volume-mount-failed, pod-sandbox-create-failed
