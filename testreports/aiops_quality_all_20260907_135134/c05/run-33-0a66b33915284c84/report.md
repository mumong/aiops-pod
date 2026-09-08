## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-kbwsx` | ContainerCreating | Pod workload-5dbb5dcd6c-kbwsx stuck in ContainerCreating state |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason` = `ContainerCreating` | 确认 Pod 停留在容器创建阶段，尚未进入就绪或运行状态。 |
| 2 | K8s Event | kubernetes | `multus NoNetworkFound`：`cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` (共 46 次) | 提供直接失败原因：Multus CNI 插件在指定命名空间中找不到名为 `unavailable-network` 的网络附件定义资源。 |
| 3 | K8s Event | kubernetes | `kubelet FailedCreatePodSandBox`：`plugin type="multus"... failed (add)... cannot find a network-attachment-definition (unavailable-network)` | 确认网络插件错误发生在沙箱创建阶段，阻止了底层网络设备的挂载。 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"}` 当前值为 `1` | 独立指标确认当前只有一个 Pod 处于等待状态，与事件频度一致。 |

**证据印证说明**：
Kubernetes 事件（Fact 2, 3）与指标（Fact 4）相互印证，确认 `ContainerCreating` 状态是由 CNI 插件失败直接引起的。`NoNetworkFound` 错误明确指出了缺失的特定资源对象，排除了通用网络或运行时故障的可能性。

## 🎯 根因分析 · g1

### 因果链

```text
命名空间 aiops-case-05 缺失 NetworkAttachmentDefinition 资源 'unavailable-network' → Multus CNI 插件无法建立 Pod 沙箱网络 → 容器无法启动，Pod 卡在 ContainerCreating 状态
```

### 根因结论

已确认根因：Pod `workload-5dbb5dcd6c-kbwsx` 的启动受阻是由于其网络配置引用了不存在的 CNI 网络附件定义。

*   **证据支撑**：Kubernetes 事件（如 Fact 2, 3）反复报错 `cannot find a network-attachment-definition (unavailable-network)`，直接导致 `FailedCreatePodSandBox` 错误。
*   **未知项**：目前证据无法确认 `unavailable-network` 资源是否应在其他命名空间存在，或是已被意外删除，亦或该配置属于无效操作。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 24.5s
├─ 并发证据采集: 58.8s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx: 58.8s (Evidence 49.5s, RCA 9.1s)
└─ 汇总总结: 8.5s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx**: pod-imagepull-failed, pod-sandbox-create-failed
