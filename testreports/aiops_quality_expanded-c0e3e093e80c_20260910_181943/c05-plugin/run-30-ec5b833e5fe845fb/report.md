## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v14/workload` | ContainerCreating | Pod aiops-case-v14/workload 状态为 Pending，容器持续处于 ContainerCreating 状态，sandbox 创建失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedCreatePodSandBox`: Failed to create pod sandbox: ... plugin type="multus" ... failed to find plugin "aiops-unavailable" in path [/opt/cni/bin /opt/cni/bin] | 直接归因于 CNI 插件缺失，解释了网络 sandbox 创建的失败机制 |
| 2 | K8s State | kubernetes | 实体 `aiops-case-v14/workload` 状态为 `Pending`，容器 `app` 状态为 `ContainerCreating` | 确认了 Pod 处于调度成功但容器初始化受阻的停滞状态 |
| 3 | K8s Config | kubernetes | 容器 `app` 请求 `cpu: 5m`, `memory: 8Mi`；限制 `cpu: 50m`, `memory: 32Mi` | 证明资源请求极低，排除了因资源配额不足导致调度或启动失败的可能性 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"}` 值为 `1`；`kube_pod_status_phase{phase="Pending"}` 值为 `1` | 时间序列观测与 K8s 状态一致，证实该异常是当前的持续性现象 |
| 5 | K8s Event | kubernetes | Pod 事件流显示 `Initialized: True`，但 `ContainersReady: False`，`Ready: False` | 进一步佐证容器组已初始化但网络等前置条件未满足，阻碍了容器就绪 |

证据 1 指出 `multus` 网络插件在 CNI 搜索路径中找不到名为 `aiops-unavailable` 的二进制文件，这是容器无法创建网络的直接原因。证据 2、4 和 5 从 K8s 状态、时序指标和 Pod 条件层面互相印证，确认了集群因该网络配置错误而处于 `Pending` 等待态，且重启计数为 0，表明故障发生在启动阶段而非运行后崩溃。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置引用了不存在的 CNI 插件 'aiops-unavailable' → Multus 网络添加操作在 CNI 路径中找不到插件二进制 → Pod sandbox 创建失败 → 容器持续处于 ContainerCreating 状态
```

### 根因结论

已确认根因为：Pod `aiops-case-v14/workload` 在通过 Multus 申请 secondary network 时，配置引用了名为 `aiops-unavailable` 的 CNI 插件，但该插件的二进制文件在目标节点（node2）的 CNI 路径（如 `/opt/cni/bin`）中缺失 [证据 1]。这一配置错误导致 kubelet 无法建立 Pod 的网络 sandbox，从而引发 Pod 永远卡在 `Pending` 和 `ContainerCreating` 状态的直接现象 [证据 2, 4, 5]。

现有证据不足以说明该插件缺失的深层原因（例如：是节点部署遗漏、路径配置错误，还是集群全局性的镜像/配置未同步），需补充其他节点的同源拓扑数据以判断影响范围。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 19.5s
├─ 并发证据采集: 39.9s
│  └─ g1 aiops-case-v14/workload: 39.9s (Evidence 30.1s, RCA 9.6s)
└─ 汇总总结: 10.4s
```

📋 Runbook 参考

- **g1 aiops-case-v14/workload**: pod-volume-mount-failed
