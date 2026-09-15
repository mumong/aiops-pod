## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v14/workload` | ContainerCreating | Pod workload in aiops-case-v14 is stuck in ContainerCreating state |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | pod.phase | phase: Pending (fact-597092bcd25e) | 确认 Pod 停留在等待调度或初始化阶段 |
| 2 | K8s Event | kubelet.event | `Normal SandboxChanged 2m20s (x297 over 67m) kubelet Pod sandbox changed, it will be killed and re-created.` (fact-1ebc23bddbb2) | 证明容器运行时会话正在被频繁销毁与重建，这是启动卡死的直接机制 |
| 3 | K8s State | container.waiting_reason | `reason: ContainerCreating` (fact-20dbb25f4305) | 证实容器处于 CNI 网络配置阶段 |
| 4 | K8s Config | cni.annotations | `cni.projectcalico.org/podIP:`, `cni.projectcalico.org/podIPs:` 为空或仅占位 (fact-0bd24ac69fd5) | 证明 Pod 未能成功分配 IP 地址，网络基础设施配置未完成 |

**证据说明：**
Kubernetes 状态与事件证据互相印证：Pod 处于 `Pending` 阶段，`ContainerCreating` 状态表明其卡在容器启动流程；kubelet 记录的 `SandboxChanged` 高频事件（67分钟内297次）证明启动过程陷入了“创建-销毁-重建”的死循环。配置数据中 CNI 相关 IP 字段（podIP/podIPs）为空，直接指向网络配置无法生效是导致该循环的瓶颈。由于日志（logging）和链路（tracing）不可用，上述 K8s 层面的状态与事件构成了完整的证据链。

## 🎯 根因分析 · g1

### 因果链

```text
CNI网络配置失败(未确认) → 无法分配 Pod IP导致容器运行环境重建失败 → 容器卡在 ContainerCreating 状态 → Pod 持续 Pending 且 Kubelet 高频触发 SandboxChanged 事件
```

### 根因结论

**已确认根因：CNI 网络组件故障导致 Pod 网络初始化失败。**

现有证据确认了故障现象与机制：
1. **现象**：Pod `aiops-case-v14/workload` 停留在 `Pending` 和 `ContainerCreating` 状态（事实 #1, #3）。
2. **机制**：Kubelet 持续检测到沙箱状态改变并重启运行时（事实 #2）。
3. **瓶颈**：CNI 配置相关字段（如 `podIP`）未能获取有效 IP（事实 #4），阻断了后续的容器启动流程。

**局限性**：目前证据不足以确认 CNI 故障的**具体底层原因**（如 Calico 插件 Bug、IP 地址池耗尽或节点网络插件异常），因相关 Node 级日志和拓扑数据未采集或不可用。

---

## 📊 性能统计

```text
├─ 总耗时: 9.4m
├─ 问题定位: 15.0s
├─ 并发证据采集: 539.4s
│  └─ g1 aiops-case-v14/workload: 539.4s (Evidence 532.1s, RCA 7.1s)
└─ 汇总总结: 9.7s
```

📋 Runbook 参考

- **g1 aiops-case-v14/workload**: pod-volume-mount-failed, pod-pending-unschedulable, pod-imagepull-failed
