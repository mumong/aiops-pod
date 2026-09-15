## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v06/workload` | ContainerCreating | Pod aiops-case-v06/workload 卡在 ContainerCreating 状态（Pending），无法启动容器 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet (x15 over 14m) | `MountVolume.SetUp failed for volume "input" : hostPath type check failed: /var/lib/aiops-fixture-unavailable-7f394bef/input is not a directory` | 直接报错，指出挂载失败的根本原因是路径类型检查未通过 |
| 2 | K8s State | Pod | `status: Pending`, `ContainersReady: False` (reason: ContainersNotReady, message: containers with unready status: [app]) | 证实 Pod 卡在启动前阶段，无法进入 Ready 状态 |
| 3 | K8s Event | kubelet (x6 over 12m) | `Unable to attach or mount volumes: unmounted volumes=[input], unattached volumes=[input]: timed out waiting for the condition` | 进一步印证挂载动作处于等待超时状态 |
| 4 | K8s Config | Pod Spec | `volume name: "input"`, `hostPath path: /var/lib/aiops-fixture-unavailable-7f394bef/input` | 提供导致挂载失败的具体配置路径 |
| 5 | K8s State | Container | `reason: ContainerCreating` | 明确容器当前正处于尝试创建/挂载卷的阶段 |
| 6 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"} = 1` | 从监控指标确认容器处于等待原因对应的状态，与事件一致 |

**证据链关联说明：**
Kubernetes 事件（Fact 1 & 3）直接指出了故障原因为“HostPath 类型检查失败”，即路径 `/var/lib/aiops-fixture-unavailable-7f394bef/input` 在 Node2 上不是目录（Fact 4）。这一机制导致了 Pod 处于 Pending 状态（Fact 2），容器无法推进到 ContainerCreating（Fact 5），进而反映在 Prometheus 指标上为 waiting_reason=ContainerCreating（Fact 6）。

## 🎯 根因分析 · g1

### 因果链

```text
HostPath 路径 '/var/lib/aiops-fixture-unavailable-7f394bef/input' 在节点上不存在或非目录 → MountVolume.SetUp 执行失败 → Volume 'input' 挂载阻断 → Pod aiops-case-v06/workload 卡在 ContainerCreating/Pending 状态
```

### 根因结论

**已确认的根因**：Pod `aiops-case-v06/workload` 挂载的 HostPath 卷 `input` 配置的路径 `/var/lib/aiops-fixture-unavailable-7f394bef/input` 在目标节点（Node2）上不符合要求（不是目录）。

**证据支撑**：
1. **Kubelet 事件 (Fact 1, 3)**：连续报错 `hostPath type check failed` 和 `timed out waiting for the condition`，明确指出挂载失败的具体原因和受阻的卷名称 `input`。
2. **Pod 配置 (Fact 4)**：确认了卷名为 `input`，且对应的宿主机路径即为报错中提及的路径。
3. **容器状态 (Fact 5, 6)**：容器卡在 `ContainerCreating`，与挂载阶段受阻的物理现象完全吻合。

**结论**：故障完全由卷挂载配置（HostPath 路径/类型不匹配）导致，排除资源限制或容器内部问题。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 18.5s
├─ 并发证据采集: 41.2s
│  └─ g1 aiops-case-v06/workload: 41.2s (Evidence 31.7s, RCA 9.5s)
└─ 汇总总结: 11.3s
```

📋 Runbook 参考

- **g1 aiops-case-v06/workload**: pod-volume-mount-failed
