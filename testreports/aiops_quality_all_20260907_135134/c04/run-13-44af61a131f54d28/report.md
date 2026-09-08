## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-7ds5p` | CreateContainerConfigError | Pod workload-6584f97c76-7ds5p 处于 Pending 状态，Container 处于 CreateContainerConfigError，无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet (fact-8ff15971a44a) | `Warning Failed ... Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | **直接证明**：Kubelet 因 Secret 缺 Key 导致注入配置失败，是状态异常的起因 |
| 2 | K8s State | kubelet (fact-a801c88bdbc8) | Pod 状态: `Pending` | 表现现象：因配置错误导致 Pod 无法进入运行态 |
| 3 | Metric | Prometheus (fact-e2b92c3fdf76) | `kube_pod_container_status_waiting_reason` 值为 1，Label: `reason="CreateContainerConfigError"` | 独立验证：集群指标显示容器处于配置错误等待状态 |
| 4 | Metric | Prometheus (fact-3dfd9d5c5c52) | `kube_pod_container_status_restarts_total` 值为 0 | 排除干扰：容器因配置阶段失败从未启动，故不存在重启行为 |

**证据关联说明：**
K8s Event (1) 给出了容器无法启动的精确错误原因（Secret key 缺失），Metric (3) 在集群层面独立验证了该状态码为 `CreateContainerConfigError`。两者因果与现象高度一致，共同排除了网络或调度等其他故障可能。

## 🎯 根因分析 · g1

### 因果链

```text
Secret aiops-case-04/workload-input 缺失 key 'unavailable-key' → kubelet 注入配置失败 → 容器状态变为 CreateContainerConfigError → Pod 卡死在 Pending 状态
```

### 根因结论

**已确认根因**：Pod `workload-6584f97c76-7ds5p` 引用的 Secret `aiops-case-04/workload-input` 中缺少其 Spec 中指定的 key `'unavailable-key'`。
- 这一配置错误导致 `kubelet` 在尝试挂载/注入环境变量或卷时失败（证据 1）。
- 直接引发容器进入 `CreateContainerConfigError` 状态（证据 3），从而使 Pod 保持 `Pending` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 9.6m
├─ 问题定位: 16.2s
├─ 并发证据采集: 554.2s
│  └─ g1 aiops-case-04/workload-6584f97c76-7ds5p: 554.2s (Evidence 546.0s, RCA 8.1s)
└─ 汇总总结: 7.8s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-7ds5p**: pod-config-error
