## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-nhd7v` | ContainerCreating | Pod workload-5dbb5dcd6c-nhd7v in namespace aiops-case-05 is stuck in ContainerCreating/Pending state, failing to schedule containers. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `ContainerCreating` (container: app, fact-23030adb24e2) | 确定 Pod 当前停滞的容器状态 |
| 2 | K8s Event | Multus | `NoNetworkFound`: cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05) (fact-00cf9a578004 等 46 条) | 指出网络插件找不到名为 'unavailable-network' 的 CNI 配置 |
| 3 | K8s Event | Kubelet | `FailedCreatePodSandBox`: failed to setup network for sandbox... plugin type="multus"... failed (add) (fact-1d1728fbaf36 等 198 次) | 证实网络配置缺失直接导致 Pod 沙箱创建失败并持续重试 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` = 1, reason=`ContainerCreating` (fact-2277812a0509) | 从监控层面确认容器处于等待状态 |

**证据关联说明**：
K8s Event 中的 `NoNetworkFound` 与 `FailedCreatePodSandBox` 在时间线上紧密伴随，明确展示了 Multus 插件因找不到网络资源导致底层网络插件失败，进而使 kubelet 无法创建沙箱。Metric 数据作为独立的监控视角，确认了容器处于因网络错误导致的 `ContainerCreating` 等待态，与事件日志相互印证。Logging 和 Tracing 因容器未启动而无数据。

## 🎯 根因分析 · g1

### 因果链

```text
Namespace 'aiops-case-05' 中缺少名为 'unavailable-network' 的 NetworkAttachmentDefinition 资源 
  → Multus CNI 插件无法解析并获取网络委托配置 
  → Pod 沙箱网络初始化失败 (FailedCreatePodSandBox) 
  → 容器无法启动，Pod 持续处于 ContainerCreating 状态
```

### 根因结论

已确认的根因是：Pod `workload-5dbb5dcd6c-nhd7v` 的 Spec 中引用了名为 `unavailable-network` 的 CNI 网络附件定义，但该资源在 `aiops-case-05` 命名空间中不存在 (事实 1-3)。这一配置缺失导致 Multus 插件无法完成网络插件链的初始化，进而引发 Pod 沙箱创建失败及容器的持续重试等待 (事实 2-4)。

关于为何 `unavailable-network` 资源缺失（如 YAML 未部署、名称拼写错误或依赖问题），当前证据表明其为未知原因，缺乏决定性事实支持进一步推断。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 18.1s
├─ 并发证据采集: 45.1s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v: 45.1s (Evidence 35.1s, RCA 9.8s)
└─ 汇总总结: 9.9s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v**: pod-volume-mount-failed, pod-sandbox-create-failed
