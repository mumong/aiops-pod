## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-wvcb2` | CreateContainerConfigError | Pod `aiops-case-04/workload-6584f97c76-wvcb2` 处于 `Pending` 状态，容器 `app` 持续报 `CreateContainerConfigError`，未成功启动过。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Failed 56m (x12 over 58m) kubelet Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 提供直接错误原因，确认为 Secret Key 缺失导致的配置注入失败 |
| 2 | K8s State | kubernetes | `CreateContainerConfigError` (Container `app`) | 确认容器创建阶段因配置缺失而直接中止，未进入运行状态 |
| 3 | K8s State | kubernetes | `PodPhase: Pending` (58m 内持续), `restart_count: 0` | 证实 Pod 因配置错误被调度器拦截，未产生任何容器生命周期事件 |

*注：Metrics (`CreateContainerConfigError: 1`, `restarts: 0`) 与 K8s 状态一致，确认了故障的持续性；Logging/Tracing 因容器未启动而无有效数据。*

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 引用 Secret aiops-case-04/workload-input 的 key 'unavailable-key' → 
Secret 中实际不存在该 key → 
kubelet 无法完成环境变量注入/卷挂载 → 
触发 CreateContainerConfigError 导致容器拒绝创建 → 
Pod 维持 Pending 状态，重启次数为 0
```

### 根因结论

**已确认根因：** Pod `aiops-case-04/workload-6584f97c76-wvcb2` 的 Spec 中引用了 Secret `aiops-case-04/workload-input` 中不存在的 key `unavailable-key`。
**依据：** 
- 事件 `fact-8f479a313541` / `fact-cced7e416c57` 明确指出 kubelet 报错找不到 `unavailable-key`。
- 容器状态 `fact-a2f751296189` 显示具体的等待原因为该 key 缺失。
- 状态 `fact-aae66c34aa2f` 确认错误类型为 `CreateContainerConfigError`，这与配置缺失导致的配置阶段失败机制完全吻合。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 21.4s
├─ 并发证据采集: 64.6s
│  └─ g1 aiops-case-04/workload-6584f97c76-wvcb2: 64.6s (Evidence 54.9s, RCA 9.6s)
└─ 汇总总结: 8.0s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-wvcb2**: pod-config-error
