## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-h4lt9` | CreateContainerConfigError | CreateContainerConfigError |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | Warning Failed: couldn't find key unavailable-key in Secret aiops-case-04/workload-input | 直接定位配置引用失败的具体缺失键 |
| 2 | K8s State | kubernetes | Pod 状态 Pending；容器 Waiting (CreateContainerConfigError) | 确认故障停留在配置拉取阶段，未触发容器内逻辑 |
| 3 | K8s Config | kubernetes | 资源 request/limit 配置正常 (CPU: 5m/50m, Memory: 8Mi/32Mi) | 排除因资源配额导致的调度或启动障碍 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="CreateContainerConfigError"}` 值为 1 | 从监控侧交叉印证了 K8s Event 的诊断状态 |
| 5 | Metric | prometheus | `kube_pod_container_status_restarts_total` 值为 0 | 证实尚未进入重启恢复循环，处于初始化失败状态 |

**证据总结：**
Kubernetes 的事件日志与监控指标（Metric）在“CreateContainerConfigError”这一状态上高度一致，均指向配置拉取阶段的阻断。K8s 状态确证了 Pod 处于 Pending 且无重启计数，排除了运行时资源不足或逻辑崩溃的可能。

## 🎯 根因分析 · g1

### 因果链

```text
Secret aiops-case-04/workload-input 中缺失键 unavailable-key → kubelet 获取配置数据失败 → 容器启动阶段配置验证失败 → Pod Pending (CreateContainerConfigError)
```

### 根因结论

**已确认的根因**：Pod 模板中引用的 `Secret aiops-case-04/workload-input` 不存在或结构中缺少名为 `unavailable-key` 的字段，导致容器化配置过程被拒绝。
- **证据**：K8s Event 明确报告找不到该键（`fact-3a9ec6aa1925`），Metric 确认了由此引发的 `CreateContainerConfigError` 状态（`fact-d2271e8741ef`）。

---

## 📊 性能统计

```text
├─ 总耗时: 57.3s
├─ 问题定位: 16.8s
├─ 并发证据采集: 33.2s
│  └─ g1 aiops-case-04/workload-6584f97c76-h4lt9: 33.2s (Evidence 25.7s, RCA 7.3s)
└─ 汇总总结: 7.4s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-h4lt9**: pod-config-error
