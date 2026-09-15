## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-h4lt9` | CreateContainerConfigError | Pod `workload-6584f97c76-h4lt9` 配置引用了 Secret `aiops-case-04/workload-input` 中的 key `unavailable-key`，但该 Secret 中实际仅包含 `available-key`，导致 Kubelet 在创建容器阶段因找不到指定密钥而失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubelet | `CreateContainerConfigError` (Container: app) | 判定容器启动在配置加载阶段即已阻断 |
| 2 | K8s Event | kubelet | `Warning Failed: Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 直接指出导致失败的具体缺失资源名称及位置 |
| 3 | Metric | prometheus | `kube_pod_container_status_waiting_reason=1` (reason=CreateContainerConfigError) | 独立确认了 K8s 内部状态指标与事件记录一致 |
| 4 | K8s Config | kubelet | resource_request: cpu=5m, memory=8Mi; resource_limit: cpu=50m, memory=32Mi | 确认资源配置极低且非导致当前启动失败的原因 |

当前 Kubernetes 状态指标、事件记录及容器状态共同证实，Pod 因缺失特定的 Secret key (`unavailable-key`) 导致 Kubelet 无法完成容器配置加载，从而进入 `Pending` 状态；资源请求/限制配置处于正常范围内且未引发调度或 OOM 问题。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置引用不存在的 Secret key (`unavailable-key`) → Kubelet 验证 Secret 数据失败 → 容器启动被阻断 (CreateContainerConfigError) → Pod 保持 Pending 状态且无法就绪
```

### 根因结论

已确认的根因为 Pod 配置错误。Pod `aiops-case-04/workload-6584f97c76-h4lt9` 的容器配置中引用了 Secret `aiops-case-04/workload-input` 中的 key `unavailable-key`，但该 Secret 中实际并不包含此 key，直接导致 Kubelet 在创建容器阶段因找不到指定密钥而阻断启动。

证据支持：
- **Kubernetes 事件 (fact-6982f36be56d)** 明确指出了缺失的 key 和 Secret 路径。
- **Kubernetes 状态 (fact-b0714b5204dc, fact-cc011631e933)** 显示容器处于 `CreateContainerConfigError`，原因是找不到密钥。
- **Prometheus 指标 (fact-dd51c7b3c099)** 在 `kube_pod_container_status_waiting_reason` 中确认了 `CreateContainerConfigError` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 17.2s
├─ 并发证据采集: 42.7s
│  └─ g1 aiops-case-04/workload-6584f97c76-h4lt9: 42.7s (Evidence 34.3s, RCA 8.3s)
└─ 汇总总结: 8.6s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-h4lt9**: pod-config-error
