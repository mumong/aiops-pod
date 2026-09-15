## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v14/workload` | ContainerCreating | 节点 node2 的 CNI 插件路径 [/opt/cni/bin] 中缺失 Pod 声明所需的 'aiops-unavailable' 插件二进制文件，导致 Multus 无法完成 sandbox 的网络配置，进而使 Pod 停留在 ContainerCreating 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_reason`: `ContainerCreating` (container: app) | 确认容器处于等待启动状态，未进入运行态 |
| 2 | K8s Event | Kubernetes | `FailedCreatePodSandBox`: `failed to find plugin "aiops-unavailable" in path [/opt/cni/bin /opt/cni/bin]` (plugin: multus-cni-network) | 直接证据：Kubelet 在配置网络时因缺失特定 CNI 插件二进制文件而失败 |
| 3 | K8s Config | Kubernetes | `resource_request.cpu`: `5m`, `resource_request.memory`: `8Mi` | 上下文：确认非资源配额引发的调度阻塞 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason=1` (reason: ContainerCreating) | 验证集群级指标与 Pod 状态一致 |

证据内容说明：
- K8s 事件（证据 2）与状态（证据 1、4）一致指向同一个失败机制：CNI 网络配置阶段异常。
- 资源请求配置（证据 3）排除了资源不足（CPU/Memory）作为根因的可能性。
- 日志与追踪维度因 Pod 未启动而未采集到有效诊断数据。

## 🎯 根因分析 · g1

### 因果链

```text
CNI 插件 'aiops-unavailable' 二进制文件在 node2 [/opt/cni/bin] 中缺失 → Multus 网络插件执行 ADD 操作失败 → Pod Sandbox 创建失败 → Pod 停留在 ContainerCreating 状态
```

### 根因结论

已确认根因：节点 `node2` 的 CNI 插件路径 `/opt/cni/bin` 中缺失 Pod 声明所需的 `aiops-unavailable` 插件二进制文件。

该缺失直接导致 Multus 无法完成 `secondary-net` 的网络配置，进而使得 `kubelet` 在尝试创建 Pod Sandbox 时因找不到插件而报错（证据 2）。这解释了为何 Pod 状态停留在 `ContainerCreating` 且未发生重启（证据 1、4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 49.9s
├─ 并发证据采集: 36.8s
│  └─ g1 aiops-case-v14/workload: 36.8s (Evidence 31.5s, RCA 5.2s)
└─ 汇总总结: 7.4s
```

📋 Runbook 参考

- **g1 aiops-case-v14/workload**: pod-imagepull-failed, pod-sandbox-create-failed, pod-volume-mount-failed
