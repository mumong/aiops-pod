## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v04/workload` | ContainerCreating | Pod workload (aiops-case-v04) stuck in ContainerCreating/Pending with FailedMount errors |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning FailedMount 96s (x15 over 15m) kubelet MountVolume.SetUp failed for volume "input" : secret "unavailable-input" not found` | 核心病因：明确指出了挂载卷 `input` 时因找不到 Secret `unavailable-input` 而失败 |
| 2 | K8s Event | kubernetes | `Warning FailedMount 18s (x7 over 13m) kubelet Unable to attach or mount volumes: unmounted volumes=[input]...` | 持续复现：进一步佐证 `input` 卷的挂载失败是当前持续存在的阻塞状态 |
| 3 | K8s State | kubernetes | `Waiting Reason: ContainerCreating`; `Phase: Pending` | 症状确认：容器卡在初始化前的挂载阶段，未进入运行状态 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"} = 1` | 指标印证：Prometheus 侧观测到容器确实处于等待挂载的状态 |
| 5 | K8s Config | kubernetes | `container "app" resources: cpu_request=5m, memory_request=8Mi, cpu_limit=50m, memory_limit=32Mi` | 排除资源：资源请求/限制极小，排除了因资源不足导致调度和启动阻塞的可能性 |

**证据关联：**
K8s 事件（#1, #2）与 Pod 状态（#3）直接关联，指出了阻塞点在“挂载卷”而非“启动容器”。指标（#4）从观测侧证实了这一“等待”状态。配置（#5）排除了资源瓶颈，反向聚焦于依赖资源（Secret）缺失的问题。

## 🎯 根因分析 · g1

### 因果链

```text
Namespace 'aiops-case-v04' 中缺少 Secret 'unavailable-input' → Kubelet 无法挂载 Pod 定义的 'input' 卷 → 容器沙箱初始化失败 → Pod 长期处于 ContainerCreating/Pending 状态
```

### 根因结论

已确认的根因为 **缺失 Kubernetes Secret**。

Pod 的卷配置引用了名为 `input` 的 Secret，但该 Secret 在 `aiops-case-v04` 命名空间中不存在。这导致 kubelet 在尝试挂载该卷时持续报错（证据 #1, #2），进而阻止了容器沙箱的创建和初始化（证据 #3）。Prometheus 指标（证据 #4）一致反映了该等待状态。

*证据支持：#1, #2, #3, #4*

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 26.9s
├─ 并发证据采集: 35.4s
│  └─ g1 aiops-case-v04/workload: 35.4s (Evidence 29.5s, RCA 5.8s)
└─ 汇总总结: 8.9s
```

📋 Runbook 参考

- **g1 aiops-case-v04/workload**: pod-volume-mount-failed, pod-sandbox-create-failed, pod-imagepull-failed, pod-config-error
