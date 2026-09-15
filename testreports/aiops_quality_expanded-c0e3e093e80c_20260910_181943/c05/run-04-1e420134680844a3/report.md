## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-bntfh` | ContainerCreating | Pod workload-5dbb5dcd6c-bntfh in aiops-case-05 is stuck in Pending state due to ContainerCreating failure. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `kubernetes` | `container.waiting_reason`: reason=`ContainerCreating` | 确认 Pod 处于等待分配资源的阻塞状态 |
| 2 | K8s Event | `multus` | `reason=NoNetworkFound`: `cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` (46次重复) | 证明 Multus 插件在获取 CNI 委派时，无法在指定命名空间找到名为 `unavailable-network` 的网络定义资源 |
| 3 | K8s Event | `kubelet` | `reason=FailedCreatePodSandBox`: `failed to setup network for sandbox ... plugin type="multus" ... GetKubernetesDelegate: cannot find a network-attachment-definition` | 证明容器运行时因网络插件返回错误而拒绝创建 Pod 沙箱，导致启动过程终止 |
| 4 | Metric | `prometheus` | `kube_pod_container_status_waiting_reason`: reason=`ContainerCreating`, value=`1`, sample_count=`1` | 提供数值层面的佐证，确认容器处于 `ContainerCreating` 等待状态 |

**证据关联性说明：**
1.  **K8s Event (Multus) & K8s Event (Kubelet) 形成闭环**：K8s 事件 `fact-00ab...` 至 `fact-7590...` 显示 Multus 插件反复报告找不到 `unavailable-network` 定义；紧接着的 `FailedCreatePodSandBox` 事件（如 `fact-0b04...`、`fact-1e2e...` 等）确认了正是这一网络配置缺失导致了 Kubelet 创建沙箱的失败。两者互为因果，直接锁定了故障链路。
2.  **Metric 状态佐证**：Prometheus 指标 `fact-3855438e2721` 中 `reason=ContainerCreating` 的数值确认，与 K8s 事件反映的“网络创建失败导致 Pod 无法进入运行/就绪状态”的宏观表现一致，未出现其他维度的冲突信息（日志/Tracing 因容器未启动不可用）。

## 🎯 根因分析 · g1

### 因果链

```text
Missing NetworkAttachmentDefinition 'unavailable-network' → Multus CNI plugin delegate fetch failed (GetKubernetesDelegate) → Kubelet FailedCreatePodSandBox → Pod stuck in ContainerCreating (Pending)
```

### 根因结论

**已确认的根因：**
Pod `workload-5dbb5dcd6c-bntfh` 在 `aiops-case-05` 命名空间中请求了名为 `unavailable-network` 的 Multus `NetworkAttachmentDefinition`，但该资源在集群中不存在（未创建或已被删除）。

**证据支撑：**
-   **K8s Event (Multus)** 显示 46 次 `NoNetworkFound` 警告，明确指出无法在 `aiops-case-05` 命名空间中找到该网络定义（见证据 #2）。
-   **K8s Event (Kubelet)** 显示 `FailedCreatePodSandBox` 错误，其深层原因为 `GetKubernetesDelegate` 失败，同样指向 `unavailable-network` 缺失（见证据 #3）。
-   **K8s State & Metric** 确认容器因此停留在 `ContainerCreating` 状态，未能拉起（见证据 #1, #4）。

**未确认/受限事实：**
输入事实中的 `unknowns` 字段指出，由于权限限制，无法通过工具验证 `unavailable-network` 是否曾经存在或为何未被创建，但这不影响当前“资源缺失导致启动失败”的根因判定。

---

## 📊 性能统计

```text
├─ 总耗时: 6.5m
├─ 问题定位: 17.7s
├─ 并发证据采集: 360.5s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-bntfh: 360.5s (Evidence 351.1s, RCA 9.2s)
└─ 汇总总结: 12.8s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-bntfh**: pod-volume-mount-failed
