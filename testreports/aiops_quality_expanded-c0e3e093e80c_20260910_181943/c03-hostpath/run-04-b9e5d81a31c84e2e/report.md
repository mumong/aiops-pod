## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v06/workload` | ContainerCreating | HostPath卷定义的目标目录`/var/lib/aiops-fixture-unavailable-7f394bef/input`在节点`node2`上不存在（类型检查失败），导致Kubelet无法挂载卷，Pod卡在`ContainerCreating`阶段。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `FailedMount`：MountVolume.SetUp failed for volume "input" : hostPath type check failed: /var/lib/aiops-fixture-unavailable-7f394bef/input is not a directory | 直接证明 HostPath 卷挂载失败的具体错误原因 |
| 2 | K8s Event | kubelet | `FailedMount`：Unable to attach or mount volumes: unmounted volumes=[input], unattached volumes=[input]: timed out waiting for the condition | 证实挂载操作因目录问题导致持续重试并超时 |
| 3 | K8s State | pod.condition | `ContainersReady`: `False` (ContainersNotReady)；`Ready`: `False` (ContainersNotReady) | 确认 Pod 因容器未就绪而无法满足就绪条件 |
| 4 | K8s State | pod.status / container.waiting_reason | pod.phase: `Pending`；container waiting reason: `ContainerCreating` | 描述当前 Pod 与容器的停滞状态 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason` = `1` (container="app", reason="ContainerCreating") | 独立观测到容器处于 `ContainerCreating` 等待状态 |
| 6 | Metric | prometheus | `kube_pod_status_phase` = `1` (phase="Pending") | 独立观测到 Pod 处于 `Pending` 阶段 |

**证据印证说明**
Kubernetes 的 Warning 事件（#1, #2）明确指出了 `FailedMount` 的原因是 `hostPath type check failed`，这直接解释了 K8s 状态（#3, #4）中 Pod 为何停滞在 `Pending` 和 `ContainerCreating`。同时，Prometheus 指标（#5, #6）提供了同一现象的独立侧面验证（Pending 状态与 ContainerCreating 等待），确认了该异常的持续存在。

## 🎯 根因分析 · g1

### 因果链

```text
节点`node2`上路径`/var/lib/aiops-fixture-unavailable-7f394bef/input`不存在或类型不匹配 → HostPath类型检查失败导致挂载失败 → 容器等待卷就绪，无法启动进入Running状态 → Pod处于Pending/ContainerCreating状态
```

### 根因结论
已确认的根因为 HostPath 卷挂载失败。Pod `workload` 定义的目标目录 `/var/lib/aiops-fixture-unavailable-7f394bef/input` 在节点 `node2` 上不存在（类型检查失败）[事实 #1]，导致 Kubelet 无法完成卷挂载 [事实 #2]，进而致使容器因无法就绪而停滞在 `ContainerCreating` 阶段 [事实 #3, #4, #5]。

目前证据不足以区分该目录缺失是持久化的配置错误（路径拼写错误/未创建）还是节点文件系统发生了临时故障 [事实 unknowns]。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 43.1s
├─ 并发证据采集: 44.3s
│  └─ g1 aiops-case-v06/workload: 44.3s (Evidence 33.6s, RCA 10.6s)
└─ 汇总总结: 9.8s
```

📋 Runbook 参考

- **g1 aiops-case-v06/workload**: pod-volume-mount-failed, pod-imagepull-failed
