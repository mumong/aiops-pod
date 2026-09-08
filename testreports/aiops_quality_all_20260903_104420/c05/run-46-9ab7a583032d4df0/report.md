## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-nhd7v` | ContainerCreating | Pod workload-5dbb5dcd6c-nhd7v 卡在 ContainerCreating 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `reason: NoNetworkFound`, `message: ... multus cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cni.cncf.io "unavailable-network" not found` (共 46 次) | 持续报错，证明 Multus CNI 在多次重试中均无法解析指定的网络定义 |
| 2 | K8s State | Kubernetes | `container.waiting_reason: ContainerCreating` | 确认 Pod 处于因网络依赖等待而卡住的阻塞状态 |
| 3 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{container="app", reason="ContainerCreating"} = 1` (采样值 1) | 确认 Pod 的 `app` 容器当前处于 `ContainerCreating` 等待原因状态 |

**证据关联：**
Kubernetes 事件明确指出了失败的具体原因是 Multus CNI 找不到 `aiops-case-05` 命名空间下的 `unavailable-network` 网络附着定义，且该错误持续了数十分钟。K8s 状态和 Metric 从容器维度和监控维度证实了 Pod 长期处于该网络依赖引发的等待状态，事件中的错误原因与容器的阻塞状态完全一致。

## 🎯 根因分析 · g1

### 因果链
```text
Pod 注解引用不存在的 Multus NAD 'unavailable-network' → Multus CNI 在 sandbox 创建阶段无法解析网络定义 → kubelet 持续报 NoNetworkFound 错误 → Pod 卡在 ContainerCreating 状态
```

### 根因结论
根因是 Pod `aiops-case-05/workload-5dbb5dcd6c-nhd7v` 配置了引用 `unavailable-network` 网络附着定义，但 Multus 在 `aiops-case-05` 命名空间中找不到该定义。
这一配置错误导致 Multus CNI 无法完成网络沙箱初始化，从而引发 kubelet 持续报 `NoNetworkFound` 错误，使 Pod 的 `app` 容器长时间停留在 `ContainerCreating` 状态。
证据充分（见证据 1、2、3），且 `diagnosis_publishable` 状态为真，该根因已被确认。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 21.1s
├─ 并发证据采集: 45.5s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v: 45.5s (Evidence 38.1s, RCA 7.1s)
└─ 汇总总结: 8.3s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v**: pod-imagepull-failed, pod-sandbox-create-failed, pod-volume-mount-failed
