## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-nhd7v` | ContainerCreating | Pod workload-5dbb5dcd6c-nhd7v 卡在 ContainerCreating 状态，未能启动容器。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning  FailedCreatePodSandBox  28s (x62 over 13m)  kubelet ... Failed to create pod sandbox ... plugin type="multus" name="multus-cni-network" failed ... cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` | 确认 kubelet 无法创建 Pod Sandbox 的直接错误及持续时间，指向 Multus 查找网络失败 |
| 2 | K8s State | Kubernetes | `ContainerCreating` | 确认 Pod 当前的等待状态，验证应用未启动 |
| 3 | K8s Event | Kubernetes | `Warning  NoNetworkFound  2s ... multus ... cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` | 确认 Multus CNI 插件反复确认找不到目标网络定义，排除偶发网络问题 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{container="app", reason="ContainerCreating"} = 1` | 数值指标佐证 Pod 处于 ContainerCreating 状态的当前事实 |

上述 Kubernetes 事件和指标高度一致，明确指向 `unavailable-network` 定义缺失导致 Pod 无法初始化。由于容器未启动，Logging 和 Tracing 维度无应用日志或 Flow 数据可查，符合预期。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了网络注解 k8s.v1.cni.cncf.io/networks: unavailable-network → 
Multus 插件在 aiops-case-05 命名空间中查找 NetworkAttachmentDefinition 失败 → 
kubelet 报告 FailedCreatePodSandBox 错误 → 
Pod 状态停留在 ContainerCreating，无法启动容器
```

### 根因结论

**已确认的根因：Pod 请求了不存在的网络定义 `unavailable-network`，导致 Multus CNI 插件初始化失败。**

证据 #1 和 #2 显示 Pod 持续卡在 `ContainerCreating` 状态。证据 #1 的 Kubernetes Event 明确记录了 `FailedCreatePodSandBox` 错误，并指出错误源于 Multus 插件无法在 `aiops-case-05` 命名空间中找到名为 `unavailable-network` 的 `network-attachment-definitions.k8s.cni.cncf.io` 资源。证据 #3 进一步证实 Multus 插件在长达 13 分钟的观察窗口内反复报出 `NoNetworkFound`，排除了临时性网络抖动或资源未就绪的可能。证据 #4 的 Metric 数据支持 Pod 一直处于等待状态。综合判定，Pod 启动失败的根本原因在于其网络配置引用了一个尚未创建或拼写错误的网络附件定义。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 32.0s
├─ 并发证据采集: 40.6s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v: 40.6s (Evidence 30.7s, RCA 9.5s)
└─ 汇总总结: 9.8s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v**: pod-imagepull-failed, pod-volume-mount-failed, pod-sandbox-create-failed
