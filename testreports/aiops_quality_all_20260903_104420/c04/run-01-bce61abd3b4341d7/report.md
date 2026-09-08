## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-wvcb2` | CreateContainerConfigError | Pod aiops-case-04/workload-6584f97c76-wvcb2 持续处于 Pending 状态，容器 app 报错 CreateContainerConfigError |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_reason`: app 容器为 `CreateContainerConfigError` | 直接锁定失败类型为容器配置错误 |
| 2 | K8s State | Kubernetes | `container.waiting_message`: `couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 明确失败原因：Secret 中缺少指定 key |
| 3 | K8s Event | Kubernetes | `Warning Failed`: `kubelet` 报错 `couldn't find key unavailable-key in Secret aiops-case-04/workload-input` (x7 over 61s) | 证实 Kubelet 在尝试启动容器时因 Secret 注入失败而反复报错 |
| 4 | K8s State | Kubernetes | `pod.phase`: `Pending`, `ContainersReady`: `False` | 确认 Pod 处于不可用状态，且从未进入运行阶段 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="CreateContainerConfigError"}`: `1` | 从监控层面交叉验证了 Pod 卡在配置错误阶段的状态 |
| 6 | Metric | Prometheus | `kube_pod_container_status_restarts_total`: `0` | 证明容器尚未启动过，排除了运行时崩溃导致重启的可能 |

**证据说明：**
Kubernetes 的 `waiting_reason`、`waiting_message` 以及 Event 日志共同指向了确切的故障机制：Pod 定义中引用了 Secret `workload-input` 中的 key `unavailable-key`，但该 key 在 Secret 中实际不存在，导致 `kubelet` 无法完成环境变量注入。Metrics 数据中 `waiting_reason=CreateContainerConfigError` 为 1 且 `restart_count` 为 0，进一步从时序数据上证实了该错误是启动前发生的，且并未发生过实际运行和重启。

## 🎯 根因分析 · g1

### 因果链

```text
Secret workload-input 中不存在 key 'unavailable-key' → Pod spec 引用该 Secret key 注入环境变量 → kubelet 注入配置失败 → 容器无法启动，状态变更为 CreateContainerConfigError
```

### 根因结论

已确认的根因为 **Pod 容器定义中引用了 Secret `workload-input` 中不存在的 key `unavailable-key`**。

证据表明，容器在初始化阶段即遭到 `kubelet` 拦截。具体表现为：
1.  **直接错误**：Kubernetes 状态报告 `CreateContainerConfigError`，且明确指出 `couldn't find key unavailable-key in Secret aiops-case-04/workload-input`（见证据 #1, #2）。
2.  **失败机制**：`kubelet` 事件日志证实了在尝试创建容器时，因找不到所需的 Secret key 而连续触发 `Warning Failed` 事件（见证据 #3）。
3.  **排除其他因素**：重启计数为 0 且处于 Pending 状态，排除了应用运行时崩溃或资源不足等后续阶段的问题（见证据 #4, #6）。

现有证据充分支持上述根因结论，无需补充其他维度的事实。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 18.1s
├─ 并发证据采集: 61.4s
│  └─ g1 aiops-case-04/workload-6584f97c76-wvcb2: 61.4s (Evidence 52.1s, RCA 9.2s)
└─ 汇总总结: 10.5s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-wvcb2**: pod-config-error
