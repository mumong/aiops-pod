## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-nhd7v` | ContainerCreating | Pod aiops-case-05/workload-5dbb5dcd6c-nhd7v 处于 ContainerCreating 状态，Sandbox 创建失败 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `FailedCreatePodSandBox ... rpc error: ... failed to setup network for sandbox "7f2022547e54a993897c2c733a53498366fa219308352d43859e74270439677b": plugin type="multus" name="multus-cni-network" failed (add): ... failed getting the delegate: getKubernetesDelegate: cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` | 直接确认 Pod Sandbox 创建失败，且归因于 Multus 插件在 `aiops-case-05` 命名空间下找不到 `unavailable-network` 网络定义 |
| 2 | K8s Event | multus | `Warning NoNetworkFound ... cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cni.cncf.io "unavailable-network" not found` | 提供底层 CNI 插件（multus）的视角，与 kubelet 报告的一致性，确认 `unavailable-network` 资源不存在 |
| 3 | K8s State | kubelet | `waiting_reason: "ContainerCreating", container: "app"` | 反映 Pod 因上述网络配置错误而停滞在初始化阶段 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` (container: "app", reason: "ContainerCreating") | 从监控系统侧独立验证了容器因等待原因卡在 `ContainerCreating` 状态的事实 |

**证据综合说明：**
Kubernetes 事件 (`fact-0299edf7ba88`, `fact-151f81412df1`) 提供了因果链的完整技术细节：Multus 在尝试加载网络 delegate 时因找不到 `unavailable-network` 而报错，导致 `kubelet` 无法创建 Pod Sandbox。`ContainerCreating` 状态 (`fact-85db3739dcd0`) 和对应 Metric (`fact-e9a4a7efbcbe`) 共同确认了这一停滞状态的当前性。Logging/Tracing 均为 `not_applicable`，符合容器未启动的物理状态。

## 🎯 根因分析 · g1

### 因果链

```text
命名空间 'aiops-case-05' 中缺失 NetworkAttachmentDefinition 'unavailable-network' → Multus CNI 插件无法获取网络委托配置 → 网络插件执行失败 (FailedCreatePodSandBox) → Pod 卡在 ContainerCreating 状态
```

### 根因结论

已确认的根因为 **`aiops-case-05` 命名空间中缺失 `unavailable-network` 网络资源定义** (`fact-0299edf7ba88`, `fact-151f81412df1`)。该 Pod 的注解请求了此网络，但 Multus CNI 插件在集群 API 中查询不到对应的 `network-attachment-definitions.k8s.cni.cncf.io` 对象，导致网络初始化环节失败，进而阻塞了整个 Pod 的 Sandbox 创建。

证据不足项：当前缺乏关于 `unavailable-network` 定义为何缺失（如：未被创建、被误删、或 YAML 遗漏）的具体操作历史或配置变更记录。

---

## 📊 性能统计

```text
├─ 总耗时: 10.0m
├─ 问题定位: 20.3s
├─ 并发证据采集: 565.3s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v: 565.3s (Evidence 556.1s, RCA 9.1s)
└─ 汇总总结: 11.8s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v**: pod-volume-mount-failed
