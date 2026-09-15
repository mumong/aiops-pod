## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-h4lt9` | CreateContainerConfigError | Pod workload-6584f97c76-h4lt9 处于 CreateContainerConfigError 状态，容器未能启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_reason`: CreateContainerConfigError; `container.waiting_message`: couldn't find key unavailable-key in Secret aiops-case-04/workload-input (fact-12d27c876e5b, fact-20f04f1375c4) | 直接揭示容器启动失败的具体配置原因 |
| 2 | K8s Event | Kubernetes | `event.message`: Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input (事实关联 x12 over 22m) (fact-7ed74a12f688) | 确认为持续性错误，排除一次性瞬态故障 |
| 3 | K8s State | Kubernetes | `pod.status`: Pending; `pod.phase`: Pending (fact-77fd7efe98f2, fact-e77300449f97) | 确认 Pod 无法进入运行阶段 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="CreateContainerConfigError"}` = 1 (fact-354254b960cb) | 观测数据与 K8s 状态相互印证 |

上述证据链闭环：Prometheus 监控捕获到等待原因，Kubernetes 状态与事件日志共同指向特定的 Secret 键值缺失，确认为配置层面的直接错误。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置引用了 Secret aiops-case-04/workload-input 中的 key unavailable-key → 
Namespace aiops-case-04 中不存在名为 workload-input 的 Secret → 
Kubelet 无法注入配置并报错 → 
Pod 持续处于 CreateContainerConfigError 状态 (Pending)
```

### 根因结论

已确认的根因为 **Pod 配置引用了不存在的 Secret (`aiops-case-04/workload-input`) 及其 Key (`unavailable-key`)**，导致 Kubelet 无法完成配置注入，容器始终处于等待启动状态 [证据 1, 2]。现有 K8s State 与 Event 事实已形成完整证据链，支持发布该诊断结论 [支持 1, 2, 4]。

---

## 📊 性能统计

```text
├─ 总耗时: 54.1s
├─ 问题定位: 10.2s
├─ 并发证据采集: 35.9s
│  └─ g1 aiops-case-04/workload-6584f97c76-h4lt9: 35.9s (Evidence 28.0s, RCA 7.8s)
└─ 汇总总结: 7.9s
```

📋 Runbook 参考

- 未调用 Runbook
