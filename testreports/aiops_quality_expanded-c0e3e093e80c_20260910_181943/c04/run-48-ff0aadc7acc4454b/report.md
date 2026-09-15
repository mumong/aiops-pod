## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-h4lt9` | CreateContainerConfigError | Pod aiops-case-04/workload-6584f97c76-h4lt9 处于 Pending 状态，容器 `app` 因 CreateContainerConfigError 无法启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | fact-2d0419e679ab: `container.waiting_message`="couldn't find key unavailable-key in Secret aiops-case-04/workload-input" | 确认故障直接原因：引用了不存在的 Secret Key |
| 2 | K8s State | kubernetes | fact-9d59f588e7d6: `container.waiting_reason`="CreateContainerConfigError" | 确认 Pod 无法进入 Running 状态 |
| 3 | K8s State | kubernetes | fact-27db43284b01: `pod.status`="Pending" | 确认 Pod 停留在调度/启动前阶段 |
| 4 | Metric | prometheus | fact-4136c3177946: `kube_pod_container_status_waiting_reason`=1 (labels: `reason`="CreateContainerConfigError") | 独立观测到与 K8s 状态一致的等待原因 |
| 5 | K8s State | kubernetes | fact-0d4e53f0d5ce: `ContainersReady`=False, `ContainersNotReady`, containers=[app] | 进一步印证容器因配置错误未能就绪 |
| 6 | K8s State | kubernetes | fact-4d9c4563cbf0: `container.restart_count`=0 | 排除容器因业务逻辑崩溃导致的重启，确认启动阶段即失败 |

**证据关联说明：**
Kubernetes 核心状态与指标高度一致：`CreateContainerConfigError` 直接导致 Pod 处于 `Pending` 状态，且未发生任何重启。Metric 数据（fact-4136c3177946）在时间戳上与 K8s 状态相符，独立验证了等待原因并非网络或资源不足，而是明确的配置错误。Logging 和 Tracing 被标注为 `not_applicable`，符合容器未启动的物理限制。

## 🎯 根因分析 · g1

### 因果链

```text
Deployment 引用了不存在的 Secret Key (unavailable-key) → kubelet 无法解析并挂载配置 → 容器状态变为 CreateContainerConfigError → Pod 持续处于 Pending 状态
```

### 根因结论

已确认的根因是 **Pod 配置中引用了不存在的 Secret Key**。

具体而言，Pod `aiops-case-04/workload-6584f97c76-h4lt9` 的容器 `app` 在启动时，试图从 Secret `workload-input` 中读取 `unavailable-key` 作为配置（环境变量或挂载），但该 Key 实际上并不存在于该 Secret 中。这一配置错误直接触发了 `CreateContainerConfigError` 状态，导致容器无法启动，Pod 因此一直处于 `Pending` 阶段。该结论由 K8s 原生事件（fact-2d0419e679ab）和 Prometheus 指标（fact-4136c3177946）共同支撑，证据充分，无需补充日志或追踪数据。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 17.6s
├─ 并发证据采集: 55.2s
│  └─ g1 aiops-case-04/workload-6584f97c76-h4lt9: 55.2s (Evidence 45.8s, RCA 9.3s)
└─ 汇总总结: 10.4s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-h4lt9**: pod-config-error
