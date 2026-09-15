## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-h4lt9` | CreateContainerConfigError | Pod aiops-case-04/workload-6584f97c76-h4lt9 处于 Pending 状态，容器 app 因 CreateContainerConfigError 无法启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning Failed: Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` (12 次重试) | 直接指出容器启动失败的具体原因是 Secret 中缺少指定密钥 |
| 2 | K8s State | kubernetes | Pod 状态为 `Pending`，容器 `app` 重启次数为 0 | 确认为静态配置挂载故障，而非运行时崩溃或资源竞争 |
| 3 | K8s Config | kubernetes | 容器 `app` 资源请求 `CPU: 5m`, `Memory: 8Mi`；限制 `CPU: 50m`, `Memory: 32Mi` | 确认资源分配在合法范围内，排除因资源不足导致调度的可能性 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="CreateContainerConfigError"} = 1` | 指标维度直接匹配事件中的报错原因，作为量化佐证 |

**证据印证说明**：
Kubernetes 事件（#1）明确记录了 `kubelet` 挂载配置时因找不到 Secret 键值而失败。Metric 数据（#4）从监控侧确认了容器处于 `CreateContainerConfigError` 等待状态。结合 Pod 保持 `Pending` 且无重启（#2）的现象，证实故障发生在容器创建前的配置准备阶段，证据链闭环。

## 🎯 根因分析 · g1

### 因果链

```text
Secret aiops-case-04/workload-input 中缺少键 unavailable-key → kubelet 解析并挂载卷失败 → 容器 app 创建失败，状态转为 CreateContainerConfigError → Pod 无法调度进入 Running 状态，保持 Pending
```

### 根因结论

**已确认根因**：Pod `aiops-case-04/workload-6584f97c76-h4lt9` 的容器配置引用了不存在的 Secret 键。
具体而言，Secret `aiops-case-04/workload-input` 中不存在键 `unavailable-key`（见证据 #1），导致 `kubelet` 无法完成挂载操作。这直接导致容器进入 `CreateContainerConfigError` 状态，并引发 Pod 处于 `Pending` 状态（见证据 #2, #4）。

---

## 📊 性能统计

```text
├─ 总耗时: 52.8s
├─ 问题定位: 19.4s
├─ 并发证据采集: 25.4s
│  └─ g1 aiops-case-04/workload-6584f97c76-h4lt9: 25.4s (Evidence 19.9s, RCA 5.4s)
└─ 汇总总结: 8.0s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-h4lt9**: pod-config-error
