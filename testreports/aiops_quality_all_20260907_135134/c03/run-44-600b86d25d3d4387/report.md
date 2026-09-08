## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-2xgjz` | ContainerCreating | workload-5b5fc86c8c-2xgjz is stuck in ContainerCreating/Pending state. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `fact-73286e2fecdd`: MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found | 确认 Volume 绑定失败的直接错误原因 |
| 2 | K8s Event | kubernetes | `fact-1f2ce2d827ba`: 4m17s (x31 over 72m) Unable to attach or mount volumes... timed out waiting for the condition | 证实挂载阻塞为持续发生的严重故障，而非瞬时抖动 |
| 3 | K8s State | kubernetes | `fact-ad5509ef19af`: Pod Status: Pending; `fact-f4c8deed7334`: Container Waiting Reason: ContainerCreating | 确认容器卡在初始化阶段，无法进入运行态 |
| 4 | K8s State | kubernetes | `fact-16f26d739072`: ContainersReady=False (ContainersNotReady: app) | 确认就绪探针条件长期不满足 |
| 5 | Metric | prometheus | `fact-361cf4a568b8`: `kube_pod_container_status_waiting_reason{reason="ContainerCreating"}` = 1 | 指标层面的客观状态印证：容器处于等待创建状态 |
| 6 | Metric | prometheus | `fact-924c30c2cafa`: `kube_pod_container_status_restarts_total` = 0 | 确认容器未发生过启动失败，属于启动阻塞 |

K8s 事件（#1, #2）直接指出了具体的缺失资源标识符 `unavailable-config`。指标（#5）与事件状态相互印证，确认该挂载故障是持续的阻塞原因，而非一次性事件（#6 确认无重启）。日志和链路追踪（Logging/Tracing）因容器未启动未采集到数据，但 Kubernetes 维度的状态与错误信息已构成闭环证据。

## 🎯 根因分析 · g1

### 因果链

```text
Pod  Spec 请求 Volume 'input' 绑定 ConfigMap 'unavailable-config' (非 Optional) → 
Kubelet 执行 MountVolume.SetUp 因找不到 ConfigMap 报错 → 
Pod 持续 Pending / ContainerCreating，无法调度进入 Running 状态 → 
工作负载长时间未就绪且无应用日志产生
```

### 根因结论

已确认的根因是：**Pod 定义中引用的 ConfigMap 'unavailable-config' 在集群中不存在，且该 Volume 配置为非可选（Optional=false）**。

*   该缺失资源直接导致了 `MountVolume.SetUp failed` 错误（`fact-73286e2fecdd`）。
*   由于挂载无法完成，Kubelet 反复重试并触发超时（`fact-1f2ce2d827ba`），致使容器永远卡在 `ContainerCreating` 状态（`fact-f4c8deed7334`, `fact-361cf4a568b8`）。
*   现有 K8s 事件与状态证据充分，可直接发布。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 14.2s
├─ 并发证据采集: 44.5s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-2xgjz: 44.5s (Evidence 36.8s, RCA 7.5s)
└─ 汇总总结: 10.4s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-2xgjz**: pod-imagepull-failed, pod-volume-mount-failed, pod-sandbox-create-failed, pod-config-error
