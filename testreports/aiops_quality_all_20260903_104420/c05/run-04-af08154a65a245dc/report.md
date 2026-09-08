## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-nhd7v` | ContainerCreating | Pod 配置请求了不存在的 Multus NetworkAttachmentDefinition 'unavailable-network'，导致 kubelet 调用 CNI 插件配置网络失败，Pod 卡在 ContainerCreating 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | multus | `Warning NoNetworkFound ... cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` | 直接指出网络资源缺失，解释为何无法建立网络配置 |
| 2 | K8s Event | kubelet | `Warning FailedCreatePodSandBox ... plugin type="multus" name="multus-cni-network" failed (add) ... error in getting k8s network for pod` | 证实由于 CNI 插件加载失败，Pod 沙箱创建被中断 |
| 3 | K8s Config | Pod Spec | `Annotations: k8s.v1.cni.cncf.io/networks: unavailable-network` | 明确根因源头：Pod 配置引用了未定义的自定义网络 |
| 4 | K8s State | Pod Status | `ContainersNotReady: containers with unready status: [app]` | 确认异常现象，Pod 处于非就绪状态 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"} = 1` | 量化指标与 K8s 状态一致，确认容器持续处于等待创建阶段 |

**证据综合：**
K8s 配置（#3）请求了 `unavailable-network`，但集群中不存在该定义，导致 Multus 插件报错并中断网络初始化（#1, #2）。这一失败直接阻止了 Pod 沙箱的创建，使其停留在 `ContainerCreating` 状态（#4, #5）。

## 🎯 根因分析 · g1

### 因果链
```text
Pod Spec 配置 `k8s.v1.cni.cncf.io/networks: unavailable-network` → 
Multus CNI 在 namespace `aiops-case-05` 查找失败（NoNetworkFound） → 
Kubelet 创建 Pod Sandbox 时网络初始化失败（FailedCreatePodSandBox） → 
Pod 卡在 ContainerCreating 状态 (ContainerCreating)
```

### 根因结论
已确认的根因为 **Pod 配置引用了不存在的 Multus NetworkAttachmentDefinition `unavailable-network`**。

具体而言：
1.  Pod `workload-5dbb5dcd6c-nhd7v` 的注解指定使用网络 `unavailable-network`（证据 #3）；
2.  Multus 插件在 `aiops-case-05` 命名空间中未找到该定义（证据 #1）；
3.  网络初始化失败导致 Kubelet 无法创建 Pod Sandbox（证据 #2）；
4.  最终导致 Pod 持续处于 `ContainerCreating` 状态（证据 #4, #5）。

所有证据指向一致，无冲突或缺失。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 35.7s
├─ 并发证据采集: 46.9s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v: 46.9s (Evidence 38.9s, RCA 7.8s)
└─ 汇总总结: 9.8s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v**: pod-imagepull-failed, pod-volume-mount-failed, pod-sandbox-create-failed
