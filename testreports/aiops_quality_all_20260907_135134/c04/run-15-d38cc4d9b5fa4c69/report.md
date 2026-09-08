## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-7ds5p` | CreateContainerConfigError | Pod workload-6584f97c76-7ds5p 处于 Pending 阶段，容器状态 Waiting (CreateContainerConfigError)；kubelet 报错无法在 Secret workload-input 中找到 key unavailable-key，导致容器配置失败，应用未启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` (Warning Failed, x12 over 25m) | 直接证明容器配置阶段因 Secret Key 缺失被 Kubelet 阻断。 |
| 2 | K8s State | Kubernetes | `Pod status: Pending`, `container restart_count: 0` | 确认 Pod 处于等待阶段，且应用容器尚未发生过重启。 |
| 3 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` (reason: `CreateContainerConfigError`) = 1 | 从监控指标维度印证 K8s 事件的异常分类。 |

上述证据形成闭环：`K8s Event` 提供了缺失 `workload-input/unavailable-key` 的具体报错原文，与 `Metric` 中的 `CreateContainerConfigError` 状态完全对应，确证根因为配置项不可用，而非资源不足或其他网络问题。

## 🎯 根因分析 · g1

### 因果链
```text
Pod Spec 引用了不存在的 Secret Key (aiops-case-04/workload-input 中的 unavailable-key) → Kubelet 在容器创建阶段验证 Secret 配置失败 → 容器启动被强制阻止，状态保持为 Waiting (CreateContainerConfigError) → Pod 持续处于 Pending 状态
```

### 根因结论
已确认根因为 **Secret 引用错误**。
`aiops-case-04/workload-input` 中不存在 `unavailable-key`，导致 Pod `workload-6584f97c76-7ds5p` 无法完成配置加载（见证据 #1、#3）。该配置错误直接阻断了容器的启动流程，使得应用无法运行。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 27.7s
├─ 并发证据采集: 38.9s
│  └─ g1 aiops-case-04/workload-6584f97c76-7ds5p: 38.9s (Evidence 30.4s, RCA 8.3s)
└─ 汇总总结: 6.3s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-7ds5p**: pod-config-error
