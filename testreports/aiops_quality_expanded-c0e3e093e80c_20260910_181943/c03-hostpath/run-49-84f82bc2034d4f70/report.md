## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v06/workload` | ContainerCreating | node2 上 /var/lib/aiops-fixture-unavailable-7f394bef/input 路径类型不匹配或不存在，导致 hostPath 挂载失败 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning FailedMount`: `MountVolume.SetUp failed for volume "input" : hostPath type check failed: /var/lib/aiops-fixture-unavailable-7f394bef/input is not a directory` (事实 ID: fact-fd36b9ffe8b7) | 核心证据：指出挂载失败的确切原因是宿主机路径 `/var/lib/aiops-fixture-unavailable-7f394bef/input` 类型不匹配。 |
| 2 | K8s State | Kubernetes | `container.waiting_reason`: `ContainerCreating` (事实 ID: fact-ad70dc62ba33) | 现象验证：Pod 处于等待挂载卷的持续重试或阻塞状态。 |
| 3 | K8s State | Kubernetes | `pod.condition`: `ContainersReady=False` (fact-4123fd357731), `Ready=False` (fact-65e72781fa46), `PodScheduled=True` (fact-898912a3b083) | 现象验证：Pod 成功调度到节点，但因容器未就绪而整体处于非运行状态。 |
| 4 | K8s Event | Kubernetes | `Warning FailedMount`: `Unable to attach or mount volumes: unmounted volumes=[input]... timed out waiting for the condition` (事实 ID: fact-ef5a2a618591) | 现象验证：侧面印证挂载操作在较长窗口（80m）内持续失败。 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{container="app", reason="ContainerCreating"}` = 1 (fact_id: fact-0c434e8f17f5) | 趋势验证：单一采样确认集群监控侧也捕获到应用容器处于 ContainerCreating 等待期。 |

**证据说明**
1. 证据 1 (K8s Event) 给出了具体的失败根因：Kubelet 在校验 hostPath 挂载卷时发现 `/var/lib/aiops-fixture-unavailable-7f394bef/input` 存在但不是目录。这与 Pod 处于 `ContainerCreating` 状态（证据 2）直接对应，因为容器必须等待挂载卷成功才能启动。
2. 证据 3 (Pod Condition) 确认了 Pod 的生命周期状态，Pod 已被调度 (`PodScheduled=True`) 但容器未能就绪，排除了资源不足导致未调度的可能性，将问题聚焦在已分配节点（即 node2，由现象描述可知）的本地存储卷上。
3. 证据 4 和 5 分别从 Event 历史窗口和 Metrics 实时状态两个维度印证了故障的持续性和当前状态。

## 🎯 根因分析 · g1

### 因果链

```text
宿主机目录 /var/lib/aiops-fixture-unavailable-7f394bef/input 不存在或非目录类型 → kubelet 挂载 hostPath 卷校验失败 → 容器无法启动 (ContainerCreating) → Pod 持续处于未就绪状态
```

### 根因结论
**已确认根因**：Pod `aiops-case-v06/workload` 的挂载卷 `input` 在宿主机节点 `node2` 上无法被正确识别。具体表现为 Kubelet 在执行 `MountVolume.SetUp` 时检测到路径 `/var/lib/aiops-fixture-unavailable-7f394bef/input` 的类型校验失败（非目录或不存在）。此故障直接导致应用容器无法启动并持续处于 `ContainerCreating` 状态。

**未知项**：该路径在宿主机上不存在的确切原因（是宿主机环境初始化失败、路径配置错误还是文件权限问题），当前工具未采集到宿主机侧的文件系统状态事实。

---

## 📊 性能统计

```text
├─ 总耗时: 55.9s
├─ 问题定位: 13.6s
├─ 并发证据采集: 29.8s
│  └─ g1 aiops-case-v06/workload: 29.8s (Evidence 23.3s, RCA 6.3s)
└─ 汇总总结: 12.6s
```

📋 Runbook 参考

- **g1 aiops-case-v06/workload**: pod-imagepull-failed, pod-config-error
