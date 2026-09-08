## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-2xgjz` | ContainerCreating | Pod aiops-case-03/workload-5b5fc86c8c-2xgjz 持续处于 ContainerCreating 状态，phase 为 Pending，无法进入 Running。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning FailedMount  7m48s (x20 over 51m)  kubelet  Unable to attach or mount volumes: unmounted volumes=[input]` | 确认挂载阻塞导致 Pod 无法启动，重复频率高 |
| 2 | K8s Event | kubernetes | `Warning FailedMount  2m8s (x33 over 53m)   kubelet  MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` | 明确指出挂载失败的根本原因为 ConfigMap 缺失 |
| 3 | K8s State | kubernetes | `container.waiting_reason`: `ContainerCreating` | 确认 Pod 卡在预启动阶段，未进入运行态 |
| 4 | K8s State | kubernetes | `pod.phase`: `Pending`, `ContainersNotReady` | 确认 Pod 因容器未就绪而保持 Pending 状态 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason{container="app", reason="ContainerCreating"} = 1` | 指标层面印证容器状态确实为 ContainerCreating |
| 6 | K8s Config | kubernetes | `container.resource_limit.memory`: `32Mi`, `container.resource_request.memory`: `8Mi` | 排除资源超限 OOM 或无法调度因素 |

**证据关联说明：**
K8s Event #1 和 #2 提供了直接的错误链路，指出 `volume "input"` 挂载失败；Event #2 进一步指明具体原因是 ConfigMap `unavailable-config` 不存在。K8s State #3 和 #4 从状态层面印证了挂载阻塞导致的 ContainerCreating/Pending 现象。Metric #5 提供了独立于 K8s API 的外部确认（waiting_reason=ContainerCreating），与事件事实完全一致。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'unavailable-config' 不存在 → Pod volume 'input' 挂载失败 (非可选依赖) → kubelet 持续重试挂载 → Pod 卡在 ContainerCreating / Pending
```

### 根因结论

已确认的根因：Pod 的 `volumes` 定义中引用了名为 `input` 的 ConfigMap，且配置为非可选（Optional 缺失或为 false），但在当前 namespace `aiops-case-03` 中不存在该 ConfigMap。这导致 kubelet 执行 `MountVolume.SetUp` 时因找不到配置源而持续报错并阻塞挂载流程（见证据 #2）。由于核心容器 `app` 依赖该挂载卷且无法完成初始化，Pod 持续处于 `ContainerCreating` 等待状态，无法进入 `Running`（见证据 #3, #4, #5）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 24.5s
├─ 并发证据采集: 42.5s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-2xgjz: 42.5s (Evidence 33.2s, RCA 9.2s)
└─ 汇总总结: 9.4s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-2xgjz**: pod-volume-mount-failed
