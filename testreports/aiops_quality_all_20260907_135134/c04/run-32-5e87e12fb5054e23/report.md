## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-7ds5p` | CreateContainerConfigError | Pod配置中引用了Secret aiops-case-04/workload-input中不存在的key 'unavailable-key'，导致kubelet无法创建容器 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_reason: CreateContainerConfigError` (fact-56d9e111448c) | 直接确认容器因配置错误处于 Waiting 状态 |
| 2 | K8s State | Kubernetes | `container.waiting_message: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` (fact-732603e2cd97) | 明确指出了缺失的 Secret Key 名称及所在 Secret |
| 3 | K8s Event | Kubernetes | `Warning Failed ... Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` (fact-f604b2b7c92d) | 提供了事件维度的复现记录与时间窗口，确认是 Kubelet 报错 |
| 4 | K8s State | Kubernetes | `pod.status: Pending` (fact-1196e040e8e8) | 确认 Pod 因容器未启动而处于 Pending 状态 |
| 5 | K8s State | Kubernetes | `container.restart_count: 0` (fact-3b501cdfa0da) | 排除重启风暴，证实为启动初期的配置拦截 |
| 6 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="CreateContainerConfigError"} = 1` (fact-d6c138f33160) | 监控指标层面的佐证，状态与 K8s 节点侧记录一致 |

**证据互证说明：**
Kubernetes 的 `waiting_message`（事实 #2）与 Event 信息（事实 #3）在错误原文上完全一致，均指向 `Secret aiops-case-04/workload-input` 中缺失 `unavailable-key`。Metric 数据（事实 #6）确认了该状态已被持续暴露。重启计数为 0 排除了应用运行时的间歇性崩溃，指向了启动前的静态配置校验失败。Logging 和 Tracing 维度因容器未启动被标记为不可用（Not Applicable），属于符合预期的现象。

## 🎯 根因分析 · g1

### 因果链

```text
Pod YAML 配置引用了不存在的 Secret Key 'unavailable-key' → kubelet 无法获取指定 Key 导致配置校验失败 → 容器无法创建并持续处于 Waiting 状态 → Pod 整体处于 Pending 状态且不可用
```

### 根因结论

**已确认根因：Pod 配置中引用了 Secret `aiops-case-04/workload-input` 中不存在的 Key `'unavailable-key'`。**

证据编号 #2 和 #3 提供了明确的原始错误信息，证实 Kubernetes 在尝试拉取 Secret 配置时发现指定的 Key 缺失。该配置错误导致 Kubelet 拒绝了容器创建请求（`CreateContainerConfigError`），致使 Pod 无法进入运行状态。证据链完整，诊断已发布。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 22.6s
├─ 并发证据采集: 29.6s
│  └─ g1 aiops-case-04/workload-6584f97c76-7ds5p: 29.6s (Evidence 23.1s, RCA 6.4s)
└─ 汇总总结: 10.0s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-7ds5p**: pod-config-error
