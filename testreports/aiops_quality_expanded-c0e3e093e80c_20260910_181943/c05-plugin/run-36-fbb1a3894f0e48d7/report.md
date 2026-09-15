## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v14/workload` | ContainerCreating | Pod aiops-case-v14/workload 处于 ContainerCreating (Pending) 状态 54分钟，Sandbox 创建失败，Pod 未获取 IP |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `FailedCreatePodSandBox 54m kubelet ... failed to setup network for sandbox "a2dd4c27504ff4dc1725009cd80c4198a6788079c9569c90df5c4e4e4d96e7f7": plugin type="multus" name="multus-cni-network" failed (add): [aiops-case-v14/workload:secondary-net]: error adding container to network "secondary-net": failed to find plugin "aiops-unavailable" in path [/opt/cni/bin /opt/cni/bin]` | **确证**：直接指出网络插件 "aiops-unavailable" 缺失导致 Sandbox 创建失败 |
| 2 | K8s State | Kubernetes | `Pod status: Pending` | **现象**：Pod 长期停滞在 Pending 状态，未进入运行或错误重启循环 |
| 3 | Metric | Prometheus | `kube_pod_container_status_waiting_reason = 1` (reason: `ContainerCreating`) | **现象**：监控确认容器等待状态持续存在 |
| 4 | Metric | Prometheus | `kube_pod_status_phase = 1` (phase: `Pending`), `restarts = 0` | **排除**：确认 Pod 未处于 Succeeded 或其他状态，且重启次数为 0，非应用逻辑崩溃 |

当前异常证据高度一致。Kubernetes 事件的报错原文（第 1 行）直接说明了底层机制，而 Metrics 仅验证了该结果导致的持续等待状态（第 2、3 行），无冲突信息。Logging/Tracing 因容器未启动（第 4 行），无相关诊断数据。

## 🎯 根因分析 · g1

### 因果链

```text
目标节点 CNI 插件 "aiops-unavailable" 缺失 → Multus 网络初始化失败 → Pod Sandbox 创建被 kubelet 拒绝 → Pod 永久处于 ContainerCreating (Pending) 状态
```

### 根因结论

**已确认根因**：Pod `aiops-case-v14/workload` 的网络配置引用了名为 `aiops-unavailable` 的 CNI 插件，但该插件在当前工作节点（node2）的二进制路径 `/opt/cni/bin` 中不存在。

- 证据编号 #1 明确展示了 `failed to find plugin "aiops-unavailable"` 的报错，这是导致 `FailedCreatePodSandBox` 的直接技术原因。
- 证据编号 #2、#3 和 #4 验证了该错误导致了长期的网络初始化停滞，且容器因启动失败而未发生重启。
- 现有证据链完整，足以判定故障根因为节点上缺失对应的 CNI 插件二进制文件。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 17.1s
├─ 并发证据采集: 35.6s
│  └─ g1 aiops-case-v14/workload: 35.6s (Evidence 27.1s, RCA 8.3s)
└─ 汇总总结: 9.4s
```

📋 Runbook 参考

- **g1 aiops-case-v14/workload**: pod-imagepull-failed, pod-volume-mount-failed
