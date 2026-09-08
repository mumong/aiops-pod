## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-nhd7v` | ContainerCreating | Pod workload-5dbb5dcd6c-nhd7v 处于 ContainerCreating (Pending) 状态，Sandbox 创建失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `kubernetes` (fact-024bab3ca9b8) | `Warning NoNetworkFound ... cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cncf.io "unavailable-network" not found` | 核心证据：K8s 事件直接记录 `multus` 组件找不到指定的网络资源 |
| 2 | K8s Event | `kubernetes` (fact-06006ad8379c) | `Warning FailedCreatePodSandBox ... rpc error: code = Unknown desc = failed to setup network for sandbox ... plugin type="multus" ... failed getting the delegate: getKubernetesDelegate: cannot find a network-attachment-definition ... not found` | 核心证据：沙箱创建失败的具体堆栈，将网络错误映射到具体的插件（multus）和阶段 |
| 3 | K8s State | `kubernetes` (fact-71460cf2d9ea) | `container.waiting_reason: ContainerCreating` | 现象确认：容器长期处于等待状态，等待网络配置完成 |
| 4 | Metric | `prometheus` (fact-a52c6a17b13e) | `kube_pod_container_status_waiting_reason{container="app", reason="ContainerCreating"} = 1` | 辅助证据：监控指标确认应用容器 `app` 正以 `ContainerCreating` 原因等待 |

多组 `NoNetworkFound` 警告与 `FailedCreatePodSandBox` 错误在时间轴上连续出现，共同指向 Multus 插件因无法解析 Pod 依赖的 `NetworkAttachmentDefinition` 而阻断网络初始化。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 定义引用不存在的 'unavailable-network' 资源 → Multus CNI 查询失败并抛出 NoNetworkFound 错误 → 容器沙箱创建阻塞失败 → 应用 Pod 持续处于 ContainerCreating 状态
```

### 根因结论

已确认根因为：Pod 定义中引用的 `NetworkAttachmentDefinition` 资源 `unavailable-network` 在 `aiops-case-05` 命名空间中不存在（#1, #2）。这导致 Multus CNI 插件无法获取网络配置，直接阻断了 Pod 沙箱的建立（#2），致使应用容器长期处于 `ContainerCreating` 的等待状态（#3, #4）。

缺失决定性事实：输入中 `kubectl get` 尝试获取该 CRD 记录失败（提示 resource type 不存在），且诊断过程未确认该 CRD 类型在集群中是否已正确安装。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 20.1s
├─ 并发证据采集: 43.6s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v: 43.6s (Evidence 35.2s, RCA 8.3s)
└─ 汇总总结: 9.7s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v**: pod-volume-mount-failed, pod-sandbox-create-failed, pod-imagepull-failed, pod-config-error
