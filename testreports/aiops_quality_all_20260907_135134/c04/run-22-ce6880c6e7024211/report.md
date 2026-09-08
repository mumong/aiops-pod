## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-7ds5p` | CreateContainerConfigError | Pod aiops-case-04/workload-6584f97c76-7ds5p 处于 Pending 状态，容器 app 因 CreateContainerConfigError 无法启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes (fact-7a1d030e27bd) | `Warning Failed Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 明确指向配置缺失的致命错误，是容器无法启动的直接原因 |
| 2 | K8s State | kubernetes (fact-dd92fe8fe1d7) | Pod `aiops-case-04/workload-6584f97c76-7ds5p` 状态为 `Pending` | 确认 Pod 当前不可用且处于等待阶段 |
| 3 | K8s State | kubernetes (fact-a81cfe31e3bf) | 容器 `app` 的 `restart_count` 为 0 | 表明容器从未成功启动，排除了运行后崩溃或健康检查失败的可能 |
| 4 | Metric | prometheus (fact-9b5d14cdfb6a) | `kube_pod_container_status_waiting_reason` (app) = 1, reason=`CreateContainerConfigError` | 从监控指标层面确认了容器处于“配置错误等待”状态 |
| 5 | K8s Config | kubernetes (fact-2fa3488b6fe5, fact-38a3d3a0f441) | 资源 Request: CPU 5m, Memory 8Mi | 提供资源需求上下文，非故障成因 |

证据间互相印证：K8s Event (证据1) 明确指出了缺失的具体 Secret Key，这与 K8s State (证据3) 中重启次数为 0 的现象一致，说明 Pod 卡在启动初始化阶段。Metric (证据4) 进一步从指标维度确认了 `CreateContainerConfigError` 状态，与 Event 的致命错误信息形成闭环。

## 🎯 根因分析 · g1

### 因果链

```text
Pod spec 引用了 Secret 'aiops-case-04/workload-input' 中不存在的 key 'unavailable-key' → kubelet 在容器启动时注入配置失败 → 容器启动失败，状态转为 Waiting (Reason: CreateContainerConfigError) → Pod 持续处于 Pending 状态，无日志产出
```

### 根因结论

**已确认的根因**：Pod 配置错误。Pod 规范中引用了 Secret `aiops-case-04/workload-input` 中的 `unavailable-key`，但该 key 在 Secret 中不存在。
此配置错误导致 kubelet 在创建容器前无法注入所需的环境变量或卷数据，直接触发了 `CreateContainerConfigError`，致使容器无法启动（证据编号：1, 4, 3）。

---

## 📊 性能统计

```text
├─ 总耗时: 56.1s
├─ 问题定位: 19.5s
├─ 并发证据采集: 27.4s
│  └─ g1 aiops-case-04/workload-6584f97c76-7ds5p: 27.4s (Evidence 21.0s, RCA 6.3s)
└─ 汇总总结: 9.1s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-7ds5p**: pod-config-error
