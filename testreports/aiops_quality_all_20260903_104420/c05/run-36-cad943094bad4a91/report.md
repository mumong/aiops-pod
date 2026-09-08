## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-nhd7v` | ContainerCreating | Pod 声明了 Multus CNI 网络注解 `k8s.v1.cni.cncf.io/networks: unavailable-network`，但 Namespace `aiops-case-05` 中不存在对应的 `NetworkAttachmentDefinition` 资源，导致 Multus 插件报 `NoNetworkFound` 错误，无法创建 PodSandbox，使 Pod 持续处于 `ContainerCreating` 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `event.message`: `Warning NoNetworkFound ... multus cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cni.cncf.io "unavailable-network" not found` (`fact-001253afb01c` 等 46 条重复记录) | 明确指示 Multus 插件尝试寻找名为 `unavailable-network` 的网络定义失败。 |
| 2 | K8s Event | Kubernetes | `event.message`: `Warning FailedCreatePodSandBox ... rpc error: code = Unknown desc = failed to setup network for sandbox ... plugin type="multus" name="multus-cni-network" failed (add): Multus: ... error loading k8s delegates k8s args: ... getKubernetesDelegate: cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` (`fact-61c3f89864cb`) | 确认网络配置失败直接导致 Kubelet 无法创建 Pod 沙箱。 |
| 3 | K8s State | Kubernetes | `container.waiting_reason`: `ContainerCreating` (Container: `app`) (`fact-ea24f1277a13`) | 证实 Pod 处于无法启动的等待状态，与事件记录中的调度失败一致。 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason`: value `1`, reason `ContainerCreating` (`fact-ba7bfacf817c`) | 时序指标佐证 Pod 容器持续处于 `ContainerCreating` 状态。 |

**证据印证说明：**
Kubernetes 事件 `fact-001253afb01c` 与 `fact-61c3f89864cb` 建立了从“找不到网络定义”到“创建沙箱失败”的因果链；状态 `fact-ea24f1277a13` 与指标 `fact-ba7bfacf817c` 一致确认了该失败的持续现状。Logging 与 Tracing 因容器未启动且无 IP 而被确认为不适用（not_applicable）。

## 🎯 根因分析 · g1

### 因果链

```text
Namespace 缺少 'unavailable-network' NetworkAttachmentDefinition 资源 → Multus CNI 插件执行 add 操作时报错 'NoNetworkFound' → Kubelet 调用 CNI 失败导致 PodSandbox 创建被拒 → Pod 状态持续卡在 ContainerCreating
```

### 根因结论

已确认根因：Pod `aiops-case-05/workload-5dbb5dcd6c-nhd7v` 配置了不存在的 Multus 网络注解 `unavailable-network`（证据 #1 `fact-001253afb01c`）。这导致 Multus 插件在注入网络时无法找到对应的 `NetworkAttachmentDefinition` 资源，直接导致容器沙箱创建失败（证据 #2 `fact-61c3f89864cb`），表现为 Pod 无法脱离 `ContainerCreating` 状态（证据 #3 `fact-ea24f1277a13`）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 23.4s
├─ 并发证据采集: 47.6s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v: 47.6s (Evidence 38.4s, RCA 8.9s)
└─ 汇总总结: 11.3s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v**: pod-volume-mount-failed
