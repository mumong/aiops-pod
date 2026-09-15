## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-xn974` | ContainerCreating | Pod aiops-case-03/workload-5b5fc86c8c-xn974 处于 ContainerCreating 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `pod.condition`: Initialized=True, PodScheduled=True, ContainersReady=False (ContainersNotReady), Ready=False | 确认 Pod 调度成功并进入等待容器创建阶段，但容器未完成就绪。 |
| 2 | K8s State | Kubernetes | `container.waiting_reason`: ContainerCreating | 明确指出容器处于创建等待状态，排除了 CrashLoopBackOff 等运行后失败场景。 |
| 3 | K8s Config | Kubernetes | `container.resource_request`: cpu="5m", memory="8Mi" | 提供资源请求背景，低资源配置通常不直接导致挂载阶段阻滞。 |
| 4 | K8s Config | Kubernetes | `container.resource_limit`: cpu="50m", memory="32Mi" | 提供资源限制背景，仅作为状态参考，无直接因果关联。 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` (reason="ContainerCreating", value=1) | 观测证据：确认在 Prometheus 指标窗口内，容器确实卡在 ContainerCreating 阶段。 |
| 6 | Metric | Prometheus | `kube_pod_status_phase` (phase="Pending", value=1) | 观测证据：确认 Pod 在指标层面也被标记为 Pending 状态，与 K8s 状态一致。 |
| 7 | Metric | Prometheus | `kube_pod_container_status_restarts_total` (value=0) | 负面证据：排除了因容器崩溃重启导致的阻滞。 |
| 8 | K8s Event | Kubernetes (RCA事实) | FailedMount (Volume 'input' 引用不存在的 ConfigMap 'unavailable-config') | **核心阻滞原因**：Kubelet 因无法找到 ConfigMap 而阻塞挂载，导致状态停滞。 |

**证据分析说明：**
Kubernetes 状态与 Prometheus 指标（Evidence 1, 2, 5, 6）高度一致，确认了容器处于 `ContainerCreating/Pending` 阶段且无重启历史。结合 K8s Event 中的具体报错事实，排除了资源不足或拉取失败的可能性，将阻滞原因锁定在卷挂载失败。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 引用 ConfigMap 'unavailable-config' → ConfigMap 不存在导致 FailedMount → kubelet 无法完成 Volume 挂载 → Pod 持续处于 ContainerCreating 状态
```

### 根因结论

**已确认的根因：Pod 定义中的 Volume 'input' 挂载了一个不存在的 ConfigMap 'unavailable-config'。**

**分析：**
根据 K8s Event 及诊断数据，Pod 虽然成功调度（PodScheduled=True），但在启动容器前必须挂载卷。由于目标 ConfigMap `unavailable-config` 在命名空间 `aiops-case-03` 中不存在，Kubelet 的挂载操作失败（FailedMount）。这一阻塞机制导致容器无法完成初始化，从而使得 Pod 永远停留在 `ContainerCreating` 状态。证据 8 直接指出了缺失的资源对象，证据 1、2、5 和 6 提供了该状态持续存在的观测验证。

---

## 📊 性能统计

```text
├─ 总耗时: 54.8s
├─ 问题定位: 16.6s
├─ 并发证据采集: 27.9s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-xn974: 27.9s (Evidence 21.1s, RCA 6.6s)
└─ 汇总总结: 10.3s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-xn974**: pod-volume-mount-failed
