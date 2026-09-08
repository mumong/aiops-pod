## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-7ds5p` | CreateContainerConfigError | Pod aiops-case-04/workload-6584f97c76-7ds5p 处于 Pending 状态，容器 app 处于 CreateContainerConfigError 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubelet | Pod phase: Pending | 描述当前 Pod 始终处于调度完成但未就绪的状态 [fact-28827c176613] |
| 2 | K8s Event | kubelet | Warning Failed: couldn't find key unavailable-key in Secret aiops-case-04/workload-input (41m, x12 over 43m) | 直接指出容器启动失败的具体缺失配置及对应资源标识 [fact-8d2f994efd45] |
| 3 | K8s State | kubelet | container.app waiting_reason: CreateContainerConfigError | 确认容器未进入运行态，而是停留在配置校验阶段 [fact-fac8576c3c98] |
| 4 | K8s State | kubelet | container.app waiting_message: couldn't find key unavailable-key in Secret aiops-case-04/workload-input | 与 Event 信息一致，佐证是配置注入失败导致无法启动 [fact-8ef3e93a045a] |
| 5 | K8s Config | kubelet | resource_limit.cpu: 50m, resource_limit.memory: 32Mi | 提供 Pod 资源约束背景，排除因资源配额导致 Pending 的可能 [fact-06c0df9e4eb5, fact-2bf6ddd68644] |
| 6 | Metric | prometheus | kube_pod_container_status_waiting_reason[container="app", reason="CreateContainerConfigError"] = 1 | 从观测层面持续确认该 Pod 处于因配置错误导致的等待状态 [fact-ba3f14910744] |
| 7 | Metric | prometheus | kube_pod_container_status_restarts_total[container="app"] = 0 | 证明容器未能成功拉起，无重启记录，与 CreateContainerConfigError 一致 [fact-96db19779692] |

**证据小结：**
Kubernetes 状态与 Event 明确指出了 `CreateContainerConfigError` 且缺失 `Secret` 中的特定 key (`unavailable-key`)；Prometheus Metrics 从集群观测侧独立印证了容器卡在等待状态且无重启发生。由于容器未启动，日志和 Trace 数据为空，物理上无法提供补充证据。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置引用 Secret aiops-case-04/workload-input 中的 unavailable-key → Secret 中缺失该 key 导致 kubelet 无法注入环境变量 → 容器配置校验失败 (CreateContainerConfigError) → Pod 处于 Pending 状态
```

### 根因结论

已确认的根因为：Pod `aiops-case-04/workload-6584f97c76-7ds5p` 的配置中引用了 Secret `aiops-case-04/workload-input` 的 `unavailable-key` 字段，但该 Secret 中实际上不存在该 key。这导致 kubelet 在启动容器前进行配置注入失败，直接引发了 `CreateContainerConfigError` [fact-8d2f994efd45, fact-8ef3e93a045a]，使得 Pod 一直处于 `Pending` 状态 [fact-28827c176613, fact-ba3f14910744]。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 15.5s
├─ 并发证据采集: 36.3s
│  └─ g1 aiops-case-04/workload-6584f97c76-7ds5p: 36.3s (Evidence 28.3s, RCA 7.9s)
└─ 汇总总结: 11.4s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-7ds5p**: pod-config-error
