## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-bntfh` | ContainerCreating | Pod workload-5dbb5dcd6c-bntfh stuck in ContainerCreating/Pending state |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason`: reason=ContainerCreating, container=app | 确认 Pod 处于容器创建等待状态，验证了调度阻塞的现象 |
| 2 | K8s Event | multus | `NoNetworkFound`：cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cni.cncf.io "unavailable-network" not found | 指出 Multus CNI 插件在指定名称空间下找不到名为 "unavailable-network" 的依赖网络定义 |
| 3 | K8s Event | kubelet | `FailedCreatePodSandBox`：failed to setup network for sandbox: plugin type="multus" name="multus-cni-network" failed (add): ... getKubernetesDelegate: cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05) | 确认 kubelet 因网络插件解析失败导致 Pod Sandbox 创建报错并持续重试 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason`：reason=ContainerCreating, value=1 (sample_count=1, trend_evaluable=false) | 提供 Pod 持续处于 Waiting 状态的监控指标佐证 |

**证据链印证：**
K8s 指标 (E4) 显示 Pod 持续等待，E2 (Multus 事件) 和 E3 (Kubelet 事件) 均明确指出失败原因在于找不到 `unavailable-network` 网络定义。E1 (Pod 状态) 是上述网络资源缺失导致的直接阻塞表现。四个证据共同指向 CNI 网络依赖缺失导致的启动故障。

## 🎯 根因分析 · g1

### 因果链

```text
namespace aiops-case-05 中缺少 NetworkAttachmentDefinition 'unavailable-network' → Multus CNI 无法解析网络代理并建立网络环境 → kubelet 创建 Pod Sandbox 失败并持续重试 → Pod 永久停留在 ContainerCreating 状态
```

### 根因结论

已确认根因为 `namespace aiops-case-05 中缺少 Multus 所需的网络定义资源 'unavailable-network'`。
Multus CNI 插件在执行 Pod 网络初始化时，尝试查找指定的 `NetworkAttachmentDefinition`，因该资源不存在导致网络插件报错（Evidence #2, #3）。这一资源缺失直接导致 `kubelet` 无法完成 Pod Sandbox 的网络配置，进而使 Pod 持续处于 `ContainerCreating` 等待状态（Evidence #1, #4）。证据链闭环完整，确认了资源缺失是本次异常的唯一根因。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 35.9s
├─ 并发证据采集: 45.7s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-bntfh: 45.7s (Evidence 36.7s, RCA 8.8s)
└─ 汇总总结: 9.3s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-bntfh**: pod-volume-mount-failed, pod-sandbox-create-failed
