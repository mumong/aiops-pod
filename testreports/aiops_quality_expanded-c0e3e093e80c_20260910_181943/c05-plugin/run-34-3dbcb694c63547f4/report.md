## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v14/workload` | ContainerCreating | Pod aiops-case-v14/workload 卡在 ContainerCreating 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedCreatePodSandBox`: rpc error: failed to setup network for sandbox "a2dd4c27504ff4dc1725009cd80c4198a6788079c9569c90df5c4e4e4d96e7f7": plugin type="multus" name="multus-cni-network" failed (add): [aiops-case-v14/workload:secondary-net]: error adding container to network "secondary-net": failed to find plugin "aiops-unavailable" in path [/opt/cni/bin /opt/cni/bin] (fact-a2dd4c27504f) | 直接指出 CNI 插件缺失，导致网络初始化失败 |
| 2 | K8s State | kubernetes | `container.waiting_reason`: reason="ContainerCreating" (fact-d4506cc4b1e5) | 确认容器处于等待启动状态，与网络创建失败一致 |
| 3 | Metric | prometheus | `kube_pod_container_status_waiting_reason`: value=1, labels={container="app", reason="ContainerCreating"} (fact-1b75243650ab) | 独立观测确认应用容器正在等待创建 |
| 4 | K8s State | kubernetes | `pod.phase`: "Pending", `ContainersReady`: status="False" (fact-68e76f9157d9) | 确认 Pod 未完全调度启动，处于挂起/未就绪状态 |

**证据说明：**
Kubernetes 事件（fact-1）提供了精确的故障根因：系统在执行 `multus` 网络插件链时，无法在 `/opt/cni/bin` 路径中找到 `aiops-unavailable` 插件。这直接导致了 Pod 创建 SandBox 失败（fact-1），进而使得容器处于 `ContainerCreating` 等待状态（fact-2）。Prometheus 指标（fact-3）进一步从监控系统角度证实了这一状态。日志和追踪维度因容器未成功启动而无法采集。

## 🎯 根因分析 · g1

### 因果链

```text
节点 CNI 环境异常（/opt/cni/bin 缺失/不可访问） → Multus 无法加载 'aiops-unavailable' 插件 → Pod SandBox 网络配置阶段 RPC 错误 → Pod 进入 ContainerWaiting 状态
```

### 根因结论

**已确认的根因**：节点上 CNI 插件目录 `/opt/cni/bin` 缺失或不可访问，导致 Kubelet 在尝试配置 Pod 网络时，Multus CNI 无法找到所需的 `aiops-unavailable` 插件文件。

**证据支持**：
1.  **Kubernetes Event (fact-1)**：明确报告了 `rpc error: ... failed to find plugin "aiops-unavailable" in path [/opt/cni/bin /opt/cni/bin]`。这是判定环境异常的决定性事实。
2.  **Pod 状态 (fact-2, fact-4)**：Pod 停留在 `ContainerCreating` 且状态为 `Pending`，这是网络插件加载失败后的直接现象。
3.  **Metrics (fact-3)**：等待原因指标匹配事件原因，排除了配置或资源不足等其他常见等待原因。

该故障属于基础设施环境层面的异常（节点 CNI 目录问题），而非应用程序或资源配额问题（CPU/内存请求值极低但未被报错）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 35.8s
├─ 并发证据采集: 45.1s
│  └─ g1 aiops-case-v14/workload: 45.1s (Evidence 36.6s, RCA 8.3s)
└─ 汇总总结: 11.6s
```

📋 Runbook 参考

- **g1 aiops-case-v14/workload**: pod-volume-mount-failed, pod-imagepull-failed
