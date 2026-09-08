## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-nhd7v` | ContainerCreating | Pod `workload-5dbb5dcd6c-nhd7v` 的 `k8s.v1.cni.cncf.io/networks` 注解引用了不存在的 NetworkAttachmentDefinition `unavailable-network`，导致 Multus CNI 无法完成网络插件初始化，进而使 kubelet 创建 Pod Sandbox 失败（FailedCreatePodSandBox），容器长期卡在 `ContainerCreating` 阶段。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_reason`: `ContainerCreating` | 确认容器状态停滞在启动阶段，排除运行或崩溃重启问题 |
| 2 | K8s Event | Multus | `reason`: `NoNetworkFound`, `message`: `cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` | 直接指向 Pod 注解引用的网络定义缺失，是引发故障的核心原因 |
| 3 | K8s Event | Kubelet | `reason`: `FailedCreatePodSandBox`, `message`: `Failed to create pod sandbox: ... plugin type="multus" name="multus-cni-network" failed (add)` | 证实网络插件初始化失败导致 Pod 沙箱创建被终止，解释了为何容器未启动 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason`: `reason="ContainerCreating"`, `value=1` | 聚合数据与 K8s 事件中的 `ContainerCreating` 状态一致，确认为当前持续存在的等待状态 |

**证据印证分析：**
`K8s Event #2` 明确指出 `NoNetworkFound` 是因为找不到 `unavailable-network`；该事件紧接着引发 `K8s Event #3` 中 Multus 插件执行失败，直接导致 Kubelet 无法建立沙箱。`K8s State #1` 和 `Metric #4` 从结果侧一致反映了这种卡死在 `ContainerCreating` 的等待状态。数据链路清晰，无冲突。

## 🎯 根因分析 · g1

### 因果链

```text
注解引用不存在的 NetworkAttachmentDefinition `unavailable-network` → Multus CNI 查找失败返回 NoNetworkFound → kubelet 创建 Pod Sandbox 失败 (FailedCreatePodSandBox) → Pod 状态卡死在 ContainerCreating
```

### 根因结论

**已确认根因**：Pod `workload-5dbb5dcd6c-nhd7v` 存在配置错误，其 `k8s.v1.cni.cncf.io/networks` 注解引用了一个不存在的 `NetworkAttachmentDefinition` 资源 `unavailable-network`。

**证据支撑**：
- **直接原因**：`Multus CNI` 在尝试初始化网络插件时，在 `aiops-case-05` 命名空间下无法定位名为 `unavailable-network` 的 `NetworkAttachmentDefinition`（证据表 #2）。
- **故障传播**：该网络定义缺失导致 Multus 插件执行报错，Kubelet 因此无法完成 Pod 沙箱的创建过程（证据表 #3）。
- **最终现象**：由于无法建立底层网络沙箱，容器生命周期停滞在启动前的等待阶段，表现为长期 `ContainerCreating` 且未产生任何应用日志（证据表 #1, #4）。

---

## 📊 性能统计

```text
├─ 总耗时: 7.0m
├─ 问题定位: 48.2s
├─ 并发证据采集: 358.9s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v: 358.9s (Evidence 351.4s, RCA 7.3s)
└─ 汇总总结: 10.2s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v**: pod-volume-mount-failed
