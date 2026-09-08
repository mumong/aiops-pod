## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-kbwsx` | ContainerCreating | Pod aiops-case-05/workload-5dbb5dcd6c-kbwsx 配置了 Multus CNI 引用不存在的 NetworkAttachmentDefinition 'unavailable-network'，导致 kubelet 无法完成 Pod Sandbox 的网络初始化。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Failed to create pod sandbox: rpc error... plugin type="multus" ... failed getting the delegate: network-attachment-definitions.k8s.cni.cncf.io "unavailable-network" not found` (fact-076e0ba7d881) | 确认 Pod 创建因 CNI 插件执行失败而中止 |
| 2 | K8s Event | multus | `cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` (fact-09cc19ebdc2d) | 直接指明缺失的依赖资源对象名称 |
| 3 | K8s State | Kubernetes | `ContainerCreating`, reason: `ContainerCreating` (fact-93475059fd92) | 确认 Pod 处于等待初始化的停滞状态 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{container="app", reason="ContainerCreating"} = 1` (fact-cee317e3e825) | 量化确认等待状态的持续性 |

事件日志在长达 60 分钟的窗口内持续报出 `NoNetworkFound`，且 `kubelet` 报错明确指出 CNI 插件 `multus` 在 `aiops-case-05` 命名空间中找不到 `unavailable-network`。指标数据确认了该等待状态未被解除。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置引用不存在的 CNI 网络定义 → Multus 插件查找 delegate 失败 → kubelet 创建 Sandbox 中止 → Pod 卡死在 ContainerCreating 状态
```

### 根因结论

已确认根因为 **Pod 配置了不存在的 NetworkAttachmentDefinition 'unavailable-network'**。

依据证据 #1 和 #2，Pod 的 CNI 配置要求引用 `unavailable-network` 这一自定义网络，但该对象在 `aiops-case-05` 命名空间中缺失，导致网络初始化流程不可逆地失败。证据 #3 和 #4 佐证了这一故障的持续影响。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 27.6s
├─ 并发证据采集: 49.5s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx: 49.5s (Evidence 40.5s, RCA 8.8s)
└─ 汇总总结: 7.9s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx**: pod-volume-mount-failed, pod-imagepull-failed, pod-sandbox-create-failed
