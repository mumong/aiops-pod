## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v14/workload` | ContainerCreating | Pod aiops-case-v14/workload 持续处于 ContainerCreating (Pending) 状态，无法分配 Pod IP |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning FailedCreatePodSandBox ... failed to setup network for sandbox ... plugin type="multus" name="multus-cni-network" failed ... failed to find plugin "aiops-unavailable" in path [/opt/cni/bin /opt/cni/bin]` (fact-eef9ede7ca79) | 核心证据：明确报错，节点 CNI 路径中缺失 Multus 插件，直接阻断网络配置 |
| 2 | K8s State | Kubernetes | `container.waiting_reason`: `ContainerCreating` (fact-066518b10d8c) | 状态证据：Pod 卡在沙箱创建阶段，未进入运行态 |
| 3 | K8s Config | Kubernetes | `container.resource_limit.memory`: `32Mi`, `cpu`: `50m` (fact-4e37f90639ac, fact-56570d6e4d69) | 背景证据：容器资源限额极低，排除因资源耗尽导致节点拒绝调度或 OOM 的可能性 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` (reason=`ContainerCreating`) = `1` (fact-2c7521d58ead) | 指标印证：Metrics 侧观测到容器持续处于等待状态，与 K8s 事件中的 `ContainerCreating` 状态一致 |

**证据关系说明：**
1. K8s 侧的 `FailedCreatePodSandBox` 事件与 `ContainerCreating` 状态相互印证，确认故障停留在容器初始化/网络配置阶段。
2. Metric 观测到的 `waiting_reason=ContainerCreating` 为 K8s 事件提供了时序上的持续状态支撑，排除了瞬态故障的可能性。
3. 极低的资源限制配置（32Mi 内存，50m CPU）排除了节点资源争用或内存 OOM 引发异常的干扰因素。

## 🎯 根因分析 · g1

### 因果链

```text
节点 node2 CNI 插件路径 (/opt/cni/bin) 中缺失 'aiops-unavailable' 插件 → Multus 无法配置 secondary-net 网络 → FailedCreatePodSandBox 错误阻断容器创建 → Pod 卡在 ContainerCreating (Pending) 状态，无法分配 Pod IP
```

### 根因结论

**已确认的根因**：节点 `node2` 的 CNI 插件路径 `/opt/cni/bin` 中缺失 `aiops-unavailable` 插件，导致 Multus 在执行 `secondary-net` 网络配置时报错，进而使 Pod 沙箱创建失败。

该结论由以下事实强力支撑：
- K8s 事件 `fact-eef9ede7ca79` 明确指出 `failed to find plugin "aiops-unavailable" in path [/opt/cni/bin /opt/cni/bin]`，直接锁定了缺失插件这一根本原因。
- K8s 状态 `fact-066518b10d8c` 与 Metric 指标 `fact-2c7521d58ead` 共同确认了异常状态为持续的 `ContainerCreating`，与沙箱网络配置失败的机制完全吻合。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 24.5s
├─ 并发证据采集: 41.0s
│  └─ g1 aiops-case-v14/workload: 41.0s (Evidence 32.9s, RCA 7.9s)
└─ 汇总总结: 10.8s
```

📋 Runbook 参考

- **g1 aiops-case-v14/workload**: pod-sandbox-create-failed, pod-imagepull-failed, pod-volume-mount-failed
