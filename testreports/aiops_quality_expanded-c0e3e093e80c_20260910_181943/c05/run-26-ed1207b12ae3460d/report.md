## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-bntfh` | ContainerCreating | Pod workload-5dbb5dcd6c-bntfh 停滞在 ContainerCreating 状态，无法启动容器。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning  NoNetworkFound ... multus cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cni.cncf.io "unavailable-network" not found` (记录于 fact-0463b6ee2595, 覆盖 2m5s 至 59m) | 证实 Multus 插件因找不到指定的网络定义而持续报错，直接导致容器无法完成网络初始化。 |
| 2 | K8s State | Kubernetes | `container: app`, `reason: ContainerCreating` (fact-ac7a66d9581f) | 证实 Pod 进程停留在初始化阶段，等待网络等前置条件完成。 |
| 3 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"} = 1` (fact-44514bb4f8ae, sample_count=1) | 监控指标确认 Pod 处于等待状态，佐证事件中的失败机制持续存在。 |

**证据印证：**
Kubernetes Event 明确指出了失败的根本原因（缺少 `unavailable-network` 定义），K8s State 和 Metric 均从不同维度确认了 Pod 当前因网络配置失败而卡在 `ContainerCreating` 状态。

## 🎯 根因分析 · g1

### 因果链

```text
Pod YAML 中引用了不存在的 Multus NetworkAttachmentDefinition 'unavailable-network' → Multus CNI 插件在 aiops-case-05 命名空间中找不到该定义 → 网络初始化失败 (FailedCreatePodSandBox) → Pod 停滞在 ContainerCreating 状态
```

### 根因结论

**已确认的根因：** Pod 配置中请求了一个不存在的网络定义 `unavailable-network`。
- **证据引用：** Event 事实 (fact-0463b6ee2595) 提供了直接证据，指出 Multus 插件无法找到该定义；State 事实 (fact-ac7a66d9581f) 和 Metric 事实 (fact-44514bb4f8ae) 验证了这一机制导致的直接后果是 Pod 无法启动。
- 尽管 `formal_rca` 提示存在 `get-pod-yaml` 相关证据，但基于当前提供的 Kubernetes Event 数据，根因（缺少网络定义引用）已经得到充分的事实支撑，无需额外证据即可判定。

---

## 📊 性能统计

```text
├─ 总耗时: 6.3m
├─ 问题定位: 22.5s
├─ 并发证据采集: 347.3s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-bntfh: 347.3s (Evidence 339.0s, RCA 8.1s)
└─ 汇总总结: 8.9s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-bntfh**: pod-volume-mount-failed
