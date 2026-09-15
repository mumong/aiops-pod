## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v14/workload` | ContainerCreating | Pod aiops-case-v14/workload 配置了 Multus CNI secondary 网络，但该网络引用的 CNI 插件 'aiops-unavailable' 在调度节点 node2 的 /opt/cni/bin 路径中不存在，导致容器沙箱创建失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod `aiops-case-v14/workload` | 状态 `Pending`，原因 `ContainerCreating` | 确认容器尚未启动，处于阻塞等待阶段 |
| 2 | K8s Event | `kubelet` 事件 | `FailedCreatePodSandBox`: `failed to setup network for sandbox ... plugin type="multus" ... failed to find plugin "aiops-unavailable" in path [/opt/cni/bin /opt/cni/bin]` | 提供决定性证据，明确指出 Multus 插件 `aiops-unavailable` 缺失导致沙箱创建失败 |
| 3 | Metric | Prometheus `kube_pod_container_status_waiting_reason` | 指标值为 `1`，标签 `reason: "ContainerCreating"` | 量化证实 Pod 处于容器创建等待状态 |
| 4 | K8s Config | Pod 配置 | 资源 Request: `5m` CPU, `8Mi` Memory; Limit: `50m` CPU, `32Mi` Memory | 确认资源请求与限制均处于合理低水位，排除资源竞争或 OOM 因素 |
| 5 | K8s Config | Pod 注解 | `k8s.v1.cni.cncf.io/networks: secondary-net` | 确认 Pod 确实配置了调用 `secondary-net` 的多网络接口 |

证据 2 直接指出了失败机制：节点缺少插件二进制文件；证据 1 和 3 分别通过集群状态和监控指标印证了该失败导致的阻塞现象。配置检查（证据 4、5）确认了资源与网络定义的合理性，排除干扰项。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置引用了不存在的 CNI 插件 'aiops-unavailable' (事实 5) → 节点 node2 插件二进制文件缺失 (事实 2) → Kubelet 创建 Pod 沙箱失败 (事实 2) → Pod 阻塞在 ContainerCreating (事实 1, 3)
```

### 根因结论

已确认根因为 **CNI 插件文件缺失导致网络初始化失败**。

Pod `aiops-case-v14/workload` 通过 Multus 配置了 `secondary-net`，该网络定义调用了名为 `aiops-unavailable` 的插件。调度 Pod 所在的节点 `node2` 在 CNI 插件路径 `/opt/cni/bin` 下未找到该插件的二进制文件。这导致 Kubelet 无法完成 Pod 网络沙箱的创建，致使容器无法启动并停留在 `ContainerCreating` 状态（参见事实 2）。

该结论由 Kubernetes 事件（fact-29b4ac9a7e4f）、Pod 状态（fact-24b29eef28b5）及等待指标（fact-19aaf2311dbf）共同支撑。

---

## 📊 性能统计

```text
├─ 总耗时: 52.1s
├─ 问题定位: 17.9s
├─ 并发证据采集: 24.5s
│  └─ g1 aiops-case-v14/workload: 24.5s (Evidence 17.4s, RCA 6.9s)
└─ 汇总总结: 9.6s
```

📋 Runbook 参考

- **g1 aiops-case-v14/workload**: pod-volume-mount-failed
