## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-h4lt9` | CreateContainerConfigError | Pod workload-6584f97c76-h4lt9 处于 Pending 状态，容器 app 启动失败并持续报错 CreateContainerConfigError |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `CreateContainerConfigError`: couldn't find key unavailable-key in Secret aiops-case-04/workload-input | 确定启动失败的确切原因及关联资源 |
| 2 | K8s State | kubernetes | `Pending`: Ready=False, ContainersNotReady | 确认容器卡死在启动前状态 |
| 3 | K8s State | kubernetes | `restart_count`: 0 | 确认实例从未进入 Running 阶段 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason`: CreateContainerConfigError=1 | 通过遥测数据二次确认了容器状态 |
| 5 | Metric | prometheus | `kube_pod_container_status_restarts_total`: 0 | 印证了容器无实际运行历史 |
| 6 | K8s Config | kubernetes | Resource Limits: CPU=50m, Mem=32Mi; Requests: CPU=5m, Mem=8Mi | 排除资源超配导致的调度或启动问题 |

**证据互证说明：**
1. 维度间一致性：K8s 控制面状态 (fact-4ed37669a29c) 与 Prometheus 遥测指标 (fact-a305651921af) 在 `CreateContainerConfigError` 上完全一致。
2. 排除干扰：重启计数为 0 (fact-b1c25e6b726d) 结合资源限制合理，说明 Pod 尚未经历任何生命周期循环，问题完全发生在配置拉取阶段。
3. 缺失数据：因物理限制，日志与 Trace 为 `not_applicable`，不影响当前诊断结论。

## 🎯 根因分析 · g1

### 因果链
```text
Secret 'workload-input' 缺少键 'unavailable-key' → kubelet 无法注入缺失配置 → 抛出 CreateContainerConfigError → Pod 持续处于 Pending 状态
```

### 根因结论
已确认根因为：**Pod 配置文件引用了 Secret `aiops-case-04/workload-input` 中不存在的键 `unavailable-key`** (证据 #1, #6)。

由于配置引用不匹配，kubelet 在创建容器阶段即被阻断，导致 Pod 无法推进至 `Running` 状态，也无法产生任何应用日志或运行时指标。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 18.1s
├─ 并发证据采集: 49.0s
│  └─ g1 aiops-case-04/workload-6584f97c76-h4lt9: 49.0s (Evidence 40.7s, RCA 8.2s)
└─ 汇总总结: 8.1s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-h4lt9**: pod-config-error
