## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v12/workload` | Terminating | Pod aiops-case-v12/workload 初始状态为 Terminating，但实际未正常退出，处于挂起状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `pod.condition={"status": "True", "type": "ContainersReady"} (fact_id=fact-5fdd566ce1d2)` | 确认生命周期、状态、事件或配置 |
| 2 | K8s State | kubernetes | `pod.condition={"status": "True", "type": "PodScheduled"} (fact_id=fact-77a8aefbe44f)` | 确认生命周期、状态、事件或配置 |
| 3 | K8s State | kubernetes | `pod.condition={"status": "True", "type": "Initialized"} (fact_id=fact-84abb93332a0)` | 确认生命周期、状态、事件或配置 |
| 4 | Metric | prometheus | `kube_pod_status_phase=1 unitless（phase=Running） (fact_id=fact-7b241103712b)` | 量化资源、状态或变化 |
| 5 | Metric | prometheus | `[症状/持续性] kube_pod_container_status_restarts_total=0 count (fact_id=fact-c7fd85e37bd7)` | 量化资源、状态或变化 |
| 6 | Metric | prometheus | `[负向观测/排除] kube_pod_status_phase=0 unitless（phase=Succeeded） (fact_id=fact-2318968763bb)` | 量化资源、状态或变化 |
| 7 | Metric | prometheus | `[负向观测/排除] kube_pod_status_phase=0 unitless（phase=Failed） (fact_id=fact-2ec69082e42e)` | 量化资源、状态或变化 |
| 8 | Logging | elasticsearch | `application started (fact_id=fact-61b824970025)` | 保留应用或容器错误原文 |

## 🎯 根因分析 · g1

### 因果链

```text
应用设计为 preStop hook 等待外部信号文件 /state/teardown-requested → 文件 /state/teardown-requested 从未出现，preStop 钩子无法退出 → Pod 停留在 Terminating 状态，无法真正删除
```

### 根因结论

Pod 的 preStop lifecycle hook 设计为无限循环等待特定文件 /state/teardown-requested 出现，该文件从未被创建，导致 preStop 阶段超时，进而使 Pod 卡在 Terminating 阶段无法完成删除。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 17.4s
├─ 并发证据采集: 41.4s
│  └─ g1 aiops-case-v12/workload: 41.4s (Evidence 32.0s, RCA 9.3s)
└─ 汇总总结: 6.5s
```

📋 Runbook 参考

- **g1 aiops-case-v12/workload**: pod-terminating-stuck
