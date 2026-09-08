## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-nhd7v` | ContainerCreating | Pod workload-5dbb5dcd6c-nhd7v in aiops-case-05 stuck in ContainerCreating/Pending state |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `FailedCreatePodSandBox` (fact-0edaeab49810): `failed to setup network for sandbox... plugin type="multus"... failed (add)... cannot find a network-attachment-definition (unavailable-network)` | 直接证明 CNI 网络配置失败，导致容器沙箱无法创建 |
| 2 | K8s Event | Kubernetes | `NoNetworkFound` (fact-1387e3cdd4fc): `cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` | 明确指出缺失的 NetworkAttachmentDefinition 资源名称及命名空间 |
| 3 | K8s Config | Kubernetes | Annotation `k8s.v1.cni.cncf.io/networks: unavailable-network` (fact-f08d8320aabd) | 确定 Pod 请求了不存在网络资源的源头 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` (fact-595f7d73983b): 值为 `1`，标签 `reason: ContainerCreating` | 确认当前容器处于等待创建网络的阻塞状态 |
| 5 | Metric | Prometheus | `kube_pod_container_status_restarts_total` (fact-1aa3735038f0): 值为 `0` | 确认应用代码未被调度执行，故障位于 Pod 启动前阶段 |

**证据说明：**
Kubernetes 事件（#1, #2）清晰表明 Multus 插件因找不到 `unavailable-network` 定义而初始化网络失败。Pod 配置（#3）确认了该引用的来源。Metric 数据（#4, #5）从系统层面验证了容器卡在 `ContainerCreating` 且从未启动过，这与 CNI 插件报错导致的沙箱创建失败完全吻合。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 定义了不存在的 Multus 网络引用 → Multus CNI 无法找到 delegate 资源 → Kubelet 无法创建 Pod 沙箱 → Pod 卡在 ContainerCreating/Pending
```

### 根因结论

已确认根因：Pod `aiops-case-05/workload-5dbb5dcd6c-nhd7v` 的 Spec 中包含无效的 Multus 网络注解 `k8s.v1.cni.cncf.io/networks: unavailable-network`（证据 #3），该引用指向命名空间 `aiops-case-05` 中并不存在的 NetworkAttachmentDefinition 资源。这导致 Multus CNI 插件在尝试加载网络配置时失败（证据 #1, #2），进而导致 kubelet 拒绝创建 Pod 沙箱，使 Pod 持续停留在 `ContainerCreating` 状态（证据 #4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 31.7s
├─ 并发证据采集: 33.0s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v: 33.0s (Evidence 23.8s, RCA 9.0s)
└─ 汇总总结: 9.9s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v**: pod-sandbox-create-failed
