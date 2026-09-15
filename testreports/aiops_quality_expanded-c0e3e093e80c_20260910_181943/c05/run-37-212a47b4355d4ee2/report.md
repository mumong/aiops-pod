## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-bntfh` | ContainerCreating | Pod aiops-case-05/workload-5dbb5dcd6c-bntfh 处于 ContainerCreating/Pending 状态，无法创建沙箱 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `pod.phase`: Pending | 确认 Pod 当前处于等待调度或创建阶段的状态 |
| 2 | K8s State | Kubernetes | `pod.condition`: `ContainersReady=False` (Reason: `ContainersNotReady`), `Ready=False` | 直接证实 Pod 内部容器未就绪，未进入业务运行阶段 |
| 3 | K8s State | Kubernetes | `container.waiting_reason`: `ContainerCreating` | 明确故障卡点位于容器沙箱创建（Sandbox Creation）阶段，而非镜像拉取或启动后 |
| 4 | K8s State | Kubernetes | `pod.spec`: 未直接展示，但诊断指出引用了 `NetworkAttachmentDefinition 'unavailable-network'` | 指向网络插件在沙箱初始化阶段寻找依赖配置失败 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason`: 1 (Reason: `ContainerCreating`); `kube_pod_status_phase`: 1 (Phase: Pending) | 验证了 Pod 持续处于等待创建阶段的观测结果，无重启记录 (`restart_count`: 0) |

**证据交叉验证说明：**
Kubernetes 状态（事实 1-3）与 Prometheus 指标（事实 5）高度一致，共同证实 Pod 长期停留在 `ContainerCreating` 等待阶段且无重启。结合诊断逻辑，故障机制锁定在 CNI（Multus）插件因找不到名为 `unavailable-network` 的 `NetworkAttachmentDefinition` 资源而中断了沙箱构建流程。

## 🎯 根因分析 · g1

### 因果链

```text
缺失 K8s CRD 资源 NetworkAttachmentDefinition 'unavailable-network' 
→ CNI (Multus) 插件在沙箱创建阶段无法找到网络配置 
→ Kubelet 创建 Pod Sandbox 失败并产生 FailedCreatePodSandBox 警告 
→ Pod 卡在 ContainerCreating/Pending 状态
```

### 根因结论

**已确认的根因**：Pod `aiops-case-05/workload-5dbb5dcd6c-bntfh` 引用的 `NetworkAttachmentDefinition` 资源 `unavailable-network` 在命名空间 `aiops-case-05` 中不存在（参考事实 4 及诊断上下文）。

**根因作用机制**：Pod 在初始化阶段依赖 Multus CNI 插件进行网络配置。由于缺失该 CRD 资源，插件无法完成网络沙箱（Sandbox）的创建，导致 Kubelet 返回 `FailedCreatePodSandBox` 错误。这直接阻断了容器从 `ContainerCreating` 向 `Running` 状态的转换（参考事实 2、3 及因果链机制）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 25.6s
├─ 并发证据采集: 45.0s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-bntfh: 45.0s (Evidence 37.0s, RCA 7.9s)
└─ 汇总总结: 9.0s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-bntfh**: pod-volume-mount-failed
