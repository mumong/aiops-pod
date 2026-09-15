## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v14/workload` | ContainerCreating | Pod aiops-case-v14/workload 处于 ContainerCreating (Pending) 状态，无法分配 Pod IP。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Warning FailedCreatePodSandBox ... failed to create pod sandbox: rpc error ... plugin type="multus" name="multus-cni-network" failed ... error adding container to network "secondary-net": failed to find plugin "aiops-unavailable" in path [/opt/cni/bin /opt/cni/bin]` | 确认网络插件缺失导致沙箱创建失败的直接原因。 |
| 2 | K8s State | pod.status | `Pending` | 确认 Pod 处于不可调度/不可运行的最终挂起状态。 |
| 3 | K8s State | container.waiting_reason | `ContainerCreating` | 确认容器正处于等待网络/存储初始化的阶段。 |
| 4 | K8s Config | resource_limit.memory | `32Mi` | 确认内存限制极低，排除因资源超卖导致的 OOM。 |
| 5 | Metric | kube_pod_container_status_waiting_reason | `1` (reason: `ContainerCreating`, sample_count: 1) | 确认集群中存在持续的等待中容器状态。 |
| 6 | Metric | kube_pod_container_status_restarts_total | `0` (container: `app`, sample_count: 1) | 确认应用容器未尝试启动过，无历史崩溃记录。 |

**证据说明：**
- **维度印证**：
  - K8s 维度中，`Event` (fact-1) 提供的 `FailedCreatePodSandBox` 错误明确指向 CNI 插件路径中缺少 `aiops-unavailable`；这与 `State` (fact-2, 3) 的 `Pending`/`ContainerCreating` 状态完全一致，表明失败发生在调度后的网络初始化阶段。
  - Metric 维度中，`waiting_reason` 的 `1` (fact-5) 与 K8s 事件中的 `ContainerCreating` 状态相吻合，确认了问题在监控层面表现为持续的容器等待状态。
- **排除项**：
  - `resource_limit.memory` (fact-4) 为 `32Mi`，属于极小值，且 Metric 中重启次数为 0 (fact-6)，证明并非资源不足引发崩溃或无法分配。
  - `logging` 与 `tracing` 均为 `not_applicable`，因为容器未成功启动。

## 🎯 根因分析 · g1

### 因果链
```text
节点 node2 CNI 插件路径 [/opt/cni/bin] 缺失 'aiops-unavailable' 二进制文件 → Multus 网络插件初始化 secondary-net 失败 → kubelet 报错 FailedCreatePodSandBox → Pod 状态持续为 Pending/ContainerCreating，分配 Pod IP 失败
```

### 根因结论
**已确认根因**：Pod 配置了使用 Multus 的 `secondary-net` 网络，但在调度节点（Node 2）的 `/opt/cni/bin` 路径中，缺失名为 `aiops-unavailable` 的 CNI 插件二进制文件。这导致 kubelet 在创建 Pod 沙箱（sandbox）并尝试添加容器到网络时，无法找到对应插件，直接抛出 `FailedCreatePodSandBox` 错误，使 Pod 陷入 `ContainerCreating` 状态（见证据 1, 2, 3）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 30.2s
├─ 并发证据采集: 36.3s
│  └─ g1 aiops-case-v14/workload: 36.3s (Evidence 27.8s, RCA 8.3s)
└─ 汇总总结: 10.9s
```

📋 Runbook 参考

- **g1 aiops-case-v14/workload**: pod-imagepull-failed, pod-volume-mount-failed, pod-config-error
