## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v14/workload` | ContainerCreating | Pod workload 处于 ContainerCreating 状态，因 FailedCreatePodSandBox 无法创建沙箱 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `FailedCreatePodSandBox 17m kubelet Failed to create pod sandbox: ... plugin type="multus" name="multus-cni-network" failed (add): [aiops-case-v14/workload:secondary-net]: error adding container to network "secondary-net": failed to find plugin "aiops-unavailable" in path [/opt/cni/bin /opt/cni/bin]` | 直接失败，指出 Multus 尝试配置 secondary-net 网络时，无法在 CNI 路径中找到插件 `aiops-unavailable` |
| 2 | K8s State | Kubernetes | `pod.phase: Pending` | Pod 处于 Pending 状态 |
| 3 | K8s State | Kubernetes | `container.waiting_reason: ContainerCreating` | Pod 容器处于等待创建状态 |
| 4 | K8s Config | Kubernetes | `container.resource_limit.memory: 32Mi` | 配置了极低内存上限，非本次失败主因 |
| 5 | K8s Config | Kubernetes | `container.resource_request.memory: 8Mi` | 配置了极低内存请求，非本次失败主因 |
| 6 | K8s Config | Kubernetes | `container.resource_request.cpu: 5m` | 配置了极低 CPU 请求，非本次失败主因 |
| 7 | K8s Config | Kubernetes | `container.resource_limit.cpu: 50m` | 配置了极低 CPU 上限，非本次失败主因 |
| 8 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"} = 1` (2026-09-14T08:29:26.025000Z) | 监控确认当前 app 容器处于 ContainerCreating 等待状态 |
| 9 | Metric | Prometheus | `kube_pod_container_status_restarts_total = 0` (2026-09-14T08:29:26.025000Z) | 确认容器从未成功启动过，不存在重启现象 |

**证据说明：**
Kubernetes 事件与状态明确指向 `FailedCreatePodSandBox` 错误，且原因明确指出找不到 `aiops-unavailable` CNI 插件。Metric 数据独立确认了当前处于等待状态且重启次数为 0，佐证了 Pod 从未成功运行过。虽然日志与追踪未采集（因容器未启动），但 Kubernetes 层面的 CNI 错误已构成直接且完整的证据链。

## 🎯 根因分析 · g1

### 因果链

```text
node2 节点 CNI 路径 /opt/cni/bin 下缺失 aiops-unavailable 插件二进制文件 → Multus 尝试为 Pod 的 secondary-net 配置网络时加载插件失败 → Kubelet 创建 Pod 沙箱失败 (FailedCreatePodSandBox) → Pod 卡在 ContainerCreating / Pending 状态，无法启动
```

### 根因结论

已确认根因为 **CNI 插件 `aiops-unavailable` 的二进制文件在节点上缺失**。

*   **证据支持**：
    1.  Kubernetes Event (证据 #1) 直接报告了 `failed to find plugin "aiops-unavailable" in path [/opt/cni/bin /opt/cni/bin]`。
    2.  Kubernetes State (证据 #2, #3) 和 Prometheus Metric (证据 #8) 共同确认了 Pod 因网络插件问题导致容器无法创建并处于等待状态。
    3.  Metric (证据 #9) 排除了因容器启动后崩溃重启导致的短暂不稳定，确认是从未启动。

该缺失导致 Multus 无法完成 `secondary-net` 的网络配置，进而阻碍了 Pod 沙箱的建立。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 80.2s
├─ 并发证据采集: 31.9s
│  └─ g1 aiops-case-v14/workload: 31.9s (Evidence 26.3s, RCA 5.4s)
└─ 汇总总结: 12.4s
```

📋 Runbook 参考

- **g1 aiops-case-v14/workload**: pod-imagepull-failed, pod-sandbox-create-failed, pod-volume-mount-failed
