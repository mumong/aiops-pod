## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v14/workload` | ContainerCreating | Pod aiops-case-v14/workload 通过 Multus CNI 引用了名为 'secondary-net' 的附属网络，该网络配置要求使用 'aiops-unavailable' 插件；由于调度节点 node2 的 CNI 二进制路径 (/opt/cni/bin) 中缺失该插件可执行文件，导致 kubelet 无法创建 Pod Sandbox，进而使 Pod 状态长期停留在 ContainerCreating。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedCreatePodSandBox`: "failed to setup network for sandbox ... plugin type=\"multus\" ... failed to find plugin \"aiops-unavailable\" in path [/opt/cni/bin /opt/cni/bin]" | 直接定位 CNI 插件缺失，阻断网络初始化 |
| 2 | K8s Event | kubernetes | 事件记录表明 Pod 注解 `k8s.v1.cni.cncf.io/networks: secondary-net`，指示通过 Multus 引用附属网络 | 确认 Pod 试图初始化附属网络环境 |
| 3 | K8s State | kubernetes | Pod 条件：`ContainersReady=False`, `ContainersNotReady`; Pod Phase 处于 `Pending` | 确认容器未启动且处于等待状态 |
| 4 | K8s State | kubernetes | 容器状态：`waiting_reason` 为 `ContainerCreating` | 明确当前卡滞的创建阶段 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason` 值 1 (labels: reason="ContainerCreating"); 样本数 1 | 独立监控数据确认当前状态 |
| 6 | K8s Config | kubernetes | 资源请求/限制：CPU (5m/50m), Memory (8Mi/32Mi) | 排除资源不足作为阻塞原因 |

K8s 事件明确指出了 `aiops-unavailable` 插件在指定路径下的缺失是导致 Pod 沙箱创建失败的直接原因。Metric 监控数据与 K8s 事件中的状态码（ContainerCreating）及条件（ContainersReady=False）互相印证，证实了该异常状态的持续性。由于 Pod 在沙箱创建阶段即已阻塞，容器未启动，因此无 Metrics 流量、Logging 日志或 Tracing 数据可用于进一步验证。

## 🎯 根因分析 · g1

### 因果链

```text
调度节点缺少 CNI 插件文件 → 附属网络初始化失败 → Pod 沙箱创建被阻断 → Pod 状态停滞在 ContainerCreating
```

### 根因结论

已确认根因为 **CNI 插件缺失导致附属网络初始化失败**。

具体而言，Pod `aiops-case-v14/workload` 配置了名为 `secondary-net` 的附属网络，但在调度节点 `node2` 的 CNI 二进制路径 (`/opt/cni/bin`) 中未能找到必需的 `aiops-unavailable` 插件可执行文件，导致 kubelet 无法建立 Pod Sandbox [1]。该基础设施缺失直接阻断了容器启动流程，表现为 Pod 状态长期停滞在 `ContainerCreating` [2][3][4]。现有的 K8s 事件与监控指标均一致指向此单点缺失，证据充分。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 16.1s
├─ 并发证据采集: 37.0s
│  └─ g1 aiops-case-v14/workload: 37.0s (Evidence 30.2s, RCA 6.6s)
└─ 汇总总结: 9.3s
```

📋 Runbook 参考

- **g1 aiops-case-v14/workload**: pod-volume-mount-failed
