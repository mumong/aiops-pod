## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v14/workload` | ContainerCreating | Pod aiops-case-v14/workload 的配置引用了名为 `aiops-unavailable` 的 CNI 插件作为 Multus 附加网络组件，但节点 node2 的 CNI 插件路径中缺少该二进制文件，导致 kubelet 无法建立 Pod Sandboxed，从而卡在 ContainerCreating 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedCreatePodSandBox`: failed to setup network for sandbox ... plugin type="multus" name="multus-cni-network" failed (add): [aiops-case-v14/workload:secondary-net]: error adding container to network "secondary-net": failed to find plugin "aiops-unavailable" in path [/opt/cni/bin /opt/cni/bin] | 直接证明 Multus 在节点路径下找不到 `aiops-unavailable` 插件二进制，导致网络初始化失败 |
| 2 | K8s State | kubernetes | `container.waiting_reason`: reason="ContainerCreating" | 确认 Pod 状态卡在创建阶段，未进入运行态 |
| 3 | Metric | prometheus | `kube_pod_container_status_waiting_reason`: reason="ContainerCreating" (value=1) | 独立于 Kubernetes API 的观测，确认 Pod 持续处于等待创建容器状态 |
| 4 | Metric | prometheus | `kube_pod_container_status_restarts_total`: value=0 | 排除应用进程崩溃重启的可能，确认故障发生在容器启动前 |

上述证据链表明：应用本身未产生崩溃或重启，故障锁定在沙箱（Sandbox）创建阶段。Kubernetes 事件明确指出失败机制是 Multus 插件缺失（`failed to find plugin "aiops-unavailable"`），Metric 数据印证了该 Pod 长时间处于 `ContainerCreating` 状态，排除业务逻辑或容器内应用问题。

## 🎯 根因分析 · g1

### 因果链

```text
Multus 配置引用缺失的 CNI 插件 'aiops-unavailable' → Multus 在节点 [/opt/cni/bin] 中查找失败 → Pod Sandbox 网络初始化失败 (FailedCreatePodSandBox) → Pod 卡在 ContainerCreating/Pending 状态
```

### 根因结论

**已确认根因**：Pod `aiops-case-v14/workload` 配置使用了名为 `aiops-unavailable` 的 CNI 插件作为 Multus 附加网络组件，但调度节点 `node2` 上 `/opt/cni/bin` 路径中不存在该插件二进制文件。

证据 `[1]` 直接捕获了该错误，`[2]` 和 `[3]` 证实了该错误导致的持久化状态。此配置与环境的不匹配直接导致了 Pod 无法完成网络绑定。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 17.8s
├─ 并发证据采集: 39.6s
│  └─ g1 aiops-case-v14/workload: 39.6s (Evidence 31.4s, RCA 8.1s)
└─ 汇总总结: 8.2s
```

📋 Runbook 参考

- **g1 aiops-case-v14/workload**: pod-imagepull-failed, pod-volume-mount-failed
