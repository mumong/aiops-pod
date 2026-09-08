## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-kbwsx` | ContainerCreating | Pod workload-5dbb5dcd6c-kbwsx stuck in ContainerCreating/Pending state |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | multus | `cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cncf.io "unavailable-network" not found` | 直接证明多租户网络插件无法找到所需的 NAD 资源 |
| 2 | K8s Event | kubelet | `Failed to create pod sandbox: ... plugin type="multus" name="multus-cni-network" failed (add): ... getKubernetesDelegate: cannot find a network-attachment-definition (unavailable-network) ... not found` | 证实底层 CNI 因网络配置缺失导致 Pod 沙箱创建失败 |
| 3 | K8s State | container.waiting_reason | `container: app, reason: ContainerCreating` | 描述当前 Pod 容器无法启动的停滞状态 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{container="app", reason="ContainerCreating"} = 1` | 持续观测到该 Pod 处于等待状态，状态未恢复 |

**证据关联说明：**
Kubernetes 事件（#1, #2）明确指出了失败原因是“找不到 `unavailable-network` 网络附加定义（NAD）”，这直接导致了 kubelet 无法创建 Pod 沙箱（#2），进而表现为容器持续处于 `ContainerCreating` 状态（#3, #4）。Metric 数据佐证了该等待状态在当前时间点依然持续存在。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了不存在的 Multus 网络依赖 -> NAD 资源检索失败 -> CNI 插件拒绝创建 Pod 沙箱 -> Pod 停滞在 ContainerCreating 状态
```

### 根因结论

**已确认的根因：** Pod 配置请求了名为 `unavailable-network` 的网络附加定义（NetworkAttachmentDefinition），但该资源在 `aiops-case-05` 命名空间中不存在。

Multus CNI 插件在尝试为该 Pod 建立网络环境时，必须解析该网络定义（#1, #2）。由于该定义缺失，插件无法完成网络初始化，导致 kubelet 报 `FailedCreatePodSandBox` 错误，最终使 Pod 无法进入运行阶段，长期停留在 `ContainerCreating` 状态（#3, #4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 61.3s
├─ 并发证据采集: 41.8s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx: 41.8s (Evidence 35.0s, RCA 6.6s)
└─ 汇总总结: 8.5s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx**: pod-volume-mount-failed, pod-imagepull-failed, pod-sandbox-create-failed
