## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-nhd7v` | ContainerCreating | Pod 注解指定的 Multus NetworkAttachmentDefinition 'unavailable-network' 在 namespace 'aiops-case-05' 中不存在，导致 CNI 网络插件初始化失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `aiops-case-05/workload-5dbb5dcd6c-nhd7v` 处于 `ContainerCreating` 状态 | 确认异常持续存在 |
| 2 | K8s Event | Kubernetes (Multus) | `Warning NoNetworkFound ... cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` | 直接定位缺失的 CNI 资源 |
| 3 | K8s Event | Kubernetes (Kubelet) | `Warning FailedCreatePodSandBox ... rpc error: code = Unknown desc = failed to setup network for sandbox ... plugin type="multus" name="multus-cni-network" failed (add)` | 确认网络初始化失败导致 Sandbox 创建失败 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{container="app", reason="ContainerCreating"} = 1` | 指标层面验证容器持续处于等待状态 |

**证据关联分析：**
1. 指标（#4）显示容器处于 `ContainerCreating` 等待状态，状态与事件（#2）持续报错的时间范围一致，排除了瞬时抖动。
2. 核心事件（#2）与内核事件（#3）高度吻合：Multus 明确报告找不到名为 `unavailable-network` 的网络定义，进而导致 Kubelet 创建 Pod Sandbox 的网络设置失败。

## 🎯 根因分析 · g1

### 因果链

```text
缺少 'unavailable-network' NAD → 网络定义查找失败 → Multus CNI 插件初始化失败 → Pod Sandbox 创建失败 (ContainerCreating)
```

### 根因结论

已确认根因：Pod `aiops-case-05/workload-5dbb5dcd6c-nhd7v` 配置了引用 `unavailable-network` 的网络注解，但在 `aiops-case-05` 命名空间中不存在对应的 `NetworkAttachmentDefinition` 资源（证据编号 #2、#3）。

该缺失导致 Multus 插件无法完成网络配置，直接引发容器启动失败。日志（logging）和链路追踪（tracing）处于 `not_applicable` 状态，是因为容器进程尚未启动，但这与当前“网络初始化阶段失败”的结论不冲突且不构成矛盾。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 15.2s
├─ 并发证据采集: 45.7s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v: 45.7s (Evidence 38.6s, RCA 6.9s)
└─ 汇总总结: 8.3s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v**: pod-imagepull-failed, pod-volume-mount-failed
