## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v14/workload` | ContainerCreating | Pod aiops-case-v14/workload 卡在 ContainerCreating 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubelet | `FailedCreatePodSandBox... failed to find plugin "aiops-unavailable" in path [/opt/cni/bin /opt/cni/bin]` | 核心证据：指示 Multus 插件加载因 CNI 二进制文件缺失而失败 |
| 2 | K8s State | Kubelet | `pod.status: Pending` | 确认 Pod 卡在 Pending 状态，等待网络准备 |
| 3 | K8s State | Kubelet | `container.waiting_reason: ContainerCreating` | 确认容器正在尝试创建但卡住 |
| 4 | K8s Config | Kubernetes | `cni.projectcalico.org/podIPs:`, `k8s.v1.cni.cncf.io/networks: secondary-net` | 提供上下文：Pod 尝试使用 secondary-net 网络，触发插件调用 |
| 5 | K8s Config | Kubernetes | `container.resource_limit.memory: 32Mi`, `cpu: 50m` | 排除资源限制导致沙箱创建失败 |
| 6 | Metric | Prometheus | `kube_pod_container_status_waiting_reason: 1` (reason=ContainerCreating) | 佐证 K8s 状态，确认等待原因与 K8s State 一致 |

**证据分析：**
所有证据共同指向单一失败路径：Pod 因为配置了 `secondary-net`，被 Multus 调用时找不到 `aiops-unavailable` 插件二进制文件，导致 CNI 网络插件初始化失败，进而导致 Pod Sandbox 无法创建，Pod 保持在 `Pending` / `ContainerCreating` 状态。

## 🎯 根因分析 · g1

### 因果链

```text
节点 node2 的 CNI 路径 ([/opt/cni/bin /opt/cni/bin]) 缺失 CNI 插件二进制文件 aiops-unavailable → Multus 网络插件在配置 secondary-net 时无法加载所需插件 → kubelet 创建 Pod Sandbox 失败，容器无法启动 → Pod 进入 Pending，容器状态为 ContainerCreating
```

### 根因结论

**已确认的根因：** 节点 `node2` 的 CNI 插件路径 (`/opt/cni/bin`) 下缺少 `aiops-unavailable` 插件的二进制文件，导致 `aiops-case-v14/workload` Pod 使用的 Multus 网络插件调用失败（证据 #1）。

**现象关联：**
这直接解释了为什么 Pod 卡在 `Pending` 状态且容器处于 `ContainerCreating`（证据 #2, #3, #6）。资源限制（证据 #5）已被排除，因为错误明确是“找不到插件”，而非资源不足。

**未决项：**
输入事实中未确认节点 `node2` 上其他使用相同插件的 Pod 状态，也未说明该插件二进制文件应存在于何种路径或通过何种方式部署。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 47.3s
├─ 并发证据采集: 42.9s
│  └─ g1 aiops-case-v14/workload: 42.9s (Evidence 34.1s, RCA 8.7s)
└─ 汇总总结: 9.6s
```

📋 Runbook 参考

- **g1 aiops-case-v14/workload**: pod-imagepull-failed, pod-volume-mount-failed
