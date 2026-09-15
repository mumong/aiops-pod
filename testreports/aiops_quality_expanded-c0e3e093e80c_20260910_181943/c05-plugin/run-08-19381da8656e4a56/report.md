## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v14/workload` | ContainerCreating | Pod aiops-case-v14/workload 处于 ContainerCreating 状态，Sandbox 创建失败 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `FailedCreatePodSandBox`: failed to setup network for sandbox "a2dd4c...": plugin type="multus" name="multus-cni-network" failed... error adding container to network "secondary-net": failed to find plugin "aiops-unavailable" in path [/opt/cni/bin /opt/cni/bin] | 定位失败机制：Multus 插件 `aiops-unavailable` 缺失导致网络配置阻塞 |
| 2 | K8s State | Kubernetes | Pod `aiops-case-v14/workload` 状态 `ContainerCreating` | 呈现启动停滞现象 |
| 3 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"} = 1` | 确认 Pod 持续处于创建等待状态 |

证据表明，Pod 因缺少指定的 CNI 插件二进制文件而无法完成网络初始化，导致始终卡在 ContainerCreating 阶段。

## 🎯 根因分析 · g1

### 因果链

```text
节点 node2 缺少 CNI 插件 'aiops-unavailable' 二进制文件 → Multus 尝试创建网络沙箱时因找不到插件报错 → Pod 沙箱创建失败，状态停留在 ContainerCreating → 容器无法启动 (waiting_reason: ContainerCreating)
```

### 根因结论

已确认的根因是节点 `node2` 缺失 `aiops-unavailable` CNI 插件二进制文件。由于 Pod `aiops-case-v14/workload` 配置了二级网络 `secondary-net`，调度至该节点后，Multus 插件在 `/opt/cni/bin` 目录下找不到 `aiops-unavailable` 二进制文件，导致网络沙箱创建失败（证据 1），进而使 Pod 无法脱离 `ContainerCreating` 状态（证据 2, 3）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 29.4s
├─ 并发证据采集: 36.5s
│  └─ g1 aiops-case-v14/workload: 36.5s (Evidence 28.1s, RCA 8.3s)
└─ 汇总总结: 6.5s
```

📋 Runbook 参考

- **g1 aiops-case-v14/workload**: pod-imagepull-failed, pod-volume-mount-failed, pod-pending-unschedulable, pod-sandbox-create-failed
