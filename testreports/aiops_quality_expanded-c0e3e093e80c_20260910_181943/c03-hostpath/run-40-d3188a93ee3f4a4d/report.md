## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v06/workload` | ContainerCreating | Pod workload 持续处于 ContainerCreating 状态，无法启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes (kubelet) | `Warning FailedMount 7m5s (x40 over 72m) kubelet MountVolume.SetUp failed for volume "input" : hostPath type check failed: /var/lib/aiops-fixture-unavailable-7f394bef/input is not a directory` | 直接证实 Pod 挂载卷失败的具体原因：宿主机节点路径检查不通过 |
| 2 | K8s Event | Kubernetes (kubelet) | `Warning FailedMount 113s (x31 over 70m) kubelet Unable to attach or mount volumes: unmounted volumes=[input], unattached volumes=[input]: timed out waiting for the condition` | 补充证实挂载操作的长时序超时状态，支撑故障持续时间 |
| 3 | K8s State | Kubernetes (Pod) | `status: Pending, phase: Pending, container: app reason: ContainerCreating` | 描述 Pod 的持续异常状态，与挂载失败的事实保持一致 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"} = 1` | 监控指标独立确认容器处于等待状态，与 K8s 状态吻合 |
| 5 | Metric | Prometheus | `kube_pod_container_status_restarts_total{container="app"} = 0` | 排除应用运行中崩溃重启动画的可能，确认问题处于启动前置阶段 |

**证据分析**：
Kubernetes 的 `FailedMount` 事件明确指出了宿主机节点上 `/var/lib/aiops-fixture-unavailable-7f394bef/input` 路径缺失或类型错误（非目录），这是导致 `input` 卷挂载超时失败的根本原因。这一事实与 Pod 持续卡在 `ContainerCreating` 状态及 `kube_pod_container_status_waiting_reason` 指标完全吻合。

## 🎯 根因分析 · g1

### 因果链

```text
宿主机 node2 路径 /var/lib/aiops-fixture-unavailable-7f394bef/input 缺失或类型错误 → kubelet 执行 MountVolume.SetUp 时 HostPath 类型检查失败 → Volume 'input' 挂载持续超时/失败 → Pod 持续处于 ContainerCreating 状态，无法启动
```

### 根因结论

已确认的根因为：Pod 配置中引用的 HostPath 卷所对应的宿主机节点路径 (`/var/lib/aiops-fixture-unavailable-7f394bef/input`) 在调度目标节点 (`node2`) 上不存在，或者存在但并非目录类型。

该缺失/错误直接导致了 `MountVolume.SetUp` 检查失败（证据 #1、#2），进而引发挂载操作超时失败，使得 Pod 无法完成存储卷挂载步骤，最终停滞在 `ContainerCreating` 状态（证据 #3）。Prometheus 指标独立证实了这一挂载依赖导致的等待现象（证据 #4）。

缺失的确切事实为：该路径在 `node2` 上缺失的具体运维原因（如是否被清理脚本删除）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 15.6s
├─ 并发证据采集: 43.8s
│  └─ g1 aiops-case-v06/workload: 43.8s (Evidence 36.2s, RCA 7.5s)
└─ 汇总总结: 10.1s
```

📋 Runbook 参考

- **g1 aiops-case-v06/workload**: pod-volume-mount-failed
