## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v06/workload` | ContainerCreating | HostPath卷挂载失败：Pod aiops-case-v06/workload 定义的 Volume 'input' 映射的宿主机路径 '/var/lib/aiops-fixture-unavailable-7f394bef/input' 在节点 node2 上不存在或类型不匹配（非目录），导致 kubelet 无法完成挂载操作，容器持续处于 Waiting 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | pod condition | ContainersReady=False, Ready=False (reason: ContainersNotReady, msg: containers with unready status: [app]) | 确认容器 `app` 持续处于未就绪状态 |
| 2 | K8s Event | kubelet mount failure (fact-9c057d98f758) | `MountVolume.SetUp failed for volume "input" : hostPath type check failed: /var/lib/aiops-fixture-unavailable-7f394bef/input is not a directory` | 直接证明 HostPath 卷挂载失败的具体原因（路径非目录或不存在） |
| 3 | K8s Event | kubelet timeout (fact-9e25c459aaa1) | `timed out waiting for the condition` | 证实挂载操作长期阻塞直至超时，是导致 Pod Pending 的直接技术原因 |
| 4 | K8s State | pod phase | phase: Pending | 确认 Pod 因挂载问题停留在 Pending 阶段 |
| 5 | Metric | kube_pod_container_status_waiting_reason | 1 (reason: ContainerCreating) | 独立确认容器正在等待资源或挂载，支持挂载阻塞现象 |
| 6 | Metric | kube_pod_container_status_restarts_total | 0 | 证实容器从未启动成功，排除因 OOM 或应用崩溃导致的重启 |
| 7 | K8s Config | resource limits/requests | cpu: 50m/5m, memory: 32Mi/8Mi | 资源限制极低，与挂载失败的硬件/路径问题无关 |

**证据说明：**
- **事实 2（真实错误）** 与 **事实 3（超时机制）** 直接印证了挂载操作失败是物理层面的 HostPath 错误，而非资源不足或网络问题。
- **事实 1 & 4（Pod 状态）** 与 **事实 5（Metric 等待原因）** 一致，表明等待原因源于挂载步骤，而非拉取镜像。
- **事实 6（重启次数为 0）** 排除了应用运行时故障导致的问题，锁定故障发生在容器启动前。

## 🎯 根因分析 · g1

### 因果链

```text
宿主机节点 node2 路径 '/var/lib/aiops-fixture-unavailable-7f394bef/input' 不存在或非目录 → kubelet 执行 HostPath 挂载前置检查失败 (hostPath type check failed) → 卷 "input" 挂载超时并报错 → Pod aiops-case-v06/workload 卡在 Pending/ContainerCreating 状态，容器 app 无法启动
```

### 根因结论

已确认的根因是 **HostPath 卷挂载失败**。

Pod `aiops-case-v06/workload` 中定义的 Volume `input` 映射到节点 `node2` 上的宿主机路径 `/var/lib/aiops-fixture-unavailable-7f394bef/input`。根据证据事实 `fact-9c057d98f758`，kubelet 在执行挂载操作时发现该路径“不是目录”（is not a directory）或不存在，导致挂载前置检查（type check）失败。这一物理路径不匹配问题直接导致了后续持续的挂载超时（事实 `fact-9e25c459aaa1`），使得 Pod 无法进入 Running 状态，呈现为 Pending 及 ContainerCreating 的等待现象。现有证据已充分覆盖 K8s 状态、事件及指标，确凿地指向此配置/环境不一致问题。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 22.2s
├─ 并发证据采集: 34.5s
│  └─ g1 aiops-case-v06/workload: 34.5s (Evidence 29.3s, RCA 5.1s)
└─ 汇总总结: 11.6s
```

📋 Runbook 参考

- **g1 aiops-case-v06/workload**: pod-imagepull-failed
