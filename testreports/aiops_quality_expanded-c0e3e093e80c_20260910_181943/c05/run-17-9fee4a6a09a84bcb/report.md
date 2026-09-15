## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-bntfh` | ContainerCreating | Pod workload-5dbb5dcd6c-bntfh (aiops-case-05) 卡在 ContainerCreating 状态，无法完成网络初始化。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `kubelet` (fact-3247bf2f14eb) | `FailedCreatePodSandBox`: Failed to create pod sandbox... plugin type="multus" name="multus-cni-network" failed (add): ... cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cni.cncf.io "unavailable-network" not found | 确认 Pod 启动时的底层阻断原因，直接指向缺失的 CNI 网络定义。 |
| 2 | K8s Event | `multus` (fact-065a44ef2491) | `NoNetworkFound`: cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cni.cncf.io "unavailable-network" not found | 确认 Multus 插件在解析 Pod 网络请求时的具体失败信息。 |
| 3 | K8s Event | `kubelet` (fact-021b23868b48) | `FailedCreatePodSandBox`: Failed to create pod sandbox... failed setup network for sandbox "1c732291ae159cc396441fe6bf611159112dfd21478aa8f8c53ac5746776660a" | 记录网络插件失败导致的 Sandbox 创建失败案例。 |
| 4 | Metric | `prometheus` (fact-902dbec45cf6) | `kube_pod_container_status_waiting_reason` = 1 (Reason: `ContainerCreating`) | 验证 Pod 当前持续卡在等待状态，与事件中的网络初始化失败现象一致。 |

**证据说明：**
事件维度（#1, #2）提供了决定性证据，明确指出 Multus 插件在命名空间 `aiops-case-05` 中找不到名为 `unavailable-network` 的网络定义，导致 Sandbox 创建失败。指标数据（#4）确认了容器处于 `ContainerCreating` 等待状态，这与网络初始化卡死的现象完全吻合。

## 🎯 根因分析 · g1

### 因果链
```text
Pod 配置引用了不存在的 Multus 网络 'unavailable-network' → Multus 插件在命名空间 aiops-case-05 中查找失败 → kubelet 创建 Pod Sandbox 的网络插件调用报错 → Pod 持续处于 ContainerCreating 状态
```

### 根因结论
已确认的根因为：Pod 配置引用了一个在命名空间 `aiops-case-05` 中不存在的 Multus NetworkAttachmentDefinition（名为 `unavailable-network`）。这导致 Multus CNI 插件无法完成网络插件加载，进而使 kubelet 无法创建 Pod Sandbox。证据（#1, #2）均明确指出了具体的缺失资源名称和命名空间，因果关系清晰。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 51.8s
├─ 并发证据采集: 45.5s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-bntfh: 45.5s (Evidence 37.4s, RCA 8.0s)
└─ 汇总总结: 10.5s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-bntfh**: pod-imagepull-failed, pod-sandbox-create-failed, pod-volume-mount-failed
