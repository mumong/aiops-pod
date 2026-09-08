## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-kbwsx` | ContainerCreating | Pod aiops-case-05/workload-5dbb5dcd6c-kbwsx 处于 ContainerCreating/Pending 状态，反复发生 FailedCreatePodSandBox 失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Failed to create pod sandbox: ... Failed to setup network ... plugin type="multus" ... error loading k8s delegates: cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` (fact-04dc68fe7921) | 确立 kubelet 创建沙箱失败的具体报错链，指向 CNI 插件找不到网络定义 |
| 2 | K8s Event | multus | `cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` (fact-143f901989c5) | 明确错误源：Multus 插件无法定位名为 `unavailable-network` 的 NetworkAttachmentDefinition 资源 |
| 3 | K8s Config | Pod Spec | `k8s.v1.cni.cncf.io/networks: unavailable-network` (fact-114335b47aac) | 证实 Pod 规范中硬编码引用了该网络，与报错缺失的 CRD 名称一致 |
| 4 | K8s State | Pod Status | `status: ContainerCreating, reason: ContainerCreating` (fact-10ace1c8aa48) | 提供当前容器状态，说明工作负载卡在网络准备阶段 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason {reason="ContainerCreating"} = 1` (fact-9e36a7642712) | 量化确认 Pod 持续处于等待状态，且未发生重启 (fact-03b9f47f7b52 显示 restarts=0) |

**证据分析：**
K8s 事件（Fact 1、2）清晰地展示了因果链：Pod Spec 引用了 `unavailable-network`（Fact 3），但 Multus 插件在 `aiops-case-05` 命名空间中找不到对应的 CRD，导致网络初始化失败，最终 kubelet 无法创建沙箱。Metrics 数据（Fact 5）辅助验证了 Pod 长期处于 `ContainerCreating` 的阻塞状态，且重启计数为 0，排除了容器启动后崩溃的可能。

## 🎯 根因分析 · g1

### 因果链

```text
缺失 NetworkAttachmentDefinition CRD 'unavailable-network' → Multus CNI 无法获取网络代理配置 (NoNetworkFound) → kubelet 调用 runtime 创建 Pod Sandbox 失败 (FailedCreatePodSandBox) → Pod 处于 Pending/ContainerCreating 状态且无法就绪
```

### 根因结论

**已确认根因：** 工作负载 `aiops-case-05/workload-5dbb5dcd6c-kbwsx` 的 Pod 规范中引用了名为 `unavailable-network` 的 Multus 网络附加定义，但该 NetworkAttachmentDefinition CRD 在 `aiops-case-05` 命名空间中不存在（支持证据：fact-143f901989c5, fact-114335b47aac）。

**造成现象：** 这一配置错误导致 Multus CNI 插件无法为 Pod 建立网络环境，直接引发 kubelet 在创建容器沙箱时遭遇 `FailedCreatePodSandBox` 错误（支持证据：fact-04dc68fe7921），使得 Pod 持续卡在 `ContainerCreating` 状态，无法进入运行阶段。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 17.8s
├─ 并发证据采集: 53.2s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx: 53.2s (Evidence 42.8s, RCA 10.0s)
└─ 汇总总结: 11.9s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx**: pod-sandbox-create-failed, pod-imagepull-failed, pod-volume-mount-failed
