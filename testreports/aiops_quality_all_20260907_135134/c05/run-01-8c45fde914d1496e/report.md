## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-kbwsx` | ContainerCreating | Pod Spec 引用了不存在的 NetworkAttachmentDefinition 'unavailable-network'，导致 Multus CNI 无法配置 Pod 网络 Sandbox |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `FailedCreatePodSandBox ... plugin type="multus" name="multus-cni-network" failed ... getKubernetesDelegate: cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` | 直接证实 Multus CNI 因找不到名为 `unavailable-network` 的依赖资源而失败创建 Pod 沙箱 |
| 2 | K8s Event | multus | `NoNetworkFound ... cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cni.cncf.io "unavailable-network" not found` | 确认 `unavailable-network` 定义在目标命名空间中物理缺失，解释了失败的具体原因 |
| 3 | K8s Config | Pod Annotations | `cni.projectcalico.org/networks: unavailable-network` | 证实 Pod 规格确实引用了该命名中不存在的网络定义，是故障的配置源头 |
| 4 | K8s State | Pod Phase | `Pending`, `status: ContainerCreating`, `Ready: False` | 证实 Pod 处于因依赖项缺失而阻塞的状态，未进入运行阶段 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"}=1` | 独立指标观测，与 K8s 事件状态一致，证实容器因等待网络配置而处于阻塞中 |

**证据总结：**
K8s 事件明确指出 Multus CNI 插件在配置网络时，因在 `aiops-case-05` 命名空间中找不到名为 `unavailable-network` 的 `NetworkAttachmentDefinition` 资源而报错 `NoNetworkFound`。Pod 的 Annotation 证实了这一引用的存在。指标数据与 K8s 状态一致，佐证了该 Pod 因网络配置失败而停滞在 `ContainerCreating` 阶段。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 引用不存在的 NetworkAttachmentDefinition 'unavailable-network' (fact-3) 
→ Multus CNI 插件查找网络定义失败并报错 (fact-1, fact-2) 
→ Pod 沙箱创建失败，容器状态维持在 ContainerCreating (fact-4, fact-5) 
→ Pod 呈现 Pending 且无法 Ready
```

### 根因结论

已确认的根因为 **Pod 配置错误**。Pod `aiops-case-05/workload-5dbb5dcd6c-kbwsx` 的 CNI 网络配置中声明了依赖名为 `unavailable-network` 的网络定义，但该资源在对应的 `aiops-case-05` 命名空间中不存在。这导致 Multus CNI 无法完成网络沙箱配置，进而阻塞了容器的启动，使其无法进入 Ready 状态。证据之间（事件报错、配置引用、状态指标）形成完整且自洽的闭环，无需补充其他维度的观测事实。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 37.3s
├─ 并发证据采集: 41.5s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx: 41.5s (Evidence 36.0s, RCA 5.3s)
└─ 汇总总结: 10.3s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx**: pod-volume-mount-failed, pod-imagepull-failed
