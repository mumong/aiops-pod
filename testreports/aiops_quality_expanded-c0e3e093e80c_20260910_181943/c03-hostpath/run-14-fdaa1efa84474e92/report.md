## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v06/workload` | ContainerCreating | Pod aiops-case-v06/workload 处于 ContainerCreating 状态，无法启动容器 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning FailedMount 78s (x15 over 15m) ... MountVolume.SetUp failed for volume "input" : hostPath type check failed: /var/lib/aiops-fixture-unavailable-7f394bef/input is not a directory` | 直接确认 hostPath 卷挂载失败的具体错误及持续时间 |
| 2 | K8s Event | Kubernetes | `Warning FailedMount 2m11s (x6 over 13m) ... Unable to attach or mount volumes: unmounted volumes=[input] ... timed out waiting for the condition` | 佐证卷挂载操作的阻塞状态与超时行为 |
| 3 | K8s State | Kubernetes | `pod.condition`: `ContainersReady=False`, `Ready=False` (reason: ContainersNotReady) | 确认容器未能进入就绪状态，反映阻塞发生在容器启动前阶段 |
| 4 | K8s State | Kubernetes | `pod.phase/status`: `Pending` | 确认 Pod 处于调度后、容器创建前的挂起阶段 |
| 5 | K8s Event | Kubernetes | `container.waiting_reason`: `ContainerCreating` (Container: app) | 确认应用容器正处于尝试创建的等待状态 |
| 6 | Metric | Prometheus | `kube_pod_container_status_waiting_reason`: value=`1` (Container: app, Reason: ContainerCreating, sample_count: 1) | 独立从监控维度确认容器处于等待状态 |

**证据关联分析：**
Kubernetes 事件（证据 1、2）明确指出挂载卷 `input` 时因 `hostPath` 路径 `/var/lib/aiops-fixture-unavailable-7f394bef/input` 校验失败（非目录）而受阻。这种底层的挂载失败导致 Pod 状态停滞在 `Pending`（证据 4），进而使得容器无法完成启动，表现为 `ContainerCreating` 状态（证据 3、5、6）。各证据共同指向卷资源不可用这一单点故障，且不存在冲突信息。

## 🎯 根因分析 · g1

### 因果链
```text
hostPath volume 'input' 指向的路径不存在/类型不符 → Node kubelet 挂载卷失败 → 卷挂载操作阻塞/超时 → 容器无法启动 (ContainerCreating)
```

### 根因结论
已确认根因为：Pod 定义的 volume `input` 挂载了一个在节点上无效的 `hostPath` 路径 `/var/lib/aiops-fixture-unavailable-7f394bef/input`。
依据证据 1 和 2，kubelet 在尝试挂载该卷时明确报告了 `hostPath type check failed` 且随后发生了挂载超时。这直接阻断了容器创建流程，导致 Pod 处于 `Pending` 状态且应用容器停留在 `ContainerCreating`（证据 3、4、5）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 16.3s
├─ 并发证据采集: 43.5s
│  └─ g1 aiops-case-v06/workload: 43.5s (Evidence 34.2s, RCA 9.2s)
└─ 汇总总结: 9.6s
```

📋 Runbook 参考

- **g1 aiops-case-v06/workload**: pod-sandbox-create-failed, pod-volume-mount-failed
