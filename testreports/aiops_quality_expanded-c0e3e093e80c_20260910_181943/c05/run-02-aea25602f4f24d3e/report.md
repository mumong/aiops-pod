## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-bntfh` | ContainerCreating | Pod workload-5dbb5dcd6c-bntfh 的 Multus CNI 插件引用了名为 'unavailable-network' 的 NetworkAttachmentDefinition，但该 CR 在命名空间 aiops-case-05 中不存在，导致 CNI 无法创建 Pod 网络沙箱，Pod 持续处于 Pending/ContainerCreating 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod `workload-5dbb5dcd6c-bntfh` (ns: `aiops-case-05`) 状态 `Pending` / 容器状态 `ContainerCreating` | 确认 Pod 处于启动阻塞状态，未进入运行阶段 |
| 2 | K8s Event | kubernetes | `FailedCreatePodSandBox`: kubelet 报错 `failed to setup network for sandbox`: Multus plugin 失败 | 直接反映 CNI 插件在创建网络沙箱时发生错误 |
| 3 | K8s Event | kubernetes | `NoNetworkFound`: Multus 报错 `cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): ... "unavailable-network" not found` | 精确定位网络配置缺失，明确缺失对象的名称和命名空间 |
| 4 | K8s Config | kubernetes | 容器 `app` 存在注解引用 `cni.projectcalico.org/networks: unavailable-network` | 证实 Pod 定义中显式配置了该不存在的网络，是引发上述报错的直接原因 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason` 值为 `1`，标签 `reason=ContainerCreating` | 从监控维度印证容器长期停留在等待创建状态 |

**证据小结：**
Kubernetes 事件 (`fact-06ff1146fc23`, `fact-ad76d73b8759`) 明确指出 Pod 无法创建网络沙箱是因为找不到名为 `unavailable-network` 的 `network-attachment-definition`，结合 Pod 注解事实 (`fact-0fc63cb437b8`)，确认该网络配置存在于 Pod 定义中但关联资源缺失，直接阻断了 Pod 的启动流程。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 定义引用了不存在的 NetworkAttachmentDefinition 'unavailable-network' (证据 4)
  → Multus CNI 插件加载网络配置失败并报错 'not found' (证据 3)
  → Kubelet 无法为 Pod 创建网络沙箱 (证据 2)
  → Pod 持续处于 Pending 状态，容器停留在 ContainerCreating (证据 1)
```

### 根因结论

**已确认根因：**
Pod `aiops-case-05/workload-5dbb5dcd6c-bntfh` 配置了 Multus CNI 插件，并引用了名为 `unavailable-network` 的 `NetworkAttachmentDefinition`。由于该资源在命名空间 `aiops-case-05` 中不存在，Multus 插件无法初始化网络，导致 Pod 的 CNI 配置阶段失败，Pod 持续卡在 Pending/ContainerCreating 状态。

**证据支撑：**
1.  **网络报错**：`NoNetworkFound` 事件（如 `fact-06ff1146fc23`）直接报错找不到指定的 NetworkAttachmentDefinition。
2.  **配置关联**：Kubernetes 事实（如 `fact-0fc63cb437b8`）证实 Pod 内部确实配置了该网络引用。
3.  **状态阻塞**：Pod 状态（证据 1）和等待指标（证据 5）证实问题持续存在，无重启恢复迹象。

**未确认事项：**
输入中的 `unknowns` 提到了该引用是拼写错误还是确实遗漏创建，以及是否影响其他 Pod。当前事实已证实“引用缺失导致阻塞”这一故障现象，但关于引用本身的修正意图（如正确名称是什么）需要人工核对。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 15.3s
├─ 并发证据采集: 49.0s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-bntfh: 49.0s (Evidence 40.2s, RCA 8.6s)
└─ 汇总总结: 12.5s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-bntfh**: pod-volume-mount-failed
