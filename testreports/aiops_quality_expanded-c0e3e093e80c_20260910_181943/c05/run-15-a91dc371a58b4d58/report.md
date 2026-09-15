## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-bntfh` | ContainerCreating | Pod aiops-case-05/workload-5dbb5dcd6c-bntfh 卡在 ContainerCreating 状态，沙箱创建失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `container.waiting_reason` | `ContainerCreating` (fact-69d394771e60) | 确认 Pod 卡在启动阶段，未进入 `Running` 状态。 |
| 2 | K8s Event | `multus` (聚合事实) | `cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cncf.io "unavailable-network" not found` (fact-042cd4783caf) | 明确指出 Multus 插件在 `aiops-case-05` 命名空间中找不到名为 `unavailable-network` 的网络定义资源。 |
| 3 | K8s Event | `kubelet` (聚合事实) | `FailedCreatePodSandBox ... failed to setup network ... plugin type="multus" name="multus-cni-network" failed (add)` (fact-198371ecd40a) | 证实底层容器沙箱因网络配置失败无法创建，直接阻断了容器启动。 |
| 4 | Metric | `prometheus` (fact-042cd4783caf) | `kube_pod_container_status_waiting_reason` = `1` (ContainerCreating) (fact-d7a9f8e07141) | 从指标层面印证了 Pod 的等待原因与事件日志中的状态完全一致。 |

**证据综合说明：**
Kubernetes 事件日志（#2, #3）提供了确切的错误路径：Multus CNI 插件在执行 `add` 操作时，因在 `aiops-case-05` 命名空间中无法定位到 `unavailable-network` 这一网络定义资源而失败。这种网络配置缺失直接导致 kubelet 无法建立容器网络沙箱（#3），进而导致 Pod 长期停留在 `ContainerCreating` 状态（#1, #4）。指标与事件数据互为印证，共同指向配置资源缺失这一单一故障点。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置引用了不存在的 network-attachment-definition 'unavailable-network' → Multus CNI 插件无法获取网络定义，创建沙箱时网络配置步骤失败 → kubelet 抛出 FailedCreatePodSandBox 错误，Pod 无法进入运行状态 → 用户侧 Pod 状态持续卡在 ContainerCreating
```

### 根因结论

**已确认根因：** Pod YAML 中通过 `NetworkAttachmentDefinition` 引用了名为 `unavailable-network` 的网络定义，但该资源在当前集群 `aiops-case-05` 命名空间中不存在。
- **事实支撑：** Kubernetes 事件日志明确指出 `getKubernetesDelegate` 失败，原因是找不到 `network-attachment-definitions.k8s.cncf.io "unavailable-network"` (见证据 #2)；同时 kubelet 报告了由此引发的 `FailedCreatePodSandBox` 异常 (见证据 #3)。
- **现象解释：** 由于 Multus 在容器初始化阶段依赖该网络定义来配置网络插件，资源缺失导致网络设置这一硬性依赖失败，致使 Pod 无法通过启动验证。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 31.1s
├─ 并发证据采集: 53.3s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-bntfh: 53.3s (Evidence 44.3s, RCA 8.9s)
└─ 汇总总结: 11.1s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-bntfh**: pod-volume-mount-failed
