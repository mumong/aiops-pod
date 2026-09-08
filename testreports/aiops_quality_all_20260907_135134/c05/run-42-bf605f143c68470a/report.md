## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-kbwsx` | ContainerCreating | Pod 被配置为通过 Multus CNI 使用 NetworkAttachmentDefinition 'unavailable-network'，但该资源在 namespace 'aiops-case-05' 中不存在，导致 Multus 无法初始化网络插件，进而引发 kubelet 反复失败创建 Pod 沙箱（FailedCreatePodSandBox）。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | 容器 `app` 等待原因: `ContainerCreating` | 确认 Pod 当前处于无法进入 Running 状态的挂起阶段 |
| 2 | K8s Event | Kubernetes | `Warning NoNetworkFound`: `cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` (记录 46 次) | 持续表明 Multus 调度器因找不到指定网络定义而拒绝初始化网络 |
| 3 | K8s Event | Kubernetes | `Warning FailedCreatePodSandBox`: `Failed to create pod sandbox: ... plugin type="multus" ... error loading k8s delegates ... cannot find a network-attachment-definition (unavailable-network) ... not found` | 提供底层失败机制，指出 `multus` 插件在尝试加载 delegate 时直接报错 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{container="app", reason="ContainerCreating"} = 1` (timestamp: 2026-09-07T12:17:34.321000Z) | 辅助确认 Pod 处于等待状态的当前指标快照 |

**证据链逻辑说明：**
状态指标 (E4) 证实了 Pod 处于等待期，Kubernetes 事件 E2 提供了高频且明确的配置缺失报错（找不到 `unavailable-network`），E3 则展示了该报错导致的具体执行失败（`FailedCreatePodSandBox`）。三者结合完整锁定了故障是由于 Pod 请求的网络资源不存在，导致容器无法完成启动流程。Logging 和 Tracing 因容器未启动无法采集，无证据冲突。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置引用了不存在的 NetworkAttachmentDefinition 'unavailable-network' → Multus CNI 插件在初始化阶段查找资源失败 (NoNetworkFound) → kubelet 创建 Pod 沙箱 (Sandbox) 失败 → 容器状态永久维持在 ContainerCreating
```

### 根因结论

**已确认根因：** 异常组 `g1` 的故障由网络配置缺失直接导致。

Pod 中的应用容器 `app` 被配置为通过 Multus CNI 使用名为 `unavailable-network` 的网络插件，但该 NetworkAttachmentDefinition 在命名空间 `aiops-case-05` 中不存在。这导致 Multus 插件在启动时无法加载必要的网络配置，进而致使 `kubelet` 反复尝试创建 Pod 沙箱失败（证据 2、证据 3），最终 Pod 陷入 `ContainerCreating` 状态无法运行（证据 1）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 32.5s
├─ 并发证据采集: 52.1s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx: 52.1s (Evidence 46.0s, RCA 5.9s)
└─ 汇总总结: 9.5s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx**: pod-sandbox-create-failed, pod-imagepull-failed, pod-config-error
