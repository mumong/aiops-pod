## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-h4lt9` | CreateContainerConfigError | Pod workload-6584f97c76-h4lt9 处于 Pending 状态，容器持续报错 CreateContainerConfigError 无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `kubelet` | `Warning Failed 47m (x12 over 49m) kubelet Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` (fact-5f3bb044d7d2) | 证明 kubelet 在挂载配置时明确报告了 Secret 键值缺失，直接定位到配置引用错误。 |
| 2 | K8s State | `kubelet` | `container.waiting_message`: `couldn't find key unavailable-key in Secret aiops-case-04/workload-input` (fact-1d0bd3d4e906) | 容器等待状态详细错误信息，与 Event 消息一致，确认错误发生于容器配置阶段。 |
| 3 | K8s State | `kubelet` | `container.waiting_reason`: `CreateContainerConfigError` (fact-65f78c62a2a0) | 确认故障类型为配置类错误，而非资源不足或容器内部逻辑错误。 |
| 4 | Metric | `prometheus` | `kube_pod_container_status_waiting_reason{container="app", reason="CreateContainerConfigError"} = 1` (fact-324275e24c05) | 独立于 kubelet 日志，从集群监控视角验证了容器正卡在 `CreateContainerConfigError` 状态。 |
| 5 | K8s State | `kubelet` | `pod.phase`: `Pending` (fact-72a2bdc49df4) | 宏观层面展示 Pod 始终无法完成初始化，因为基础容器配置无法加载。 |

**证据印证关系：**
Event (fact-5f3bb044d7d2) 与 Waiting Message (fact-1d0bd3d4e906) 在错误细节上完全重合，共同锁定了 `Secret` 中的键名错误；Metric (fact-324275e24c05) 的 `CreateContainerConfigError` 状态作为辅助验证，确认了集群层面监控到的异常与底层事件原因一致。

## 🎯 根因分析 · g1

```text
Secret aiops-case-04/workload-input 中未包含请求的 key 'unavailable-key' → Kubelet 挂载 Secret 失败并抛出异常 → 容器启动被挂起，状态设为 CreateContainerConfigError → Pod 处于 Pending 状态，持续报错
```

### 根因结论
**已确认的根因：** Pod `aiops-case-04/workload-6584f97c76-h4lt9` 在 YAML 中引用了 Secret `aiops-case-04/workload-input` 中不存在的 key `unavailable-key`。
**形成机制：** Kubelet 在创建容器阶段尝试挂载 Secret 卷时，因找不到指定 key 而抛出 `Error: couldn't find key unavailable-key` (fact-5f3bb044d7d2)，导致容器配置加载失败，抛出 `CreateContainerConfigError` (fact-65f78c62a2a0)。
**证据支持：** Kubernetes Event 与 Container Waiting Message 提供了完全一致且详细的错误原因描述（fact-5f3bb044d7d2, fact-1d0bd3d4e906），且 Metric 状态（fact-324275e24c05）独立确认了该异常状态。现有事实已充分闭环，证据充足。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 12.5s
├─ 并发证据采集: 61.1s
│  └─ g1 aiops-case-04/workload-6584f97c76-h4lt9: 61.1s (Evidence 53.7s, RCA 7.2s)
└─ 汇总总结: 11.9s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-h4lt9**: pod-config-error, pod-notready-probe-failed, pod-crashloop-runtime, pod-pending-unschedulable
