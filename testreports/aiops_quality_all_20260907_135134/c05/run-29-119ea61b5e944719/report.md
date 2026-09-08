## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-kbwsx` | ContainerCreating | Pod aiops-case-05/workload-5dbb5dcd6c-kbwsx 处于 ContainerCreating 状态，持续失败无法启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_reason`: `ContainerCreating` (fact-09f8d6701f3f) | 确认应用容器 `app` 处于等待状态，未能进入 Running 状态 |
| 2 | K8s Event | Multus | `Warning  NoNetworkFound`: `cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cni.cncf.io "unavailable-network" not found` (fact-0044fd32af04 等 46 条重复记录) | 持续报错，明确指出 Multus 无法在 `aiops-case-05` 命名空间中找到名为 `unavailable-network` 的网络定义资源 |
| 3 | K8s Event | Kubelet | `Warning  FailedCreatePodSandBox`: `rpc error: code = Unknown desc = failed to setup network for sandbox "...": plugin type="multus" ... error in getting k8s network for pod: GetNetworkDelegates: failed getting the delegate: getKubernetesDelegate: cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cni.cncf.io "unavailable-network" not found` (fact-af115ac841d3) | 底层沙箱创建失败的直接证据，表明 CNI 插件因网络定义缺失而返回错误，阻塞了 Pod 生命周期 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` = `1` (factor: `ContainerCreating`, fact-d9cd00575f74) | 监控指标确认了 `ContainerCreating` 状态的持续存在，与 K8s Event 的失败现象一致 |

**证据分析：**
Kubernetes 事件日志 (fact-0044fd32af04) 与 Kubelet 沙箱创建失败记录 (fact-af115ac841d3) 均一致指出 `unavailable-network` 这一 NetworkAttachmentDefinition 不存在。这种持续性的资源缺失导致 Multus CNI 无法为 Pod 配置网络接口，直接导致 Kubelet 无法创建沙箱，进而使 Pod 无限期卡在 `ContainerCreating` 状态 (fact-09f8d6701f3f, fact-d9cd00575f74)。

## 🎯 根因分析 · g1

### 因果链

```text
网络附加定义 'unavailable-network' 在 aiops-case-05 命名空间中不存在 → Multus CNI 插件无法获取网络配置并执行 add 操作 → 容器运行时无法创建 Pod Sandbox (FailedCreatePodSandBox) → Pod aiops-case-05/workload-5dbb5dcd6c-kbwsx 持续处于 ContainerCreating 状态
```

### 根因结论

已确认的根因是：Pod YAML 中引用的 Multus 网络附加定义（`unavailable-network`）在目标命名空间 `aiops-case-05` 中不存在。

这一配置错误导致 Multus 插件在初始化网络时查无此定义，进而使 Kubelet 的 `CreatePodSandbox` 调用失败。由于网络配置是 Pod 启动的必要前提，该错误直接导致容器始终无法完成初始化并进入 `ContainerCreating` 状态。证据 2 (K8s Event) 与证据 3 (K8s Event) 相互印证了这一因果链条。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 21.7s
├─ 并发证据采集: 64.1s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx: 64.1s (Evidence 56.4s, RCA 7.6s)
└─ 汇总总结: 12.1s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx**: pod-volume-mount-failed, pod-config-error
