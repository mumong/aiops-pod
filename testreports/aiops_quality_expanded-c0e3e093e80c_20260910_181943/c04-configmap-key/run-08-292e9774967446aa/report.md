## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v11/workload` | CreateContainerConfigError | Pod spec 引用的 ConfigMap 'aiops-case-v11/workload-input' 中缺失 key 'unavailable-key'，导致 kubelet 无法完成容器环境初始化，从而进入 CreateContainerConfigError 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | fact-a2bf73bd18dc | `restart_count: 0` | 症状：Pod 处于初始挂起阶段，尚未发生重启。 |
| 2 | K8s Event | fact-c54e175821a8 | `Error: couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input` | 根因：kubelet 明确报告配置项加载失败。 |
| 3 | Metric | fact-91d82d64cd9a | `kube_pod_container_status_waiting_reason: 1 (reason=CreateContainerConfigError)` | 症状：指标确认容器停留在配置错误等待状态。 |

K8s Event 中的具体缺失键名 (`unavailable-key`) 直接解释了 Metric 中的 `CreateContainerConfigError` 原因，两者共同锁定了 Pod 无法初始化的确切原因。Pod 未启动且未重启 (`restart_count: 0`) 与配置加载错误这一静态依赖缺失的逻辑相符。由于容器未启动，Logging 与 Tracing 维度未采集到数据，属于正常现象。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 缺失 key 'unavailable-key' (fact-c54e175821a8) → 容器启动前置检查失败 → kubelet 返回 CreateContainerConfigError → Pod 状态卡死在 Pending (fact-91d82d64cd9a)
```

### 根因结论

**已确认根因**：Pod spec 引用的 ConfigMap `aiops-case-v11/workload-input` 中缺失 key `unavailable-key`。

该缺失导致 kubelet 在初始化容器环境时无法注入环境变量或挂载卷，直接触发了 `CreateContainerConfigError` 状态。这一结论由 K8s 事件 (fact-c54e175821a8) 中的原始错误原文直接证实，并得到 Metrics (fact-91d82d64cd9a) 中对应的等待原因指标支持。

---

## 📊 性能统计

```text
├─ 总耗时: 50.0s
├─ 问题定位: 11.3s
├─ 并发证据采集: 31.3s
│  └─ g1 aiops-case-v11/workload: 31.3s (Evidence 25.7s, RCA 5.5s)
└─ 汇总总结: 7.3s
```

📋 Runbook 参考

- **g1 aiops-case-v11/workload**: pod-config-error
