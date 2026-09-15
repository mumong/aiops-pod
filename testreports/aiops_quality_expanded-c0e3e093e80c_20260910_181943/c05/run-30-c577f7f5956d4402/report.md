## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-bntfh` | ContainerCreating | Pod `workload-5dbb5dcd6c-bntfh` 卡在 `ContainerCreating` 阶段是由于 Multus CNI 插件在调度节点 `node2` 上尝试查找网络附加定义（NetworkAttachmentDefinition）`unavailable-network` 失败。Kubernetes Events 明确报告了 `NoNetworkFound` 和 `FailedCreatePodSandBox` 错误，证实集群中缺少该网络资源的定义，导致沙箱创建失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod Phase: Pending, Condition ContainersReady: False, Reason: ContainersNotReady | 确认 Pod 停留在调度后、容器未启动的中间状态 |
| 2 | K8s State | Kubernetes | Waiting Reason: ContainerCreating | 明确容器处于沙箱创建及 CNI 配置阶段，尚未进入应用生命周期 |
| 3 | K8s State | Kubernetes | Restart Count: 0 | 排除应用逻辑导致的 CrashLoopBackOff 或反复崩溃重启 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` (reason=ContainerCreating, value=1) | 时间维度指标印证了 K8s 状态机的当前停滞点 |
| 5 | K8s Event | Kubernetes | NoNetworkFound / FailedCreatePodSandBox | 直接证实 Multus CNI 因找不到指定网络定义而导致的底层沙箱创建失败 |

证据链闭环：Pod 卡在 `ContainerCreating` 且重启计数为 0，排除了应用运行时故障。Prometheus 指标与 K8s 事件结合，锁定了问题发生在 CNI 插件尝试注入网络时。`FailedCreatePodSandBox` 结合 `NoNetworkFound` 明确指出了缺失的依赖资源导致了阻塞。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 定义引用网络附加定义 unavailable-network → Multus CNI 插件在 node2 上执行查找 → 因集群中不存在该 NetworkAttachmentDefinition 资源导致 NoNetworkFound → CNI 调用失败触发 FailedCreatePodSandBox → Pod 沙箱无法创建，长期卡在 ContainerCreating 状态
```

### 根因结论

已确认根因为**网络附加定义（NetworkAttachmentDefinition）`unavailable-network` 资源缺失**（见证据 #5）。

Pod 在调度至 `node2` 后，Kubelet 调用 Multus CNI 插件尝试查找并配置名为 `unavailable-network` 的网络。由于该定义在集群中不存在，插件返回 `NoNetworkFound` 错误，导致 Kubernetes 无法完成 Pod SandBox 的创建（见证据 #5 和 #2）。这一状态机层面的阻塞使得 Pod 无法进入 `Running` 阶段，从而表现为持续卡在 `ContainerCreating`。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 19.9s
├─ 并发证据采集: 38.5s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-bntfh: 38.5s (Evidence 32.1s, RCA 6.3s)
└─ 汇总总结: 7.8s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-bntfh**: pod-imagepull-failed
