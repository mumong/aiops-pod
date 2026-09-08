## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-kbwsx` | ContainerCreating | Pod workload-5dbb5dcd6c-kbwsx stuck in ContainerCreating/Pending state with network setup failure |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `FailedCreatePodSandBox` (fact-87de853bb4cd)：46m 内重试 196 次，报错 `failed to setup network for sandbox` | 确认容器无法创建的直接机制与频率 |
| 2 | K8s Event | multus | `NoNetworkFound` (fact-0ab726b3ca54, fact-131818ae3764)：`cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` | 定位 Multus 插件因找不到 NAD 而拒绝网络挂载的确切原因 |
| 3 | K8s Event | kubelet | `FailedCreatePodSandBox` (fact-26dbcdd2d24d)：`getKubernetesDelegate: cannot find a network-attachment-definition... "unavailable-network" not found` | 串联 Delegate 解析失败到具体的命名空间与资源缺失 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` (fact-b344d01bcf04)：值为 `1`，label `reason="ContainerCreating"` | 客观佐证 Pod 处于等待网络/配置就绪的状态且无法推进 |

**证据逻辑关联：**
- 证据 1、2、3 形成闭环：Multus 在初始化网络时寻找 `unavailable-network` 的 NAD（证据 2 & 3），因该资源缺失导致网络插件配置失败（证据 3），进而导致 kubelet 反复失败并创建 Pod Sandbox（证据 1）。
- 证据 4 从指标维度交叉验证了 Pod 因网络挂载失败而卡在 `ContainerCreating` 状态的客观事实。

## 🎯 根因分析 · g1

### 因果链

```text
NAD资源'unavailable-network'在命名空间缺失 → Multus插件解析Delegate失败 → 容器网络挂载失败(SandBox创建失败) → Pod卡在ContainerCreating/Pending状态
```

### 根因结论

已确认的根因为 Pod 关联的 Multus 网络引用资源缺失。Pod 配置请求了 `aiops-case-05` 命名空间下的 `unavailable-network` 网络附件定义（NAD），但该资源不存在，导致 Multus CNI 插件在尝试为 Pod 配置网络时持续报错 `NoNetworkFound` 并终止执行。

由于网络挂载失败，`kubelet` 无法完成 Pod 沙箱（Sandbox）的创建，引发高频率的 `FailedCreatePodSandBox` 事件，致使该 Pod 始终停留在 `ContainerCreating` 或 `Pending` 状态，无法启动容器。

- **引用证据**：Multus 报错见证据 2, 3；Kubelet 重复失败见证据 1；指标状态见证据 4。
- **剩余未知**：现有证据仅能确认 NAD 缺失这一静态事实。对于 `unavailable-network` 是遭受临时删除、配置拼写错误，还是该 Pod 所属的其他应用组件也在等待同一网络定义，尚无更多事实支撑。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 14.7s
├─ 并发证据采集: 53.1s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx: 53.1s (Evidence 43.0s, RCA 10.0s)
└─ 汇总总结: 11.2s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx**: pod-volume-mount-failed, pod-sandbox-create-failed
