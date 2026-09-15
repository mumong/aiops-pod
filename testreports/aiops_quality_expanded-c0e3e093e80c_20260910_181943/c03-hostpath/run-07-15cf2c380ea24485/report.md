## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v06/workload` | ContainerCreating | Pod workload (aiops-case-v06) stuck in ContainerCreating (Phase=Pending) due to volume mount failure. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `aiops-case-v06/workload` 处于 `Pending` (phase) / `ContainerCreating` (status)，Pod `Ready` 与 `ContainersReady` 状态均为 `False` | 确立当前故障现象 |
| 2 | K8s Event | Kubernetes | `Warning FailedMount`: kubelet 报告 `hostPath type check failed: /var/lib/aiops-fixture-unavailable-7f394bef/input is not a directory` | 直接定位失败机制 |
| 3 | K8s Event | Kubernetes | `Warning FailedMount`: `timed out waiting for the condition` 关于未挂载/未附加的 `input` 卷 | 确认卷挂载操作处于挂起/超时状态 |
| 4 | K8s Config | Kubernetes | `volumeMounts` 引用名称为 `input` 的卷 | 确立引发问题的卷名称及引用关系 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"} = 1` | 从监控维度佐证容器处于等待创建状态 |
| 6 | Metric | Prometheus | `kube_pod_container_status_restarts_total = 0` | 确认尚未发生过容器启动/重启 |

证据印证：Kubernetes 事件 (2, 3) 直接揭示了 `input` 卷挂载失败的具体错误（`hostPath type check failed`），结合配置事实 (4) 确认该卷名对应挂载点。监控指标 (5) 从宏观上佐证了容器卡在 `ContainerCreating` 阶段，而 (6) 排除了容器反复重启的可能性，确认故障发生在卷挂载及容器启动的前置阶段。

## 🎯 根因分析 · g1

### 因果链

```text
HostPath 卷目标路径在节点上不存在或不是目录 → kubelet 执行 hostPath 类型检查失败 (FailedMount) → 卷挂载阻塞 → Pod 处于 Pending / ContainerCreating 状态
```

### 根因结论

已确认的根因是 **Volume 挂载配置错误**。

Pod `aiops-case-v06/workload` 配置了一个名为 `input` 的 HostPath 卷，其指向目标路径 `/var/lib/aiops-fixture-unavailable-7f394bef/input`。节点上的 kubelet 在执行卷挂载时，发现该路径**不存在或不是一个目录**（事实 `fact-bc7c7067aa9c`），导致 `FailedMount` 事件。由于关键卷挂载失败，容器无法创建，因此 Pod 卡在 `ContainerCreating` 状态（事实 `fact-71f3e5134208`, `fact-8caf9578e6b2`），且未产生任何重试（重启计数为 0，事实 `fact-c5f0a82228d5`）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 14.4s
├─ 并发证据采集: 39.9s
│  └─ g1 aiops-case-v06/workload: 39.9s (Evidence 30.8s, RCA 9.0s)
└─ 汇总总结: 9.7s
```

📋 Runbook 参考

- **g1 aiops-case-v06/workload**: pod-volume-mount-failed, pod-sandbox-create-failed, pod-imagepull-failed, pod-config-error
