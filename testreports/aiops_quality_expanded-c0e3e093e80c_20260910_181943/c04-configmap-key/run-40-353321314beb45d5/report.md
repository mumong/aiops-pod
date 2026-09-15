## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v11/workload` | CreateContainerConfigError | aiops-case-v11/workload pod处于Pending状态，容器app因CreateContainerConfigError无法启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `pod.phase`: Pending | 确认容器组未进入运行态 |
| 2 | K8s State | Kubernetes | `container.waiting_reason`: CreateContainerConfigError | 锁定故障发生在容器启动配置阶段 |
| 3 | K8s Event | Kubernetes | `Warning  Failed  59m`: Error: couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input | 直接指出具体缺失的 ConfigMap key 和对象名 |
| 4 | K8s State | Kubernetes | `container.waiting_message`: couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input | 证实 kubelet 读取配置时的确切报错信息 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` (reason=CreateContainerConfigError) 值为 1 | 从监控维度独立印证了等待状态的成因 |

Kubernetes Event (fact-ffa8e70e38aa) 与 State (fact-7523e152dfdd) 明确显示了配置引用失败的具体细节。Prometheus 指标 (fact-da4344b9e320) 从聚合层面证实了该 Pod 因相同原因持续处于等待状态。Metric 与 K8s 事件在错误原因上完全一致，形成闭环。

## 🎯 根因分析 · g1

### 因果链

```text
Pod spec错误引用ConfigMap中不存在的key 'unavailable-key' → kubelet在创建容器时发现ConfigMap key缺失 → 容器启动失败并进入Waiting状态，Reason为CreateContainerConfigError → Pod持续处于Pending状态，无法调度运行
```

### 根因结论

已确认根因：Pod spec 中引用了 ConfigMap `aiops-case-v11/workload-input` 中不存在的 key `unavailable-key`。

这一错误直接导致 kubelet 在启动容器时无法注入配置，进而报 `CreateContainerConfigError` 并阻止容器运行。现象表现为 Pod 永久处于 Pending 状态且未重启（restart_count=0）。该结论由 K8s Event (fact-d64f109ad4e1)、K8s State (fact-7523e152dfdd) 及 Metric (fact-da4344b9e320) 共同支撑。

---

## 📊 性能统计

```text
├─ 总耗时: 59.6s
├─ 问题定位: 17.0s
├─ 并发证据采集: 34.3s
│  └─ g1 aiops-case-v11/workload: 34.3s (Evidence 27.2s, RCA 7.0s)
└─ 汇总总结: 8.3s
```

📋 Runbook 参考

- **g1 aiops-case-v11/workload**: pod-config-error
