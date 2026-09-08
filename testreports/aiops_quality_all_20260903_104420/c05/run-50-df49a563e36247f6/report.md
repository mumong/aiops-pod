## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-nhd7v` | ContainerCreating | Pod workload-5dbb5dcd6c-nhd7v in namespace aiops-case-05 stuck in Pending/ContainerCreating status due to Multus CNI network attachment failure. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | multus (kubelet) | `Warning NoNetworkFound ... cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` (记录 46 条，持续 60m+，时间戳如 `60m`, `30s`, `2m7s`) | 直接表明 Multus CNI 在 Pod 所在命名空间内找不到指定的网络配置，为持续性的致命错误。 |
| 2 | K8s Event | kubelet | `Warning FailedCreatePodSandBox ... error loading k8s delegates k8s args: TryLoadPodDelegates: error in getting k8s network for pod: GetNetworkDelegates: failed getting the delegate: ... "unavailable-network" not found` (重复 626 次，累计 138m) | 证明网络配置缺失已导致底层沙箱创建彻底失败，是 Pod 无法进入 Running 状态的核心阻断点。 |
| 3 | K8s State | container status | `container: app, reason: ContainerCreating` | 确认容器当前处于等待状态，未发生 CrashLoop，印证故障发生在容器启动前的网络配置阶段。 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` 值 `1`，标签 `reason="ContainerCreating"` (sample_count=1) | 从监控系统角度佐证 Pod 处于等待状态，且状态持续（无样本量变化表明未恢复）。 |

**证据分析**：
- **K8s State** (fact 3) 显示容器卡在启动前的等待阶段，结合 **Metric** (fact 4) 确认该等待状态的持续性。
- **Multus Event** (fact 1) 与 **Kubelet Event** (fact 2) 形成了完美的因果闭环：Multus 报告缺失网络定义，Kubelet 报告沙箱创建失败，两者均明确指向唯一的失败原因 `unavailable-network`。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置引用不存在的网络定义 (unavailable-network) → Multus CNI 无法解析网络插件依赖 → 沙箱创建被拒绝 (FailedCreatePodSandBox) → Pod 永久卡在 ContainerCreating 状态
```

### 根因结论

**已确认根因：网络配置引用缺失导致 Pod 启动阻塞。**

当前 Pod (`aiops-case-05/workload-5dbb5dcd6c-nhd7v`) 的容器配置中引用了一个名为 `unavailable-network` 的 `NetworkAttachmentDefinition`。由于该资源在 `aiops-case-05` 命名空间中不存在，Multus CNI 插件在初始化网络时抛出 `NoNetworkFound` 错误，进而导致 `kubelet` 无法创建 Pod 沙箱。该机制错误由以下事实直接支撑：
1. **K8s Event (fact 1, 2)**：大量重复的 `NoNetworkFound` 警告和 `FailedCreatePodSandBox` 错误，明确指出找不到 `"unavailable-network"`。
2. **K8s State (fact 3)**：容器状态为 `ContainerCreating`，表明 Pod 调度成功但因网络准备失败而停滞。

**未知/未确认部分**：
输入数据未包含该命名空间下的 CNI 资源列表及历史变更记录，因此无法确认 `unavailable-network` 资源是被意外删除还是从未创建。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 27.7s
├─ 并发证据采集: 53.4s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v: 53.4s (Evidence 41.3s, RCA 11.9s)
└─ 汇总总结: 11.7s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v**: pod-imagepull-failed, pod-sandbox-create-failed
