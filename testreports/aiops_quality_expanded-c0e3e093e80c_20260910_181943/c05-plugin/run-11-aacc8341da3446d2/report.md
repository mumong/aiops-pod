## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v14/workload` | ContainerCreating | CNI插件缺失：Node 'node2' 的CNI路径 /opt/cni/bin 中缺少Pod依赖的 'aiops-unavailable' 插件二进制文件，导致Multus网络初始化失败，Pod停滞在ContainerCreating阶段。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedCreatePodSandBox: failed to setup network for sandbox "...": plugin type="multus" ... failed to find plugin "aiops-unavailable" in path [/opt/cni/bin /opt/cni/bin]` | 直接指出 Multus 插件加载失败的具体原因及路径 |
| 2 | K8s State | kubernetes | `container.waiting_reason: ContainerCreating` | 确认容器卡在创建阶段，未进入运行态 |
| 3 | K8s Config | kubernetes | `container.resource_limit.memory: 32Mi, cpu: 50m` | 排除资源限制（OOM/CPU Throttling）导致启动失败的可能性 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"} = 1` | 独立观测确认 Pod 处于等待状态，无重启记录 |

**证据印证说明：**
Kubernetes 事件（证据 1）详细描述了 `FailedCreatePodSandBox` 错误，明确指向 Multus 在 `/opt/cni/bin` 中找不到 `aiops-unavailable` 插件；K8s 状态（证据 2）和 Prometheus 指标（证据 4）共同佐证了该异常并非资源不足，而是网络初始化阶段的工具链缺失，导致 Pod 无法完成沙箱创建。

## 🎯 根因分析 · g1

### 因果链

```text
Node 'node2' CNI 路径缺失插件二进制 → Multus 网络初始化失败 (FailedCreatePodSandBox) → 容器无法创建 → 状态滞留 ContainerCreating
```

### 根因结论

已确认根因为 **CNI 插件缺失**（引用证据 1）。节点 `node2` 的 `/opt/cni/bin` 目录中缺少 Multus 所需的 `aiops-unavailable` 插件二进制文件，导致网络沙箱创建失败，Pod 停滞在 `ContainerCreating` 状态（引用证据 1, 2）。

---

## 📊 性能统计

```text
├─ 总耗时: 53.5s
├─ 问题定位: 16.1s
├─ 并发证据采集: 30.4s
│  └─ g1 aiops-case-v14/workload: 30.4s (Evidence 25.2s, RCA 5.1s)
└─ 汇总总结: 7.0s
```

📋 Runbook 参考

- **g1 aiops-case-v14/workload**: pod-volume-mount-failed, pod-imagepull-failed
